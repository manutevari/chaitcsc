# CSC Mitra AI

A working Streamlit application providing an AI assistant, grievance filing, knowledge base search, and role dashboards for Citizen Service Centre (CSC) workflows.

> **This README describes what is actually implemented and wired up**, not an aspirational architecture. See `CLEANUP_NOTES.md` for what was removed from the original repo and why.

## What this actually is

- A **Streamlit** app (`app.py` → `pages/*.py`), not a microservice/FastAPI/LangGraph system.
- Chat/knowledge orchestration lives in `backend/mas_engine.py`, which calls sibling flat modules directly (no framework indirection).
- Vector search is **raw PostgreSQL (`psycopg2`) + OpenAI embeddings** — not ChromaDB.
- Voice is **OpenAI Whisper (STT) + OpenAI TTS**, request/response — not real-time streaming, no interruption handling.
- There is **no LangGraph orchestration, no multi-agent framework, no separate microservice API** in the running app, despite `requirements.txt` listing `langgraph`/`chromadb`/`fastapi` (those were unused dependencies pulled in by scaffolding that has since been removed — see below).

## Pages / Features

- `pages/1_CSC_Assistant.py` — AI chat assistant over CSC services
- `pages/2_Grievance_Redressal.py` — complaint filing and tracking
- `pages/3_Knowledge_Base.py` — document ingestion / search
- `pages/4_VLE_Dashboard.py`, `5_Officer_Dashboard.py`, `6_Admin_Dashboard.py` — role dashboards

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your own keys — do NOT commit this file
streamlit run app.py
```

You will need at minimum an `OPENAI_API_KEY` (chat + embeddings) and a Postgres connection (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`) for vector search and grievance storage. Optional: `TAVILY_API_KEY` for web search fallback, `OPENAI_AUDIO_API_KEY` for voice.

## LLM Manager (config-driven model routing)

Model selection used to be a hardcoded, fixed-order provider list in
`mas_engine.py`. It's now handled by `backend/llm/` — a real, tested module
that loads the model catalog from YAML, tracks per-model health (circuit
breaker) and telemetry (rolling success rate / latency) from actual call
outcomes, scores candidates instead of always trying the same order, and
falls back automatically on failure or guardrail rejection. See
`backend/llm/README.md` for usage, how to add a model, and how to run its
test suite (`backend/tests/test_llm_manager.py`, 6 tests, no network/API
keys required — provider calls are monkeypatched).

## Audit report

`AUDIT_REPORT.md` has a full, verified read-through of this codebase —
what's genuinely solid, what's dead code, what's duplicated, and a gap
analysis against a larger enterprise-scope architecture brief this repo
has been asked to become more than once. Worth reading before proposing
another big-bang rewrite.

## Known gaps (honest list)

- No automated tests (`backend/tests/` was empty in the original repo and has been removed).
- No OCR agent, fraud detection, notifications, analytics pipeline, or learning loop — these were requested in a later architecture spec but never built.
- Voice is turn-based, not streaming; no interruption support; language handling is a simple normalize/detect, not full Hindi/Hinglish NLU.
- Single-process Streamlit deployment — no horizontal scaling, no separate API gateway.

## History note

This repo was originally paired with a second repository (`grievance-redressal-chatbot`) intended for merging under a large architecture spec. That second repo was an empty scaffold (every file 0 bytes) and contributed nothing — it was dropped rather than merged. See `CLEANUP_NOTES.md`.
