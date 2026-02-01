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

<!-- Context injected via behavior's context.include - no duplication -->

## Capabilities

- **Deep Research**: Multi-step web research with citations via `perplexity_research` tool
- **Research Expert**: Specialized agent for complex research tasks (`perplexity:research-expert`)
- **Cost-Aware Guidance**: Know when to use deep research vs free alternatives

## Quick Reference

| Need | Use | Cost |
|------|-----|------|
| Deep multi-source research | `perplexity_research` tool or delegate to `perplexity:research-expert` | Token-based |
| Quick web lookup | `web_search` tool | Free |
| Fetch specific URL | `web_fetch` tool | Free |

**Note**: Research output includes token count for cost tracking. Typical queries use 10-15k tokens.

## When to Use Deep Research

- Complex questions requiring synthesis from multiple sources
- Current events, news, or rapidly changing topics
- Fact-checking with verified citations needed
- Market research, competitive analysis
- Technical topics requiring authoritative sources

## Environment

Requires `PERPLEXITY_API_KEY` environment variable.

---

@foundation:context/shared/common-system-base.md
