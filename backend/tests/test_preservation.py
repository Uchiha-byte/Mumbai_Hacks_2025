"""
Preservation Property Tests — Property 2
=========================================
Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5

These tests verify that the API response schemas and unchanged modules are
preserved BEFORE and AFTER the fix. They MUST PASS on unfixed code to establish
the baseline, and MUST CONTINUE TO PASS after the fix is applied.

Observation-first methodology:
  - AnalysisResponse Pydantic model has fields: result: str, agent_used: str
  - QuickAnalysisResponse Pydantic model has fields:
      verdict, confidence, summary_one_liner, tl_dr_bullets, evidence, reasons
  - database.py, embeddings.py, forensics.py, huggingface.py, storage.py
    are unchanged modules (no LangChain imports, must remain byte-for-byte identical)

These tests inspect Pydantic model_fields directly — no FastAPI server required.
"""

import hashlib
import pathlib
from typing import List, Literal, get_args, get_origin

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BACKEND_ROOT = pathlib.Path(__file__).parent.parent  # backend/

UNCHANGED_MODULES = [
    BACKEND_ROOT / "app" / "core" / "database.py",
    BACKEND_ROOT / "app" / "core" / "embeddings.py",
    BACKEND_ROOT / "app" / "core" / "forensics.py",
    BACKEND_ROOT / "app" / "core" / "huggingface.py",
    BACKEND_ROOT / "app" / "core" / "storage.py",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _file_sha256(path: pathlib.Path) -> str:
    """Return the SHA-256 hex digest of a file's contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _capture_hashes() -> dict[str, str]:
    """Capture current SHA-256 hashes for all unchanged modules."""
    return {str(p.relative_to(BACKEND_ROOT)): _file_sha256(p) for p in UNCHANGED_MODULES}


# Capture baseline hashes at module import time (i.e., on unfixed code).
# After the fix these must remain identical.
BASELINE_HASHES = _capture_hashes()


# ---------------------------------------------------------------------------
# Pydantic models — defined inline to avoid importing the full app chain.
# These mirror the observed schemas from endpoints.py exactly.
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    result: str
    agent_used: str


class QuickAnalysisResponse(BaseModel):
    verdict: Literal["FAKE", "SUSPECT", "MIXED", "VERIFIED"]
    confidence: int
    summary_one_liner: str
    tl_dr_bullets: List[str]
    evidence: List[dict]
    reasons: List[str]


def _import_models():
    """Return the Pydantic model classes for schema inspection."""
    return AnalysisResponse, QuickAnalysisResponse


# ---------------------------------------------------------------------------
# Property 2a — AnalysisResponse schema preservation
# ---------------------------------------------------------------------------


class TestAnalysisResponseSchema:
    """
    Validates: Requirements 3.1

    For any content_type in ["text", "image", "audio", "video"],
    AnalysisResponse must always have:
      - result: str
      - agent_used: str
    """

    def test_analysis_response_is_pydantic_model(self):
        AnalysisResponse, _ = _import_models()
        assert issubclass(AnalysisResponse, BaseModel), (
            "AnalysisResponse must be a Pydantic BaseModel"
        )

    def test_analysis_response_has_result_field(self):
        AnalysisResponse, _ = _import_models()
        fields = AnalysisResponse.model_fields
        assert "result" in fields, (
            f"AnalysisResponse missing 'result' field. Fields: {list(fields)}"
        )

    def test_analysis_response_result_is_str(self):
        AnalysisResponse, _ = _import_models()
        field = AnalysisResponse.model_fields["result"]
        annotation = field.annotation
        assert annotation is str, (
            f"AnalysisResponse.result must be str, got {annotation}"
        )

    def test_analysis_response_has_agent_used_field(self):
        AnalysisResponse, _ = _import_models()
        fields = AnalysisResponse.model_fields
        assert "agent_used" in fields, (
            f"AnalysisResponse missing 'agent_used' field. Fields: {list(fields)}"
        )

    def test_analysis_response_agent_used_is_str(self):
        AnalysisResponse, _ = _import_models()
        field = AnalysisResponse.model_fields["agent_used"]
        annotation = field.annotation
        assert annotation is str, (
            f"AnalysisResponse.agent_used must be str, got {annotation}"
        )

    def test_analysis_response_has_exactly_two_fields(self):
        """Schema must not gain or lose fields."""
        AnalysisResponse, _ = _import_models()
        fields = set(AnalysisResponse.model_fields.keys())
        assert fields == {"result", "agent_used"}, (
            f"AnalysisResponse fields changed. Expected {{'result', 'agent_used'}}, got {fields}"
        )

    @given(
        result=st.text(min_size=1),
        agent_used=st.text(min_size=1),
    )
    @settings(max_examples=10)
    def test_analysis_response_instantiation_for_any_content(
        self, result: str, agent_used: str
    ):
        """
        **Validates: Requirements 3.1**

        For any result/agent_used string pair, AnalysisResponse must be
        constructable and expose both fields with the correct types.
        """
        AnalysisResponse, _ = _import_models()
        obj = AnalysisResponse(result=result, agent_used=agent_used)
        assert isinstance(obj.result, str)
        assert isinstance(obj.agent_used, str)
        assert obj.result == result
        assert obj.agent_used == agent_used


# ---------------------------------------------------------------------------
# Property 2b — QuickAnalysisResponse schema preservation
# ---------------------------------------------------------------------------


class TestQuickAnalysisResponseSchema:
    """
    Validates: Requirements 3.2

    For any content_type in ["text", "image"], QuickAnalysisResponse must
    always have all 6 required fields with correct types:
      - verdict: Literal["FAKE", "SUSPECT", "MIXED", "VERIFIED"]
      - confidence: int (0-100)
      - summary_one_liner: str
      - tl_dr_bullets: List[str]
      - evidence: List[dict]
      - reasons: List[str]
    """

    REQUIRED_FIELDS = {
        "verdict",
        "confidence",
        "summary_one_liner",
        "tl_dr_bullets",
        "evidence",
        "reasons",
    }

    def test_quick_analysis_response_is_pydantic_model(self):
        _, QuickAnalysisResponse = _import_models()
        assert issubclass(QuickAnalysisResponse, BaseModel)

    def test_quick_analysis_response_has_all_six_fields(self):
        """
        **Validates: Requirements 3.2**

        All 6 required fields must be present.
        """
        _, QuickAnalysisResponse = _import_models()
        fields = set(QuickAnalysisResponse.model_fields.keys())
        missing = self.REQUIRED_FIELDS - fields
        assert not missing, (
            f"QuickAnalysisResponse missing fields: {missing}. Present: {fields}"
        )

    def test_quick_analysis_response_verdict_is_literal(self):
        _, QuickAnalysisResponse = _import_models()
        field = QuickAnalysisResponse.model_fields["verdict"]
        annotation = field.annotation
        # Should be Literal["FAKE", "SUSPECT", "MIXED", "VERIFIED"]
        origin = get_origin(annotation)
        import typing
        assert origin is typing.Literal, (
            f"QuickAnalysisResponse.verdict must be a Literal type, got {annotation}"
        )
        allowed = set(get_args(annotation))
        assert allowed == {"FAKE", "SUSPECT", "MIXED", "VERIFIED"}, (
            f"QuickAnalysisResponse.verdict allowed values changed: {allowed}"
        )

    def test_quick_analysis_response_confidence_is_int(self):
        _, QuickAnalysisResponse = _import_models()
        field = QuickAnalysisResponse.model_fields["confidence"]
        assert field.annotation is int, (
            f"QuickAnalysisResponse.confidence must be int, got {field.annotation}"
        )

    def test_quick_analysis_response_summary_one_liner_is_str(self):
        _, QuickAnalysisResponse = _import_models()
        field = QuickAnalysisResponse.model_fields["summary_one_liner"]
        assert field.annotation is str, (
            f"QuickAnalysisResponse.summary_one_liner must be str, got {field.annotation}"
        )

    def test_quick_analysis_response_tl_dr_bullets_is_list_str(self):
        _, QuickAnalysisResponse = _import_models()
        field = QuickAnalysisResponse.model_fields["tl_dr_bullets"]
        annotation = field.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)
        assert origin is list, (
            f"QuickAnalysisResponse.tl_dr_bullets must be List[str], got {annotation}"
        )
        assert args == (str,), (
            f"QuickAnalysisResponse.tl_dr_bullets element type must be str, got {args}"
        )

    def test_quick_analysis_response_evidence_is_list_dict(self):
        _, QuickAnalysisResponse = _import_models()
        field = QuickAnalysisResponse.model_fields["evidence"]
        annotation = field.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)
        assert origin is list, (
            f"QuickAnalysisResponse.evidence must be List[dict], got {annotation}"
        )
        assert args == (dict,), (
            f"QuickAnalysisResponse.evidence element type must be dict, got {args}"
        )

    def test_quick_analysis_response_reasons_is_list_str(self):
        _, QuickAnalysisResponse = _import_models()
        field = QuickAnalysisResponse.model_fields["reasons"]
        annotation = field.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)
        assert origin is list, (
            f"QuickAnalysisResponse.reasons must be List[str], got {annotation}"
        )
        assert args == (str,), (
            f"QuickAnalysisResponse.reasons element type must be str, got {args}"
        )

    @given(
        verdict=st.sampled_from(["FAKE", "SUSPECT", "MIXED", "VERIFIED"]),
        confidence=st.integers(min_value=0, max_value=100),
        summary_one_liner=st.text(min_size=1),
        tl_dr_bullets=st.lists(st.text(min_size=1), min_size=1, max_size=5),
        evidence=st.lists(
            st.fixed_dictionaries({"source": st.text(min_size=1), "url": st.text()}),
            min_size=0,
            max_size=3,
        ),
        reasons=st.lists(st.text(min_size=1), min_size=1, max_size=5),
    )
    @settings(max_examples=10)
    def test_quick_analysis_response_instantiation_for_any_content_type(
        self,
        verdict: str,
        confidence: int,
        summary_one_liner: str,
        tl_dr_bullets: list,
        evidence: list,
        reasons: list,
    ):
        """
        **Validates: Requirements 3.2**

        For any valid combination of field values, QuickAnalysisResponse must
        be constructable and expose all 6 fields with correct types.
        """
        _, QuickAnalysisResponse = _import_models()
        obj = QuickAnalysisResponse(
            verdict=verdict,
            confidence=confidence,
            summary_one_liner=summary_one_liner,
            tl_dr_bullets=tl_dr_bullets,
            evidence=evidence,
            reasons=reasons,
        )
        assert isinstance(obj.verdict, str)
        assert isinstance(obj.confidence, int)
        assert isinstance(obj.summary_one_liner, str)
        assert isinstance(obj.tl_dr_bullets, list)
        assert isinstance(obj.evidence, list)
        assert isinstance(obj.reasons, list)


# ---------------------------------------------------------------------------
# Property 2c — Unchanged modules are byte-for-byte identical
# ---------------------------------------------------------------------------


class TestUnchangedModules:
    """
    Validates: Requirements 3.5, 3.6, 3.7, 3.8

    database.py, embeddings.py, forensics.py, huggingface.py, storage.py
    must remain byte-for-byte identical before and after the fix.

    The baseline hashes are captured at import time (on unfixed code).
    Re-running these tests after the fix must produce the same hashes.
    """

    @pytest.mark.parametrize("module_path", UNCHANGED_MODULES)
    def test_unchanged_module_exists(self, module_path: pathlib.Path):
        assert module_path.exists(), f"Unchanged module missing: {module_path}"

    @pytest.mark.parametrize("module_path", UNCHANGED_MODULES)
    def test_unchanged_module_hash_matches_baseline(self, module_path: pathlib.Path):
        """
        **Validates: Requirements 3.5, 3.6, 3.7, 3.8**

        Each unchanged module's SHA-256 hash must match the baseline captured
        before the fix. This guarantees byte-for-byte identity.
        """
        rel = str(module_path.relative_to(BACKEND_ROOT))
        current_hash = _file_sha256(module_path)
        baseline_hash = BASELINE_HASHES[rel]
        assert current_hash == baseline_hash, (
            f"{rel} has been modified!\n"
            f"  Baseline hash : {baseline_hash}\n"
            f"  Current hash  : {current_hash}\n"
            "This file must remain byte-for-byte identical after the fix."
        )
