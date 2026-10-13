# Testing Guide

## Backend Tests

```bash
cd backend
pytest tests/ -v
```

Tests cover:
- Input sanitisation and validation
- Prompt injection detection
- Response guardrails (secret blocking)
- Calculator tool (arithmetic, sqrt, errors)
- DateTime tool
- Tool registry (register, execute, unknown tool)
- Demo provider (generate, structured)
- AI Orchestrator (demo mode pipeline)
- Pydantic schema validation
- API root endpoint

All tests mock external API calls — no Gemini API key needed.

## Frontend Build Verification

```bash
cd frontend
npm run build
```

Ensures TypeScript compiles and Vite bundles without errors.

## Manual Testing Checklist

- [ ] Application loads at localhost:5173
- [ ] Chat sends and receives messages
- [ ] Conversation history appears in sidebar
- [ ] Conversation switching loads correct messages
- [ ] New Chat clears messages
- [ ] Delete conversation works
- [ ] Theme switching (light/dark/system)
- [ ] Settings persist after refresh
- [ ] Analytics dashboard loads
- [ ] Export (JSON/TXT) downloads file
- [ ] Empty states display correctly
- [ ] Error messages display on network failure
- [ ] Mobile responsive layout
