"""
Pre-trained FAQ & Rule-based Response Matcher.
Provides instant, deterministic answers for known queries and system FAQs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class FAQMatch:
    question: str
    answer: str
    category: str
    confidence: float
    source: str = "Pre-trained Knowledge Base"


class FAQMatcher:
    """
    Rule-based & pre-trained FAQ response system.
    Returns high-confidence curated answers for standard questions.
    """

    FAQ_DATABASE = [
        {
            "patterns": [
                r"what is (?:this )?(?:dynamic ai )?chatbot",
                r"what does (?:this )?(?:dynamic ai )?chatbot do",
                r"what can (?:this )?(?:dynamic ai )?chatbot do",
                r"what are the features of (?:this )?(?:dynamic ai )?chatbot",
                r"tell me about (?:this )?(?:dynamic ai )?chatbot",
                r"tell me about (?:this )?project",
            ],
            "question": "What is the Dynamic AI Chatbot?",
            "answer": (
                "**Dynamic AI Chatbot** is a full-stack conversational AI assistant built with "
                "**FastAPI**, **Google Gemini**, **PostgreSQL (pgvector)**, and **Redis**.\n\n"
                "**Key Capabilities:**\n"
                "- 🧠 **NLP Engine**: Real-time intent recognition, NER entity extraction, and sentiment/emotion detection.\n"
                "- 📚 **RAG (Retrieval-Augmented Generation)**: Vector search with PostgreSQL pgvector (vector(384)) over uploaded PDFs, docs, and notes.\n"
                "- 🎙️ **Voice & 📷 Image**: Speech-to-text input, voice reading, and multimodal image inspection.\n"
                "- ⚡ **Rule + Generative AI**: Instant answers for common FAQs and generative synthesis for complex tasks.\n"
                "- 🔄 **Self-Learning**: RLHF reinforcement feedback tracking from user ratings."
            ),
            "category": "About",
        },
        {
            "patterns": [
                r"how does rag work",
                r"what is rag",
                r"explain retrieval augmented generation",
                r"how do you use rag",
            ],
            "question": "How does RAG work in this chatbot?",
            "answer": (
                "**RAG (Retrieval-Augmented Generation)** enhances AI accuracy by referencing factual documents before answering:\n\n"
                "1. **Upload & Chunking**: You upload a document (PDF, TXT, MD). The system splits it into overlapping 500-character chunks.\n"
                "2. **Vector Embeddings**: Each chunk is converted into 384-dimensional semantic vector embeddings and indexed in **PostgreSQL pgvector**.\n"
                "3. **Semantic Search**: When you ask a question (or use the `#rag` tag), the system computes native `<=>` cosine distance in PostgreSQL to fetch the most relevant chunks.\n"
                "4. **Grounded Generation**: The LLM synthesizes an answer using *only* your verified document context and cites the source document."
            ),
            "category": "Architecture",
        },
        {
            "patterns": [
                r"how (?:do i|to) upload (?:a )?document",
                r"how to add (?:my )?documents to rag",
                r"upload document for rag",
            ],
            "question": "How do I upload documents to RAG?",
            "answer": (
                "To upload a document for RAG search:\n\n"
                "1. Click the **📄 Upload Document (RAG)** button next to the chat bar.\n"
                "2. Select your file (`.pdf`, `.txt`, `.md`, `.docx`, `.csv`).\n"
                "3. The system will automatically chunk and index it into **PostgreSQL pgvector**.\n"
                "4. In the chat, type your question with the `#rag` tag (e.g., `#rag What are the company policies?`) to get grounded answers citing your file!"
            ),
            "category": "Usage",
        },
        {
            "patterns": [
                r"what (?:tech stack|technologies) are used",
                r"how is (?:this|the) backend built",
                r"what is the architecture",
            ],
            "question": "What is the technology stack?",
            "answer": (
                "**Technology Stack:**\n"
                "- **Backend**: FastAPI 0.115, Python 3.11, Uvicorn, AsyncPG, SQLAlchemy 2.0\n"
                "- **Vector DB**: PostgreSQL 16 pgvector (native vector(384) cosine distance)\n"
                "- **Cache & State**: Redis 7 Alpine\n"
                "- **Relational DB**: PostgreSQL 16 Alpine\n"
                "- **Frontend**: React 18, Vite 6, Tailwind CSS, Lucide Icons, Recharts\n"
                "- **AI & Vision**: Google Gemini 2.5 Flash + Local Hybrid NLP Pipeline\n"
                "- **Infrastructure**: Docker Compose (low-memory tuned under ~450 MB RAM)"
            ),
            "category": "Architecture",
        },
        {
            "patterns": [
                r"how to deploy (?:this )?freely",
                r"can i deploy this for free",
                r"free deployment options",
            ],
            "question": "How can I deploy this project for free ($0/month)?",
            "answer": (
                "This project can be deployed **100% free with zero credit card required**:\n\n"
                "1. **Database**: Free serverless PostgreSQL on **Neon.tech** (0.5GB free, instant connection string).\n"
                "2. **Cache**: Free Redis on **Upstash.com** (10,000 commands/day free).\n"
                "3. **Backend**: Free Web Service on **Render.com** (connects to Neon and Upstash via env vars).\n"
                "4. **Frontend**: Free Static Site on **Vercel** or **Render**.\n\n"
                "See `docs/deployment.md` for the step-by-step master guide!"
            ),
            "category": "Deployment",
        },
    ]

    def match(self, message: str) -> Optional[FAQMatch]:
        """Try to match message against pre-trained FAQ database."""
        text_lower = message.lower().strip()
        # Strip trailing punctuation
        text_clean = re.sub(r"[?!.,]", "", text_lower).strip()

        for item in self.FAQ_DATABASE:
            for pattern in item["patterns"]:
                if re.search(pattern, text_clean):
                    return FAQMatch(
                        question=item["question"],
                        answer=item["answer"],
                        category=item["category"],
                        confidence=0.95,
                    )

        # Token Jaccard similarity fallback
        msg_tokens = set(text_clean.split())
        best_match = None
        best_sim = 0.0

        for item in self.FAQ_DATABASE:
            q_tokens = set(re.sub(r"[?!.,]", "", item["question"].lower()).split())
            intersection = len(msg_tokens.intersection(q_tokens))
            union = len(msg_tokens.union(q_tokens))
            sim = intersection / union if union > 0 else 0.0
            if sim > best_sim and sim >= 0.65:
                best_sim = sim
                best_match = item

        if best_match:
            return FAQMatch(
                question=best_match["question"],
                answer=best_match["answer"],
                category=best_match["category"],
                confidence=round(best_sim, 2),
            )

        return None


_faq_matcher: Optional[FAQMatcher] = None


def get_faq_matcher() -> FAQMatcher:
    """Return singleton FAQMatcher instance."""
    global _faq_matcher
    if _faq_matcher is None:
        _faq_matcher = FAQMatcher()
    return _faq_matcher
