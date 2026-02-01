# Perplexity Research Guide

This guide covers best practices for using Perplexity's Agentic Research API effectively.

## Understanding the API

### Endpoints

Perplexity offers three main API endpoints:

| Endpoint | Purpose | When to Use |
|----------|---------|-------------|
| `/v1/chat/completions` | OpenAI-compatible chat | Standard LLM interactions |
| `/v1/responses` | Grounded LLM with web search | Deep research (this tool) |
| `/v1/search` | Raw web search results | Simple lookups |

The `perplexity_research` tool uses the `/v1/responses` endpoint for deep, grounded research.

### Available Presets

| Preset | Model | Max Steps | Tools | Best For |
|--------|-------|-----------|-------|----------|
| `fast-search` | Fast model | 1 | web_search | Quick queries |
| `pro-search` | GPT-5.1 | 3 | web_search, fetch_url | Balanced research |
| `deep-research` | GPT-5.2 | 10 | web_search, fetch_url | Exhaustive analysis |

### Models (Chat API)

For reference, Perplexity's chat models:
- `sonar` - Lightweight, fast web-grounded search
- `sonar-pro` - Stronger search and retrieval
- `sonar-reasoning` - Multi-step reasoning with search
- `sonar-reasoning-pro` - Premium reasoning (DeepSeek-R1 based)

## Research Best Practices

### Query Formulation

**The 4 C's of Good Research Queries:**

1. **Clear** - Unambiguous question
2. **Constrained** - Time, geography, domain limits
3. **Complete** - All necessary context included
4. **Concrete** - Specific deliverable expected

**Examples:**

| Bad Query | Good Query |
|-----------|------------|
| "Tell me about AI" | "What are the 3 most significant AI regulation changes in the EU in 2024?" |
| "Cloud pricing" | "Compare AWS, Azure, and GCP pricing for GPU instances (A100) as of January 2025" |
| "Quantum computing news" | "What are the top 3 quantum computing breakthroughs announced in the last 30 days with their practical applications?" |

### Depth Calibration

**Use `pro-search` (default) when:**
- Balanced depth needed
- 2-5 sources sufficient
- Time-sensitive response needed

**Use `sonar-pro` when:**
- Comprehensive coverage critical
- Complex multi-faceted topic
- Higher cost acceptable

**Use `sonar-reasoning` when:**
- Analysis required, not just facts
- Comparing/contrasting needed
- Reasoning chain valuable

### Citation Quality

**Always verify:**
- Source recency (is the date relevant?)
- Source authority (primary vs secondary)
- Source bias (consider perspective)
- Claim consistency (do sources agree?)

**Citation format:**
```
According to [Source Name][1], [claim]. This is corroborated by [Another Source][2].

[1] Source Title: https://example.com/article
[2] Another Source: https://example.org/research
```

## Common Research Patterns

### Pattern 1: Comparative Analysis

```
Query: "Compare [A] vs [B] vs [C] on dimensions [X, Y, Z] as of [date]"

Structure response as:
| Dimension | A | B | C |
|-----------|---|---|---|
| X | ... | ... | ... |
| Y | ... | ... | ... |
```

### Pattern 2: Current State Assessment

```
Query: "What is the current state of [topic] as of [date]? Include recent developments, key players, and trends."

Structure response as:
- Overview
- Recent Developments (last N months)
- Key Players
- Emerging Trends
- Outlook
```

### Pattern 3: Fact Verification

```
Query: "Verify: [claim]. Provide evidence for or against with citations."

Structure response as:
- Verdict: TRUE/FALSE/PARTIALLY TRUE/UNVERIFIABLE
- Evidence For
- Evidence Against
- Confidence Level
- Sources
```

### Pattern 4: Technical Deep Dive

```
Query: "Explain [technical topic] including: architecture, key components, trade-offs, and current best practices."

Structure response as:
- Conceptual Overview
- Architecture/Components
- Trade-offs
- Best Practices
- References
```

## Error Handling

### Rate Limits

If rate limited:
1. Wait for the specified retry time
2. Consider using a less intensive preset
3. Batch queries if possible

### Timeout

If timeout occurs:
1. Reduce `max_steps` parameter
2. Narrow the query scope
3. Use `pro-search` instead of `deep-research`

### Insufficient Results

If results are sparse:
1. Broaden the query slightly
2. Remove overly specific constraints
3. Try alternative query phrasings

## Cost Optimization

### Query Consolidation

**Instead of:**
```
Query 1: "What is Company A's revenue?"
Query 2: "What is Company B's revenue?"
Query 3: "What is Company C's revenue?"
Cost: ~$15
```

**Use:**
```
Single query: "Compare revenues of Company A, B, and C for fiscal year 2024"
Cost: ~$5
```

### Tiered Approach

1. Start with free `web_search` for simple facts
2. Escalate to `perplexity_research` only if insufficient
3. Use `deep-research` preset only for truly complex topics

### Caching Strategy

For frequently asked topics:
- Cache research results with timestamp
- Refresh only when data is stale
- Reuse citations across related queries
