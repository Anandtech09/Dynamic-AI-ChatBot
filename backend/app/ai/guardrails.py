"""
Response guardrails — post-processing safety checks on LLM output.
"""

from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# Patterns that should never appear in AI responses
_BLOCKED_PATTERNS = [
    r"(?i)my\s+api\s*key\s+is",
    r"(?i)here\s+is\s+(my|the)\s+system\s+prompt",
    r"(?i)GEMINI_API_KEY\s*=",
    r"(?i)DATABASE_URL\s*=",
    r"(?i)SECRET_KEY\s*=",
    r"sk-[a-zA-Z0-9]{20,}",  # OpenAI-style keys
    r"AIza[a-zA-Z0-9_-]{35}",  # Google API key pattern
]

_COMPILED = [re.compile(p) for p in _BLOCKED_PATTERNS]


def apply_guardrails(response: str) -> str:
    """
    Check the LLM response for leaked secrets or blocked content.
    Returns the sanitised response.
    """
    for pattern in _COMPILED:
        if pattern.search(response):
            logger.warning("Guardrail triggered — blocked pattern found in response")
            return (
                "I'm sorry, I can't share that information. "
                "Is there something else I can help you with?"
            )

    # Truncate excessively long responses
    if len(response) > 15000:
        response = response[:15000] + "\n\n*[Response truncated due to length]*"

    return response
