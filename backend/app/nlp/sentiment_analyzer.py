"""
Sentiment & Emotion Analyzer — Lexicon + VADER-inspired rule-based sentiment and multi-class emotion detection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class SentimentScore:
    label: str  # positive, neutral, negative
    score: float  # 0.0 to 1.0 confidence
    compound: float  # -1.0 to +1.0


@dataclass
class EmotionScore:
    label: str  # joy, curiosity, anger, sadness, surprise, fear, neutral
    score: float  # 0.0 to 1.0


@dataclass
class SentimentAnalysisResult:
    sentiment: str
    sentiment_score: float
    emotion: str
    emotion_score: float


class SentimentAnalyzer:
    """
    Offline Sentiment and Emotion Analyzer with negation detection,
    booster words, and multi-class emotion classification.
    """

    POSITIVE_WORDS = {
        "good": 1.5, "great": 2.0, "excellent": 2.5, "awesome": 2.5, "amazing": 2.5,
        "love": 2.5, "like": 1.0, "best": 2.0, "fantastic": 2.5, "helpful": 1.8,
        "perfect": 2.2, "wonderful": 2.2, "happy": 1.8, "glad": 1.5, "thanks": 1.5,
        "thank": 1.5, "appreciate": 1.8, "super": 1.8, "brilliant": 2.2, "nice": 1.2,
        "cool": 1.2, "faster": 1.2, "improved": 1.5, "solved": 1.8, "works": 1.2,
        "success": 2.0, "delight": 2.0, "pleased": 1.5, "flawless": 2.5, "clean": 1.2,
    }

    NEGATIVE_WORDS = {
        "bad": -1.5, "terrible": -2.5, "horrible": -2.5, "awful": -2.5, "hate": -2.5,
        "poor": -1.5, "wrong": -1.8, "useless": -2.2, "unhelpful": -2.0, "slow": -1.2,
        "broken": -2.0, "bug": -1.5, "error": -1.5, "fail": -2.0, "failed": -2.0,
        "annoying": -1.8, "frustrated": -2.0, "frustrating": -2.0, "angry": -2.0,
        "sad": -1.8, "confused": -1.2, "stuck": -1.5, "crash": -2.2, "crashed": -2.2,
        "worse": -1.8, "worst": -2.5, "issue": -1.2, "problem": -1.5, "disaster": -2.5,
    }

    NEGATION_WORDS = {"not", "never", "no", "without", "hardly", "barely", "isn't", "aren't", "wasn't", "weren't", "don't", "doesn't", "didn't", "won't"}
    BOOSTER_WORDS = {"very": 1.5, "extremely": 2.0, "super": 1.8, "really": 1.5, "absolutely": 2.0, "completely": 1.8, "so": 1.3}

    EMOTION_LEXICONS = {
        "joy": {"happy", "glad", "delighted", "love", "awesome", "great", "excellent", "wonderful", "enjoy", "fun", "pleased", "hooray", "yay"},
        "curiosity": {"how", "why", "what", "where", "when", "curious", "wonder", "explain", "learn", "tell", "explore", "know", "question"},
        "anger": {"angry", "hate", "mad", "furious", "annoyed", "frustrated", "terrible", "worst", "damn", "stupid", "idiot", "garbage"},
        "sadness": {"sad", "depressed", "unhappy", "sorrow", "regret", "lost", "fail", "failed", "unfortunate", "disappointed", "hopeless"},
        "surprise": {"wow", "whoa", "unexpected", "surprise", "surprised", "shocking", "unbelievable", "omg", "incredible"},
        "fear": {"afraid", "scared", "fear", "danger", "risky", "vulnerability", "threat", "worried", "panic"},
    }

    def analyze(self, text: str) -> SentimentAnalysisResult:
        """Run complete sentiment and emotion analysis pipeline."""
        sent = self.analyze_sentiment(text)
        emot = self.analyze_emotion(text)
        return SentimentAnalysisResult(
            sentiment=sent.label,
            sentiment_score=sent.score,
            emotion=emot.label,
            emotion_score=emot.score,
        )

    def analyze_sentiment(self, text: str) -> SentimentScore:
        """Calculate sentiment polarity and confidence."""
        words = re.findall(r"\b\w+\b", text.lower())
        if not words:
            return SentimentScore(label="neutral", score=0.5, compound=0.0)

        total_score = 0.0
        word_count = len(words)

        for i, word in enumerate(words):
            score = 0.0
            if word in self.POSITIVE_WORDS:
                score = self.POSITIVE_WORDS[word]
            elif word in self.NEGATIVE_WORDS:
                score = self.NEGATIVE_WORDS[word]

            if score != 0.0:
                # Check for preceding negation in window of 3 words
                prev_window = words[max(0, i - 3):i]
                has_negation = any(nw in prev_window for nw in self.NEGATION_WORDS)
                if has_negation:
                    score = -score * 0.75

                # Check for preceding booster words
                for bw, multiplier in self.BOOSTER_WORDS.items():
                    if bw in prev_window:
                        score *= multiplier

                total_score += score

        # Normalized compound score between -1.0 and 1.0
        normalized = total_score / (abs(total_score) + 15.0) if total_score != 0 else 0.0

        if normalized >= 0.15:
            label = "positive"
            conf = min(0.98, 0.60 + abs(normalized) * 0.40)
        elif normalized <= -0.15:
            label = "negative"
            conf = min(0.98, 0.60 + abs(normalized) * 0.40)
        else:
            label = "neutral"
            conf = 0.65

        return SentimentScore(
            label=label,
            score=round(conf, 2),
            compound=round(normalized, 3),
        )

    def analyze_emotion(self, text: str) -> EmotionScore:
        """Detect dominant emotion with confidence score."""
        words = set(re.findall(r"\b\w+\b", text.lower()))
        if not words:
            return EmotionScore(label="neutral", score=0.5)

        emotion_hits: Dict[str, int] = {}
        for emotion, lexicon in self.EMOTION_LEXICONS.items():
            hits = len(words.intersection(lexicon))
            if hits > 0:
                emotion_hits[emotion] = hits

        # Check for curiosity indicators like questions
        if "?" in text:
            emotion_hits["curiosity"] = emotion_hits.get("curiosity", 0) + 2

        if not emotion_hits:
            return EmotionScore(label="neutral", score=0.60)

        sorted_emotions = sorted(emotion_hits.items(), key=lambda x: x[1], reverse=True)
        top_emotion, hit_count = sorted_emotions[0]
        conf = min(0.95, 0.55 + hit_count * 0.15)

        return EmotionScore(label=top_emotion, score=round(conf, 2))

    detect_emotion = analyze_emotion


_sentiment_analyzer: Optional[SentimentAnalyzer] = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Return singleton SentimentAnalyzer instance."""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer
