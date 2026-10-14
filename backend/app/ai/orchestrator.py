"""
AI Orchestrator — the central intelligence pipeline.

Coordinates: context loading → NLP analysis → RAG retrieval → tool execution
→ response generation → guardrails → metadata recording.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, AsyncIterator, Dict, List, Optional

from app.ai.guardrails import apply_guardrails
from app.ai.prompts.prompt_templates import (
    ENTITY_EXTRACTION_PROMPT,
    FOLLOW_UP_PROMPT,
    INTENT_EXTRACTION_PROMPT,
    SENTIMENT_ANALYSIS_PROMPT,
    SYSTEM_PROMPT,
    TITLE_GENERATION_PROMPT,
    SUMMARY_PROMPT,
    UNIFIED_CHAT_RESPONSE_SCHEMA_PROMPT,
    get_language_instruction,
)
from app.ai.providers import DemoProvider, LLMProvider, get_llm_provider
from app.core.config import get_settings
from app.nlp.faq_matcher import get_faq_matcher
from app.nlp.intent_classifier import get_intent_classifier
from app.nlp.ner_extractor import get_ner_extractor
from app.nlp.self_learning import get_self_learning_service
from app.nlp.sentiment_analyzer import get_sentiment_analyzer
from app.tools import ToolRegistry, create_tool_registry

logger = logging.getLogger(__name__)


def _parse_json_safe(text: str) -> Dict:
    """Attempt to parse JSON from LLM output, stripping markdown fences if present."""
    text = text.strip()
    # Remove ```json ... ``` wrappers
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from LLM: %s", text[:200])
        return {}


class OrchestratorResult:
    """Container for the full pipeline result."""

    def __init__(self):
        self.reply: str = ""
        self.intent: Optional[str] = None
        self.intent_confidence: Optional[float] = None
        self.secondary_intents: List[str] = []
        self.sentiment: Optional[str] = None
        self.sentiment_score: Optional[float] = None
        self.emotion: Optional[str] = None
        self.emotion_score: Optional[float] = None
        self.entities: List[Dict] = []
        self.sources: List[Dict] = []
        self.tools_used: List[str] = []
        self.suggestions: List[str] = []
        self.response_time_ms: int = 0
        self.token_count: int = 0
        self.model_used: str = ""
        self.is_fallback: bool = False
        self.is_error: bool = False
        self.error_code: Optional[str] = None
        self.is_demo: bool = False
        self.is_rag: bool = False
        self.is_faq: bool = False
        self.image_url: Optional[str] = None


class AIOrchestrator:
    """
    Central AI pipeline orchestrating NLP analysis, context building,
    tool execution, RAG retrieval, and response generation.
    """

    def __init__(
        self,
        llm: Optional[LLMProvider] = None,
        tool_registry: Optional[ToolRegistry] = None,
        rag_service: Any = None,
    ):
        self.llm = llm or get_llm_provider()
        self.rag_service = rag_service
        self.tool_registry = tool_registry or create_tool_registry(rag_service)
        self.settings = get_settings()
        self.is_demo = self.settings.is_demo_mode or isinstance(self.llm, DemoProvider)

        # Dedicated NLP components
        self.intent_classifier = get_intent_classifier()
        self.ner_extractor = get_ner_extractor()
        self.sentiment_analyzer = get_sentiment_analyzer()
        self.faq_matcher = get_faq_matcher()
        self.self_learning = get_self_learning_service()

    # ── Public API ───────────────────────────────────────────────────────────

    async def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        conversation_summary: str = "",
        language: str = "en",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        image_data: Optional[str] = None,
        rag_document_title: Optional[str] = None,
    ) -> OrchestratorResult:
        """
        Full pipeline: NLP analysis → FAQ match → RAG retrieval → tool execution → generate → guardrails.
        """
        result = OrchestratorResult()
        result.is_demo = self.is_demo
        start = time.monotonic()

        try:
            # 1. High-speed local NLP Pipeline (Intent, Sentiment, Emotion, NER)
            intent_res = self.intent_classifier.classify(user_message)
            result.intent = intent_res.intent
            result.intent_confidence = intent_res.confidence
            result.secondary_intents = intent_res.secondary_intents

            sent_res = self.sentiment_analyzer.analyze(user_message)
            result.sentiment = sent_res.sentiment
            result.sentiment_score = sent_res.sentiment_score
            result.emotion = sent_res.emotion
            result.emotion_score = sent_res.emotion_score

            raw_entities = self.ner_extractor.extract(user_message)
            result.entities = [
                {
                    "text": e.text,
                    "label": e.label,
                    "start": e.start,
                    "end": e.end,
                    "confidence": e.confidence,
                }
                for e in raw_entities
            ]

            # Detect explicit #rag tag in query or targeted document selection
            is_explicit_rag = any(tag in user_message.lower() for tag in ["#rag", "[rag]", "rag:"])
            if is_explicit_rag or rag_document_title:
                result.intent = "rag_search"
                result.intent_confidence = 0.98

            # 2. Pre-trained FAQ matcher (Rule + ML instant answers)
            if not is_explicit_rag and not image_data and not rag_document_title:
                faq_hit = self.faq_matcher.match(user_message)
                if faq_hit and faq_hit.confidence >= 0.65:
                    result.reply = faq_hit.answer
                    result.is_faq = True
                    result.intent = "faq_query"
                    result.intent_confidence = faq_hit.confidence
                    result.suggestions = self._build_predictive_suggestions(
                        result.intent, result.entities, faq_hit.category
                    )
                    self.self_learning.record_interaction("faq_query", result.sentiment)
                    result.response_time_ms = int((time.monotonic() - start) * 1000)
                    return result

            # 3. Tool detection & execution
            tool_results = await self._handle_tools(user_message, result.intent)
            if tool_results:
                result.tools_used = list(tool_results.keys())

            # 4. RAG retrieval (triggered if #rag tag present, rag_document_title selected, or rag_search intent)
            rag_context = ""
            rag_results = []
            clean_rag_query = re.sub(r"(?i)#rag|\[rag\]|rag:\s*", "", user_message).strip()
            if not clean_rag_query:
                clean_rag_query = user_message

            should_search_rag = is_explicit_rag or bool(rag_document_title) or result.intent == "rag_search"

            if self.rag_service and should_search_rag:
                try:
                    rag_results = await self.rag_service.search(
                        clean_rag_query,
                        top_k=3,
                        document_title=rag_document_title,
                    )
                    if rag_results:
                        result.is_rag = True
                        rag_context = "\n\n".join(
                            [
                                f"[Source: {r.get('title', 'Unknown')}]\n{r.get('content', '')}"
                                for r in rag_results
                            ]
                        )
                        result.sources = [
                            {
                                "title": r.get("title", "Unknown"),
                                "section": r.get("section", ""),
                                "score": r.get("score", 0),
                                "rrf_score": r.get("rrf_score"),
                                "recall_at_k": r.get("recall_at_k"),
                            }
                            for r in rag_results
                        ]
                except Exception as e:
                    logger.warning("RAG retrieval failed: %s", e)

            # 5. Multimodal Image Analysis handling
            image_analysis_note = ""
            if image_data:
                image_analysis_note = (
                    "\n\n📷 **Image Attachment Received**: Visual input has been passed to the multimodal engine."
                )

            # 6. Response Generation (Demo Mode vs LLM Mode)
            if self.is_demo:
                result.reply = self._generate_contextual_demo_reply(
                    user_message=user_message,
                    intent=result.intent,
                    emotion=result.emotion,
                    entities=result.entities,
                    rag_results=rag_results,
                    is_explicit_rag=is_explicit_rag,
                    clean_rag_query=clean_rag_query,
                    tool_results=tool_results,
                    image_data=image_data,
                )
                result.token_count = len(result.reply.split())
                result.model_used = "demo-local-nlp"
            else:
                # Build context and generate response via LLM with structured NLP classification
                system = self._build_system_prompt(
                    language=language,
                    emotion=result.emotion,
                    rag_context=rag_context,
                    tool_results=tool_results,
                    structured_nlp_output=True,
                )
                messages = self._build_messages(
                    conversation_history, conversation_summary, user_message
                )

                llm_result = await self.llm.generate(
                    messages=messages,
                    system_prompt=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                raw_content = llm_result["content"]
                result.token_count = llm_result.get("usage", {}).get("total_tokens", 0)
                result.model_used = llm_result.get("model", "")

                # Parse structured JSON output from LLM
                parsed = _parse_json_safe(raw_content)
                if parsed and "reply" in parsed and isinstance(parsed["reply"], str):
                    result.reply = parsed["reply"]
                    if parsed.get("intent"):
                        result.intent = parsed["intent"]
                    if parsed.get("intent_confidence") is not None:
                        result.intent_confidence = float(parsed["intent_confidence"])
                    if isinstance(parsed.get("sentiment"), dict):
                        result.sentiment = parsed["sentiment"].get("label", result.sentiment)
                        result.sentiment_score = float(parsed["sentiment"].get("score", result.sentiment_score or 0.85))
                    elif isinstance(parsed.get("sentiment"), str):
                        result.sentiment = parsed["sentiment"]
                    if isinstance(parsed.get("emotion"), dict):
                        result.emotion = parsed["emotion"].get("label", result.emotion)
                        result.emotion_score = float(parsed["emotion"].get("score", result.emotion_score or 0.85))
                    elif isinstance(parsed.get("emotion"), str):
                        result.emotion = parsed["emotion"]
                    if parsed.get("entities") and isinstance(parsed["entities"], list):
                        result.entities = parsed["entities"]
                    if parsed.get("suggestions") and isinstance(parsed["suggestions"], list):
                        result.suggestions = parsed["suggestions"]
                else:
                    result.reply = raw_content

                # Apply guardrails
                result.reply = apply_guardrails(result.reply)

            # 7. Predictive Follow-up Suggestions (generate fallback if not provided by LLM)
            if not result.suggestions:
                result.suggestions = self._build_predictive_suggestions(
                    result.intent, result.entities, rag_sources=result.sources
                )

            # 8. Reinforcement Learning / Self-Learning update
            self.self_learning.record_interaction(result.intent, result.sentiment)

        except Exception as e:
            logger.error("Orchestrator error: %s", e, exc_info=True)
            result.reply = "I'm sorry, I encountered an issue processing your request. Please try again."
            result.is_fallback = True
            result.is_error = True
            result.error_code = type(e).__name__

        result.response_time_ms = int((time.monotonic() - start) * 1000)
        return result

    async def process_message_stream(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        conversation_summary: str = "",
        language: str = "en",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """Stream response tokens. NLP analysis happens before streaming starts."""
        system = self._build_system_prompt(language)
        messages = self._build_messages(
            conversation_history, conversation_summary, user_message
        )

        async for chunk in self.llm.generate_stream(
            messages=messages,
            system_prompt=system,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield chunk

    async def generate_title(self, first_message: str) -> str:
        """Generate a concise conversation title from the first message."""
        clean_msg = re.sub(r'#\w+\s*', '', first_message).strip()
        clean_msg = re.sub(r'["\'{}]', '', clean_msg).strip()
        if not clean_msg:
            return "New Chat"

        if not self.is_demo:
            try:
                prompt = TITLE_GENERATION_PROMPT.format(message=clean_msg)
                result = await self.llm.generate(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=25,
                )
                title = result.get("content", "").strip().strip('"').strip("'").strip()
                if title and not title.startswith("{") and not title.startswith("[") and "intent" not in title and len(title) > 2:
                    return title[:60]
            except Exception as e:
                logger.warning("Gemini title generation failed: %s", e)

        # Fallback / Demo mode: clean title from first 5-6 words
        words = clean_msg.split()
        if len(words) <= 5:
            title = " ".join(words)
        else:
            title = " ".join(words[:5]) + "..."
        return title[:50].capitalize()

    async def generate_summary(self, conversation_text: str) -> str:
        """Generate a conversation summary for context compression."""
        try:
            prompt = SUMMARY_PROMPT.format(conversation=conversation_text)
            return await self.llm.generate_structured(prompt)
        except Exception:
            return ""

    # ── Private Helpers ──────────────────────────────────────────────────────

    async def _analyse_message(self, message: str) -> Dict:
        """Run intent + sentiment + entity extraction via structured LLM calls."""
        if self.is_demo:
            return {
                "primary_intent": "unknown",
                "confidence": 0.5,
                "sentiment": "neutral",
                "sentiment_score": 0.5,
                "emotion": "neutral",
                "emotion_score": 0.5,
                "entities": [],
            }

        combined = {}
        try:
            # Intent extraction
            intent_prompt = INTENT_EXTRACTION_PROMPT.format(message=message)
            intent_raw = await self.llm.generate_structured(intent_prompt)
            intent_data = _parse_json_safe(intent_raw)
            combined.update(intent_data)
        except Exception as e:
            logger.warning("Intent extraction failed: %s", e)

        try:
            # Sentiment + emotion
            sent_prompt = SENTIMENT_ANALYSIS_PROMPT.format(message=message)
            sent_raw = await self.llm.generate_structured(sent_prompt)
            sent_data = _parse_json_safe(sent_raw)
            combined.update(sent_data)
        except Exception as e:
            logger.warning("Sentiment analysis failed: %s", e)

        try:
            # Entity extraction
            ent_prompt = ENTITY_EXTRACTION_PROMPT.format(message=message)
            ent_raw = await self.llm.generate_structured(ent_prompt)
            ent_data = _parse_json_safe(ent_raw)
            combined["entities"] = ent_data.get("entities", [])
        except Exception as e:
            logger.warning("Entity extraction failed: %s", e)

        return combined

    async def _handle_tools(self, message: str, intent: Optional[str]) -> Dict[str, Any]:
        """Detect and execute tools based on intent and message content."""
        if not self.settings.enable_tools:
            return {}

        results = {}
        msg_lower = message.lower()

        # Calculator: detect math expressions
        if intent == "calculation" or any(
            op in msg_lower for op in ["calculate", "compute", "what is", "how much is"]
        ):
            # Try to extract a math expression
            math_match = re.search(
                r'[\d]+[\s]*[\+\-\*\/\^]+[\s]*[\d]+(?:[\s]*[\+\-\*\/\^]+[\s]*[\d]+)*',
                message
            )
            if math_match:
                calc_result = await self.tool_registry.execute(
                    "calculator", expression=math_match.group()
                )
                if "error" not in calc_result:
                    results["calculator"] = calc_result

        # DateTime
        if any(kw in msg_lower for kw in ["what time", "current time", "what date", "today's date", "what day"]):
            dt_result = await self.tool_registry.execute("datetime")
            results["datetime"] = dt_result

        return results

    def _build_system_prompt(
        self,
        language: str = "en",
        emotion: Optional[str] = None,
        rag_context: str = "",
        tool_results: Optional[Dict] = None,
        structured_nlp_output: bool = False,
    ) -> str:
        """Assemble the full system prompt with all context."""
        parts = [SYSTEM_PROMPT]
        parts.append(get_language_instruction(language))

        if structured_nlp_output:
            parts.append(UNIFIED_CHAT_RESPONSE_SCHEMA_PROMPT)

        if emotion and emotion not in ("neutral", "unknown"):
            parts.append(
                f"\nThe user's emotional state appears to be: {emotion}. "
                "Adapt your tone appropriately — be empathetic if they are frustrated or sad, "
                "enthusiastic if they are excited."
            )

        if rag_context:
            parts.append(
                "\n--- KNOWLEDGE BASE CONTEXT ---\n"
                "Use the following retrieved information to ground your answer. "
                "Cite the source when using this information. "
                "If the information doesn't answer the question, say so.\n\n"
                f"{rag_context}\n--- END CONTEXT ---"
            )

        if tool_results:
            tool_text = "\n--- TOOL RESULTS ---\n"
            for name, data in tool_results.items():
                tool_text += f"Tool: {name}\nResult: {json.dumps(data)}\n\n"
            tool_text += "--- END TOOL RESULTS ---\n"
            tool_text += "Incorporate these tool results naturally into your response."
            parts.append(tool_text)

        return "\n\n".join(parts)

    def _build_messages(
        self,
        conversation_history: List[Dict[str, str]],
        summary: str,
        current_message: str,
    ) -> List[Dict[str, str]]:
        """Build the message list with bounded context window."""
        messages = []

        # Add summary if available
        if summary:
            messages.append({
                "role": "user",
                "content": f"[Previous conversation summary: {summary}]"
            })
            messages.append({
                "role": "assistant",
                "content": "I understand the context. Please continue."
            })

        # Add recent history (bounded)
        max_msgs = self.settings.max_context_messages
        recent = conversation_history[-max_msgs:] if len(conversation_history) > max_msgs else conversation_history
        messages.extend(recent)

        # Add current message
        messages.append({"role": "user", "content": current_message})
        return messages

    def _generate_contextual_demo_reply(
        self,
        user_message: str,
        intent: Optional[str],
        emotion: Optional[str],
        entities: List[Dict],
        rag_results: List[Dict],
        is_explicit_rag: bool,
        clean_rag_query: str,
        tool_results: Optional[Dict],
        image_data: Optional[str],
    ) -> str:
        """Synthesize rich, grounded response for demo/local mode."""
        # 1. RAG retrieval match
        if rag_results:
            top_doc = rag_results[0]
            sources_list = ", ".join([f"`{r.get('title', 'Document')}`" for r in rag_results])
            return (
                f"### 📚 Knowledge Base Retrieval [RAG: {top_doc.get('title', 'Document')}]\n\n"
                f"{top_doc.get('content', '')}\n\n"
                f"---\n"
                f"**Citations**: {sources_list} | **Vector Store**: PostgreSQL (pgvector) | **Confidence**: {top_doc.get('score', 0.92):.2f}\n"
                f"💡 *Retrieved via semantic embedding matching on query: \"{clean_rag_query}\"*"
            )

        # 2. Explicit #rag tag query with no document match
        if is_explicit_rag:
            return (
                f"### 🔍 RAG Knowledge Search\n\n"
                f"No indexed documents directly matched your query: *\"{clean_rag_query}\"* in the vector store.\n\n"
                f"**How to use RAG**:\n"
                f"1. Click the **Attach Document** (📄) icon in the chat input.\n"
                f"2. Select a `.txt`, `.pdf`, `.md`, or `.csv` file to chunk and index.\n"
                f"3. Query again using `#rag your query` to pull answers grounded in your uploaded documents!"
            )

        # 3. Multimodal image query
        if image_data:
            return (
                f"### 🖼️ Multimodal Vision Analysis\n\n"
                f"Image input received and parsed via the multimodal pipeline.\n\n"
                f"- **Prompt**: *\"{user_message}\"*\n"
                f"- **Vision Engine**: Active (Gemini Vision / Multimodal Processor)\n"
                f"- **Detected Entities**: {', '.join([e.get('text', '') for e in entities]) or 'None'}\n\n"
                f"In production mode with `GEMINI_API_KEY`, Gemini 1.5 Flash generates comprehensive visual scene analysis, optical character recognition (OCR), and contextual answers."
            )

        # 4. Tool results
        if tool_results:
            if "calculator" in tool_results:
                calc = tool_results["calculator"]
                return f"🔢 **Calculation Result**: `{calc.get('expression', '')}` = **{calc.get('result', '')}**"
            if "datetime" in tool_results:
                dt = tool_results["datetime"]
                return f"🕒 **Current Date & Time**: **{dt.get('formatted', '')}** ({dt.get('timezone', 'UTC')})"

        # 5. Greeting or general conversational
        if intent == "greeting":
            return (
                "👋 **Hello! Welcome to the Dynamic AI Chatbot.**\n\n"
                "I am equipped with:\n"
                "- 🧠 **Local NLP Pipeline**: Real-time Intent Recognition, NER, Sentiment & Emotion analysis.\n"
                "- 📚 **Vector RAG**: PostgreSQL pgvector document chunking & semantic search (try `#rag <topic>`).\n"
                "- 🎙️ **Voice & Vision**: Speech-to-text recording, Text-to-speech, and Image analysis.\n"
                "- 🔄 **Self-Learning (RLHF)**: Learns policy weights from your thumbs-up/down ratings.\n\n"
                "How can I assist you today?"
            )

        if intent == "farewell":
            return "Goodbye! Have a great day ahead! Feel free to return anytime if you have more questions."

        if intent == "help":
            return (
                "### ℹ️ How to Use This Chatbot\n\n"
                "- **Search Knowledge (RAG)**: Type `#rag <query>` or click the **#RAG** button to query uploaded docs.\n"
                "- **Upload Document**: Click the 📄 icon to chunk and index custom PDF/TXT/MD/CSV files.\n"
                "- **Voice Input**: Click the 🎙️ icon to speak your prompt.\n"
                "- **Image Analysis**: Click the 🖼️ icon to upload an image for multimodal analysis.\n"
                "- **Rate Responses**: Use 👍 / 👎 to train the RLHF reinforcement learning model!"
            )

        # Default contextual response
        emotion_note = f" (Tone: {emotion})" if emotion and emotion != "neutral" else ""
        entity_str = f" Entities identified: {', '.join([e['text'] for e in entities])}." if entities else ""
        return (
            f"**[Dynamic Chatbot]**{emotion_note}\n\n"
            f"I processed your query with intent **'{intent}'** (confidence {0.85:.2f}).{entity_str}\n\n"
            f"You can query the RAG knowledge base by including `#rag`, upload custom documents for chunking, "
            f"or ask structured questions about machine learning, NLP, and system architecture."
        )

    def _build_predictive_suggestions(
        self,
        intent: Optional[str] = None,
        entities: Optional[List[Dict]] = None,
        category: str = "",
        rag_sources: Optional[List[Dict]] = None,
    ) -> List[str]:
        """Generate smart predictive suggestions based on intent and entities."""
        suggestions = []

        if rag_sources and len(rag_sources) > 0:
            top_title = rag_sources[0].get("title", "document")
            suggestions.append(f"Can you summarize key points from {top_title}?")
            suggestions.append("How do I upload more documents to RAG?")
            suggestions.append("Explain the technical architecture of this chatbot")
            return suggestions

        if intent == "rag_search":
            return [
                "Summarize retrieved knowledge base documents",
                "How does PostgreSQL pgvector chunking and embedding work?",
                "Upload a PDF or TXT document to search",
            ]

        if intent == "greeting":
            return [
                "What features does this chatbot support?",
                "Search knowledge base with #rag",
                "How does the NLP pipeline work?",
            ]

        if intent == "technical":
            return [
                "Show me code architecture for the backend",
                "How does RLHF self-learning adapt over time?",
                "What embeddings are used in pgvector?",
            ]

        if intent == "faq_query":
            return [
                "What NLP models and features are running?",
                "How do I upload custom documents for RAG?",
                "Show system analytics and response stats",
            ]

        # Entity-based suggestion
        if entities and len(entities) > 0:
            first_ent = entities[0].get("text", "")
            if first_ent:
                suggestions.append(f"Tell me more about {first_ent}")

        suggestions.extend([
            "Search knowledge base with #rag",
            "What features does this chatbot support?",
            "How does sentiment analysis and emotion detection work?",
        ])
        return suggestions[:3]

    async def _generate_suggestions(self, last_response: str) -> List[str]:
        """Generate follow-up question suggestions."""
        try:
            topic = last_response[:200]
            prompt = FOLLOW_UP_PROMPT.format(topic=topic)
            raw = await self.llm.generate_structured(prompt)
            data = _parse_json_safe(raw)
            suggestions = data.get("suggestions", [])
            return suggestions[:3]
        except Exception:
            return self._build_predictive_suggestions()
