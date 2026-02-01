# Research Cost Decision Framework

Perplexity research uses **token-based pricing**. Typical queries use 10-15k tokens.
Actual cost depends on the model/preset used - generally much lower than $5 per query.

Use this framework to decide when deep research is worth it.

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

Ask: "Is this research task valuable enough to justify a paid API call?"

- **YES**: Use Perplexity (token-based cost, typically 10-15k tokens)
- **NO**: Use free alternatives
- **MAYBE**: Start with free `web_search`, escalate if insufficient

## Preset Cost Factors

| Preset | Token Usage | When to Use |
|--------|-------------|-------------|
| `pro-search` | ~10-15k tokens | Default for most research |
| `sonar-pro` | ~15-25k tokens | Need comprehensive coverage |
| `sonar-reasoning` | ~20-30k tokens | Complex analysis, reasoning chains |

**Note**: Token count is reported at the end of each research output for cost tracking.

## Anti-Patterns

Do NOT use Perplexity for:
- "What is [well-known fact]?"
- Code syntax questions
- Information you already have in context
- Multiple queries that could be one

Consolidate into ONE well-crafted query when possible.

## Query Optimization

**Good queries** (worth the token cost):
- "What are the top 3 quantum computing companies for drug discovery and their 2024 funding?"
- "Compare pricing and features of AWS, Azure, and GCP for ML workloads as of today"

**Bad queries** (use web_search instead):
- "What is quantum computing?"
- "What is AWS?"
- "Tell me about cloud providers"
