"""Tests for research-expert agent body content (Task 3: preset → mode/model)."""

import re
from pathlib import Path


AGENT_PATH = Path(__file__).parent.parent / "agents" / "research-expert.md"


def _parse_frontmatter(content: str) -> tuple[str, str]:
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_yaml, body_after_frontmatter).
    """
    match = re.match(r"^---\n(.*?\n)---\n(.*)", content, re.DOTALL)
    assert match, "File must start with --- frontmatter --- block"
    return match.group(1), match.group(2)


def _get_body() -> str:
    """Get the body content (after frontmatter) of the agent file."""
    content = AGENT_PATH.read_text()
    _, body = _parse_frontmatter(content)
    return body


class TestNoPresetReferences:
    """The word 'preset' must not appear anywhere in the file."""

    def test_no_preset_in_file(self):
        """grep -n 'preset' agents/research-expert.md returns zero results."""
        content = AGENT_PATH.read_text().lower()
        assert "preset" not in content, (
            "The word 'preset' must not appear anywhere in research-expert.md"
        )


class TestCapabilitiesSection:
    """Step 1: The capabilities line references both APIs."""

    def test_capabilities_mentions_research_mode(self):
        """Capabilities line mentions /v1/responses API (research mode)."""
        body = _get_body()
        assert "/v1/responses API (research mode)" in body, (
            "Capabilities should mention '/v1/responses API (research mode)'"
        )

    def test_capabilities_mentions_chat_completions(self):
        """Capabilities line mentions /v1/chat/completions (chat mode)."""
        body = _get_body()
        assert "/v1/chat/completions (chat mode)" in body, (
            "Capabilities should mention '/v1/chat/completions (chat mode)'"
        )

    def test_no_old_presets_line(self):
        """Old 'with presets' phrasing is gone."""
        body = _get_body()
        assert "with presets" not in body.lower(), (
            "Old 'with presets' phrasing should be removed"
        )


class TestModeSection:
    """Step 2: The preset table is replaced with mode and model sections."""

    def test_section_heading_choose_right_mode(self):
        """Section heading is '### 3. Choose the Right Mode'."""
        body = _get_body()
        assert "### 3. Choose the Right Mode" in body, (
            "Should have heading '### 3. Choose the Right Mode'"
        )

    def test_no_old_preset_heading(self):
        """Old '### 3. Choose the Right Preset' heading is gone."""
        body = _get_body()
        assert "Choose the Right Preset" not in body, (
            "Old 'Choose the Right Preset' heading should be removed"
        )

    def test_mode_table_has_auto(self):
        """Mode table contains 'auto' mode row."""
        body = _get_body()
        assert "| `auto` |" in body, "Mode table must have 'auto' row"

    def test_mode_table_has_research(self):
        """Mode table contains 'research' mode row."""
        body = _get_body()
        assert "| `research` |" in body, "Mode table must have 'research' row"

    def test_mode_table_has_chat(self):
        """Mode table contains 'chat' mode row."""
        body = _get_body()
        assert "| `chat` |" in body, "Mode table must have 'chat' row"

    def test_mode_selection_label(self):
        """Mode selection explanatory text is present."""
        body = _get_body()
        assert "**Mode selection**" in body, "Should have '**Mode selection**' label"

    def test_chat_model_selection_label(self):
        """Chat model selection explanatory text is present."""
        body = _get_body()
        assert "**Chat model selection**" in body, (
            "Should have '**Chat model selection**' label"
        )

    def test_model_table_has_sonar_pro(self):
        """Model table contains 'sonar-pro' model row."""
        body = _get_body()
        assert "| `sonar-pro` |" in body, "Model table must have 'sonar-pro' row"

    def test_model_table_has_sonar(self):
        """Model table contains 'sonar' model row."""
        body = _get_body()
        assert "| `sonar` |" in body, "Model table must have 'sonar' row"

    def test_model_table_has_sonar_reasoning(self):
        """Model table contains 'sonar-reasoning' model row."""
        body = _get_body()
        assert "| `sonar-reasoning` |" in body, (
            "Model table must have 'sonar-reasoning' row"
        )

    def test_no_old_pro_search_preset(self):
        """Old 'pro-search' preset row is gone."""
        body = _get_body()
        assert "pro-search" not in body, "Old 'pro-search' preset should be removed"


class TestWorkflowStep:
    """Step 3: Workflow step 5 references 'mode' not 'preset'."""

    def test_workflow_step_references_mode(self):
        """Workflow step 5 says 'with appropriate mode'."""
        body = _get_body()
        assert "with appropriate mode" in body, (
            "Workflow step 5 should reference 'appropriate mode'"
        )

    def test_workflow_step_no_preset(self):
        """Workflow step 5 does NOT say 'with appropriate preset'."""
        body = _get_body()
        assert "with appropriate preset" not in body, (
            "Workflow step 5 should not reference 'appropriate preset'"
        )
