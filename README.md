# Amplifier Bundle: Perplexity Research

Deep web research capabilities for Amplifier using Perplexity's Agentic Research API.

## Highlights

### Categorized References with URLs for Follow-Up Research

Unlike basic search, this bundle returns **structured, categorized references** that downstream agents can use for deeper investigation:

```markdown
## References

### Academic Sources
- [1] HEMA: A Hippocampus-Inspired Extended Memory Architecture...
  URL: https://arxiv.org/abs/2504.16754
- [2] Episodic Retrieval in Cognitive Science...
  URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC1074338/

### News & Industry
- [3] AI Emulates Brain's Memory Replay...
  URL: https://neurosciencenews.com/place-cell-ai-learning-23202/

### Documentation
- [4] Memory Architecture Implementation Guide
  URL: https://github.com/example/memory-arch

---
Tokens: 7756
```

**Why this matters:** Other agents can use `web_fetch` on these URLs to dive deeper into specific sources. The research-expert agent includes a **Deep Dive Suggestions** table prioritizing which sources merit follow-up:

| Priority | Source | URL | Investigation Focus |
|----------|--------|-----|---------------------|
| High | arxiv paper | [URL] | Full methodology section |
| Medium | GitHub repo | [URL] | Benchmark comparisons |

### Domain-Specific Query Enhancement

The research-expert agent intelligently adapts queries based on your domain context:

| You Say | Agent Does |
|---------|------------|
| "from neuroscience perspective" | Adds domain terms, prioritizes academic sources |
| "recent 2024-2025 papers" | Adds time constraints, notes publication dates |
| "industry perspective" | Includes analyst reports, market coverage |

```
User: "Research AI memory architectures from a neuroscience angle"

Agent uses:
  query: "AI memory architectures inspired by hippocampus and biological neural systems"
  instructions: "Prioritize peer-reviewed neuroscience journals and computational 
                 neuroscience sources. Focus on biological mechanisms."
```

---

## Installation

### Option 1: Amplifier CLI (Recommended)

```bash
# Add the bundle to your registry
amplifier bundle add git+https://github.com/colombod/amplifier-bundle-perplexity@main

# Set it as your active bundle (or compose with your existing bundle)
amplifier bundle use perplexity

# Verify installation
amplifier bundle list
```

### Option 2: Compose with Your Existing Bundle

Add to your bundle's includes:

```yaml
includes:
  - bundle: git+https://github.com/colombod/amplifier-bundle-perplexity@main
```

### Option 3: Use Directly Without Installing

```bash
# Run with the bundle directly (one-time use)
amplifier run --bundle git+https://github.com/colombod/amplifier-bundle-perplexity@main "Research quantum computing breakthroughs"
```

## Environment Setup

Set your Perplexity API key:

```bash
export PERPLEXITY_API_KEY=pplx-xxxxx
```

Or add to your shell profile (`~/.bashrc`, `~/.zshrc`):

```bash
echo 'export PERPLEXITY_API_KEY="pplx-xxxxx"' >> ~/.bashrc
source ~/.bashrc
```

## Quick Start

After installation:

```bash
# Start interactive session with perplexity bundle
amplifier

# In the session, delegate research to the expert agent:
> Delegate to perplexity:research-expert to research the latest advances in fusion energy
```

Or use the tool directly:

```bash
# Single research query
amplifier run "Use perplexity_research to find information about CRISPR breakthroughs in 2025"
```

---

## Features

- **Deep Research Tool**: Multi-step web research with categorized citations via `perplexity_research`
- **Research Expert Agent**: Domain-aware research with structured handoff for downstream agents
- **Categorized References**: Sources grouped by type (Academic, News, Docs, Other) with extractable URLs
- **Deep Dive Suggestions**: Prioritized follow-up recommendations for agents with `web_fetch`
- **Cost-Aware Guidance**: Token-based pricing (~10-15k tokens typical)

## Usage

### Direct Tool Use

```
Use the perplexity_research tool to find current information about quantum computing breakthroughs in 2025.
```

### Agent Delegation (Recommended)

```
Delegate to perplexity:research-expert to research AI from a neuroscience perspective, focusing on hippocampus-inspired architectures.
```

The agent will:
1. Enhance your query with domain-specific terms
2. Set appropriate source preferences via `instructions`
3. Return categorized references for follow-up
4. Provide Deep Dive Suggestions for downstream agents

### Chaining with Follow-Up Research

After getting research results, use the categorized URLs for deeper investigation:

```
Based on the research results, use web_fetch on the High-priority academic sources 
to extract the full methodology sections.
```

### Recipes

```bash
# Deep research with verification
amplifier tool invoke recipes operation=execute \
  recipe_path=perplexity:recipes/deep-research.yaml \
  context='{"research_question": "What are the latest developments in fusion energy?"}'

# Fact-checking
amplifier tool invoke recipes operation=execute \
  recipe_path=perplexity:recipes/fact-check.yaml \
  context='{"claims": "Claim 1\nClaim 2\nClaim 3"}'
```

## Cost Awareness

**Token-based pricing** (~10-15k tokens typical per query). Each response includes token count for tracking.

### When to Use Deep Research

- Complex questions requiring synthesis from multiple sources
- Current events, news, or rapidly changing topics
- Fact-checking with verified citations
- Market research, competitive analysis
- Domain-specific research (neuroscience, academic, industry angles)

### When to Use Free Alternatives

- Simple factual lookups → use `web_search`
- Static/historical information → use `web_search`
- Code documentation → use existing docs

## Components

### Tool: perplexity_research (embedded)

Deep research using Perplexity's /v1/responses API. The tool code is embedded in this bundle.

**Parameters:**
- `query` (required): Research question
- `preset`: `pro-search` (default), `sonar-pro`, `sonar-reasoning`
- `reasoning_effort`: `low`, `medium` (default), `high`
- `max_steps`: 1-10 (default: 5)
- `instructions`: Source preferences, domain focus, time constraints

**Output Features:**
- Main research content with inline citations `[1]`, `[2]`
- Categorized References section (Academic, News, Docs, Other)
- Each reference includes full URL for `web_fetch`
- Token count for cost tracking

### Agent: perplexity:research-expert

Specialized research agent with:
- **Advanced Query Formulation**: Domain-aware query enhancement
- **Source Preferences**: Uses `instructions` parameter for targeted research
- **Categorized Output**: References grouped by source type
- **Deep Dive Suggestions**: Prioritized URLs for downstream agent follow-up
- **Cost-Benefit Framework**: Knows when deep research is worth it

### Recipes

| Recipe | Purpose | Est. Cost |
|--------|---------|-----------|
| `deep-research.yaml` | Multi-step research with verification | ~$0.10-0.50 |
| `fact-check.yaml` | Verify claims with tiered approach | ~$0.05-0.30 |

## URL Categorization

The tool automatically categorizes sources:

| Category | Detected Domains |
|----------|------------------|
| **Academic** | arxiv.org, doi.org, pubmed, nature.com, ieee.org, .edu, scholar.google |
| **News & Industry** | techcrunch, wired, bloomberg, reuters, medium, substack |
| **Documentation** | github.com, docs.*, api.*, developer.* |
| **Other** | Everything else |

## API Reference

### Perplexity Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `/v1/responses` | Agentic research (this bundle) |
| `/v1/chat/completions` | Standard chat (separate provider module) |

### Available Presets

| Preset | Depth | Best For |
|--------|-------|----------|
| `pro-search` | Medium | Balanced research |
| `sonar-pro` | Deep | Comprehensive coverage |
| `sonar-reasoning` | Deep + Analysis | Complex reasoning |

## Related Modules

- **amplifier-module-provider-perplexity**: LLM provider for chat completions (separate module for using Perplexity as your AI backend)

## License

MIT

## Contributing

Issues and PRs welcome at https://github.com/colombod/amplifier-bundle-perplexity
