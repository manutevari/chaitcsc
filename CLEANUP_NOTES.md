# Cleanup Notes

This zip is a cleaned version of the uploaded `cscagent` repository. The second
uploaded repository, `grievance-redressal-chatbot-main`, was **not merged**
because every file in it was empty (0 bytes) — `main.py`, `requirements.txt`,
`chatbot/nlp.py`, `chatbot/ui.py`, `chatbot/rag.py`, `db/tickets.py`,
`db/schema.sql`, all `config/*` files, and the Docker files. Only `README.md`
had content (2 lines). There was nothing to merge or preserve from it.

## What was removed from `cscagent` and why

All of the following were confirmed, by grep, to have **zero references**
from the code that actually runs (`app.py`, `streamlit_app.py`, `pages/*.py`,
`backend/mas_engine.py` and the flat modules it imports):

| Removed | Reason |
|---|---|
| `backend/agents/` (8 files) | Never imported anywhere. Unwired agent stubs. |
| `backend/graph/` | Only file in the repo that imported `langgraph`; never called. |
| `backend/services/` | Only file that imported `chromadb`; never called. Real vector search is in `backend/database.py` via raw `psycopg2`. |
| `backend/models/`, `backend/api/`, `backend/workflows/`, `backend/db/` | Unreferenced scaffolding (Pydantic models / FastAPI routers / repositories with no callers). |
| `backend/dashboards/` | Empty directory. |
| `backend/vectorstore/` | Empty Chroma placeholder directory. |
| `backend/main.py` | **Broken.** FastAPI entry point importing `from app.api import ...` — no `app` package exists in this repo (should have been `backend.api`, and even then nothing else calls it). Not used by the real Streamlit app. |
| `backend/llm_orchestrator.py` | 0 bytes. |
| `backend/csc_knowledge_schema.sql`, `backend/docker-compose.yml` | Orphaned, not referenced by the working `backend/Dockerfile` or any script. |
| top-level `dashboards/` | 8-line stub files per role, duplicating the *names* of the real, working `pages/*_Dashboard.py` (160–230 lines each) which is what's actually used. |
| `knowledge_base/` | Empty directory. |
| `__pycache__/` everywhere | Build artifacts, not source. |
| `.git/` | Original commit history; not meaningful to carry into a repackaged zip. |
| `.env` | **Contained live, unredacted API keys** (OpenAI, Tavily, Cohere, Gemini) committed in plaintext. Removed for security — see warning below. `.env.example` (placeholders only) is kept as the setup template. |

## ⚠️ Security: rotate your keys

The `.env` file in the repo you uploaded contained real, working API keys.
Anyone who had access to that file (or the original zip) can use them.
**Rotate/revoke the OpenAI, Tavily, Cohere, and Gemini keys that were in
`.env` immediately**, and going forward keep `.env` out of version control
(it should be in `.gitignore`).

## Requirements.txt

`langgraph`, `chromadb`, `fastapi`, `langchain*`, `sqlalchemy` are still
listed and still unused by the app (they were only reachable from the
deleted scaffold) — left in place in case you rebuild on them later.
`pyyaml` and `pytest` were added; they're real dependencies of the new
`backend/llm/` package and its test suite (see below).

## What this does NOT include

The original merge request (`merge these two repos into a 16-agent LangGraph
governance OS with streaming voice, hybrid RAG, OCR, fraud detection,
notifications, analytics, and a learning loop`) describes a system that does
not exist in either uploaded repo. Building it is a substantial, multi-week+
engineering effort, not a cleanup. This zip is the honest, working baseline
you actually have today, with the dead code and the broken/leaking files
removed.

---

## Session 2: config-driven LLM Manager (`backend/llm/`)

Added a real, tested replacement for the hardcoded provider fallback chain
that used to live in `mas_engine.py` (`_provider_chain` + a for-loop). See
`backend/llm/README.md` for full details. Summary:

- **New package**: `backend/llm/` — registry (YAML-driven model catalog),
  health (per-model circuit breaker), telemetry (rolling success rate /
  latency from real call outcomes), scoring (priority + reliability + speed
  + cost), router, fallback manager, and a generic OpenAI-compatible
  provider (covers every model already in use: Groq, Gemini, OpenRouter,
  HuggingFace Router, Grok) plus an optional LiteLLM provider for anything
  that isn't OpenAI-schema.
- **`mas_engine.py` changed**: `_provider_chain()` and the old `_llm_answer()`
  HTTP-call function are gone. The system-prompt-building logic is unchanged
  and now lives in `_llm_answer_via_manager()`, which calls
  `llm.default_manager.generate(...)` once instead of looping over a fixed
  provider list by hand. The internal-terms guardrail check that used to
  gate the retry loop is now passed in as `validate_fn` — a rejected answer
  triggers fallback to the next candidate without penalizing that model's
  health (it responded fine; the content just wasn't acceptable).
- **Bug found and fixed**: `backend/__init__.py` unconditionally imported
  the `agents/` package (`from .agents import ...`) that Session 1 removed
  as dead code. Because importing *any* `backend.X` submodule always runs
  `backend/__init__.py` first, this import ran on every backend import in
  the *original* repo too — it just never crashed the app because
  `streamlit_app.py` wraps its backend imports in `try/except ImportError`
  and logs+degrades instead of failing loudly. `backend/__init__.py` is now
  empty of eager imports (see the file for the full explanation). This
  wasn't something Session 1's grep-for-`from agents`/`from backend.agents`
  caught, since it was a relative import (`from .agents`) — worth knowing if
  you audit for dead-code references elsewhere in this codebase.
- **Real tests**: `backend/tests/test_llm_manager.py`, 6 tests, all passing,
  no network calls or API keys required (the provider call is
  monkeypatched). Covers: key-based candidate filtering, fallback on
  exception, circuit breaker opening after repeated failures, validator
  rejection not penalizing health, and the all-candidates-failed error path.
  Run with `cd backend && python -m pytest tests/test_llm_manager.py -v`.
- **Not done**: no semantic cache (no evidence yet of repeated identical
  prompts in real traffic to justify one), no trained task classifier (task
  routing is a small keyword heuristic — pass `task=` explicitly when you
  already know it, which `mas_engine.py` does), no fabricated benchmark
  numbers (scoring weights are a documented, adjustable heuristic, not a
  tuned bandit — there's no production traffic yet to tune against).

---

## Session 3: audit + cleanup pass (no feature changes)

This session received the same kind of request Session 1 already
investigated once — a 17-subsystem "AI Governance Operating System" brief
(LangGraph orchestration, 15 async agents, streaming realtime voice,
hybrid RAG, RBAC, OpenTelemetry, etc.). Rather than attempt that build
blindly, this session did a full read-through audit first (see
`AUDIT_REPORT.md` for the complete findings and gap analysis against the
brief) and, per the repo owner's choice, did a **cleanup pass only** —
no new features, no architecture changes. Every `.py` file was
byte-compiled (`python -m py_compile`, 0 errors) and the existing test
suite was re-run (`pytest backend/tests/`, 6/6 passing) both before and
after these changes.

### Dead code removed
| Removed | Reason |
|---|---|
| `backend/voice/`, `backend/voice/stt/`, `backend/voice/tts/` (3 empty `__init__.py` files) | Zero references anywhere in the codebase (grepped). Leftover scaffolding from the same aspirational architecture Session 1 removed elsewhere — this one was missed. |
| `assets/css/styles.css` | Never loaded by any page (grepped). Also would have caused a real conflict if wired up: `app.py` already defines its own `.feature-card` class inline with different colors than this file's `.feature-card`. Removed rather than silently activated. `assets/README.md` corrected to stop claiming it's in use. |

### Duplicate code consolidated
- **New `backend/env_config.py`** — the "check `st.secrets`, fall back to
  `os.getenv`" helper (`get_secret`) plus `get_configured_secret` (skips
  placeholder values like `YOUR_API_KEY`), `get_setting_int`,
  `get_setting_float`, and `get_flag`. This replaces **5 independently
  copy-pasted implementations** that had been sitting in `database.py`,
  `guardrails.py`, `hitl.py`, `mas_engine.py`, and `voice_assistant.py`
  (plus a duplicated `configured_secret` in both `mas_engine.py` and
  `voice_assistant.py`, and a duplicated `_setting_int` in `knowledge.py`).
  Every call site now imports from `env_config.py` (several via `import
  ... as _secret` etc. to keep the diff to import lines only — no
  function-body changes elsewhere). `guardrails.setting()` is kept as a
  thin wrapper around `env_config.get_secret()` since other modules
  already import it by that name.
- **New `backend/pii_patterns.py`** — the Aadhaar/PAN/email/phone/IFSC/
  account-number/DOB regex patterns, which had drifted into two different
  copies: `mas_engine.py` had all 7 (labeled, for type-specific redaction
  before LLM calls), `hitl.py` had 6 — **missing DOB** (used for uniform
  redaction before writing to the review queue). Consolidating onto one
  list fixes that gap: DOB text is now redacted before it reaches the
  HITL SQLite queue too, not just before LLM calls.
- Two dead imports removed from `mas_engine.py` as a direct consequence:
  `import requests` (was already unused before this session — a
  pre-existing dead import this cleanup happened to catch) and `import
  streamlit as st` (was only used by the now-removed local `_secret()`).

### Documentation drift fixed
Five files described the architecture Session 1 already removed as if it
were live and verified — `backend/agents/`, `backend/services/`,
`backend/workflows/`, `backend/models/`, `backend/graph/`, `backend/db/`,
ChromaDB, BGE embeddings, a `DATABASE_URL`/`POSTGRES_*` env-var scheme
that doesn't match what the code reads, and a `.streamlit/` directory
that was never actually created:

- `ENTRY_POINTS.md` — backend package structure and verified-imports
  sections corrected to the real, flat `backend/` layout.
- `VERIFICATION.md` — **removed**. It was a "✅ Fixed" checklist for the
  removed packages and the `.streamlit/` files that don't exist; nothing
  in it was still true. This history is now here instead.
- `docs/architecture.md` — fully rewritten to describe the real system
  (Postgres/pgvector not ChromaDB, OpenAI embeddings not BGE, the
  `llm/` router not a hardcoded provider list, `mas_engine.ask()` not an
  8-agent graph). The original aspirational vision is kept as a clearly
  labeled "Roadmap (not built)" section at the bottom instead of being
  deleted outright.
- `docs/workflow.md` — fully rewritten with real worked examples traced
  through `mas_engine.ask()`, replacing the fictional agent-pipeline
  diagrams.
- `backend/ARCHITECTURE.md` — fully rewritten to list the real modules
  and the flat-import convention they actually use.
- `backend/CODEX_PROMPT.md` — **not** rewritten (it's a genuinely
  forward-looking spec for a separate CSC-LLM fine-tuning initiative, not
  a claim about current state), but flagged at the top: its
  "Already implemented" / "Gaps to close" lists predate
  `document_extractors.py` (multi-format ingestion already exists) and
  `CSC_ADMIN_PASSWORD` (admin gating already exists).
- `DEPLOYMENT.md` — Secrets Manager example and Database Setup section
  corrected to the real `DB_HOST`/`DB_PORT`/`DB_NAME`/`DB_USER`/
  `DB_PASSWORD` fields (was `DATABASE_URL`/`POSTGRES_*`), ChromaDB
  references removed.
- `.env.example` — fully rewritten. It previously documented
  `DATABASE_URL`, `POSTGRES_HOST`, ChromaDB paths, `JWT_SECRET`, SMTP
  settings, and a Sentry DSN — **none of which the code reads**. A
  deployer who followed it literally would set `POSTGRES_HOST` and the
  app would fail to connect, because `database.py` reads `DB_HOST`. It
  now lists exactly the env vars `backend/*.py` actually reads, matching
  `backend/secrets.toml.txt` (which was already accurate and is kept as
  the Streamlit-Cloud-secrets-format template).

### What this session deliberately did NOT do
Per the repo owner's explicit choice: no LangGraph, no multi-agent
split, no hybrid RAG upgrade, no HITL risk-tier upgrade, no realtime
voice work. See `AUDIT_REPORT.md` for the full gap analysis and a
suggested phasing for whichever of those comes next.
