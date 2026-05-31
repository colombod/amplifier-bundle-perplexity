"""Tests for behavior YAML wiring.

Verifies that behaviors/perplexity-research.yaml includes a hooks: entry for
hooks-perplexity-nudge with the required conservative config.

Uses _find_repo_root() that walks up until bundle.md is found (same helper
pattern as tool-perplexity-search tests).
"""

from __future__ import annotations

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
BEHAVIOR_PATH = REPO_ROOT / "behaviors" / "perplexity-research.yaml"


def _load_behavior() -> dict:
    with open(BEHAVIOR_PATH) as f:
        return yaml.safe_load(f)


class TestBehaviorHooksWiring:
    """The behavior YAML must contain a hooks: entry for hooks-perplexity-nudge."""

    def test_behavior_file_exists(self) -> None:
        """behaviors/perplexity-research.yaml must exist."""
        assert BEHAVIOR_PATH.exists(), f"Behavior file not found: {BEHAVIOR_PATH}"

    def test_hooks_section_present(self) -> None:
        """perplexity-research.yaml must have a hooks: section."""
        data = _load_behavior()
        assert "hooks" in data, (
            "behaviors/perplexity-research.yaml must have a 'hooks:' key. "
            f"Got keys: {list(data.keys())}"
        )

    def test_nudge_hook_entry_present(self) -> None:
        """hooks: section must include an entry for hooks-perplexity-nudge."""
        data = _load_behavior()
        hooks = data.get("hooks", [])
        module_names = [h.get("module") for h in hooks if isinstance(h, dict)]
        assert "hooks-perplexity-nudge" in module_names, (
            f"hooks: section must contain 'hooks-perplexity-nudge'. Got: {module_names}"
        )

    def test_nudge_hook_has_config(self) -> None:
        """The hooks-perplexity-nudge entry must have a config: block."""
        data = _load_behavior()
        hooks = data.get("hooks", [])
        nudge = next(
            (h for h in hooks if h.get("module") == "hooks-perplexity-nudge"), None
        )
        assert nudge is not None, "hooks-perplexity-nudge entry not found"
        assert "config" in nudge, "hooks-perplexity-nudge entry must have a 'config:' block"

    def test_nudge_hook_enabled_true(self) -> None:
        """The hooks-perplexity-nudge config must have enabled: true."""
        data = _load_behavior()
        hooks = data.get("hooks", [])
        nudge = next(
            (h for h in hooks if h.get("module") == "hooks-perplexity-nudge"), None
        )
        assert nudge is not None, "hooks-perplexity-nudge entry not found"
        config = nudge.get("config", {})
        assert config.get("enabled") is True, (
            f"hooks-perplexity-nudge config.enabled must be true, got: {config.get('enabled')}"
        )

    def test_nudge_hook_conservative_cooldown(self) -> None:
        """cooldown_turns must be >= 4 (conservative default)."""
        data = _load_behavior()
        hooks = data.get("hooks", [])
        nudge = next(
            (h for h in hooks if h.get("module") == "hooks-perplexity-nudge"), None
        )
        assert nudge is not None
        config = nudge.get("config", {})
        cooldown = config.get("cooldown_turns", 0)
        assert cooldown >= 4, (
            f"cooldown_turns should be >= 4 (conservative). Got: {cooldown}"
        )

    def test_nudge_hook_conservative_max_injections(self) -> None:
        """max_injections must be small (conservative default, <= 10)."""
        data = _load_behavior()
        hooks = data.get("hooks", [])
        nudge = next(
            (h for h in hooks if h.get("module") == "hooks-perplexity-nudge"), None
        )
        assert nudge is not None
        config = nudge.get("config", {})
        max_inj = config.get("max_injections", 100)
        assert max_inj <= 10, (
            f"max_injections should be small/conservative (<= 10). Got: {max_inj}"
        )
