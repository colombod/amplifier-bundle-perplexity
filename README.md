# Amplifier Bundle: Perplexity Research

Deep web research capabilities for Amplifier using Perplexity's Agentic Research API.

## Features

- **Deep Research Tool**: Multi-step web research with citations via `perplexity_research`
- **Research Expert Agent**: Specialized agent for complex research tasks
- **Cost-Aware Guidance**: Know when to use expensive research (~$5/query) vs free alternatives
- **Research Recipes**: Pre-built workflows for common research patterns

## Installation

### As a Bundle Dependency

Add to your bundle's includes:

```yaml
includes:
  - bundle: git+https://github.com/colombod/amplifier-bundle-perplexity@main
```

### Environment Setup

Set your Perplexity API key:

```bash
export PERPLEXITY_API_KEY=pplx-xxxxx
```

## Usage

### Direct Tool Use

```
Use the perplexity_research tool to find current information about quantum computing breakthroughs in 2025.
```

### Agent Delegation

```
Delegate to perplexity:research-expert to research and compare cloud provider ML pricing.
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

**Perplexity research costs ~$5 per query.** Use wisely.

### When to Use Deep Research

- Complex questions requiring synthesis from multiple sources
- Current events, news, or rapidly changing topics
- Fact-checking with verified citations
- Market research, competitive analysis

### When to Use Free Alternatives

- Simple factual lookups → use `web_search`
- Static/historical information → use `web_search`
- Code documentation → use existing docs

## Components

### Tool: perplexity_research (embedded)

Deep research using Perplexity's /v1/responses API. The tool code is embedded in this bundle.

Parameters:
- `query` (required): Research question
- `preset`: `pro-search` (default), `sonar-pro`, `sonar-reasoning`
- `reasoning_effort`: `low`, `medium` (default), `high`
- `max_steps`: 1-10 (default: 5)

### Agent: perplexity:research-expert

Specialized research agent with:
- Full research methodology
- Cost-benefit decision framework
- Structured output with citations
- Verification capabilities

### Recipes

| Recipe | Purpose | Est. Cost |
|--------|---------|-----------|
| `deep-research.yaml` | Multi-step research with verification | ~$10-15 |
| `fact-check.yaml` | Verify claims with tiered approach | ~$0-10 |

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
