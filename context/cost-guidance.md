# Research Cost Decision Framework

Perplexity research costs ~$5 per query. Use this framework to decide.

## Decision Matrix

| Signal | Use Perplexity | Use Free web_search |
|--------|----------------|---------------------|
| Needs synthesis from 5+ sources | Yes | No |
| Single authoritative source exists | No | Yes |
| Information changes weekly/daily | Yes | Maybe |
| Static fact (capitals, dates) | No | Yes |
| Supporting a business decision | Yes | No |
| Casual curiosity | No | Yes |
| Needs citations for credibility | Yes | Maybe |
| Answer likely in local context | No | No (don't search) |

## Cost-Per-Value Calculation

Ask: "Would I pay $5 to a human researcher for this answer?"

- **YES**: Use Perplexity
- **NO**: Use free alternatives
- **MAYBE**: Start with free `web_search`, escalate if insufficient

## Preset Cost Factors

| Preset | Relative Cost | When to Use |
|--------|---------------|-------------|
| `pro-search` | 1x (~$5) | Default for most research |
| `sonar-pro` | ~1.5x | Need comprehensive coverage |
| `sonar-reasoning` | ~2x | Complex analysis, reasoning chains |

## Anti-Patterns

Do NOT use Perplexity for:
- "What is [well-known fact]?"
- Code syntax questions
- Information you already have in context
- Multiple queries that could be one

Consolidate into ONE well-crafted query when possible.

## Query Optimization

**Good queries** (worth $5):
- "What are the top 3 quantum computing companies for drug discovery and their 2024 funding?"
- "Compare pricing and features of AWS, Azure, and GCP for ML workloads as of today"

**Bad queries** (use web_search instead):
- "What is quantum computing?"
- "What is AWS?"
- "Tell me about cloud providers"
