

---

# 🚀 Enhanced Prompt: TruthScan Backend Upgrade (FastAPI + LangChain + Gemini)

## 🧠 ROLE

You are a **senior Python backend engineer** specializing in:

* FastAPI (async-first architecture)
* LangChain agents/tools
* LLM integrations (Gemini, OpenAI, HuggingFace)
* Distributed systems & API orchestration
* Production-grade error handling, logging, and observability

Your goal is to implement **robust, scalable, and production-ready code**, not prototypes.

---

## 📦 PROJECT CONTEXT

Existing system:

* FastAPI backend
* LangChain-based multi-agent system:

  * Supervisor Agent
  * Text Agent
  * Image Agent
  * Audio Agent
  * Video Agent
  * Quick Analyzer
* Google Gemini as primary LLM
* Local JSON-based embedding storage (to be upgraded)
* No centralized DB (to be replaced with Supabase)

---

## 🎯 OBJECTIVE

Implement **4 major upgrades**:

1. Google Fact Check API Integration
2. Claim Detection (Gemini + HuggingFace fallback)
3. News Verification (NewsAPI)
4. Multi-model Ensemble AI Analysis
5. Supabase Integration (DB + Vector Search)
6. Cascade Decision Pipeline (critical)

---

## ⚙️ GLOBAL REQUIREMENTS

### ✅ Code Quality

* Fully **async/await** (no blocking I/O)
* Type hints everywhere (`typing`)
* Modular, testable classes
* Clear separation of concerns
* Production-level logging (`logging` module)

### ✅ Error Handling

* Graceful API failure fallback
* Retry with exponential backoff (for external APIs)
* Timeout handling
* Structured error responses

### ✅ Config Management

Use environment variables:

```env
GOOGLE_FACTCHECK_API_KEY=
NEWS_API_KEY=
OPENAI_API_KEY=
HUGGINGFACE_API_TOKEN=
SUPABASE_URL=
SUPABASE_ANON_KEY=
```

### ✅ Logging

* Structured logs per stage
* Log failures, API latency, decisions

---

# 📁 FILE 1: `backend/app/core/fact_check.py`

## 🔹 1. GoogleFactCheckAPI

```python
class GoogleFactCheckAPI:
```

### Methods:

* `__init__(api_key: str)`
* `async search_claims(query: str, language: str = "en") -> List[Dict]`
* `get_verdict(query: str) -> Dict`

### Features:

* Endpoint:
  `https://factchecktools.googleapis.com/v1alpha1/claims:search`
* Normalize ratings (TRUE / FALSE / MIXED)
* Aggregate multiple publishers

### Output:

```json
{
  "found": true,
  "verdict": "FAKE" | "VERIFIED" | "MIXED",
  "confidence": 0-100,
  "sources": [...]
}
```

### Improvements:

* Handle missing/ambiguous ratings
* Deduplicate claims
* Confidence based on consensus %

---

## 🔹 2. ClaimDetector (Gemini + HF fallback)

```python
class ClaimDetector:
```

### Gemini Task:

Prompt:

> Extract verifiable factual claims only. Ignore opinions.

Return:

```json
{
  "has_claims": true,
  "claims": [
    {
      "text": "...",
      "check_worthiness_score": 0.0-1.0,
      "category": "politics/science/etc"
    }
  ]
}
```

### Fallback:

Use HuggingFace:

* Model: `marieke93/MiniLM-evidence-types`
* If Gemini fails → fallback classification

---

## 🔹 3. NewsAPIClient

```python
class NewsAPIClient:
```

### Features:

* Endpoint: `https://newsapi.org/v2/everything`
* Rate limit: **100 requests/day (track in-memory)**

### Methods:

* `search_news(query, days_back=7)`
* `verify_claim_with_news(claim)`

### Logic:

* Filter credible sources:

  * BBC, Reuters, AP, NYTimes, Guardian

### Output:

```json
{
  "found_in_news": true,
  "total_articles": 12,
  "credible_sources": 4,
  "confidence": 80,
  "verdict": "VERIFIED",
  "top_articles": [...]
}
```

---

## 🔹 4. EnsembleAnalyzer (Multi-LLM Voting)

```python
class EnsembleAnalyzer:
```

### Models:

* Gemini → weight **0.4**
* GPT-3.5 (`gpt-3.5-turbo`) → weight **0.35**
* HuggingFace → weight **0.25**

### Methods:

* `analyze_with_gemini`
* `analyze_with_gpt`
* `analyze_with_huggingface`
* `ensemble_verdict`

### Requirements:

* Run in parallel (`asyncio.gather`)
* Normalize outputs
* Voting system

### Output:

```json
{
  "verdict": "FAKE",
  "confidence": 87.5,
  "vote_distribution": {
    "FAKE": 0.75,
    "VERIFIED": 0.25
  },
  "model_results": [...]
}
```

### Add:

* GPT cost tracking (tokens → USD estimate)
* Timeout fallback per model

---

## 🔹 5. SupabaseDB

```python
class SupabaseDB:
```

### Use:

* `supabase-py`
* PostgreSQL + pgvector

### Methods:

* `save_analysis`
* `save_feedback`
* `get_analysis_by_id`
* `search_similar_hoaxes` → RPC: `match_hoaxes`
* `add_known_hoax`
* `get_stats`

### Notes:

* All DB calls async
* Return UUIDs
* Handle connection failures

---

# 🔁 TEXT AGENT REFACTOR (CRITICAL)

## Cascade Strategy (STRICT ORDER)

```python
class TextAnalysisAgent:
```

### Pipeline:

### 1️⃣ Claim Detection (FAST)

* If no claims → exit early

```json
{
  "verdict": "NOT_VERIFIABLE",
  "confidence": 95
}
```

---

### 2️⃣ Google Fact Check (FASTEST + FREE)

* If confidence > 80 → RETURN

---

### 3️⃣ News Verification (RECENT CLAIMS)

* If ≥ 2 credible sources → VERIFIED

---

### 4️⃣ Ensemble AI (EXPENSIVE FALLBACK)

* Use only if above fail

---

### 5️⃣ Save to Supabase (ALL CASES)

---

## Final Output Format

```json
{
  "verdict": "...",
  "confidence": 0-100,
  "reasoning": "...",
  "source": "fact_check|news|ensemble",
  "analysis_id": "uuid"
}
```

---

# ⚡ QUICK ANALYZER UPGRADE

```python
class QuickAnalyzer:
```

### Replace FAISS → Supabase Vector Search

### Flow:

1. Generate embedding
2. Query Supabase (`match_hoaxes`)
3. If similarity > 0.85 → RETURN
4. Else → quick Google FactCheck
5. Else → UNKNOWN

### Output:

```json
{
  "verdict": "FAKE",
  "confidence": 92,
  "matched_hoax": "...",
  "similarity": 0.91
}
```

---

# 🔗 LANGCHAIN INTEGRATION

* Update tools to call new `TextAnalysisAgent`
* Ensure:

  * Async tool execution
  * Structured JSON outputs
  * Proper agent routing

---
