"""Tests for build_reminder() content.

Verifies the reminder has all required elements: XML wrapper, source tag,
perplexity:research-expert delegation, and pause/reassess language.
"""

from __future__ import annotations

from amplifier_module_hooks_perplexity_nudge import build_reminder


class TestReminderTemplateContent:
    """Verify build_reminder() produces correct content."""

    def test_has_system_reminder_xml_wrapper(self) -> None:
        """Reminder must be wrapped in system-reminder XML tags."""
        text = build_reminder()
        assert '<system-reminder source="hooks-perplexity-nudge">' in text
        assert "</system-reminder>" in text

    def test_has_correct_source_attribute(self) -> None:
        """Source attribute must be 'hooks-perplexity-nudge'."""
        text = build_reminder()
        assert 'source="hooks-perplexity-nudge"' in text

    def test_mentions_perplexity_research_expert(self) -> None:
        """Reminder must direct to perplexity:research-expert."""
        text = build_reminder()
        assert "perplexity:research-expert" in text

    def test_contains_pause_and_reassess_language(self) -> None:
        """Reminder must instruct to pause and reassess."""
        text = build_reminder()
        assert "Pause" in text or "pause" in text
        assert "reassess" in text

    def test_contains_looping_or_guessing_language(self) -> None:
        """Reminder must describe the stuck/looping condition."""
        text = build_reminder()
        # The reminder should describe the stuck state
        assert "looping" in text or "guessing" in text or "stuck" in text

    def test_is_concise(self) -> None:
        """Reminder should be concise — no more than 8 non-empty lines."""
        text = build_reminder()
        lines = [line for line in text.strip().splitlines() if line.strip()]
        assert len(lines) <= 8, f"Expected ≤8 non-empty lines, got {len(lines)}: {lines}"

    def test_no_markdown_bold_formatting(self) -> None:
        """Reminder should not use markdown bold (**) formatting."""
        text = build_reminder()
        assert "**" not in text

    def test_is_deterministic(self) -> None:
        """build_reminder() must return the same text on every call."""
        assert build_reminder() == build_reminder()

    def test_mentions_authoritative_answers(self) -> None:
        """Reminder should mention getting authoritative or multi-source answers."""
        text = build_reminder()
        assert "authoritative" in text or "multi-source" in text
