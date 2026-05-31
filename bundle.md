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

@perplexity:context/research-awareness.md

@foundation:context/shared/common-system-base.md
