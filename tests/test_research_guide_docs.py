"""Tests for docs/RESEARCH_GUIDE.md documentation accuracy.

Ensures the guide references only reachable API modes/models,
not stale preset names like 'fast-search' or 'deep-research'.
"""

import pathlib

GUIDE_PATH = pathlib.Path(__file__).parent.parent / "docs" / "RESEARCH_GUIDE.md"


def test_no_unreachable_preset_fast_search():
    """The guide must not reference the unreachable 'fast-search' preset."""
    content = GUIDE_PATH.read_text()
    assert "fast-search" not in content, (
        "Found stale 'fast-search' preset in RESEARCH_GUIDE.md. "
        "This preset is unreachable from the tool's schema."
    )


def test_no_unreachable_preset_deep_research():
    """The guide must not reference the unreachable 'deep-research' preset."""
    content = GUIDE_PATH.read_text()
    assert "deep-research" not in content, (
        "Found stale 'deep-research' preset in RESEARCH_GUIDE.md. "
        "This preset is unreachable from the tool's schema."
    )


def test_has_research_api_section():
    """The guide must document the Research API (/v1/responses)."""
    content = GUIDE_PATH.read_text()
    assert "### Research API" in content, (
        "Missing '### Research API' section in RESEARCH_GUIDE.md"
    )


def test_has_chat_api_section():
    """The guide must document the Chat API (/v1/chat/completions)."""
    content = GUIDE_PATH.read_text()
    assert "### Chat API" in content, (
        "Missing '### Chat API' section in RESEARCH_GUIDE.md"
    )


def test_research_api_documents_reasoning_effort():
    """The Research API section must mention reasoning_effort control."""
    content = GUIDE_PATH.read_text()
    assert "reasoning_effort" in content, (
        "Missing 'reasoning_effort' in Research API section"
    )


def test_research_api_documents_max_steps():
    """The Research API section must mention max_steps control."""
    content = GUIDE_PATH.read_text()
    assert "max_steps" in content, "Missing 'max_steps' in Research API section"


def test_chat_api_documents_sonar_models():
    """The Chat API section must list available sonar models."""
    content = GUIDE_PATH.read_text()
    assert "sonar-pro" in content, "Missing sonar-pro model"
    assert "sonar-reasoning" in content, "Missing sonar-reasoning model"
    # sonar (plain) should appear as a model row
    assert "| `sonar`" in content or "| `sonar` " in content, "Missing sonar model"


def test_depth_calibration_uses_mode_not_preset():
    """Depth Calibration section must reference modes, not presets."""
    content = GUIDE_PATH.read_text()
    assert "research mode" in content, (
        "Depth Calibration should reference 'research mode', not preset names"
    )
    assert "chat mode" in content, (
        "Depth Calibration should reference 'chat mode', not preset names"
    )


def test_no_available_presets_section():
    """The old 'Available Presets' section must be removed."""
    content = GUIDE_PATH.read_text()
    assert "### Available Presets" not in content, (
        "Stale '### Available Presets' section still present in RESEARCH_GUIDE.md"
    )


def test_timeout_no_preset_reference():
    """The Timeout error handling must not reference presets."""
    content = GUIDE_PATH.read_text()
    # Should use mode-based language, not preset names
    assert "instead of `deep-research`" not in content, (
        "Timeout section still references 'deep-research' preset"
    )


def test_tiered_approach_no_preset_reference():
    """The Tiered Approach section must not reference presets."""
    content = GUIDE_PATH.read_text()
    assert "`deep-research` preset" not in content, (
        "Tiered Approach still references 'deep-research' preset"
    )
