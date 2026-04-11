# Bugfix Requirements Document

## Introduction

The backend currently uses LangChain agents (supervisor, text_agent, image_agent, audio_agent, video_agent, quick_agent) as the orchestration layer for all misinformation detection logic. This introduces unnecessary complexity, heavy dependencies, and fragile agent-based routing. The fix removes all LangChain imports and dependencies entirely, replacing the agent layer with direct LLM service calls to Gemini 2.5 Flash and GPT-4o mini. Supabase integration, the existing API endpoint structure, and all frontend contracts must remain unchanged.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the backend starts THEN the system loads LangChain agent infrastructure (supervisor, image_agent, audio_agent, video_agent) via `langchain.agents.create_agent` and `langchain_core` imports, introducing unnecessary overhead and fragile agent orchestration

1.2 WHEN a `/api/v1/analyze` request is made with `content_type: "image"`, `"audio"`, or `"video"` THEN the system routes through a LangChain agent (`get_image_agent()`, `get_audio_agent()`, `get_video_agent()`) that wraps HuggingFace tool calls inside an agent loop, adding latency and failure points

1.3 WHEN a `/api/v1/analyze` request is made with `content_type: "text"` THEN the system calls `text_analysis_agent.analyze()` which uses `langchain_google_genai.ChatGoogleGenerativeAI` and `langchain_openai.ChatOpenAI` via LangChain message types (`SystemMessage`, `HumanMessage`) in `fact_check.py`

1.4 WHEN a `/api/v1/quick-analyze` request is made THEN the system calls `get_quick_analyzer()` which internally depends on `ClaimDetector` and `EnsembleAnalyzer` from `fact_check.py`, both of which use LangChain-wrapped LLM clients

1.5 WHEN `requirements.txt` is installed THEN the system installs `langchain`, `langchain-core`, `langchain-community`, `langchain-google-genai`, and `langchain-openai` packages that are no longer needed after the refactor

1.6 WHEN `app/core/llm.py` is imported THEN the system instantiates `ChatGoogleGenerativeAI` from `langchain_google_genai`, making LangChain a transitive dependency for all LLM access

### Expected Behavior (Correct)

2.1 WHEN the backend starts THEN the system SHALL load no LangChain modules — zero imports from `langchain`, `langchain_core`, `langchain_community`, `langchain_google_genai`, or `langchain_openai` anywhere in the codebase

2.2 WHEN a `/api/v1/analyze` request is made with `content_type: "image"`, `"audio"`, or `"video"` THEN the system SHALL call a direct LLM service (Gemini 2.5 Flash via `google-genai` SDK) with the media content and a structured prompt, returning a formatted analysis result without any agent loop

2.3 WHEN a `/api/v1/analyze` request is made with `content_type: "text"` THEN the system SHALL call Gemini 2.5 Flash and/or GPT-4o mini directly using their native SDKs (`google-genai` and `openai`) for claim extraction, fact-checking ensemble, and verdict generation

2.4 WHEN a `/api/v1/quick-analyze` request is made THEN the system SHALL perform claim detection and ensemble analysis by calling LLM APIs directly (no LangChain wrappers), maintaining the same response schema (`verdict`, `confidence`, `summary_one_liner`, `tl_dr_bullets`, `evidence`, `reasons`)

2.5 WHEN `requirements.txt` is installed THEN the system SHALL NOT include `langchain`, `langchain-core`, `langchain-community`, `langchain-google-genai`, or `langchain-openai` — only `google-genai` and `openai` for LLM access

2.6 WHEN `app/core/llm.py` is used THEN the system SHALL provide direct client factory functions using the `google-genai` SDK (`google.generativeai`) with no LangChain dependency

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a `/api/v1/analyze` request is made with any supported `content_type` THEN the system SHALL CONTINUE TO return a response matching the `AnalysisResponse` schema (`result: str`, `agent_used: str`) so the frontend contract is preserved

3.2 WHEN a `/api/v1/quick-analyze` request is made THEN the system SHALL CONTINUE TO return a response matching the `QuickAnalysisResponse` schema (`verdict`, `confidence`, `summary_one_liner`, `tl_dr_bullets`, `evidence`, `reasons`) unchanged

3.3 WHEN a `/api/v1/feedback` request is made THEN the system SHALL CONTINUE TO save feedback to Supabase and return the same success response structure

3.4 WHEN a `/api/v1/stats` request is made THEN the system SHALL CONTINUE TO return storage and embeddings statistics from Supabase and the local FAISS index

3.5 WHEN Supabase operations are performed (save analysis, save feedback, search similar hoaxes) THEN the system SHALL CONTINUE TO use the existing `SupabaseDB` class in `app/core/database.py` with no schema changes

3.6 WHEN the Google Fact Check API, NewsAPI, and HuggingFace inference endpoints are called THEN the system SHALL CONTINUE TO use `httpx` and the existing HTTP client logic — only the LLM orchestration layer changes

3.7 WHEN image forensics analysis is requested via quick-analyze THEN the system SHALL CONTINUE TO use `app/core/forensics.py` for manipulation detection, unchanged

3.8 WHEN the FAISS similarity search is used THEN the system SHALL CONTINUE TO use `app/core/embeddings.py` with `sentence-transformers` and `faiss-cpu`, unchanged

3.9 WHEN detection results are produced for text, image, audio, or video content THEN the system SHALL CONTINUE TO achieve at least 70-80% detection accuracy, equivalent to or better than the current agent-based approach
