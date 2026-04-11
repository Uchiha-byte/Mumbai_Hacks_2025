"""
Bug Condition Exploration Tests — Property 1
============================================
Validates: Requirements 1.1, 1.5, 1.6

These tests use Python's `ast` module to scan each affected module for LangChain
imports. They are EXPECTED TO FAIL on unfixed code — that failure is the SUCCESS
condition, proving the bug exists.

When the fix is applied (Tasks 3–6), these same tests will PASS, confirming that
all LangChain imports have been removed.

Scoped to the concrete set of affected files:
  - backend/app/core/llm.py
  - backend/app/core/fact_check.py
  - backend/app/api/endpoints.py
  - backend/app/agents/ (entire directory)
"""

import ast
import os
import pathlib
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LANGCHAIN_PACKAGES = {
    "langchain",
    "langchain_core",
    "langchain_community",
    "langchain_google_genai",
    "langchain_openai",
}

BACKEND_ROOT = pathlib.Path(__file__).parent.parent  # backend/


def _collect_langchain_imports(filepath: pathlib.Path) -> list[dict]:
    """
    Parse *filepath* with the AST and return a list of dicts describing every
    import statement whose top-level package is in LANGCHAIN_PACKAGES.

    Each dict has:
        line   – line number in the source file
        module – the imported package/module name
        stmt   – the raw import statement text
    """
    source = filepath.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(filepath))

    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in LANGCHAIN_PACKAGES:
                    hits.append({
                        "line": node.lineno,
                        "module": alias.name,
                        "stmt": f"import {alias.name}",
                    })
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top = node.module.split(".")[0]
                if top in LANGCHAIN_PACKAGES:
                    names = ", ".join(a.name for a in node.names)
                    hits.append({
                        "line": node.lineno,
                        "module": node.module,
                        "stmt": f"from {node.module} import {names}",
                    })
    return hits


def _fmt_hits(filepath: pathlib.Path, hits: list[dict]) -> str:
    lines = [f"LangChain imports found in {filepath.relative_to(BACKEND_ROOT)}:"]
    for h in hits:
        lines.append(f"  line {h['line']:>4}: {h['stmt']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Individual file tests — each is a separate function so pytest reports
# failures per-file, making counterexamples clearly identifiable.
# ---------------------------------------------------------------------------


def test_llm_py_has_no_langchain_imports():
    """
    backend/app/core/llm.py must contain zero LangChain imports.

    EXPECTED COUNTEREXAMPLE (unfixed code):
        line 1: from langchain_google_genai import ChatGoogleGenerativeAI
    """
    filepath = BACKEND_ROOT / "app" / "core" / "llm.py"
    assert filepath.exists(), f"File not found: {filepath}"

    hits = _collect_langchain_imports(filepath)
    assert hits == [], _fmt_hits(filepath, hits)


def test_fact_check_py_has_no_langchain_imports():
    """
    backend/app/core/fact_check.py must contain zero LangChain imports.

    EXPECTED COUNTEREXAMPLES (unfixed code):
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
    """
    filepath = BACKEND_ROOT / "app" / "core" / "fact_check.py"
    assert filepath.exists(), f"File not found: {filepath}"

    hits = _collect_langchain_imports(filepath)
    assert hits == [], _fmt_hits(filepath, hits)


def test_endpoints_py_has_no_langchain_imports():
    """
    backend/app/api/endpoints.py must contain zero LangChain imports.

    EXPECTED COUNTEREXAMPLE (unfixed code):
        from langchain_core.messages import HumanMessage
    """
    filepath = BACKEND_ROOT / "app" / "api" / "endpoints.py"
    assert filepath.exists(), f"File not found: {filepath}"

    hits = _collect_langchain_imports(filepath)
    assert hits == [], _fmt_hits(filepath, hits)


def test_agents_directory_does_not_exist():
    """
    backend/app/agents/ must NOT exist after the fix.

    EXPECTED COUNTEREXAMPLE (unfixed code):
        The directory backend/app/agents/ exists and contains LangChain agent files.
    """
    agents_dir = BACKEND_ROOT / "app" / "agents"
    assert not agents_dir.exists(), (
        f"agents/ directory still exists at {agents_dir}. "
        f"Files present: {sorted(p.name for p in agents_dir.iterdir())}"
    )


@pytest.mark.parametrize("agent_file", [
    "supervisor.py",
    "image_agent.py",
    "audio_agent.py",
    "video_agent.py",
    "text_agent.py",
    "quick_agent.py",
])
def test_agent_files_have_no_langchain_imports(agent_file: str):
    """
    Each file under backend/app/agents/ must contain zero LangChain imports.

    EXPECTED COUNTEREXAMPLES (unfixed code):
        supervisor.py  — from langchain.agents import create_agent
                         from langchain_core.messages import SystemMessage, HumanMessage
        image_agent.py — from langchain.agents import create_agent
                         from langchain_core.messages import SystemMessage
                         from langchain_core.tools import Tool
        audio_agent.py — from langchain.agents import create_agent
                         from langchain_core.messages import SystemMessage
                         from langchain_core.tools import Tool
        video_agent.py — from langchain.agents import create_agent
                         from langchain_core.messages import SystemMessage
                         from langchain_core.tools import Tool
    """
    filepath = BACKEND_ROOT / "app" / "agents" / agent_file
    if not filepath.exists():
        pytest.skip(f"{agent_file} not found — agents/ directory may already be deleted")

    hits = _collect_langchain_imports(filepath)
    assert hits == [], _fmt_hits(filepath, hits)
