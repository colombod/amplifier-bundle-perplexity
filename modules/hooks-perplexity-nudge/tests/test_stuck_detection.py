"""Comprehensive tests for stuck-detection logic.

Covers:
- FIRES: repeated identical error; repeated identical tool call; struggle-no-progress
- DOES NOT FIRE: disabled; within cooldown; cap reached; research used recently;
  single normal call; normal productive turns; knowledge-present guard (recent
  successful result even if earlier error existed); struggle phrase but progress
  followed; session isolation / LRU eviction
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from amplifier_module_hooks_perplexity_nudge import PerplexityNudgeHook, NudgeConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_hook(**kwargs: Any) -> PerplexityNudgeHook:
    """Create a hook with conservative defaults, optionally overriding config fields."""
    config = NudgeConfig(
        enabled=kwargs.pop("enabled", True),
        cooldown_turns=kwargs.pop("cooldown_turns", 0),  # Disable cooldown for most tests
        scan_depth=kwargs.pop("scan_depth", 10),
        max_injections=kwargs.pop("max_injections", 10),
        loop_threshold=kwargs.pop("loop_threshold", 3),
        error_repeat_threshold=kwargs.pop("error_repeat_threshold", 2),
        max_sessions=kwargs.pop("max_sessions", 64),
    )
    return PerplexityNudgeHook(config)


def _tool_msg(content: str) -> dict[str, Any]:
    """Build a tool-result message."""
    return {"role": "tool", "content": content}


def _assistant_msg(
    text: str = "",
    tool_calls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build an assistant message, optionally with tool_calls."""
    msg: dict[str, Any] = {"role": "assistant", "content": text}
    if tool_calls is not None:
        msg["tool_calls"] = tool_calls
    return msg


def _user_msg(content: str) -> dict[str, Any]:
    return {"role": "user", "content": content}


def _tool_call(name: str, args: str | dict[str, Any]) -> dict[str, Any]:
    """Build a tool_calls entry."""
    if isinstance(args, dict):
        import json
        args = json.dumps(args)
    return {"type": "function", "function": {"name": name, "arguments": args}}


def _make_data(
    messages: list[dict[str, Any]],
    session_id: str = "sess-1",
) -> dict[str, Any]:
    return {"session_id": session_id, "messages": messages}


def _fires(hook: PerplexityNudgeHook, data: dict[str, Any]) -> bool:
    """Run the hook and return True if it injects context."""
    result = asyncio.run(hook.on_provider_request("provider:request", data))
    return getattr(result, "action", None) == "inject_context"


# ---------------------------------------------------------------------------
# Fires: Signal A — repeated identical error
# ---------------------------------------------------------------------------


class TestFiresRepeatedError:
    """Signal A: same error appears >= error_repeat_threshold times."""

    def test_fires_on_repeated_identical_error(self) -> None:
        hook = _make_hook(error_repeat_threshold=2)
        error = "Error: connection refused to database"
        data = _make_data([
            _tool_msg(error),
            _tool_msg(error),
        ])
        assert _fires(hook, data)

    def test_fires_with_threshold_3(self) -> None:
        hook = _make_hook(error_repeat_threshold=3)
        error = "Error: file not found /some/path/file.txt"
        data = _make_data([
            _tool_msg(error),
            _tool_msg(error),
            _tool_msg(error),
        ])
        assert _fires(hook, data)

    def test_does_not_fire_below_threshold(self) -> None:
        hook = _make_hook(error_repeat_threshold=2)
        error = "Error: connection refused"
        data = _make_data([_tool_msg(error)])  # Only 1 occurrence
        assert not _fires(hook, data)

    def test_normalizes_paths_in_errors(self) -> None:
        """Two errors differing only in path prefix should match."""
        hook = _make_hook(error_repeat_threshold=2)
        data = _make_data([
            _tool_msg("Error: not found /home/user/project/file.py line 42"),
            _tool_msg("Error: not found /home/other/project/other.py line 99"),
        ])
        assert _fires(hook, data)

    def test_normalizes_whitespace_in_errors(self) -> None:
        """Errors with different whitespace should still match."""
        hook = _make_hook(error_repeat_threshold=2)
        data = _make_data([
            _tool_msg("Error:   connection  refused"),
            _tool_msg("Error: connection refused"),
        ])
        assert _fires(hook, data)


# ---------------------------------------------------------------------------
# Fires: Signal B — repeated identical tool call
# ---------------------------------------------------------------------------


class TestFiresToolLoop:
    """Signal B: same tool+args called >= loop_threshold times."""

    def test_fires_on_identical_tool_calls(self) -> None:
        hook = _make_hook(loop_threshold=3)
        tc = _tool_call("read_file", {"file_path": "/foo/bar.py"})
        data = _make_data([
            _assistant_msg(tool_calls=[tc]),
            _assistant_msg(tool_calls=[tc]),
            _assistant_msg(tool_calls=[tc]),
        ])
        assert _fires(hook, data)

    def test_fires_with_json_arg_normalization(self) -> None:
        """Same args with different key order or whitespace should match."""
        hook = _make_hook(loop_threshold=3)
        tc1 = _tool_call("bash", '{"command": "ls -la", "timeout": 30}')
        tc2 = _tool_call("bash", '{"timeout": 30, "command": "ls -la"}')
        data = _make_data([
            _assistant_msg(tool_calls=[tc1]),
            _assistant_msg(tool_calls=[tc2]),
            _assistant_msg(tool_calls=[tc1]),
        ])
        assert _fires(hook, data)

    def test_does_not_fire_below_loop_threshold(self) -> None:
        hook = _make_hook(loop_threshold=3)
        tc = _tool_call("read_file", {"file_path": "/foo/bar.py"})
        data = _make_data([
            _assistant_msg(tool_calls=[tc]),
            _assistant_msg(tool_calls=[tc]),
        ])
        assert not _fires(hook, data)

    def test_different_tool_names_do_not_trigger(self) -> None:
        hook = _make_hook(loop_threshold=3)
        data = _make_data([
            _assistant_msg(tool_calls=[_tool_call("read_file", {"file_path": "/a"})]),
            _assistant_msg(tool_calls=[_tool_call("write_file", {"file_path": "/a"})]),
            _assistant_msg(tool_calls=[_tool_call("bash", {"command": "ls"})]),
        ])
        assert not _fires(hook, data)

    def test_different_args_do_not_trigger(self) -> None:
        hook = _make_hook(loop_threshold=3)
        data = _make_data([
            _assistant_msg(tool_calls=[_tool_call("read_file", {"file_path": "/a"})]),
            _assistant_msg(tool_calls=[_tool_call("read_file", {"file_path": "/b"})]),
            _assistant_msg(tool_calls=[_tool_call("read_file", {"file_path": "/c"})]),
        ])
        assert not _fires(hook, data)


# ---------------------------------------------------------------------------
# Fires: Signal C — struggle phrase with no progress
# ---------------------------------------------------------------------------


class TestFiresStruggleNoProgress:
    """Signal C: struggle phrase in assistant text with no successful result after."""

    def test_fires_on_stuck_phrase_with_no_tool_result(self) -> None:
        hook = _make_hook()
        data = _make_data([
            _user_msg("Fix the import error"),
            _assistant_msg("I'm stuck, I can't figure out why this fails."),
        ])
        assert _fires(hook, data)

    def test_fires_on_still_failing_phrase(self) -> None:
        hook = _make_hook()
        data = _make_data([
            _assistant_msg("Still failing, not sure what's wrong here."),
        ])
        assert _fires(hook, data)

    def test_fires_on_going_in_circles_phrase(self) -> None:
        hook = _make_hook()
        data = _make_data([
            _assistant_msg("We're going in circles here."),
        ])
        assert _fires(hook, data)

    def test_fires_on_multiple_struggle_phrases(self) -> None:
        hook = _make_hook()
        data = _make_data([
            _assistant_msg("Still not working, keep getting the same error."),
        ])
        assert _fires(hook, data)

    def test_fires_struggle_followed_only_by_error_result(self) -> None:
        """Error result after struggle phrase does not count as progress."""
        hook = _make_hook()
        data = _make_data([
            _assistant_msg("I can't figure out what's wrong."),
            _tool_msg("Error: process failed"),  # Short error — not progress
        ])
        assert _fires(hook, data)


# ---------------------------------------------------------------------------
# Does NOT fire: conservative suppress conditions
# ---------------------------------------------------------------------------


class TestDoesNotFireConservativeCases:
    """Critical: verify the hook never fires on safe, normal sessions."""

    def test_does_not_fire_when_disabled(self) -> None:
        hook = _make_hook(enabled=False)
        # Use signals that would normally fire
        error = "Error: connection refused"
        data = _make_data([_tool_msg(error), _tool_msg(error)])
        assert not _fires(hook, data)

    def test_does_not_fire_within_cooldown(self) -> None:
        hook = _make_hook(cooldown_turns=6)
        state = hook._get_or_create_state("sess-cd")
        # Simulate a recent injection (turns_since_injection = 0 → within cooldown)
        state.turns_since_injection = 0
        error = "Error: connection refused"
        data = _make_data([_tool_msg(error), _tool_msg(error)], session_id="sess-cd")
        assert not _fires(hook, data)

    def test_does_not_fire_when_cap_reached(self) -> None:
        hook = _make_hook(max_injections=3)
        state = hook._get_or_create_state("sess-cap")
        state.total_injections = 3  # Cap reached
        error = "Error: connection refused"
        data = _make_data([_tool_msg(error), _tool_msg(error)], session_id="sess-cap")
        assert not _fires(hook, data)

    def test_does_not_fire_when_perplexity_research_used(self) -> None:
        hook = _make_hook()
        # perplexity_research mentioned in window → suppress
        data = _make_data([
            _tool_msg("Results from perplexity_research: lots of content " * 20),
            _assistant_msg("I'm stuck on this."),
        ])
        assert not _fires(hook, data)

    def test_does_not_fire_when_research_expert_mentioned(self) -> None:
        hook = _make_hook()
        data = _make_data([
            _assistant_msg(
                "I'm stuck. Let me delegate to perplexity:research-expert."
            ),
        ])
        assert not _fires(hook, data)

    def test_does_not_fire_on_single_normal_tool_call(self) -> None:
        hook = _make_hook(loop_threshold=3, error_repeat_threshold=2)
        data = _make_data([
            _assistant_msg(tool_calls=[_tool_call("read_file", {"file_path": "/a"})]),
            _tool_msg("File content: " + "x" * 300),  # Successful result
        ])
        assert not _fires(hook, data)

    def test_does_not_fire_on_normal_productive_turns(self) -> None:
        hook = _make_hook()
        data = _make_data([
            _user_msg("Implement feature X"),
            _assistant_msg("Let me read the file.", tool_calls=[
                _tool_call("read_file", {"file_path": "/src/foo.py"})
            ]),
            _tool_msg("def foo():\n    pass\n" + "x" * 300),
            _assistant_msg("Now I'll edit it.", tool_calls=[
                _tool_call("edit_file", {"file_path": "/src/foo.py", "content": "new"})
            ]),
            _tool_msg("File written successfully with some content info " * 5),
        ])
        assert not _fires(hook, data)

    def test_does_not_fire_when_most_recent_result_is_successful(self) -> None:
        """KNOWLEDGE-PRESENT GUARD: earlier error but recent success → do NOT fire.

        This is the key scenario: the session had an error, but subsequently
        got a successful, content-bearing result. The session is making progress
        and must not be nudged.
        """
        hook = _make_hook(error_repeat_threshold=2)
        big_content = "def some_function():\n" + "    pass\n" * 50  # > 200 chars
        data = _make_data([
            _tool_msg("Error: file not found"),
            _tool_msg("Error: file not found"),  # 2 identical errors → would normally fire
            _tool_msg(big_content),  # BUT most recent result is a success
        ])
        # The knowledge-present guard must suppress this even though signal A fires
        assert not _fires(hook, data)

    def test_does_not_fire_when_struggle_followed_by_successful_result(self) -> None:
        """Signal C suppressed: struggle phrase but progress was made after."""
        hook = _make_hook()
        big_content = "The answer is: " + "detail " * 50  # > 200 chars
        data = _make_data([
            _assistant_msg("I'm stuck, not sure what's wrong."),
            _tool_msg(big_content),  # Successful result AFTER the struggle phrase
        ])
        assert not _fires(hook, data)

    def test_does_not_fire_struggle_with_long_success_after_it(self) -> None:
        """Signal C gated: if a substantial successful result came after the struggle, no fire."""
        hook = _make_hook()
        success = "Here are the search results: " + "result item\n" * 30  # > 200 chars
        data = _make_data([
            _assistant_msg("Still not working, let me try a search."),
            _tool_msg(success),
        ])
        assert not _fires(hook, data)

    def test_does_not_fire_on_empty_messages(self) -> None:
        hook = _make_hook()
        data = {"session_id": "sess-1", "messages": []}
        assert not _fires(hook, data)


# ---------------------------------------------------------------------------
# Knowledge-present guard: explicit boundary tests
# ---------------------------------------------------------------------------


class TestKnowledgePresentGuard:
    """Verify the guard correctly identifies successful vs failed results."""

    def test_short_tool_result_not_treated_as_knowledge(self) -> None:
        """A short result (< 200 chars) is not 'content-bearing' even if not an error."""
        hook = _make_hook()
        error = "Error: connection refused"
        data = _make_data([
            _tool_msg(error),
            _tool_msg(error),
            _tool_msg("OK"),  # Very short success — too small to be "knowledge"
        ])
        # Short last result → guard does NOT suppress → repeated-error signal fires
        assert _fires(hook, data)

    def test_long_successful_result_suppresses(self) -> None:
        """A long non-error result suppresses even in presence of earlier errors."""
        hook = _make_hook(error_repeat_threshold=2)
        success = "The documentation says: " + "word " * 100  # > 200 chars, no error
        data = _make_data([
            _tool_msg("Error: something failed"),
            _tool_msg("Error: something failed"),
            _tool_msg(success),  # Most recent is a substantial success
        ])
        assert not _fires(hook, data)

    def test_error_result_with_long_content_does_not_suppress(self) -> None:
        """A long but error-bearing result should NOT suppress (it's still an error)."""
        hook = _make_hook()
        # A long error message — has error indicator at start
        long_error = "Error: connection refused to remote host. " + "Details: " * 50
        data = _make_data([
            _assistant_msg("I'm stuck."),
            _tool_msg(long_error),
        ])
        # Long error → knowledge guard does NOT suppress → signal C fires
        assert _fires(hook, data)

    def test_guard_uses_most_recent_not_any(self) -> None:
        """The guard checks ONLY the most recent tool result, not any tool result."""
        hook = _make_hook()
        big_success = "File contents: " + "line\n" * 50  # > 200 chars, no error
        error = "Error: permission denied"
        data = _make_data([
            _tool_msg(big_success),  # Early big success
            _assistant_msg("I'm stuck still."),
            _tool_msg(error),       # MOST RECENT is an error
        ])
        # Most recent is error → guard does NOT suppress → signal C fires
        assert _fires(hook, data)


# ---------------------------------------------------------------------------
# Session isolation and LRU eviction
# ---------------------------------------------------------------------------


class TestSessionIsolation:
    """State is isolated per session; LRU evicts oldest when max_sessions exceeded."""

    def test_sessions_are_isolated(self) -> None:
        """Injection in one session must not affect another."""
        hook = _make_hook(cooldown_turns=6)
        error = "Error: connection refused"
        msgs = [_tool_msg(error), _tool_msg(error)]

        # Fire in session A
        data_a = _make_data(msgs, session_id="sess-a")
        _fires(hook, data_a)  # This fires and sets turns_since_injection = 0

        # Session B should still fire (no cooldown shared)
        data_b = _make_data(msgs, session_id="sess-b")
        assert _fires(hook, data_b)

    def test_lru_eviction(self) -> None:
        """With max_sessions=2, adding a third session evicts the oldest."""
        hook = _make_hook(max_sessions=2, cooldown_turns=6)
        error = "Error: connection refused"
        msgs = [_tool_msg(error), _tool_msg(error)]

        # Prime sessions A and B
        hook._get_or_create_state("sess-a").turns_since_injection = 0
        hook._get_or_create_state("sess-b").turns_since_injection = 0
        assert len(hook._state) == 2

        # Adding session C evicts A (oldest)
        hook._get_or_create_state("sess-c")
        assert len(hook._state) == 2
        assert "sess-a" not in hook._state
        assert "sess-b" in hook._state
        assert "sess-c" in hook._state

    def test_cooldown_does_not_cross_sessions(self) -> None:
        """Cooldown state is not shared across sessions."""
        hook = _make_hook(cooldown_turns=10)
        error = "Error: database down"
        msgs = [_tool_msg(error), _tool_msg(error)]

        # Session A fires (injection resets its counter)
        data_a = _make_data(msgs, session_id="sess-x")
        assert _fires(hook, data_a)

        # Session B is fresh — should still fire despite A being in cooldown
        data_b = _make_data(msgs, session_id="sess-y")
        assert _fires(hook, data_b)


# ---------------------------------------------------------------------------
# Anti-spam guard: cap and cooldown
# ---------------------------------------------------------------------------


class TestAntiSpam:
    """Verify cap and cooldown prevent repeated injections."""

    def test_cap_prevents_further_injections(self) -> None:
        """Once max_injections is reached, the hook stops firing."""
        hook = _make_hook(max_injections=2, cooldown_turns=0)
        error = "Error: connection refused"
        msgs = [_tool_msg(error), _tool_msg(error)]
        data = _make_data(msgs, session_id="sess-cap")

        # First two calls fire
        assert _fires(hook, data)
        # Reset cooldown (set high) for next call
        hook._state["sess-cap"].turns_since_injection = 999
        assert _fires(hook, data)
        # Third call: cap reached
        hook._state["sess-cap"].turns_since_injection = 999
        assert not _fires(hook, data)

    def test_cooldown_prevents_consecutive_injections(self) -> None:
        """Within cooldown window, the hook does not fire again."""
        hook = _make_hook(cooldown_turns=5)
        error = "Error: connection refused"
        msgs = [_tool_msg(error), _tool_msg(error)]
        data = _make_data(msgs, session_id="sess-cool")

        # First call fires
        assert _fires(hook, data)

        # Immediately after (turns_since_injection = 1) — within cooldown
        assert not _fires(hook, data)
