"""Tests for context/research-awareness.md documentation accuracy."""

import pathlib

DOCS_PATH = pathlib.Path(__file__).parent.parent / "context" / "research-awareness.md"


def test_no_stale_preset_references():
    """The file must not reference the stale 'preset' parameter."""
    content = DOCS_PATH.read_text()
    assert "preset" not in content, (
        "Found stale 'preset' reference in research-awareness.md. "
        "The tool now uses 'mode' and 'model' parameters, not 'preset'."
    )


def test_documents_mode_parameter():
    """The API Details section must document the 'mode' parameter."""
    content = DOCS_PATH.read_text()
    assert "| `mode`" in content, "Missing 'mode' parameter row in API Details table"


def test_documents_model_parameter():
    """The API Details section must document the 'model' parameter."""
    content = DOCS_PATH.read_text()
    assert "| `model`" in content, "Missing 'model' parameter row in API Details table"


def test_documents_reasoning_effort_parameter():
    """The API Details section must document the 'reasoning_effort' parameter."""
    content = DOCS_PATH.read_text()
    assert "| `reasoning_effort`" in content, "Missing 'reasoning_effort' parameter row"


def test_documents_max_steps_parameter():
    """The API Details section must document the 'max_steps' parameter."""
    content = DOCS_PATH.read_text()
    assert "| `max_steps`" in content, "Missing 'max_steps' parameter row"


def test_documents_instructions_parameter():
    """The API Details section must document the 'instructions' parameter."""
    content = DOCS_PATH.read_text()
    assert "| `instructions`" in content, "Missing 'instructions' parameter row"


def test_documents_research_mode():
    """The API Details section must describe Research mode."""
    content = DOCS_PATH.read_text()
    assert "Research mode" in content, "Missing Research mode description"


def test_documents_chat_mode():
    """The API Details section must describe Chat mode."""
    content = DOCS_PATH.read_text()
    assert "Chat mode" in content, "Missing Chat mode description"


def test_documents_auto_mode():
    """The API Details section must describe Auto mode."""
    content = DOCS_PATH.read_text()
    assert "Auto mode" in content, "Missing Auto mode description"
