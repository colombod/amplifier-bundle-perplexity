# Perplexity Research Capabilities

You have access to deep web research via Perplexity's Agentic Research API.

## When to Use

**Delegate to `perplexity:research-expert` when:**
- Complex questions requiring synthesis from multiple sources
- Current events, news, or rapidly changing topics
- Fact-checking with verified citations
- Market research, competitive analysis
- Technical topics requiring authoritative sources

**Use standard `web_search` (free) when:**
- Simple factual lookups
- Static/historical information
- Quick verification of single facts
- Code documentation lookups

## Cost Awareness

**Perplexity research costs ~$5 per query.** This is not a free tool.

**Cost-justified scenarios:**
- Research supporting important decisions
- Topics with no authoritative single source
- Time-sensitive information needs
- Professional/business research tasks

**NOT cost-justified:**
- Curiosity questions answerable with web_search
- Information available in existing context
- Simple facts with stable answers

## Quick Reference

| Need | Tool | Cost |
|------|------|------|
| Deep research with citations | `perplexity_research` or delegate to `perplexity:research-expert` | ~$5 |
| Quick web lookup | `web_search` | Free |
| Fetch specific URL | `web_fetch` | Free |

## Presets

The `perplexity_research` tool supports different presets:

| Preset | Use When | Depth |
|--------|----------|-------|
| `pro-search` | Default - balanced research | Medium |
| `sonar-pro` | Need comprehensive coverage | Deep |
| `sonar-reasoning` | Complex analysis, reasoning chains | Deep + Reasoning |

## Delegation

For any substantial research task, delegate to `perplexity:research-expert` - it carries the full research methodology and cost-benefit framework.
