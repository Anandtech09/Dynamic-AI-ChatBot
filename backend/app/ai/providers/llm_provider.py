"""
AI provider abstraction and Gemini implementation.

The LLMProvider protocol allows swapping Gemini for another provider later.
"""

from __future__ import annotations

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from app.core.config import get_settings

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Generate a completion. Returns {"content": str, "usage": dict}."""
        ...

    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Stream a completion token by token."""
        ...

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
    ) -> str:
        """Generate a structured JSON response for NLP extraction tasks."""
        ...


class GeminiProvider(LLMProvider):
    """Google Gemini provider using the google-generativeai SDK."""

    def __init__(self):
        settings = get_settings()
        if settings.gemini_api_key and genai is not None:
            genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self._configured = bool(settings.gemini_api_key and genai is not None)

    def _get_model(self, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 2048):
        if not genai:
            raise RuntimeError("google-generativeai package is not installed")
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config,
            system_instruction=system_prompt if system_prompt else None,
        )

    def _build_contents(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """Convert message list to Gemini content format."""
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        return contents

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        if not self._configured:
            raise RuntimeError("Gemini API key not configured")

        model = self._get_model(system_prompt, temperature, max_tokens)
        contents = self._build_contents(messages)

        start = time.monotonic()
        response = await model.generate_content_async(contents)
        elapsed_ms = int((time.monotonic() - start) * 1000)

        text = response.text if response.text else ""
        usage = {}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
            }

        return {
            "content": text,
            "usage": usage,
            "elapsed_ms": elapsed_ms,
            "model": self.model_name,
        }

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        if not self._configured:
            raise RuntimeError("Gemini API key not configured")

        model = self._get_model(system_prompt, temperature, max_tokens)
        contents = self._build_contents(messages)

        response = await model.generate_content_async(contents, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
    ) -> str:
        if not self._configured:
            raise RuntimeError("Gemini API key not configured")

        model = self._get_model(system_prompt, temperature, max_tokens=1024)
        response = await model.generate_content_async(prompt)
        return response.text if response.text else "{}"


class DemoProvider(LLMProvider):
    """Fallback provider that returns canned responses when no API key is set."""

    DEMO_RESPONSES = [
        "I'm running in demo mode. Configure a Gemini API key for real AI responses.",
        "This is a demo response. The chatbot's full capabilities require a Gemini API key.",
        "Demo mode active! Set GEMINI_API_KEY in your .env file to unlock AI-powered responses.",
    ]

    def __init__(self):
        self._counter = 0

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        response_format: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        user_msg = messages[-1]["content"] if messages else ""
        self._counter += 1
        idx = self._counter % len(self.DEMO_RESPONSES)

        response = (
            f"**[Demo Mode]** You said: *\"{user_msg[:100]}\"*\n\n"
            f"{self.DEMO_RESPONSES[idx]}\n\n"
            f"In production, I would understand your intent, analyze sentiment, "
            f"retrieve relevant knowledge, and generate a contextual response."
        )

        return {
            "content": response,
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "elapsed_ms": 50,
            "model": "demo",
        }

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        result = await self.generate(messages, system_prompt, temperature, max_tokens)
        for word in result["content"].split(" "):
            yield word + " "

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.3,
    ) -> str:
        prompt_lower = prompt.lower()
        if "title" in prompt_lower:
            return "General Conversation"
        if "summary" in prompt_lower:
            return "This conversation covers general AI queries and interactive discussions."
        return json.dumps({
            "intent": "unknown",
            "confidence": 0.5,
            "sentiment": "neutral",
            "sentiment_score": 0.5,
            "emotion": "neutral",
            "emotion_score": 0.5,
            "entities": [],
        })


def get_llm_provider() -> LLMProvider:
    """Factory: returns GeminiProvider if configured, otherwise DemoProvider."""
    settings = get_settings()
    if settings.gemini_api_key:
        return GeminiProvider()
    logger.warning("No GEMINI_API_KEY set — using DemoProvider")
    return DemoProvider()
