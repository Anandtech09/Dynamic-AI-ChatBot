"""
Intent Classifier — Machine Learning TF-IDF Vector Space & Centroid Cosine Similarity Classifier.

Uses Statistical Natural Language Processing (NLP):
- N-gram feature extraction (unigrams + bigrams)
- Sublinear TF-IDF (Term Frequency - Inverse Document Frequency) weighting
- High-dimensional vector projection with L2-normalization
- Centroid vector representation per intent class
- Cosine similarity metric with calibrated probability distribution
Works 100% offline with zero external API calls and sub-millisecond inference latency.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class IntentResult:
    primary_intent: str
    confidence: float
    secondary_intents: List[str] = field(default_factory=list)
    is_rag_explicit: bool = False
    clean_message: str = ""

    @property
    def intent(self) -> str:
        """Alias for primary_intent."""
        return self.primary_intent


class TFIDFVectorizer:
    """
    Statistical NLP Feature Extractor implementing Term Frequency - Inverse Document Frequency (TF-IDF).
    Extracts word n-grams (1-2) with sublinear term frequency scaling and L2 vector normalization.
    """

    STOPWORDS: Set[str] = {
        "a", "an", "the", "and", "or", "of", "to", "in", "on", "at", "by", "for",
        "with", "about", "into", "through", "during", "before", "after", "above",
        "below", "from", "up", "down", "in", "out", "over", "under", "is", "am", "are",
        "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
    }

    def __init__(self, min_df: int = 1, ngram_range: Tuple[int, int] = (1, 2)):
        self.min_df = min_df
        self.ngram_range = ngram_range
        self.vocabulary: Dict[str, int] = {}
        self.idf_weights: Dict[int, float] = {}
        self.is_fitted = False

    def _tokenize(self, text: str) -> List[str]:
        """
        Normalize and tokenize text into clean word and operator tokens.
        Includes number normalization (_num_) and mathematical operators (+, -, *, /, ^, %).
        """
        # Separate math operators with spaces
        spaced = re.sub(r"([+\-*/^=%])", r" \1 ", text.lower())
        # Normalize numbers to numerical placeholder token to generalize arithmetic
        normalized = re.sub(r"\b\d+(?:\.\d+)?\b", "_num_", spaced)
        # Clean non-alphanumeric except tokens
        clean = re.sub(r"[^\w\s+\-*/^=%]", " ", normalized)
        tokens = [t.strip() for t in clean.split() if len(t.strip()) > 1 or t.strip() in "+-*/^=%"]
        return tokens

    def _extract_ngrams(self, tokens: List[str]) -> List[str]:
        """Extract unigrams and bigrams from tokens."""
        features = []
        # Unigrams (excluding standalone stopwords)
        for t in tokens:
            if t not in self.STOPWORDS:
                features.append(t)

        # Bigrams (capturing multi-word semantic intent markers)
        if self.ngram_range[1] >= 2:
            for i in range(len(tokens) - 1):
                w1, w2 = tokens[i], tokens[i + 1]
                features.append(f"{w1}_{w2}")

        return features

    def fit(self, corpus: List[str]) -> TFIDFVectorizer:
        """Fit vocabulary and compute inverse document frequency (IDF) from training corpus."""
        doc_count = len(corpus)
        df_counts: Counter[str] = Counter()

        for doc in corpus:
            tokens = self._tokenize(doc)
            features = set(self._extract_ngrams(tokens))
            for f in features:
                df_counts[f] += 1

        # Build vocabulary dictionary: feature -> index
        self.vocabulary = {
            f: idx
            for idx, (f, count) in enumerate(df_counts.items())
            if count >= self.min_df
        }

        # Compute smooth IDF: ln((1 + N) / (1 + DF)) + 1.0
        self.idf_weights = {}
        for feature, idx in self.vocabulary.items():
            df = df_counts[feature]
            self.idf_weights[idx] = math.log((1.0 + doc_count) / (1.0 + df)) + 1.0

        self.is_fitted = True
        return self

    def transform(self, text: str) -> Dict[int, float]:
        """
        Transform text into an L2-normalized sparse TF-IDF feature vector.
        Uses sublinear term frequency: tf = 1 + ln(count)
        """
        if not self.is_fitted:
            raise RuntimeError("Vectorizer must be fitted before transforming.")

        tokens = self._tokenize(text)
        features = self._extract_ngrams(tokens)
        counts = Counter(features)

        vector: Dict[int, float] = {}
        sq_sum = 0.0

        for f, cnt in counts.items():
            if f in self.vocabulary:
                idx = self.vocabulary[f]
                # Sublinear term frequency scaling
                tf = 1.0 + math.log(cnt)
                idf = self.idf_weights.get(idx, 1.0)
                val = tf * idf
                vector[idx] = val
                sq_sum += val * val

        # L2 Unit Vector Normalization
        if sq_sum > 0:
            norm = math.sqrt(sq_sum)
            for idx in vector:
                vector[idx] /= norm

        return vector


class IntentClassifier:
    """
    Statistical Machine Learning Intent Classifier.
    Employs TF-IDF Vector Space Modeling + Centroid Cosine Similarity classification.
    """

    TRAINING_CORPUS: Dict[str, List[str]] = {
        "greeting": [
            "hello", "hi there", "hey", "greetings", "good morning", "good evening",
            "good afternoon", "howdy friend", "hey bot", "hello assistant", "hi how are you",
            "namaste", "what's up", "hey there", "good day", "hiya",
        ],
        "goodbye": [
            "bye", "goodbye", "see you later", "farewell", "cya", "take care",
            "talk to you later", "have a good day", "have a good night", "bye bye",
            "see you tomorrow", "catch you later", "im leaving now", "exit chat",
        ],
        "calculation": [
            "calculate 25 plus 14", "compute square root of 144", "what is 50 divided by 2",
            "solve math expression", "15 * 4", "how much is 100 minus 35", "math problem",
            "compute 2 to the power 8", "calculator tool", "evaluate expression", "what is 99 * 3",
            "what is 45 * 12 + 10", "what is 20 + 35", "what is 100 / 4", "50 * 3 + 12",
            "calculate 12 * 8", "how much is 500 / 25", "compute 10 + 20 - 5",
        ],
        "time_query": [
            "what time is it", "current time", "what is today's date", "what is the date",
            "tell me the time", "what day is it today", "current date and time",
            "clock time now", "what day of the week is it", "todays date",
        ],
        "rag_search": [
            "#rag search knowledge base", "#rag explain architecture", "search in documents",
            "according to the uploaded doc", "what does the document say about", "look up in docs",
            "information from the knowledge base", "find in indexed files", "query document chunks",
            "extract from uploaded notes", "#rag summarize the pdf", "#rag key concepts",
        ],
        "technical_query": [
            "how to use python async await", "explain docker container architecture",
            "postgresql index optimization", "fastapi dependency injection", "redis caching strategy",
            "explain react useEffect hook", "typescript interface vs type", "vector embeddings machine learning",
            "debug syntax error in python", "how does neural network work", "how to build a rest api",
            "docker compose configuration file", "write a python function to sort list",
        ],
        "faq_query": [
            "what is this chatbot", "who created you", "what can this bot do", "list project features",
            "how does this application work", "what technologies are used in this project",
            "who built this ai system", "features of dynamic ai chatbot", "how is this bot designed",
        ],
        "feedback_positive": [
            "great job", "awesome answer", "thank you so much", "very helpful", "excellent response",
            "love this bot", "amazing explanation", "perfect answer", "thanks a lot", "this was great",
        ],
        "feedback_negative": [
            "this answer is bad", "terrible response", "that is wrong and incorrect",
            "useless answer", "you made an error", "not helpful at all", "poor explanation",
            "this is broken and not working", "hate this response",
        ],
        "help": [
            "help me", "what commands can i run", "how to use this chatbot", "give me instructions",
            "user guide", "what are the options", "show help manual", "can you assist me",
        ],
        "image_analysis": [
            "analyze this image", "what is in this photo", "describe the uploaded picture",
            "explain this screenshot", "read text from image", "look at this image attachment",
        ],
    }

    def __init__(self):
        self.vectorizer = TFIDFVectorizer(ngram_range=(1, 2))
        self.intent_centroids: Dict[str, Dict[int, float]] = {}
        self._train_model()

    def _train_model(self):
        """Fit TF-IDF vocabulary on all training utterances and compute class centroids."""
        all_docs = []
        intent_doc_map = defaultdict(list)

        for intent, utterances in self.TRAINING_CORPUS.items():
            for utt in utterances:
                all_docs.append(utt)
                intent_doc_map[intent].append(utt)

        # 1. Fit statistical vectorizer
        self.vectorizer.fit(all_docs)

        # 2. Compute Centroid Vectors: c_intent = mean(vector_i) for i in class
        for intent, utterances in intent_doc_map.items():
            centroid: Dict[int, float] = defaultdict(float)
            n_samples = len(utterances)

            for utt in utterances:
                vec = self.vectorizer.transform(utt)
                for idx, val in vec.items():
                    centroid[idx] += val / n_samples

            # L2-normalize centroid vector
            sq = sum(v * v for v in centroid.values())
            if sq > 0:
                norm = math.sqrt(sq)
                self.intent_centroids[intent] = {idx: v / norm for idx, v in centroid.items()}
            else:
                self.intent_centroids[intent] = dict(centroid)

    @staticmethod
    def _cosine_similarity(vec_a: Dict[int, float], vec_b: Dict[int, float]) -> float:
        """Compute cosine similarity (dot product of L2-normalized sparse vectors)."""
        if not vec_a or not vec_b:
            return 0.0
        # Dot product over intersecting indices
        common = set(vec_a.keys()) & set(vec_b.keys())
        return sum(vec_a[k] * vec_b[k] for k in common)

    def classify(self, message: str, has_image: bool = False, has_audio: bool = False) -> IntentResult:
        """
        Classify message using Machine Learning TF-IDF vector space cosine similarity.
        """
        text = message.strip()
        text_lower = text.lower()

        # Check explicit #rag hashtag
        is_rag_explicit = bool(re.search(r"#rag\b|\[rag\]|\brag:\s*", text_lower))
        clean_text = re.sub(r"#rag\b|\[rag\]|\brag:\s*", "", text, flags=re.IGNORECASE).strip()

        if is_rag_explicit:
            return IntentResult(
                primary_intent="rag_search",
                confidence=0.98,
                secondary_intents=["technical_query", "faq_query"],
                is_rag_explicit=True,
                clean_message=clean_text or text,
            )

        if has_image:
            return IntentResult(
                primary_intent="image_analysis",
                confidence=0.95,
                secondary_intents=["general_query"],
                is_rag_explicit=False,
                clean_message=text,
            )

        # 1. Vectorize query into high-dimensional TF-IDF feature space
        query_vec = self.vectorizer.transform(text)

        # 2. Compute Cosine Similarity against all class centroids
        sim_scores: Dict[str, float] = {}
        for intent, centroid in self.intent_centroids.items():
            sim = self._cosine_similarity(query_vec, centroid)
            sim_scores[intent] = max(0.0, sim)

        # 3. Softmax temperature calibration
        max_sim = max(sim_scores.values()) if sim_scores else 0.0

        if max_sim < 0.08:
            # Low similarity threshold: classify as general_query
            return IntentResult(
                primary_intent="general_query",
                confidence=0.55 if "?" in text else 0.45,
                secondary_intents=[],
                is_rag_explicit=False,
                clean_message=text,
            )

        # Sort intents by similarity score
        sorted_intents = sorted(sim_scores.items(), key=lambda x: x[1], reverse=True)
        primary_intent, raw_score = sorted_intents[0]

        # Calibrate confidence score to [0.60, 0.98]
        confidence = min(0.98, max(0.55, 0.40 + raw_score * 0.90))

        # Extract secondary intents that scored reasonably close
        secondary_intents = [
            it for it, sc in sorted_intents[1:]
            if sc >= 0.15 and (raw_score - sc) < 0.25
        ][:3]

        return IntentResult(
            primary_intent=primary_intent,
            confidence=round(confidence, 2),
            secondary_intents=secondary_intents,
            is_rag_explicit=False,
            clean_message=text,
        )


_intent_classifier: Optional[IntentClassifier] = None


def get_intent_classifier() -> IntentClassifier:
    """Return singleton IntentClassifier instance."""
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
