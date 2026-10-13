"""
Unit tests for dedicated NLP pipeline and RAG services.
"""

import pytest
from app.nlp.intent_classifier import IntentClassifier
from app.nlp.ner_extractor import NERExtractor
from app.nlp.sentiment_analyzer import SentimentAnalyzer
from app.nlp.faq_matcher import FAQMatcher
from app.nlp.self_learning import SelfLearningService
from app.services.rag_service import RAGService
from app.db.database import init_db


def test_intent_classifier():
    classifier = IntentClassifier()

    # Explicit RAG tag
    rag_res = classifier.classify("Can you tell me about the architecture #rag please?")
    assert rag_res.intent == "rag_search"
    assert rag_res.confidence >= 0.95

    # Greeting
    greet_res = classifier.classify("Hello there! Good morning")
    assert greet_res.intent == "greeting"

    # Calculation
    calc_res = classifier.classify("What is 45 * 12 + 10?")
    assert calc_res.intent == "calculation"

    # Feedback positive
    fb_res = classifier.classify("That was very helpful, thank you so much!")
    assert fb_res.intent in ("feedback_positive", "greeting")


def test_ner_extractor():
    extractor = NERExtractor()
    text = "John Doe contacted support@example.com about Python and FastAPI in New York on 2026-10-12 via https://example.com"
    entities = extractor.extract(text)
    
    labels = {e.label for e in entities}
    assert "EMAIL" in labels
    assert "URL" in labels
    assert "TECH" in labels
    assert "DATE" in labels

    # Check extracted values
    tech_entities = [e.text for e in entities if e.label == "TECH"]
    assert any("python" in t.lower() or "fastapi" in t.lower() for t in tech_entities)
    email_entities = [e.text for e in entities if e.label == "EMAIL"]
    assert "support@example.com" in email_entities


def test_sentiment_analyzer():
    analyzer = SentimentAnalyzer()

    # Positive joy
    pos_res = analyzer.analyze("I am thrilled and super happy with this amazing chatbot!")
    assert pos_res.sentiment == "positive"
    assert pos_res.emotion in ("joy", "curiosity")
    assert pos_res.sentiment_score > 0.6

    # Negative frustration
    neg_res = analyzer.analyze("This is terrible, completely broken and frustrating!")
    assert neg_res.sentiment == "negative"
    assert neg_res.emotion in ("anger", "sadness")
    assert neg_res.sentiment_score >= 0.5

    # Neutral curiosity question
    cur_res = analyzer.analyze("How does the vector database store text embeddings?")
    assert cur_res.emotion == "curiosity"


def test_faq_matcher():
    matcher = FAQMatcher()

    # Exact or near pattern match
    match = matcher.match("What is this chatbot and what does it do?")
    assert match is not None
    assert match.confidence >= 0.60
    assert "Dynamic AI Chatbot" in match.answer

    # RAG question
    match_rag = matcher.match("How does RAG work in this chatbot?")
    assert match_rag is not None
    assert "Retrieval-Augmented Generation" in match_rag.answer


def test_self_learning_service(tmp_path):
    # Use a custom state file in tmp_path
    state_file = tmp_path / "learning_test.json"
    service = SelfLearningService(state_file=str(state_file))

    service.record_interaction("technical", "positive")
    reward = service.record_feedback(rating=5, intent="technical")
    assert reward == 1.0

    neg_reward = service.record_feedback(rating=1, intent="calculation")
    assert neg_reward == -1.0

    stats = service.get_stats()
    assert stats["total_feedback"] == 2
    assert "technical" in stats["policy_weights"]
    assert stats["policy_weights"]["technical"] > 1.0


@pytest.mark.asyncio
async def test_rag_service():
    try:
        await init_db()
    except Exception:
        pytest.skip("PostgreSQL pgvector database not reachable from test environment")

    rag = RAGService()

    # Index sample document content
    content = "Dynamic AI Chatbot features PostgreSQL pgvector search with chunking and token window overlap."
    await rag.index_document(
        title="Test Knowledge Doc",
        content=content,
        metadata={"category": "test"}
    )

    docs = await rag.list_documents()
    assert any(d["title"] == "Test Knowledge Doc" for d in docs)

    # Search
    results = await rag.search("PostgreSQL pgvector search", top_k=2)
    assert len(results) > 0
    assert any("Test Knowledge Doc" in r["title"] for r in results)
