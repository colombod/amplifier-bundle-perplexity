"""Tests for bundle.md frontmatter wiring.

Verifies that the bundle includes both the foundation bundle and
the perplexity research behavior.
"""

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
BUNDLE_PATH = REPO_ROOT / "bundle.md"


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from a markdown file.

    Returns the parsed frontmatter dict.
    """
    match = re.match(r"^---\n(.*?\n)---\n", content, re.DOTALL)
    assert match, "bundle.md must start with --- frontmatter --- block"
    return yaml.safe_load(match.group(1))


def test_bundle_md_exists():
    """bundle.md must exist at the repo root."""
    assert BUNDLE_PATH.exists(), "bundle.md not found at repo root"


def test_includes_section_present():
    """bundle.md must have an 'includes:' section."""
    data = _parse_frontmatter(BUNDLE_PATH.read_text())
    assert "includes" in data, "bundle.md frontmatter must have 'includes:' key"


def test_includes_foundation_bundle():
    """includes: must contain a foundation bundle reference."""
    data = _parse_frontmatter(BUNDLE_PATH.read_text())
    includes = data["includes"]
    bundle_values = [entry["bundle"] for entry in includes if "bundle" in entry]
    has_foundation = any("amplifier-foundation" in v for v in bundle_values)
    assert has_foundation, (
        f"includes: must reference amplifier-foundation bundle. Got: {bundle_values}"
    )


def test_includes_perplexity_research_behavior():
    """includes: must contain perplexity:behaviors/perplexity-research."""
    data = _parse_frontmatter(BUNDLE_PATH.read_text())
    includes = data["includes"]
    bundle_values = [entry["bundle"] for entry in includes if "bundle" in entry]
    assert "perplexity:behaviors/perplexity-research" in bundle_values, (
        "includes: must contain 'perplexity:behaviors/perplexity-research'. "
        f"Got: {bundle_values}"
    )
