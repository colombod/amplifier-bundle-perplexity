"""Perplexity Nudge Hook Module

Detects when a session is genuinely STUCK — spinning in circles, repeating
errors, or looping tool calls — and injects a single, conservative
<system-reminder> nudging the agent to pause and delegate to
perplexity:research-expert for authoritative, outside information.

STUCK SIGNALS (requires at least one high-confidence, objective signal):
  (A) REPEATED ERROR: The same/similar error text appears >=
      error_repeat_threshold times across recent tool results.
      Paths and line numbers are normalized before comparison.
  (B) TOOL-CALL LOOP: The same tool name with near-identical arguments is
      called >= loop_threshold times within the scan window.
  (C) STRUGGLE + NO PROGRESS (secondary, gated): Recent assistant text
      contains a struggle phrase (e.g. "i'm stuck", "still failing") AND
      no successful, content-bearing tool result followed that phrase.
      Struggle phrases alone — if progress was later made — do NOT fire.

SUPPRESS CONDITIONS (conservative — keep false positives near zero):
  1. config.enabled is False
  2. Cooldown active: turns_since_injection < cooldown_turns (default 6)
  3. Cap reached: total_injections >= max_injections (default 3)
  4. Research already used recently: the message window mentions
     perplexity_research, research-expert, or a perplexity invocation
     (turns_since_research_use < cooldown_turns mirrors deepwiki pattern)
  5. KNOWLEDGE-PRESENT GUARD: The most recent meaningful tool result in the
     window is a SUCCESSFUL, content-bearing result (non-error, length >
     knowledge_threshold). This is the critical guard — if the session
     already has fresh knowledge it is making progress and must NOT be
     nudged. Only fire when the latest signal is failure/repetition, not
     fresh successful knowledge.

Config options:
    enabled: bool (default: True)
    cooldown_turns: int (default: 6) — LLM calls between re-injections
    scan_depth: int (default: 6) — Recent messages to scan
    max_injections: int (default: 3) — Cap per session
    loop_threshold: int (default: 3) — Identical tool+args calls → signal B
    error_repeat_threshold: int (default: 2) — Error repeats → signal A
    max_sessions: int (default: 64) — Max sessions before LRU eviction
"""
from __future__ import annotations

import json
import re
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from amplifier_core import HookResult

# ---------------------------------------------------------------------------
# Reminder text
# ---------------------------------------------------------------------------

_REMINDER_SOURCE = "hooks-perplexity-nudge"

_REMINDER_TEXT = (
    f'<system-reminder source="{_REMINDER_SOURCE}">\n'
    "You appear to be looping or guessing on this without converging. Pause and reassess.\n"
    "If this needs facts, current docs, an API/contract detail, or a fresh perspective, delegate to\n"
    "perplexity:research-expert to get authoritative, multi-source answers — then continue with that\n"
    "knowledge instead of guessing. (Skip this if you already have what you need.)\n"
    "</system-reminder>"
)


def build_reminder() -> str:
    """Return the stuck-nudge system reminder string."""
    return _REMINDER_TEXT


# ---------------------------------------------------------------------------
# Detection patterns
# ---------------------------------------------------------------------------

# Struggle phrases in assistant text (signal C)
_STRUGGLE_RE = re.compile(
    r"(?:"
    r"i'?m stuck"
    r"|not sure"
    r"|still failing"
    r"|still not working"
    r"|keep getting"
    r"|can'?t figure out"
    r"|let me try another"
    r"|let me guess"
    r"|going in circles"
    r"|no idea"
    r")",
    re.IGNORECASE,
)

# Error indicators in tool results (used by signal A and knowledge-present guard)
_ERROR_INDICATOR_RE = re.compile(
    r"(?:"
    r"error:"
    r"|exception:"
    r"|traceback"
    r"|failed:"
    r"|failure:"
    r"|not found"
    r"|no such"
    r"|permission denied"
    r"|connection refused"
    r"|timed out"
    r"|timeout"
    r")",
    re.IGNORECASE,
)

# Normalisation: strip paths, line numbers, and collapse whitespace (signal A)
_PATH_RE = re.compile(r"(?:/[\w._-]+)+")
_LINE_NUM_RE = re.compile(r"\bline \d+\b")
_COLON_NUM_RE = re.compile(r":\d+:")

# Patterns indicating research was already used/mentioned recently (suppress cond 4)
_RESEARCH_USED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"perplexity_research", re.IGNORECASE),
    re.compile(r"research-expert", re.IGNORECASE),
    re.compile(r"perplexity:research", re.IGNORECASE),
    re.compile(r"perplexity\.research", re.IGNORECASE),
]

# Minimum content length to consider a tool result "meaningful / content-bearing"
_KNOWLEDGE_THRESHOLD = 200  # chars


# ---------------------------------------------------------------------------
# Config and per-session state
# ---------------------------------------------------------------------------


@dataclass
class NudgeConfig:
    """Configuration for the perplexity nudge hook."""

    enabled: bool = True
    cooldown_turns: int = 6
    scan_depth: int = 6
    max_injections: int = 3
    loop_threshold: int = 3
    error_repeat_threshold: int = 2
    max_sessions: int = 64


@dataclass
class NudgeState:
    """Tracks injection state per session."""

    turns_since_injection: int = 999  # Start high so first match can trigger
    turns_since_research_use: int = 999
    total_injections: int = 0


# ---------------------------------------------------------------------------
# Main hook class
# ---------------------------------------------------------------------------


class PerplexityNudgeHook:
    """Hook that detects stuck sessions and injects a perplexity nudge."""

    def __init__(self, config: NudgeConfig) -> None:
        self.config = config
        self._state: OrderedDict[str, NudgeState] = OrderedDict()

    # ------------------------------------------------------------------
    # Session state (LRU)
    # ------------------------------------------------------------------

    def _get_or_create_state(self, session_id: str) -> NudgeState:
        """Get or create per-session state with LRU eviction."""
        if session_id in self._state:
            self._state.move_to_end(session_id)
            return self._state[session_id]
        state = NudgeState()
        self._state[session_id] = state
        if len(self._state) > self.config.max_sessions:
            self._state.popitem(last=False)
        return state

    # ------------------------------------------------------------------
    # Protocol entry point
    # ------------------------------------------------------------------

    async def __call__(self, event: str, data: dict[str, Any]) -> HookResult:
        """HookHandler protocol entry point."""
        return await self.on_provider_request(event, data)

    async def on_provider_request(
        self, _event: str, data: dict[str, Any]
    ) -> HookResult:
        """Scan messages for stuck signals before each LLM call.

        Returns HookResult(action="inject_context") when nudge fires,
        HookResult(action="continue") otherwise.
        """
        # Suppress condition 1: disabled in config
        if not self.config.enabled:
            return HookResult(action="continue")

        session_id = data.get("session_id", "__default__")
        state = self._get_or_create_state(session_id)

        # Advance turn counters every LLM call
        state.turns_since_injection += 1
        state.turns_since_research_use += 1

        # Suppress condition 3: injection cap reached for this session
        if state.total_injections >= self.config.max_injections:
            return HookResult(action="continue")

        # Suppress condition 2: still within cooldown window
        if state.turns_since_injection < self.config.cooldown_turns:
            return HookResult(action="continue")

        messages = data.get("messages", [])
        if not messages:
            return HookResult(action="continue")

        # Scan the recent message window only
        recent = messages[-self.config.scan_depth :]

        # Suppress condition 4: research was mentioned/used in the window → reset counter
        if self._research_recently_used(recent):
            state.turns_since_research_use = 0
            return HookResult(action="continue")

        # Also suppress if research counter is still cooling down
        if state.turns_since_research_use < self.config.cooldown_turns:
            return HookResult(action="continue")

        # Suppress condition 5: KNOWLEDGE-PRESENT GUARD
        # If the most recent meaningful tool result is a successful,
        # content-bearing result the session is making progress → do NOT nudge.
        # This is the critical guard against firing when knowledge is already present.
        if self._most_recent_result_is_successful(recent):
            return HookResult(action="continue")

        # Now check fire signals — any one is sufficient
        should_fire = (
            self._detect_repeated_error(recent)
            or self._detect_tool_loop(recent)
            or self._detect_struggle_no_progress(recent)
        )

        if should_fire:
            state.turns_since_injection = 0
            state.total_injections += 1
            return HookResult(
                action="inject_context",
                context_injection=build_reminder(),
                context_injection_role="user",
                ephemeral=True,
                suppress_output=True,
            )

        return HookResult(action="continue")

    # ------------------------------------------------------------------
    # Text extraction helpers
    # ------------------------------------------------------------------

    def _extract_text(self, msg: dict[str, Any]) -> str:
        """Extract plain text content from a message of any role."""
        content = msg.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                block_type = block.get("type", "")
                if block_type == "text":
                    parts.append(block.get("text", ""))
                elif block_type == "tool_result":
                    # Nested content inside a tool_result block
                    inner = block.get("content", "")
                    if isinstance(inner, str):
                        parts.append(inner)
                    elif isinstance(inner, list):
                        for ib in inner:
                            if isinstance(ib, dict) and ib.get("type") == "text":
                                parts.append(ib.get("text", ""))
            return "\n".join(parts)
        return ""

    # ------------------------------------------------------------------
    # Suppress condition 4: research recently used
    # ------------------------------------------------------------------

    def _research_recently_used(self, recent: list[dict[str, Any]]) -> bool:
        """Return True if perplexity research was mentioned or invoked recently."""
        for msg in recent:
            text = self._extract_text(msg)
            if any(p.search(text) for p in _RESEARCH_USED_PATTERNS):
                return True
            # Also catch tool_calls that invoke the research tool directly
            if msg.get("role") == "assistant":
                for tc in msg.get("tool_calls", []) or []:
                    if not isinstance(tc, dict):
                        continue
                    fn = tc.get("function", {}) or {}
                    if "perplexity" in fn.get("name", "").lower():
                        return True
        return False

    # ------------------------------------------------------------------
    # Suppress condition 5: knowledge-present guard
    # ------------------------------------------------------------------

    def _most_recent_result_is_successful(
        self, recent: list[dict[str, Any]]
    ) -> bool:
        """Return True if the most recent meaningful tool result is successful.

        KNOWLEDGE-PRESENT GUARD (suppress condition 5):
        Walk backwards through the window to find the most recent tool-result
        message that has non-trivial content.  If that result:
          - has content length > _KNOWLEDGE_THRESHOLD (200 chars), AND
          - does NOT start with error-like text
        then the session has fresh, actionable knowledge and is making progress.
        Do NOT inject a nudge in that case.

        Only fire when the latest signal from the environment is a failure,
        empty/tiny response, or the session has no recent tool results at all.
        """
        for msg in reversed(recent):
            if msg.get("role") != "tool":
                continue
            text = self._extract_text(msg).strip()
            if len(text) < 10:
                # Trivially empty — not a meaningful result, keep scanning
                continue
            # Found the most recent non-trivial tool result.
            # Check: is it content-bearing and error-free?
            if len(text) <= _KNOWLEDGE_THRESHOLD:
                # Too short to be "knowledge" (might be a one-liner error or
                # a minimal success message like "OK" or "done").
                return False
            # Content is substantial — check for error indicators in the beginning
            beginning = text[:300].lower()
            is_error = bool(_ERROR_INDICATOR_RE.search(beginning))
            return not is_error  # True → knowledge present → suppress

        # No tool results found in window → do not suppress on this guard
        return False

    # ------------------------------------------------------------------
    # Signal A: repeated identical/similar error
    # ------------------------------------------------------------------

    def _normalize_error(self, text: str) -> str:
        """Normalise an error string for near-identical comparison.

        Strips file paths, line numbers, and collapses whitespace so that
        the same logical error from different runs matches.
        """
        text = text.lower()
        text = _PATH_RE.sub("<path>", text)
        text = _LINE_NUM_RE.sub("line N", text)
        text = _COLON_NUM_RE.sub(":N:", text)
        text = " ".join(text.split())
        return text[:200]  # Use first 200 chars as the error signature

    def _detect_repeated_error(self, recent: list[dict[str, Any]]) -> bool:
        """Signal A: same/similar error in >= error_repeat_threshold tool results."""
        error_sig_counts: dict[str, int] = {}
        for msg in recent:
            if msg.get("role") != "tool":
                continue
            text = self._extract_text(msg)
            if not _ERROR_INDICATOR_RE.search(text[:500]):
                continue  # Not an error result
            sig = self._normalize_error(text)
            if not sig:
                continue
            error_sig_counts[sig] = error_sig_counts.get(sig, 0) + 1
        return any(
            count >= self.config.error_repeat_threshold
            for count in error_sig_counts.values()
        )

    # ------------------------------------------------------------------
    # Signal B: repeated identical tool call
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_args(arguments: str | dict[str, Any]) -> str:
        """Normalise tool-call arguments for comparison.

        Parses JSON if needed, then re-serialises with sorted keys so that
        two calls with the same logical parameters match even if the literal
        argument JSON differs in whitespace or key order.
        """
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except (json.JSONDecodeError, ValueError):
                return arguments.strip()
        if isinstance(arguments, dict):
            return json.dumps(arguments, sort_keys=True)
        return str(arguments)

    def _detect_tool_loop(self, recent: list[dict[str, Any]]) -> bool:
        """Signal B: same tool + near-identical args called >= loop_threshold times."""
        call_counts: dict[tuple[str, str], int] = {}
        for msg in recent:
            if msg.get("role") != "assistant":
                continue
            for tc in msg.get("tool_calls", []) or []:
                if not isinstance(tc, dict):
                    continue
                fn = tc.get("function", {}) or {}
                name = fn.get("name", "")
                if not name:
                    continue
                args = self._normalize_args(fn.get("arguments", "{}"))
                key = (name, args)
                call_counts[key] = call_counts.get(key, 0) + 1
        return any(
            count >= self.config.loop_threshold for count in call_counts.values()
        )

    # ------------------------------------------------------------------
    # Signal C: struggle phrase with no subsequent progress
    # ------------------------------------------------------------------

    def _detect_struggle_no_progress(
        self, recent: list[dict[str, Any]]
    ) -> bool:
        """Signal C: struggle phrase in assistant text with no subsequent successful result.

        Finds the LAST assistant message containing a struggle phrase, then
        checks whether any successful, content-bearing tool result appeared
        AFTER it.  If progress was made after the struggle phrase, the session
        is no longer stuck → do NOT fire.
        """
        last_struggle_idx: int | None = None
        for i, msg in enumerate(recent):
            if msg.get("role") != "assistant":
                continue
            text = self._extract_text(msg)
            if _STRUGGLE_RE.search(text):
                last_struggle_idx = i

        if last_struggle_idx is None:
            return False  # No struggle phrase detected

        # Check for a successful, content-bearing tool result AFTER the struggle
        for msg in recent[last_struggle_idx + 1 :]:
            if msg.get("role") != "tool":
                continue
            text = self._extract_text(msg).strip()
            if len(text) > _KNOWLEDGE_THRESHOLD:
                beginning = text[:300].lower()
                if not _ERROR_INDICATOR_RE.search(beginning):
                    return False  # Progress was made after the struggle → no fire

        return True  # Struggle with no subsequent progress → fire


# ---------------------------------------------------------------------------
# mount()
# ---------------------------------------------------------------------------


async def mount(
    coordinator: Any, config: dict[str, Any] | None = None
) -> Callable[[], None] | None:
    """Mount the perplexity nudge hook module.

    Registers on provider:request and returns a cleanup callable that
    unregisters the hook.  Mirrors the deepwiki-trigger mount() contract.

    Config options:
        enabled: bool (default: True) — disable to silence entirely
        cooldown_turns: int (default: 6) — turns between re-injections
        scan_depth: int (default: 6) — recent messages to scan
        max_injections: int (default: 3) — max injections per session
        loop_threshold: int (default: 3) — threshold for signal B
        error_repeat_threshold: int (default: 2) — threshold for signal A
        max_sessions: int (default: 64) — max sessions before LRU eviction

    Returns:
        Cleanup callable that unregisters the hook handler.
    """
    config = config or {}

    nudge_config = NudgeConfig(
        enabled=config.get("enabled", True),
        cooldown_turns=config.get("cooldown_turns", 6),
        scan_depth=config.get("scan_depth", 6),
        max_injections=config.get("max_injections", 3),
        loop_threshold=config.get("loop_threshold", 3),
        error_repeat_threshold=config.get("error_repeat_threshold", 2),
        max_sessions=config.get("max_sessions", 64),
    )

    hook = PerplexityNudgeHook(nudge_config)

    # Register on provider:request — fires before every LLM call
    unregister = coordinator.hooks.register(
        "provider:request",
        hook.on_provider_request,
        priority=30,  # After skills visibility (20), before most other hooks
        name="perplexity-nudge",
    )

    def cleanup() -> None:
        """Unregister the perplexity nudge hook."""
        unregister()

    return cleanup
