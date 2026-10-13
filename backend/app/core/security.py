"""
Security utilities — rate limiting, input sanitisation, CORS helpers.
"""

from __future__ import annotations

import hashlib
import re
import time
from typing import Optional

from app.core.config import get_settings


def sanitize_input(text: str) -> str:
    """Strip leading/trailing whitespace and collapse internal whitespace runs."""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def validate_message_length(text: str) -> bool:
    """Return True if the message is within the configured limit."""
    return 0 < len(text) <= get_settings().max_message_length


def hash_ip(ip: str) -> str:
    """One-way hash of client IP for privacy-conscious rate-limit keys."""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


# ── Prompt-injection defence heuristics ──────────────────────────────────────

_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"show\s+(me\s+)?(your\s+)?api\s*key",
    r"print\s+(your\s+)?environment\s+variables",
    r"disregard\s+(all\s+)?prior\s+instructions",
]

_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS]


def detect_prompt_injection(text: str) -> bool:
    """Return True if text matches known prompt-injection patterns."""
    for pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            return True
    return False
