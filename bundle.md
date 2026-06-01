---
bundle:
  name: perplexity
  version: 1.0.0
  description: Deep research capabilities via Perplexity's Agentic Research API

includes:
  # Inherit foundation's tools, session config, agents
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  # Our research behavior (adds research-expert agent + tool + context)
  - bundle: perplexity:behaviors/perplexity-research
---

# Perplexity Deep Research

<!--
  Awareness context (research-awareness.md) is injected once via the behavior's
  `context.include` (behaviors/perplexity-research.yaml). It is intentionally NOT
  @mentioned here to avoid a double-load in the standalone root-bundle path —
  the body-instruction channel and the behavior's context.include channel are not
  cross-deduplicated. The behavior is the single source of the awareness injection.
-->

@foundation:context/shared/common-system-base.md
