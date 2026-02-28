# Perplexity Bundle Sync & Provider Preferences Design

## Goal

Improve the amplifier-bundle-perplexity by adding provider preferences to the research-expert agent (haiku-tier model) and fixing all sync issues between the tool implementation (which evolved to support dual research+chat modes) and the stale docs, agent prompt, and tests.

## Background

The Perplexity bundle's tool module evolved to support a dual-mode architecture (Research API + Chat API with auto-fallback) but the surrounding surfaces -- agent prompt, context docs, behavior config, and tests -- were never updated to match. This creates three problems:

1. **Cost waste**: The research-expert agent inherits the parent session's model (often a full-size reasoning model) even though it only orchestrates Perplexity API calls and doesn't need heavy reasoning capability.
2. **Stale documentation**: The agent prompt, research-awareness context, and RESEARCH_GUIDE all reference a `preset` parameter that no longer exists in the tool's input schema, while the actual `mode`/`model` parameters are undocumented.
3. **Broken tests**: Test mocks target the old `_make_request()` method, assert the old schema, and expect the old citation format -- none of which match the current implementation.

## Approach

**Incremental Sync (Approach A)**: Fix everything in the current architecture without changing the tool's dual-mode design. Bring all surfaces into alignment with the existing implementation. The tool module itself is correct and unchanged.

## Validation Data

Three validation recipes were run against the repo before design began:

| Recipe | Result | Key Findings |
|--------|--------|-------------|
| Bundle Repo Validation | PASS (3 suggestions) | Textbook thin bundle, excellent context sink discipline, sync issues flagged |
| Agent Validation | PASS (1 warning, 2 suggestions) | No explicit `tools:` section, weak activation triggers, missing HOW dimension |
| Repo Audit | Recipe bug | Undefined `{{existing_pr_check}}` variable -- recipe defect, not a repo problem |

## Components

### Section 1: Provider Preferences for research-expert Agent

Add `provider_preferences` to the agent's YAML frontmatter targeting haiku-tier models:

```yaml
provider_preferences:
  - provider: anthropic
    model: claude-haiku-*
  - provider: openai
    model: gpt-5-mini
```

**Rationale**: The agent orchestrates Perplexity API calls -- it formulates queries, chooses parameters, and structures output. The actual deep research is performed by Perplexity's servers. The agent doesn't need heavy reasoning capability. This mirrors how foundation treats similar "orchestrate a tool API" agents (web-research, file-ops, git-ops). If neither provider matches, the agent inherits the parent session's model unchanged.

### Section 2: Agent Prompt & Frontmatter Overhaul (`agents/research-expert.md`)

**2a. Frontmatter: explicit `tools:` section**

Prevents silent breakage if the agent is spawned outside its intended behavior context:

```yaml
tools:
  - module: tool-perplexity-search
    source: git+https://github.com/colombod/amplifier-bundle-perplexity@main#subdirectory=modules/tool-perplexity-search
  - module: tool-web
    source: git+https://github.com/microsoft/amplifier-module-tool-web@main
```

**2b. Replace stale preset table in agent body**

The current table conflates Research API presets (`pro-search`) with Chat API models (`sonar-pro`, `sonar-reasoning`). Replace with two separate sections matching the actual tool `input_schema`:

- **Mode selection**: `research` (deep, multi-step) vs `chat` (faster, cheaper) vs `auto` (research with chat fallback)
- **Chat model selection**: `sonar-pro` (comprehensive), `sonar` (fast), `sonar-reasoning` (with reasoning)
- Remove all references to `preset` parameter (no longer in the tool's schema)

**2c. Strengthen description per agent validation findings**

- Change "When to delegate:" to "MUST be used when:" with imperative language
- Add "Authoritative on:" block -- multi-source synthesis, citation-backed research, current events, domain-specific deep dives, structured reference output
- Add "How it works:" block -- Uses Perplexity's Agentic Research API for autonomous multi-step web research with source discovery. Returns categorized references for downstream agents.

### Section 3: Context & Documentation Sync

**3a. `context/research-awareness.md`** (injected into parent sessions via behavior)

- Remove stale claim: "pro-search preset (the only valid preset for this API)"
- Replace with actual tool parameters: `mode` (research/chat/auto), `model` (sonar-pro/sonar/sonar-reasoning)
- Keep `reasoning_effort`, `max_steps`, `instructions` (still accurate)

**3b. `docs/RESEARCH_GUIDE.md`** (injected into agent via `@` reference)

- Split into two clear sections: Research API (`/v1/responses`) and Chat API (`/v1/chat/completions`)
- Research API: uses `pro-search` preset (hardcoded), controlled by `reasoning_effort` and `max_steps`
- Chat API: uses `model` parameter (`sonar-pro`, `sonar`, `sonar-reasoning`)
- Remove `fast-search` and `deep-research` from documentation (unreachable from current tool schema)

**3c. `context/cost-guidance.md`**: Already accurate. No changes needed.

### Section 4: Behavior Config Cleanup (`behaviors/perplexity-research.yaml`)

Remove dead `preset` field from behavior config. The tool's `_make_research_request` method hardcodes `preset="pro-search"` and ignores `self.preset`. The config field is dead code that creates false expectations.

Keep only fields that actually affect runtime behavior:

```yaml
config:
  reasoning_effort: medium
  max_steps: 5
  timeout: 120.0
```

This is a pure cleanup -- no runtime behavior changes.

### Section 5: Test Fixes (`tests/test_tool.py`)

Fix tests to match the existing implementation (not the other way around). The dual-mode architecture is sound; the tests fell behind.

**5a. Method name mismatch**: Update mock targets from `_make_request()` to `_make_research_request()` and `_make_chat_request()`.

**5b. Schema assertions**: Replace assertions checking for `preset` in `input_schema["properties"]` with assertions for the actual fields: `mode`, `model`, `reasoning_effort`, `max_steps`, `instructions`.

**5c. Citation format**: Update assertions from string format (`"Title: URL"`) to structured dict format (`{"url": ..., "title": ..., "category": ...}`).

## Files Changed

| File | Change Type | Summary |
|------|-------------|---------|
| `agents/research-expert.md` | Major rewrite | provider_preferences, tools section, mode/model docs, stronger triggers |
| `behaviors/perplexity-research.yaml` | Minor edit | Remove dead `preset` config field |
| `context/research-awareness.md` | Moderate rewrite | Replace stale preset docs with mode/model docs |
| `docs/RESEARCH_GUIDE.md` | Moderate rewrite | Split into Research API vs Chat API sections |
| `tests/test_tool.py` | Moderate rewrite | Fix mock targets, schema assertions, citation format |

## What Does NOT Change

- **`modules/tool-perplexity-search/`** -- the tool implementation is correct as-is
- **`bundle.md`** -- already clean
- **`context/cost-guidance.md`** -- already accurate
- **The dual-mode architecture** (research + chat + auto fallback) -- sound design
- **`recipes/`** -- they reference the agent, not the tool directly

## Error Handling

No new error handling is introduced. The existing tool-level error handling (API failures, timeout, fallback from research to chat in `auto` mode) is unaffected. The `provider_preferences` fallback is handled by the Amplifier runtime: if no preferred provider/model is available, the parent session's model is inherited.

## Testing Strategy

1. **Unit tests** (`tests/test_tool.py`): Fix the three breakages (mock targets, schema assertions, citation format) so tests pass against the current implementation.
2. **Bundle validation recipe**: Re-run after changes; expect the 3 sync-related suggestions to clear.
3. **Agent validation recipe**: Re-run after changes; expect the `tools:` warning and trigger/description suggestions to clear.
4. **Manual smoke test**: Spawn the research-expert agent and confirm it (a) runs on a haiku-tier model and (b) correctly executes research and chat mode queries.

## Success Criteria

1. research-expert agent spawns on haiku-tier model instead of inheriting parent's model
2. All documentation surfaces accurately describe the tool's actual `mode`/`model` parameters
3. No references to stale `preset` parameter in agent-facing or user-facing docs
4. Tests pass against the current implementation
5. Bundle validation and agent validation recipes produce cleaner results on re-run
