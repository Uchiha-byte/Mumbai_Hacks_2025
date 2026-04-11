# Remove LangChain Agents Bugfix Design

## Overview

The backend currently routes all analysis requests through LangChain agent infrastructure (`supervisor.py`, `text_agent.py`, `image_agent.py`, `audio_agent.py`, `video_agent.py`, `quick_agent.py`). This introduces unnecessary overhead, fragile agent loops, and heavy transitive dependencies. The fix removes the entire `backend/app/agents/` directory and replaces all LangChain-wrapped LLM calls with direct SDK calls using `google-genai` (Gemini 2.5 Flash) and `openai` (GPT-4o mini). All API contracts, Supabase integration, FAISS embeddings, forensics, and HuggingFace inference remain unchanged.

## Glossary

- **Bug_Condition (C)**: Any code path that imports from `langchain`, `langchain_core`, `langchain_community`, `langchain_google_genai`, or `langchain_openai`
- **Property (P)**: The desired behavior — LLM calls are made directly via `google.generativeai` and `openai` SDKs with no LangChain intermediary
- **Preservation**: All API response schemas, Supabase operations, FAISS similarity search, forensics analysis, and HuggingFace inference that must remain functionally identical after the fix
- **`get_llm()` / `get_vision_llm()`**: Factory functions in `backend/app/core/llm.py` that currently return `ChatGoogleGenerativeAI` (LangChain wrapper) — to be replaced with `google.generativeai.GenerativeModel`
- **`ClaimDetector`**: Class in `backend/app/core/fact_check.py` that uses `ChatGoogleGenerativeAI` and LangChain message types for claim extraction — to be refactored to use `google.generativeai` directly
- **`EnsembleAnalyzer`**: Class in `backend/app/core/fact_check.py` that uses both `ChatGoogleGenerativeAI` and `ChatOpenAI` (LangChain wrappers) — to be refactored to use native SDKs
- **`supervisor.py`**: LangChain agent that routes requests to sub-agents — to be deleted; routing logic moves directly into `endpoints.py`
- **`AnalysisResponse`**: API schema `{result: str, agent_used: str}` — must remain unchanged
- **`QuickAnalysisResponse`**: API schema `{verdict, confidence, summary_one_liner, tl_dr_bullets, evidence, reasons}` — must remain unchanged

## Bug Details

### Bug Condition

The bug manifests whenever any module in the backend is imported or executed. The codebase unconditionally imports LangChain packages in `llm.py`, `fact_check.py`, and all six agent files. These imports fail or add unnecessary overhead when LangChain packages are not installed, and they prevent removal of the `langchain*` dependency group from `requirements.txt`.

**Formal Specification:**
```
FUNCTION isBugCondition(module)
  INPUT: module — a Python module file in backend/app/
  OUTPUT: boolean

  RETURN EXISTS import_statement IN module.imports
         WHERE import_statement.package IN [
           "langchain",
           "langchain_core",
           "langchain_community",
           "langchain_google_genai",
           "langchain_openai"
         ]
END FUNCTION
```

### Examples

- `backend/app/core/llm.py` imports `from langchain_google_genai import ChatGoogleGenerativeAI` → **bug condition holds**; expected: `import google.generativeai as genai`
- `backend/app/core/fact_check.py` imports `from langchain_core.messages import SystemMessage, HumanMessage` → **bug condition holds**; expected: plain `str` prompts passed directly to `genai.GenerativeModel.generate_content_async()`
- `backend/app/agents/supervisor.py` imports `from langchain.agents import create_agent` → **bug condition holds**; expected: file deleted, routing logic inlined in `endpoints.py`
- `backend/app/api/endpoints.py` imports `from langchain_core.messages import HumanMessage` → **bug condition holds**; expected: no LangChain imports, direct service calls only
- `backend/app/core/database.py` has no LangChain imports → **bug condition does NOT hold**; file must remain unchanged

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- `GET /api/v1/stats` and `POST /api/v1/feedback` endpoints must continue to work exactly as before
- `SupabaseDB` class in `database.py` must be called with the same arguments and return the same data shapes
- `app/core/embeddings.py` (FAISS + sentence-transformers) must remain untouched
- `app/core/forensics.py` image manipulation detection must remain untouched
- `app/core/huggingface.py` inference client must remain untouched
- `app/core/storage.py` must remain untouched
- Google Fact Check API and NewsAPI HTTP calls via `httpx` must remain untouched
- `QuickAnalyzer.analyze_text()` and `QuickAnalyzer.analyze_image()` logic (priority waterfall: DB match → fact check → news → LLM) must produce equivalent results
- `TextAnalysisAgent.analyze()` logic (claim detection → fact check → news → ensemble) must produce equivalent results

**Scope:**
All code paths that do NOT involve LangChain imports are completely unaffected by this fix. This includes:
- All Supabase read/write operations
- FAISS vector similarity search
- HuggingFace inference API calls
- Image forensics (ELA, hash comparison, metadata extraction)
- FastAPI routing, rate limiting, and request/response validation
- Frontend API contracts (no frontend changes required)

## Hypothesized Root Cause

The root cause is architectural: LangChain was chosen as the LLM orchestration layer during initial development, but the agent abstractions (`create_agent`, `Tool`, message types) add no value for this use case. The actual work is done by direct API calls to Gemini and OpenAI, which LangChain merely wraps.

1. **Unnecessary Agent Loop in `supervisor.py`**: `create_agent` wraps simple routing logic (if content_type == "image" → call image tool) in a ReAct loop that adds latency and failure modes. The routing is deterministic and belongs directly in `endpoints.py`.

2. **LangChain Message Types in `fact_check.py`**: `SystemMessage` and `HumanMessage` from `langchain_core` are used only to format prompts for `ChatGoogleGenerativeAI.ainvoke()`. The `google.generativeai` SDK accepts plain strings or `Content` objects natively — no wrapper needed.

3. **LangChain LLM Wrappers in `llm.py`**: `ChatGoogleGenerativeAI` wraps `google.generativeai.GenerativeModel`. The wrapper adds the `convert_system_message_to_human=True` workaround, which is unnecessary when calling the native SDK directly.

4. **`langchain_openai.ChatOpenAI` in `EnsembleAnalyzer`**: Wraps `openai.AsyncOpenAI`. The native `openai` SDK is already in `requirements.txt` and supports async calls directly.

5. **Transitive Dependency Bloat**: `langchain`, `langchain-core`, `langchain-community`, `langchain-google-genai`, and `langchain-openai` are all installed but only used as thin wrappers. Removing them reduces install size and eliminates version conflict surface area.

## Correctness Properties

Property 1: Bug Condition - No LangChain Imports in Refactored Modules

_For any_ Python module file in `backend/app/` that is part of the refactored set (`llm.py`, `fact_check.py`, `endpoints.py`, and all files in `agents/`), the fixed codebase SHALL contain zero import statements referencing `langchain`, `langchain_core`, `langchain_community`, `langchain_google_genai`, or `langchain_openai`. LLM calls SHALL use `google.generativeai` and `openai` SDKs directly.

**Validates: Requirements 2.1, 2.5, 2.6**

Property 2: Preservation - API Response Schema Unchanged

_For any_ valid request to `/api/v1/analyze` or `/api/v1/quick-analyze`, the fixed endpoints SHALL return responses that conform to the same Pydantic schemas (`AnalysisResponse` and `QuickAnalysisResponse`) as the original code, with all required fields present and correctly typed.

**Validates: Requirements 3.1, 3.2**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct:

**Delete:** `backend/app/agents/` (entire directory — all 6 agent files + `__init__.py`)

---

**File:** `backend/app/core/llm.py`

**Function:** `get_llm()`, `get_vision_llm()`

**Specific Changes:**
1. **Remove LangChain import**: Delete `from langchain_google_genai import ChatGoogleGenerativeAI`
2. **Add native SDK import**: Add `import google.generativeai as genai`
3. **Replace return value**: Return `genai.GenerativeModel("gemini-2.5-flash")` after calling `genai.configure(api_key=settings.GOOGLE_API_KEY)`
4. Both `get_llm()` and `get_vision_llm()` can return the same model type (Gemini 2.5 Flash handles vision natively)

---

**File:** `backend/app/core/fact_check.py`

**Class:** `ClaimDetector`

**Specific Changes:**
1. **Remove LangChain imports**: Delete `from langchain_google_genai import ChatGoogleGenerativeAI`, `from langchain_openai import ChatOpenAI`, `from langchain_core.messages import SystemMessage, HumanMessage`
2. **Add native imports**: Add `import google.generativeai as genai` and `from openai import AsyncOpenAI`
3. **Refactor `ClaimDetector.__init__`**: Replace `ChatGoogleGenerativeAI(...)` with `genai.configure(...)` + store model name
4. **Refactor `ClaimDetector.extract_claims`**: Replace `self.gemini.ainvoke([SystemMessage(...), HumanMessage(...)])` with `await asyncio.to_thread(model.generate_content, prompt_str)` or use `genai.GenerativeModel.generate_content_async()`
5. **Refactor `EnsembleAnalyzer.__init__`**: Replace `ChatGoogleGenerativeAI(...)` with native `genai.GenerativeModel`, replace `ChatOpenAI(...)` with `AsyncOpenAI(api_key=...)`
6. **Refactor `EnsembleAnalyzer._analyze`**: Replace `model.ainvoke(prompt)` with `model.generate_content_async(prompt)` for Gemini and `client.chat.completions.create(...)` for OpenAI; access `.text` instead of `.content`

---

**File:** `backend/app/api/endpoints.py`

**Specific Changes:**
1. **Remove all agent imports**: Delete all `from app.agents.*` imports and `from langchain_core.messages import HumanMessage`
2. **Inline text analysis**: Move `TextAnalysisAgent` logic directly into the endpoint or into a new `backend/app/core/analysis_service.py` module
3. **Inline media analysis**: For image/audio/video, call HuggingFace directly (reuse `detect_deepfake_image`, `detect_deepfake_audio`, `detect_deepfake_video` functions) and format the result string without an agent loop
4. **Keep `get_quick_analyzer()`**: Move `QuickAnalyzer` class from `agents/quick_agent.py` to `app/core/` (e.g., `app/core/quick_analyzer.py`) since it contains no LangChain code itself — only its dependencies (`ClaimDetector`, `EnsembleAnalyzer`) need refactoring
5. **Preserve `agent_used` field**: Return descriptive strings like `"Gemini 2.5 Flash"`, `"HuggingFace + Gemini 2.5 Flash"` to satisfy the `AnalysisResponse` schema

---

**File:** `backend/requirements.txt`

**Specific Changes:**
1. **Remove**: `langchain>=0.1.0`, `langchain-core>=0.1.0`, `langchain-community>=0.0.20`, `langchain-google-genai>=3.1.0`, `langchain-openai>=0.0.8`
2. **Keep**: `google-genai>=1.52.0`, `openai>=1.12.0`
3. **Add if missing**: `google-generativeai` (the `google.generativeai` namespace package, distinct from `google-genai`)

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (LangChain imports present), then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bug BEFORE implementing the fix. Confirm that LangChain imports are present in the modules identified above, and that removing them without replacing the functionality breaks the endpoints.

**Test Plan**: Write import-scanning tests that parse each module's AST and assert that no `langchain*` imports exist. Run these on the UNFIXED code to observe failures and confirm the root cause.

**Test Cases**:
1. **llm.py import scan**: Assert `llm.py` has no `langchain*` imports (will fail on unfixed code — finds `langchain_google_genai`)
2. **fact_check.py import scan**: Assert `fact_check.py` has no `langchain*` imports (will fail on unfixed code — finds `langchain_google_genai`, `langchain_openai`, `langchain_core`)
3. **endpoints.py import scan**: Assert `endpoints.py` has no `langchain*` imports (will fail on unfixed code — finds `langchain_core`)
4. **agents/ directory scan**: Assert `backend/app/agents/` directory does not exist (will fail on unfixed code)

**Expected Counterexamples**:
- `langchain_google_genai` found in `llm.py` and `fact_check.py`
- `langchain_openai` found in `fact_check.py`
- `langchain_core` found in `fact_check.py` and `endpoints.py`
- `langchain.agents` found in `image_agent.py`, `audio_agent.py`, `video_agent.py`, `supervisor.py`

### Fix Checking

**Goal**: Verify that for all modules where the bug condition holds, the fixed versions contain no LangChain imports and LLM calls use native SDKs.

**Pseudocode:**
```
FOR ALL module WHERE isBugCondition(module) DO
  fixed_module := apply_fix(module)
  ASSERT NOT isBugCondition(fixed_module)
  ASSERT uses_native_sdk(fixed_module)  -- google.generativeai or openai
END FOR
```

### Preservation Checking

**Goal**: Verify that for all modules where the bug condition does NOT hold (`database.py`, `embeddings.py`, `forensics.py`, `huggingface.py`, `storage.py`), the fixed codebase produces the same behavior as the original.

**Pseudocode:**
```
FOR ALL module WHERE NOT isBugCondition(module) DO
  ASSERT original_module.source == fixed_module.source  -- file unchanged
END FOR

FOR ALL request IN [analyze_requests, quick_analyze_requests, feedback_requests, stats_requests] DO
  ASSERT response_schema(fixed_endpoint(request)) == response_schema(original_endpoint(request))
END FOR
```

**Testing Approach**: Property-based testing is recommended for API schema preservation because:
- It generates many varied request payloads automatically
- It catches schema regressions that manual tests might miss
- It provides strong guarantees that all required fields are present across input variations

**Test Plan**: Observe the response schemas on UNFIXED code first, then write property-based tests that verify the same schemas are returned after the fix.

**Test Cases**:
1. **AnalysisResponse preservation**: For any `content_type` in `["text", "image", "audio", "video"]`, the response must have `result: str` and `agent_used: str`
2. **QuickAnalysisResponse preservation**: For any `content_type` in `["text", "image"]`, the response must have all 6 required fields with correct types
3. **Unchanged modules preservation**: `database.py`, `embeddings.py`, `forensics.py`, `huggingface.py`, `storage.py` file contents are byte-for-byte identical before and after the fix
4. **Feedback endpoint preservation**: `POST /api/v1/feedback` returns `{status, feedback_id, message}` unchanged
5. **Stats endpoint preservation**: `GET /api/v1/stats` returns `{storage, embeddings}` unchanged

### Unit Tests

- Test `get_llm()` returns a `google.generativeai.GenerativeModel` instance (not a LangChain object)
- Test `ClaimDetector.extract_claims()` calls `generate_content_async` on the native Gemini model
- Test `EnsembleAnalyzer._analyze()` calls `chat.completions.create` for OpenAI path
- Test media analysis functions (`detect_deepfake_image`, `detect_deepfake_audio`, `detect_deepfake_video`) are callable directly without an agent wrapper
- Test that importing `app.core.llm`, `app.core.fact_check`, and `app.api.endpoints` raises no `ModuleNotFoundError` for `langchain*` packages

### Property-Based Tests

- Generate random `content_type` values and verify `AnalysisResponse` always has `result: str` and `agent_used: str` (fix checking — Property 1 applied to API layer)
- Generate random `QuickAnalysisRequest` payloads and verify all 6 `QuickAnalysisResponse` fields are present and correctly typed (preservation — Property 2)
- Generate random text inputs and verify `ClaimDetector.extract_claims()` always returns a dict with `has_claims: bool` and `claims: list` (structural preservation of fact_check logic)

### Integration Tests

- Test full `POST /api/v1/analyze` flow for each content type with mocked LLM responses — verify end-to-end response schema
- Test full `POST /api/v1/quick-analyze` flow for text and image — verify priority waterfall (DB match → fact check → news → LLM) still executes in order
- Test that `POST /api/v1/feedback` and `GET /api/v1/stats` are completely unaffected by the refactor
- Test that starting the FastAPI app with `langchain*` packages uninstalled does not raise `ImportError`
