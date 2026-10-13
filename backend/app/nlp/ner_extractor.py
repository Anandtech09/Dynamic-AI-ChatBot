"""
Named Entity Recognition (NER) Extractor — Rule + Lexicon hybrid extraction.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class EntityItem:
    text: str
    label: str
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: float = 0.90


class NERExtractor:
    """
    Offline Named Entity Recognizer for conversational and technical entities.
    Extracts TECH, ORG, PERSON, DATE, EMAIL, URL, LOCATION, NUMBER entities.
    """

    KNOWN_TECH = {
        "python", "fastapi", "docker", "docker compose", "postgresql", "postgres",
        "redis", "pgvector", "sqlite", "react", "typescript", "javascript",
        "vite", "nginx", "gemini", "gpt", "bert", "langchain", "pytorch",
        "tensorflow", "sql", "git", "github", "html", "css", "tailwind",
        "rest api", "graphql", "websockets", "asyncpg", "alembic", "uvicorn",
        "pydantic", "node", "nodejs", "npm", "pip", "linux", "windows", "wsl", "wsl2",
    }

    KNOWN_ORGS = {
        "google", "google deepmind", "deepmind", "openai", "microsoft", "meta",
        "amazon", "aws", "apple", "anthropic", "github", "render", "vercel",
        "neon", "upstash", "hugging face", "huggingface", "docker inc",
    }

    KNOWN_LOCATIONS = {
        "india", "usa", "us", "uk", "california", "london", "bangalore",
        "mumbai", "delhi", "new york", "san francisco", "berlin", "tokyo", "singapore",
    }

    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+")
    NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")
    DATE_PATTERN = re.compile(
        r"\b(?:today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
        r"january|february|march|april|may|june|july|august|september|october|november|december|"
        r"\d{4}|\d{1,2}/\d{1,2}/\d{2,4})\b",
        re.IGNORECASE,
    )
    PERSON_INTRO_PATTERN = re.compile(
        r"(?:my name is|i am|call me|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
        re.IGNORECASE,
    )

    def extract(self, text: str) -> List[EntityItem]:
        """Extract all recognized named entities with offsets and labels."""
        entities: List[EntityItem] = []
        seen_spans = set()

        def add_entity(match_text: str, label: str, start: int, end: int, conf: float = 0.90):
            span = (start, end)
            if span not in seen_spans and match_text.strip():
                seen_spans.add(span)
                entities.append(EntityItem(
                    text=match_text,
                    label=label,
                    start=start,
                    end=end,
                    confidence=conf,
                ))

        # 1. Emails
        for m in self.EMAIL_PATTERN.finditer(text):
            add_entity(m.group(), "EMAIL", m.start(), m.end(), 0.98)

        # 2. URLs
        for m in self.URL_PATTERN.finditer(text):
            add_entity(m.group(), "URL", m.start(), m.end(), 0.98)

        # 3. Dates
        for m in self.DATE_PATTERN.finditer(text):
            add_entity(m.group(), "DATE", m.start(), m.end(), 0.88)

        # 4. Person from conversational intro
        for m in self.PERSON_INTRO_PATTERN.finditer(text):
            name = m.group(1)
            add_entity(name, "PERSON", m.start(1), m.end(1), 0.92)

        # 5. Tech keywords
        text_lower = text.lower()
        for tech in sorted(self.KNOWN_TECH, key=len, reverse=True):
            pattern = rf"\b{re.escape(tech)}\b"
            for m in re.finditer(pattern, text_lower):
                original_text = text[m.start():m.end()]
                add_entity(original_text, "TECH", m.start(), m.end(), 0.95)

        # 6. Organization keywords
        for org in sorted(self.KNOWN_ORGS, key=len, reverse=True):
            pattern = rf"\b{re.escape(org)}\b"
            for m in re.finditer(pattern, text_lower):
                original_text = text[m.start():m.end()]
                add_entity(original_text, "ORG", m.start(), m.end(), 0.92)

        # 7. Locations
        for loc in sorted(self.KNOWN_LOCATIONS, key=len, reverse=True):
            pattern = rf"\b{re.escape(loc)}\b"
            for m in re.finditer(pattern, text_lower):
                original_text = text[m.start():m.end()]
                add_entity(original_text, "LOCATION", m.start(), m.end(), 0.85)

        # 8. Numbers (if not part of tech/date/url)
        for m in self.NUMBER_PATTERN.finditer(text):
            # Check if already covered
            covered = any(e.start <= m.start() and m.end() <= e.end for e in entities if e.start is not None and e.end is not None)
            if not covered:
                add_entity(m.group(), "NUMBER", m.start(), m.end(), 0.80)

        # Sort by start offset
        entities.sort(key=lambda e: e.start if e.start is not None else 0)
        return entities


_ner_extractor: Optional[NERExtractor] = None


def get_ner_extractor() -> NERExtractor:
    """Return singleton NERExtractor instance."""
    global _ner_extractor
    if _ner_extractor is None:
        _ner_extractor = NERExtractor()
    return _ner_extractor
