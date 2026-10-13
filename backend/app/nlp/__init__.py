"""
NLP Engine — Intent Classification, NER, Sentiment/Emotion, FAQ Matching, and Self-Learning.
"""

from app.nlp.intent_classifier import IntentClassifier, IntentResult
from app.nlp.ner_extractor import NERExtractor, EntityItem
from app.nlp.sentiment_analyzer import SentimentAnalyzer, SentimentScore, EmotionScore
from app.nlp.faq_matcher import FAQMatcher, FAQMatch
from app.nlp.self_learning import SelfLearningService

__all__ = [
    "IntentClassifier",
    "IntentResult",
    "NERExtractor",
    "EntityItem",
    "SentimentAnalyzer",
    "SentimentScore",
    "EmotionScore",
    "FAQMatcher",
    "FAQMatch",
    "SelfLearningService",
]
