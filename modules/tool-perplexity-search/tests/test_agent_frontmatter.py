"""Tests for research-expert agent frontmatter (model_role, tools, description)."""

import re
from pathlib import Path

import yaml


def _find_repo_root() -> Path:
    """Walk up from this file until we find bundle.md (repo root marker)."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "bundle.md").exists():
            return current
        current = current.parent
    raise RuntimeError(
        "Could not find repo root (bundle.md not found in any parent directory)"
    )


REPO_ROOT = _find_repo_root()
AGENT_PATH = REPO_ROOT / "agents" / "research-expert.md"


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
        """meta -> model_role -> tools are the three top-level keys."""
        data = _load_frontmatter()
        keys = list(data.keys())
        assert keys == ["meta", "model_role", "tools"], (
            f"Expected ['meta', 'model_role', 'tools'], got {keys}"
        )


class TestModelRole:
    """Tests for model_role section (replaces provider_preferences)."""

    def test_model_role_exists(self):
        """model_role key must exist."""
        data = _load_frontmatter()
        assert "model_role" in data

    def test_model_role_is_research_chain(self):
        """model_role must be the [research, general] fallback chain.

        'research' is the semantically correct primary role (deep investigation /
        multi-source synthesis) and is a real role defined in the routing-matrix
        bundle's role definitions and every curated matrix. Per the routing-matrix
        role definitions, the documented example chain for this role is
        [research, general] so it degrades to the universal catch-all when the
        research candidates' providers are not installed.
        """
        data = _load_frontmatter()
        role = data["model_role"]
        assert isinstance(role, list), f"Expected a fallback chain list, got {role!r}"
        assert role[0] == "research", f"Chain must start with 'research', got {role!r}"
        assert role[-1] in ("general", "fast"), (
            f"Chain must end with a universal catch-all (general/fast), got {role!r}"
        )
        assert role == ["research", "general"], (
            f"Expected ['research', 'general'], got {role!r}"
        )

    def test_no_provider_preferences(self):
        """provider_preferences must NOT be present (replaced by model_role)."""
        data = _load_frontmatter()
        assert "provider_preferences" not in data, (
            "provider_preferences should be removed; use model_role instead"
        )


class TestTools:
    """Tests for tools section."""

    def test_tools_exists(self):
        """tools key must exist."""
        data = _load_frontmatter()
        assert "tools" in data

    def test_two_tools(self):
        """Should have exactly two tool entries."""
        data = _load_frontmatter()
        tools = data["tools"]
        assert len(tools) == 2, f"Expected 2 tools, got {len(tools)}"

    def test_tool_perplexity_search_present(self):
        """tool-perplexity-search must be present by name."""
        data = _load_frontmatter()
        tool_names = [t["module"] for t in data["tools"]]
        assert "tool-perplexity-search" in tool_names, (
            f"tool-perplexity-search not found in tools: {tool_names}"
        )

    def test_tool_web_present(self):
        """tool-web must be present by name."""
        data = _load_frontmatter()
        tool_names = [t["module"] for t in data["tools"]]
        assert "tool-web" in tool_names, (
            f"tool-web not found in tools: {tool_names}"
        )

    def test_tool_perplexity_search_source(self):
        """tool-perplexity-search must have correct git source URL."""
        data = _load_frontmatter()
        tool = next(t for t in data["tools"] if t["module"] == "tool-perplexity-search")
        expected_source = (
            "git+https://github.com/colombod/amplifier-bundle-perplexity@main"
            "#subdirectory=modules/tool-perplexity-search"
        )
        assert tool["source"] == expected_source

    def test_tool_web_source(self):
        """tool-web must have correct git source URL."""
        data = _load_frontmatter()
        tool = next(t for t in data["tools"] if t["module"] == "tool-web")
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
