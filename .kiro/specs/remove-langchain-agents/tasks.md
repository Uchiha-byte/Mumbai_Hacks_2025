# Implementation Plan

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - LangChain Imports Present in Backend Modules
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate LangChain imports exist in the refactored module set
  - **Scoped PBT Approach**: Scope the property to the concrete set of affected files: `llm.py`, `fact_check.py`, `endpoints.py`, and all files under `backend/app/agents/`
  - Write an AST-based import scanner that parses each module and asserts zero imports from `langchain`, `langchain_core`, `langchain_community`, `langchain_google_genai`, or `langchain_openai`
  - Test each file individually so counterexamples are clearly identified:
    - `backend/app/core/llm.py` — expect to find `langchain_google_genai` (counterexample)
    - `backend/app/core/fact_check.py` — expect to find `langchain_google_genai`, `langchain_openai`, `langchain_core` (counterexample)
    - `backend/app/api/endpoints.py` — expect to find `langchain_core` (counterexample)
    - `backend/app/agents/` directory — expect directory to exist (counterexample)
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bug exists)
  - Document counterexamples found (e.g., `langchain_google_genai` found in `llm.py` at line 1)
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.5, 1.6_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - API Response Schemas Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Observe: `GET /api/v1/stats` returns `{"storage": {...}, "embeddings": {...}}` on unfixed code
  - Observe: `POST /api/v1/feedback` returns `{"status": "success", "feedback_id": ..., "message": ...}` on unfixed code
  - Observe: `AnalysisResponse` Pydantic model has fields `result: str` and `agent_used: str`
  - Observe: `QuickAnalysisResponse` Pydantic model has fields `verdict`, `confidence`, `summary_one_liner`, `tl_dr_bullets`, `evidence`, `reasons`
  - Write property-based tests that verify schema structure is preserved:
    - For any `content_type` in `["text", "image", "audio", "video"]`, `AnalysisResponse` always has `result: str` and `agent_used: str`
    - For any `content_type` in `["text", "image"]`, `QuickAnalysisResponse` always has all 6 required fields with correct types
    - `database.py`, `embeddings.py`, `forensics.py`, `huggingface.py`, `storage.py` file contents are byte-for-byte identical (unchanged modules)
  - Verify tests PASS on UNFIXED code (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3. Refactor core LLM and fact-check modules

  - [x] 3.1 Refactor `backend/app/core/llm.py` — remove LangChain, use `google.generativeai` directly
    - Remove `from langchain_google_genai import ChatGoogleGenerativeAI`
    - Add `import google.generativeai as genai`
    - Replace `get_llm()` body: call `genai.configure(api_key=settings.GOOGLE_API_KEY)` then return `genai.GenerativeModel("gemini-2.5-flash")`
    - Replace `get_vision_llm()` body identically (Gemini 2.5 Flash handles vision natively)
    - Remove `convert_system_message_to_human=True` workaround — not needed with native SDK
    - _Bug_Condition: `isBugCondition(llm.py)` — file imports `langchain_google_genai`_
    - _Expected_Behavior: `get_llm()` and `get_vision_llm()` return `genai.GenerativeModel` instances_
    - _Preservation: `app/core/config.py` and `settings.GOOGLE_API_KEY` usage unchanged_
    - _Requirements: 2.6, 1.6_

  - [x] 3.2 Refactor `backend/app/core/fact_check.py` — remove all LangChain imports
    - Remove `from langchain_google_genai import ChatGoogleGenerativeAI`
    - Remove `from langchain_openai import ChatOpenAI`
    - Remove `from langchain_core.messages import SystemMessage, HumanMessage`
    - Add `import google.generativeai as genai` and `from openai import AsyncOpenAI`
    - Refactor `ClaimDetector.__init__`: replace `ChatGoogleGenerativeAI(...)` with `genai.configure(api_key=settings.GOOGLE_API_KEY)` and store `self.model = genai.GenerativeModel("gemini-2.5-flash")`
    - Refactor `ClaimDetector.extract_claims`: replace `self.gemini.ainvoke([SystemMessage(...), HumanMessage(...)])` with `await self.model.generate_content_async(system_prompt + "\n\n" + text)`; access `.text` instead of `.content`
    - Refactor `EnsembleAnalyzer.__init__`: replace `ChatGoogleGenerativeAI(...)` with `genai.GenerativeModel("gemini-2.5-flash")`, replace `ChatOpenAI(...)` with `AsyncOpenAI(api_key=settings.OPENAI_API_KEY)`
    - Refactor `EnsembleAnalyzer._analyze`: for Gemini path use `await model.generate_content_async(prompt)` and `.text`; for OpenAI path use `await client.chat.completions.create(model="gpt-4o-mini", messages=[...])` and `.choices[0].message.content`
    - All other classes (`GoogleFactCheckAPI`, `NewsAPIClient`) remain completely unchanged
    - _Bug_Condition: `isBugCondition(fact_check.py)` — file imports `langchain_google_genai`, `langchain_openai`, `langchain_core`_
    - _Expected_Behavior: `ClaimDetector` and `EnsembleAnalyzer` call native SDKs with no LangChain intermediary_
    - _Preservation: `GoogleFactCheckAPI`, `NewsAPIClient`, claim extraction logic, ensemble verdict logic all produce equivalent results_
    - _Requirements: 2.3, 2.4, 1.3, 1.4, 3.6_

- [x] 4. Refactor `backend/app/api/endpoints.py` — remove agent imports, inline analysis logic

  - [x] 4.1 Remove all LangChain and agent imports from `endpoints.py`
    - Remove `from langchain_core.messages import HumanMessage`
    - Remove `from app.agents.supervisor import get_supervisor_agent`
    - Remove `from app.agents.image_agent import get_image_agent`
    - Remove `from app.agents.audio_agent import get_audio_agent`
    - Remove `from app.agents.video_agent import get_video_agent`
    - Remove duplicate `from app.agents.supervisor import get_supervisor_agent` import
    - _Bug_Condition: `isBugCondition(endpoints.py)` — file imports `langchain_core`_
    - _Requirements: 2.1, 1.2_

  - [x] 4.2 Move `QuickAnalyzer` class to `backend/app/core/quick_analyzer.py`
    - Copy `QuickAnalyzer` class and `get_quick_analyzer()` factory from `agents/quick_agent.py` to new file `app/core/quick_analyzer.py`
    - `QuickAnalyzer` contains no LangChain code — only its dependencies (`ClaimDetector`, `EnsembleAnalyzer`) needed refactoring in task 3.2
    - Update import in `endpoints.py`: replace `from app.agents.quick_agent import get_quick_analyzer` with `from app.core.quick_analyzer import get_quick_analyzer`
    - _Preservation: `QuickAnalyzer.analyze_text()` and `QuickAnalyzer.analyze_image()` logic (priority waterfall: DB match → fact check → news → LLM) must produce equivalent results_
    - _Requirements: 2.4, 3.2_

  - [x] 4.3 Create `backend/app/core/analysis_service.py` — inline text analysis logic
    - Move `TextAnalysisAgent` class logic from `agents/text_agent.py` into a new `TextAnalysisService` class in `app/core/analysis_service.py`
    - `TextAnalysisAgent` contains no LangChain code itself — its dependencies (`ClaimDetector`, `EnsembleAnalyzer`) were already refactored in task 3.2
    - Expose a module-level `text_analysis_service` singleton and `get_text_analysis_service()` factory
    - _Preservation: claim detection → fact check → news → ensemble waterfall logic unchanged; Supabase `db.save_analysis()` call preserved_
    - _Requirements: 2.3, 3.5_

  - [x] 4.4 Inline media analysis in `endpoints.py` — replace agent invocations with direct service calls
    - For `content_type == "image"`: import `detect_deepfake_image` from `app.core.image_service` (or inline from former `image_agent.py`), call HuggingFace directly, format result string, return `AnalysisResponse(result=..., agent_used="Gemini 2.5 Flash")`
    - For `content_type == "audio"`: call `detect_deepfake_audio` directly (move function from `audio_agent.py` to `app/core/media_service.py`), return `AnalysisResponse(result=..., agent_used="HuggingFace")`
    - For `content_type == "video"`: call `detect_deepfake_video` directly (move function from `video_agent.py` to `app/core/media_service.py`), return `AnalysisResponse(result=..., agent_used="HuggingFace")`
    - For `content_type == "text"`: replace `text_analysis_agent.analyze()` with `text_analysis_service.analyze()`
    - Remove all `agent.invoke({"messages": [HumanMessage(...)]})` patterns — no LangChain message types
    - Preserve `agent_used` field with descriptive strings: `"Gemini 2.5 Flash"`, `"HuggingFace + Gemini 2.5 Flash"`, `"HuggingFace"` etc.
    - _Bug_Condition: `isBugCondition(endpoints.py)` — uses `HumanMessage` from `langchain_core`_
    - _Expected_Behavior: all content types handled via direct service calls with no agent loop_
    - _Preservation: `AnalysisResponse` schema (`result: str`, `agent_used: str`) unchanged; rate limiting, request validation, error handling unchanged_
    - _Requirements: 2.2, 2.3, 3.1_

- [x] 5. Delete `backend/app/agents/` directory entirely
  - Verify `endpoints.py` no longer imports from any `app.agents.*` module (task 4 complete)
  - Delete `backend/app/agents/supervisor.py`
  - Delete `backend/app/agents/text_agent.py`
  - Delete `backend/app/agents/image_agent.py`
  - Delete `backend/app/agents/audio_agent.py`
  - Delete `backend/app/agents/video_agent.py`
  - Delete `backend/app/agents/quick_agent.py`
  - Delete `backend/app/agents/__init__.py`
  - Delete `backend/app/agents/` directory
  - _Bug_Condition: `agents/` directory exists and all files import from `langchain.agents`, `langchain_core`_
  - _Expected_Behavior: directory does not exist; routing logic lives in `endpoints.py` and `app/core/`_
  - _Requirements: 2.1, 1.1, 1.2_

- [x] 6. Update `backend/requirements.txt` — remove all `langchain*` packages

  - [x] 6.1 Remove LangChain packages from requirements
    - Remove `langchain>=0.1.0`
    - Remove `langchain-core>=0.1.0`
    - Remove `langchain-community>=0.0.20`
    - Remove `langchain-google-genai>=3.1.0`
    - Remove `langchain-openai>=0.0.8`
    - _Bug_Condition: `requirements.txt` lists `langchain*` packages_
    - _Requirements: 2.5, 1.5_

  - [x] 6.2 Ensure native SDK packages are present
    - Keep `google-genai>=1.52.0` (already present)
    - Keep `openai>=1.12.0` (already present)
    - Add `google-generativeai` if not already present (provides the `google.generativeai` namespace used by `genai.configure()` and `genai.GenerativeModel`)
    - _Requirements: 2.5, 2.6_

- [x] 7. Verify fix — confirm no LangChain imports remain and API schemas preserved

  - [x] 7.1 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - No LangChain Imports in Refactored Modules
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior (zero `langchain*` imports in affected files)
    - Run the AST import scanner from step 1 against the fixed codebase
    - **EXPECTED OUTCOME**: Test PASSES (confirms all LangChain imports have been removed)
    - Verify `agents/` directory no longer exists
    - _Requirements: 2.1, 2.5, 2.6_

  - [x] 7.2 Verify preservation tests still pass
    - **Property 2: Preservation** - API Response Schema Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2 against the fixed codebase
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions in API schemas or unchanged modules)
    - Confirm `database.py`, `embeddings.py`, `forensics.py`, `huggingface.py`, `storage.py` are byte-for-byte identical
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [ ] 8. Checkpoint - Ensure all tests pass
  - Run the full test suite: import scanner (task 1), schema preservation tests (task 2), and any existing tests
  - Verify the FastAPI app starts without `ImportError` for any `langchain*` package
  - Verify `POST /api/v1/analyze` works for all four content types with mocked LLM responses
  - Verify `POST /api/v1/quick-analyze` works for text and image
  - Verify `POST /api/v1/feedback` and `GET /api/v1/stats` are completely unaffected
  - Ensure all tests pass; ask the user if questions arise
