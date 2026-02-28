"""Tests for perplexity-research behavior YAML configuration."""

from pathlib import Path

import yaml


BEHAVIOR_PATH = Path(__file__).parent.parent / "behaviors" / "perplexity-research.yaml"


class TestBehaviorConfig:
    """Tests for the behavior YAML config section."""

    def test_no_preset_in_config(self):
        """Config should NOT contain 'preset' - it's hardcoded in the tool and ignored."""
        with open(BEHAVIOR_PATH) as f:
            data = yaml.safe_load(f)

        config = data["tools"][0]["config"]
        assert "preset" not in config, (
            "preset should not be in config - it's dead code "
            "(hardcoded in _make_research_request)"
        )

    def test_no_preset_anywhere_in_file(self):
        """The word 'preset' should not appear anywhere in the file."""
        content = BEHAVIOR_PATH.read_text()
        assert "preset" not in content, (
            "No mention of 'preset' should remain in the behavior YAML"
        )

    def test_expected_config_keys_present(self):
        """Config should contain only reasoning_effort, max_steps, timeout."""
        with open(BEHAVIOR_PATH) as f:
            data = yaml.safe_load(f)

        config = data["tools"][0]["config"]
        expected_keys = {"reasoning_effort", "max_steps", "timeout"}
        assert set(config.keys()) == expected_keys, (
            f"Expected config keys {expected_keys}, got {set(config.keys())}"
        )

    def test_config_indentation_preserved(self):
        """Config keys should be indented with 6 spaces."""
        content = BEHAVIOR_PATH.read_text()
        lines = content.splitlines()

        # Collect config key lines: non-empty, non-comment lines under config:
        in_config = False
        config_key_lines = []
        for line in lines:
            if line.strip().startswith("config:"):
                in_config = True
                continue
            if in_config and line.strip() and not line.strip().startswith("#"):
                # A line with less indentation means we left the config section
                if ":" in line and len(line) - len(line.lstrip()) < 6:
                    break
                if ":" in line.split("#")[0]:
                    config_key_lines.append(line)

        assert config_key_lines, "No config key lines found"
        for line in config_key_lines:
            assert line.startswith("      "), f"Bad indentation: {line!r}"
