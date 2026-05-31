"""Tests for docs/COST_GUIDANCE.md documentation accuracy.

Mirrors the style of test_research_awareness_docs.py / test_research_guide_docs.py.
"""

import pathlib


def _find_repo_root() -> pathlib.Path:
    """Walk up from this file until we find bundle.md (repo root marker)."""
    current = pathlib.Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "bundle.md").exists():
            return current
        current = current.parent
    raise RuntimeError(
        "Could not find repo root (bundle.md not found in any parent directory)"
    )


REPO_ROOT = _find_repo_root()
DOCS_PATH = REPO_ROOT / "docs" / "COST_GUIDANCE.md"


def test_cost_guidance_exists():
    """docs/COST_GUIDANCE.md must exist (moved from context/cost-guidance.md)."""
    assert DOCS_PATH.exists(), (
        "docs/COST_GUIDANCE.md not found. "
        "It should have been moved from context/cost-guidance.md."
    )


def test_no_stale_preset_references():
    """The file must not contain stale 'preset' parameter references."""
    content = DOCS_PATH.read_text()
    assert "preset" not in content, (
        "Found stale 'preset' reference in COST_GUIDANCE.md. "
        "The tool uses 'mode' and 'model' parameters, not 'preset'."
    )


def test_documents_reasoning_effort_key():
    """The file must reference 'reasoning_effort' as a configuration key."""
    content = DOCS_PATH.read_text()
    assert "reasoning_effort" in content, (
        "COST_GUIDANCE.md must mention 'reasoning_effort' guidance"
    )


def test_documents_reasoning_effort_low():
    """The file must document the 'low' reasoning_effort level."""
    content = DOCS_PATH.read_text()
    assert "low" in content, "Missing 'low' reasoning_effort level in COST_GUIDANCE.md"


def test_documents_reasoning_effort_medium():
    """The file must document the 'medium' reasoning_effort level."""
    content = DOCS_PATH.read_text()
    assert "medium" in content, (
        "Missing 'medium' reasoning_effort level in COST_GUIDANCE.md"
    )


def test_documents_reasoning_effort_high():
    """The file must document the 'high' reasoning_effort level."""
    content = DOCS_PATH.read_text()
    assert "high" in content, "Missing 'high' reasoning_effort level in COST_GUIDANCE.md"


def test_documents_token_based_pricing():
    """The file must describe token-based pricing."""
    content = DOCS_PATH.read_text()
    assert "token" in content.lower(), (
        "COST_GUIDANCE.md must describe token-based pricing"
    )


def test_has_free_alternatives_guidance():
    """The file must mention free alternatives (web_search)."""
    content = DOCS_PATH.read_text()
    assert "web_search" in content, (
        "COST_GUIDANCE.md must mention free alternatives (web_search)"
    )
