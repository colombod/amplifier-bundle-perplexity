"""Tests for research-expert agent frontmatter (provider_preferences, tools, description)."""

import re
from pathlib import Path

import yaml


AGENT_PATH = Path(__file__).parent.parent / "agents" / "research-expert.md"


def _parse_frontmatter(content: str) -> tuple[str, str]:
    """Parse YAML frontmatter from markdown content.

    Returns (frontmatter_yaml, body_after_frontmatter).
    """
    # Match --- at start, content, then closing ---
    match = re.match(r"^---\n(.*?\n)---\n(.*)", content, re.DOTALL)
    assert match, "File must start with --- frontmatter --- block"
    return match.group(1), match.group(2)


def _load_frontmatter() -> dict:
    """Load and parse the YAML frontmatter from the agent file."""
    content = AGENT_PATH.read_text()
    fm_yaml, _ = _parse_frontmatter(content)
    return yaml.safe_load(fm_yaml)


class TestFrontmatterStructure:
    """Tests that frontmatter has correct structure and top-level keys."""

    def test_frontmatter_delimiters(self):
        """Frontmatter starts with --- and ends with ---."""
        content = AGENT_PATH.read_text()
        lines = content.splitlines()
        assert lines[0] == "---", "First line must be ---"
        # Find the closing ---
        closing_idx = None
        for i in range(1, len(lines)):
            if lines[i] == "---":
                closing_idx = i
                break
        assert closing_idx is not None, "Must have closing --- delimiter"

    def test_three_toplevel_keys_in_order(self):
        """meta -> provider_preferences -> tools are the three top-level keys."""
        data = _load_frontmatter()
        keys = list(data.keys())
        assert keys == ["meta", "provider_preferences", "tools"], (
            f"Expected ['meta', 'provider_preferences', 'tools'], got {keys}"
        )


class TestProviderPreferences:
    """Tests for provider_preferences section."""

    def test_provider_preferences_exists(self):
        """provider_preferences key must exist."""
        data = _load_frontmatter()
        assert "provider_preferences" in data

    def test_two_providers(self):
        """Should have exactly two provider entries."""
        data = _load_frontmatter()
        prefs = data["provider_preferences"]
        assert len(prefs) == 2, f"Expected 2 providers, got {len(prefs)}"

    def test_first_provider_anthropic_haiku(self):
        """First provider is anthropic with claude-haiku-* model."""
        data = _load_frontmatter()
        first = data["provider_preferences"][0]
        assert first["provider"] == "anthropic"
        assert first["model"] == "claude-haiku-*"

    def test_second_provider_openai_mini(self):
        """Second provider is openai with gpt-5-mini model."""
        data = _load_frontmatter()
        second = data["provider_preferences"][1]
        assert second["provider"] == "openai"
        assert second["model"] == "gpt-5-mini"


class TestTools:
    """Tests for tools section."""

    def test_tools_exists(self):
        """tools key must exist."""
        data = _load_frontmatter()
        assert "tools" in data

    def test_one_tool(self):
        """Should have exactly one tool entry."""
        data = _load_frontmatter()
        tools = data["tools"]
        assert len(tools) == 1, f"Expected 1 tool, got {len(tools)}"

    def test_tool_web(self):
        """Tool is tool-web with correct git URL."""
        data = _load_frontmatter()
        tool = data["tools"][0]
        assert tool["module"] == "tool-web"
        expected_source = (
            "git+https://github.com/microsoft/amplifier-module-tool-web@main"
        )
        assert tool["source"] == expected_source


class TestDescription:
    """Tests for description content blocks."""

    def test_must_be_used_when_block(self):
        """Description contains 'MUST be used when:' block."""
        data = _load_frontmatter()
        desc = data["meta"]["description"]
        assert "**MUST be used when:**" in desc, (
            "Description must contain 'MUST be used when:' block"
        )

    def test_authoritative_on_block(self):
        """Description contains 'Authoritative on:' block."""
        data = _load_frontmatter()
        desc = data["meta"]["description"]
        assert "**Authoritative on:**" in desc, (
            "Description must contain 'Authoritative on:' block"
        )

    def test_how_it_works_block(self):
        """Description contains 'How it works:' block."""
        data = _load_frontmatter()
        desc = data["meta"]["description"]
        assert "**How it works:**" in desc, (
            "Description must contain 'How it works:' block"
        )

    def test_description_starts_with_expert_researcher(self):
        """Description starts with the expert researcher tagline."""
        data = _load_frontmatter()
        desc = data["meta"]["description"]
        assert desc.startswith(
            "**Expert researcher using Perplexity's Agentic Research API.**"
        )


class TestOldContentRemoved:
    """Tests that old inherited-tools comments are gone."""

    def test_no_tools_inherited_comment(self):
        """The old '# Tools inherited from parent session via behavior:' comments are gone."""
        content = AGENT_PATH.read_text()
        assert "# Tools inherited from parent session via behavior:" not in content, (
            "Old tools-inherited comment should be removed"
        )

    def test_no_tool_perplexity_search_comment(self):
        """The old '# - tool-perplexity-search' comment is gone."""
        content = AGENT_PATH.read_text()
        assert "# - tool-perplexity-search" not in content


class TestBodyUnchanged:
    """Tests that body content below frontmatter is preserved."""

    def test_body_starts_with_research_expert_heading(self):
        """Body content starts with '# Research Expert'."""
        content = AGENT_PATH.read_text()
        _, body = _parse_frontmatter(content)
        # Body should start with a blank line then the heading
        body_stripped = body.lstrip("\n")
        assert body_stripped.startswith("# Research Expert"), (
            f"Body should start with '# Research Expert', got: {body_stripped[:50]!r}"
        )

    def test_body_contains_response_contract(self):
        """Body still contains the Response Contract section."""
        content = AGENT_PATH.read_text()
        _, body = _parse_frontmatter(content)
        assert "## Response Contract" in body

    def test_body_ends_with_common_agent_base(self):
        """Body ends with the @foundation mention."""
        content = AGENT_PATH.read_text()
        _, body = _parse_frontmatter(content)
        assert "@foundation:context/shared/common-agent-base.md" in body
