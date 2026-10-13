# Dynamic AI Chatbot — Frequently Asked Questions

## What is Dynamic AI Chatbot?

Dynamic AI Chatbot is an intelligent conversational assistant powered by Google Gemini AI. It can understand natural language, maintain conversation context, detect user intent and sentiment, retrieve information from a knowledge base, and provide helpful responses.

## What can the chatbot do?

The chatbot can:
- Answer general questions on a wide range of topics
- Help with technical questions about programming, AI, and technology
- Perform calculations using built-in tools
- Search a knowledge base for specific information
- Maintain conversation context across multiple messages
- Detect user sentiment and adapt its responses
- Support multiple languages including English, Hindi, and Hinglish

## How does the AI work?

The chatbot uses Google's Gemini AI model for natural language understanding and response generation. It does NOT train a model from scratch — it leverages pretrained AI capabilities through API calls. The system adds value through its orchestration pipeline: intent recognition, entity extraction, sentiment analysis, contextual memory, and knowledge retrieval.

## Is my data private?

Conversation data is stored in a PostgreSQL database for persistence and analytics. Messages are sent to Google Gemini's API for processing. No personal data is shared with third parties beyond the AI provider. The system does not store API keys in the codebase or expose them to the frontend.

## What languages are supported?

Currently, the chatbot supports:
- **English**: Full support
- **Hindi** (हिंदी): The chatbot can understand and respond in Hindi
- **Hinglish**: A mix of Hindi and English, commonly spoken in India

More languages can be added through the extensible language configuration.

## How do I reset a conversation?

Click the "New Chat" button in the sidebar to start a fresh conversation. Your previous conversations are saved and can be accessed from the conversation history.

## What is the knowledge base?

The knowledge base is a collection of documents that the chatbot can search to provide accurate, grounded answers. When relevant information is found in the knowledge base, the chatbot cites its sources in the response metadata.

## Can the chatbot perform calculations?

Yes! The chatbot has a built-in calculator tool. You can ask it to compute mathematical expressions, and it will use the tool to provide accurate results rather than relying on the AI model's arithmetic.

## What happens if the AI service is unavailable?

If the Gemini API is temporarily unavailable, the chatbot will gracefully fall back to an error message explaining the situation. It will never crash or expose internal error details to the user.

## How is sentiment analysis done?

The system analyses user messages to detect sentiment (positive, neutral, negative) and emotion (joy, sadness, anger, frustration, etc.). This is done using structured LLM-based extraction — not simple keyword matching. Sentiment data is used for analytics and to help the AI adapt its response tone.
