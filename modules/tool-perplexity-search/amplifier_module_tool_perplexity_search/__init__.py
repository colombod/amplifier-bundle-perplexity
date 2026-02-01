"""Perplexity Agentic Research Tool for Amplifier.

This module provides deep web research capabilities using Perplexity's
Agentic Research API (/v1/responses) via the official Perplexity Python SDK.

Basic Usage:
    # In settings.yaml
    # modules:
    #   - tool-perplexity-search:
    #       api_key: ${PERPLEXITY_API_KEY}
    #
    # Then use perplexity_research tool in your agent
"""

import logging
import os
from typing import Any

import perplexity
from perplexity import AsyncPerplexity
from perplexity.types import ResponseCreateResponse

from amplifier_core import ModuleCoordinator, ToolResult

__all__ = ["PerplexityResearchTool", "mount"]

logger = logging.getLogger(__name__)


class PerplexityResearchTool:
    """Deep research tool using Perplexity's Agentic Research API.

    This tool uses the SDK's client.responses.create() method to access
    the /v1/responses endpoint for multi-step web research with citations.

    Attributes:
        name: Tool identifier for Amplifier registration
        __amplifier_module_type__: Module type marker for Amplifier
    """

    name = "perplexity_research"
    __amplifier_module_type__ = "tool"

    def __init__(
        self,
        api_key: str | None = None,
        config: dict[str, Any] | None = None,
        coordinator: ModuleCoordinator | None = None,
    ) -> None:
        """Initialize the Perplexity Research Tool.

        Args:
            api_key: Perplexity API key (or set PERPLEXITY_API_KEY env var)
            config: Optional configuration dictionary
            coordinator: Amplifier module coordinator
        """
        self._api_key = api_key
        self._client: AsyncPerplexity | None = None
        self.config = config or {}
        self.coordinator = coordinator

        # Configuration with defaults
        self.preset: str = self.config.get("preset", "pro-search")
        self.reasoning_effort: str = self.config.get("reasoning_effort", "medium")
        self.max_steps: int = self.config.get("max_steps", 5)
        self.timeout: float = self.config.get("timeout", 120.0)
        self.max_retries: int = self.config.get("max_retries", 2)

    @property
    def description(self) -> str:
        """Tool description for LLM context."""
        return """Deep research using Perplexity's Agentic Research API.

Use for:
- Complex multi-step research questions requiring synthesis
- Fact-checking with verified citations
- Current events and news analysis
- Technical research requiring multiple sources

NOT for:
- Simple factual lookups (use web_search instead - it's free)
- Questions about static/historical facts

Cost: Token-based (~10-15k tokens typical). Returns structured output with citations."""

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Research question or topic to investigate",
                },
                "mode": {
                    "type": "string",
                    "enum": ["auto", "research", "chat"],
                    "description": "API mode: 'research' for Agentic Research API (deep, multi-step), 'chat' for Chat Completions (faster, cheaper), 'auto' tries research first then falls back to chat on quota/rate limits",
                },
                "model": {
                    "type": "string",
                    "enum": ["sonar-pro", "sonar", "sonar-reasoning"],
                    "description": "Model for chat mode. sonar-pro=comprehensive, sonar=fast, sonar-reasoning=with reasoning",
                },
                "reasoning_effort": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Depth of reasoning (research mode only). Higher = more thorough but slower",
                },
                "max_steps": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Maximum research loop steps (research mode only, 1-10)",
                },
                "instructions": {
                    "type": "string",
                    "description": "Optional additional instructions for the research",
                },
            },
            "required": ["query"],
        }

    @property
    def client(self) -> AsyncPerplexity:
        """Lazily initialize the Perplexity SDK client.

        Returns:
            Configured AsyncPerplexity client for API calls

        Raises:
            ValueError: If api_key is not configured
        """
        if self._client is None:
            if self._api_key is None:
                raise ValueError("api_key must be provided for API calls")
            self._client = AsyncPerplexity(
                api_key=self._api_key,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
        return self._client

    async def close(self) -> None:
        """Close the SDK client if initialized.

        Call this method when done using the tool directly (without mount()).
        When using via mount(), cleanup is handled automatically.
        """
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def __aenter__(self) -> "PerplexityResearchTool":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit - ensures client cleanup."""
        await self.close()

    async def execute(self, input: dict[str, Any]) -> ToolResult:
        """Execute a research query using Perplexity APIs.

        Supports two API modes:
        - 'research': Agentic Research API (deep, multi-step research)
        - 'chat': Chat Completions API (faster, simpler, cheaper)
        - 'auto': Tries research first, falls back to chat on quota/rate limits

        Args:
            input: Dictionary containing:
                - query (required): Research question or topic
                - mode: API mode ('auto', 'research', 'chat')
                - model: Model for chat mode (sonar-pro, sonar, sonar-reasoning)
                - reasoning_effort: Depth of reasoning (low, medium, high)
                - max_steps: Maximum research steps (1-10)
                - instructions: Additional research instructions

        Returns:
            ToolResult with research findings, citations, and usage info
        """
        # Extract parameters
        query = input.get("query")
        if not query:
            return ToolResult(
                success=False,
                output="",
                error={"message": "Missing required parameter: query"},
            )

        # Mode selection: auto, research, or chat
        mode: str = str(input.get("mode", "auto"))
        model: str = str(input.get("model", "sonar-pro"))

        reasoning_effort: str = self.reasoning_effort
        if input.get("reasoning_effort") is not None:
            reasoning_effort = str(input["reasoning_effort"])

        max_steps: int = self.max_steps
        if input.get("max_steps") is not None:
            max_steps = int(input["max_steps"])

        instructions: str = (
            str(input["instructions"])
            if input.get("instructions")
            else "Provide thorough, well-researched answers with citations."
        )

        # Execute based on mode
        if mode == "chat":
            # Direct chat mode - skip research API
            return await self._execute_chat(query, model, instructions)
        elif mode == "research":
            # Direct research mode - no fallback
            return await self._execute_research(
                query, reasoning_effort, max_steps, instructions
            )
        else:
            # Auto mode - try research first, fallback to chat on quota/rate limits
            result = await self._execute_research(
                query, reasoning_effort, max_steps, instructions
            )

            # Check if we should fallback to chat
            if not result.success and result.error:
                error_msg = result.error.get("message", "")
                should_fallback = any(
                    trigger in error_msg.lower()
                    for trigger in ["rate limit", "quota", "429", "insufficient"]
                )

                if should_fallback:
                    logger.info(
                        f"Agentic Research API failed ({error_msg}), "
                        f"falling back to Chat API with {model}"
                    )
                    return await self._execute_chat(
                        query,
                        model,
                        instructions,
                        fallback_note=f"(Fallback from Research API: {error_msg})",
                    )

            return result

    async def _execute_research(
        self,
        query: str,
        reasoning_effort: str,
        max_steps: int,
        instructions: str,
    ) -> ToolResult:
        """Execute using Agentic Research API (responses.create)."""
        try:
            logger.debug(f"Executing Perplexity research: {query[:100]}...")

            response = await self._make_research_request(
                query=query,
                reasoning_effort=reasoning_effort,
                max_steps=max_steps,
                instructions=instructions,
            )

            # Parse typed response
            result = self._parse_response(response)

            # Format output with categorized references for downstream agents
            output = self._format_structured_output(result)

            return ToolResult(
                success=True,
                output=output,
            )

        except perplexity.RateLimitError as e:
            error_msg = f"Rate limited: {e.message}"
            logger.warning(error_msg)
            return ToolResult(
                success=False,
                output=error_msg,
                error={"message": error_msg},
            )
        except perplexity.APITimeoutError:
            error_msg = f"Research request timed out after {self.timeout}s"
            logger.warning(error_msg)
            return ToolResult(
                success=False,
                output=error_msg,
                error={"message": error_msg},
            )
        except perplexity.BadRequestError as e:
            error_msg = (
                f"Invalid request: {e.message if hasattr(e, 'message') else str(e)}"
            )
            logger.warning(f"Perplexity BadRequest: {error_msg}")
            return ToolResult(
                success=False,
                output=error_msg,
                error={"message": error_msg},
            )
        except perplexity.APIStatusError as e:
            error_msg = f"API error {e.status_code}"
            if hasattr(e, "message") and e.message:
                error_msg = f"{error_msg}: {e.message}"
            logger.warning(f"Perplexity API error: {error_msg}")
            return ToolResult(
                success=False,
                output=error_msg,
                error={"message": error_msg},
            )
        except perplexity.APIConnectionError as e:
            return ToolResult(
                success=False,
                output="",
                error={"message": f"Connection error: {e}"},
            )
        except Exception as e:
            logger.exception("Unexpected error in Perplexity research")
            return ToolResult(
                success=False,
                output="",
                error={"message": f"Research failed: {e}"},
            )

    async def _execute_chat(
        self,
        query: str,
        model: str,
        instructions: str,
        fallback_note: str = "",
    ) -> ToolResult:
        """Execute using Chat Completions API (chat.completions.create).

        This is the simpler, faster, and cheaper API for basic queries.
        Supports models: sonar-pro, sonar, sonar-reasoning.
        """
        try:
            logger.debug(f"Executing Perplexity chat ({model}): {query[:100]}...")

            response = await self._make_chat_request(query, model, instructions)

            # Extract content from chat response
            content = ""
            citations: list[dict[str, str]] = []

            if response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                content = message.content or ""

                # Extract citations if available
                if hasattr(message, "citations") and message.citations:
                    for url in message.citations:
                        if url not in [c["url"] for c in citations]:
                            citations.append(
                                {
                                    "url": url,
                                    "title": "Citation",
                                    "category": self._categorize_url(url),
                                }
                            )

            # Build result
            result: dict[str, Any] = {
                "content": content,
                "citations": citations,
                "usage": {},
                "model": model,
                "status": "completed",
            }

            if response.usage:
                result["usage"] = {
                    "input_tokens": response.usage.prompt_tokens or 0,
                    "output_tokens": response.usage.completion_tokens or 0,
                    "total_tokens": response.usage.total_tokens or 0,
                }

            output = self._format_structured_output(result)

            if fallback_note:
                output = f"{fallback_note}\n\n{output}"

            return ToolResult(success=True, output=output)

        except perplexity.RateLimitError as e:
            error_msg = f"Chat rate limited: {e.message}"
            logger.warning(error_msg)
            return ToolResult(
                success=False, output=error_msg, error={"message": error_msg}
            )
        except perplexity.APIStatusError as e:
            error_msg = f"Chat API error {e.status_code}"
            if hasattr(e, "message") and e.message:
                error_msg = f"{error_msg}: {e.message}"
            logger.warning(f"Perplexity Chat API error: {error_msg}")
            return ToolResult(
                success=False, output=error_msg, error={"message": error_msg}
            )
        except Exception as e:
            logger.exception("Unexpected error in Perplexity chat")
            return ToolResult(
                success=False, output="", error={"message": f"Chat failed: {e}"}
            )

    async def _make_chat_request(
        self, query: str, model: str, instructions: str
    ) -> Any:
        """Make request to Perplexity's Chat Completions API.

        Args:
            query: The user's question
            model: Model to use (sonar-pro, sonar, sonar-reasoning)
            instructions: System instructions

        Returns:
            Chat completion response
        """
        return await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": query},
            ],
        )

    async def _make_research_request(
        self,
        query: str,
        reasoning_effort: str,
        max_steps: int,
        instructions: str,
    ) -> ResponseCreateResponse:
        """Make request to Perplexity's Agentic Research API.

        Uses the Agentic Research API (responses.create) which is designed for
        deep research tasks with web search and URL fetching capabilities.

        Note: This API only supports the 'pro-search' preset. Other models like
        'sonar-pro' use the Chat Completions API (chat.completions.create) which
        is a different endpoint entirely.

        Args:
            query: Research question
            reasoning_effort: Reasoning depth (low, medium, high)
            max_steps: Max research steps (1-10)
            instructions: Additional instructions for the research

        Returns:
            Typed ResponseCreateResponse from SDK

        Raises:
            perplexity.APIError: On API errors
        """
        # Agentic Research API - use responses.create with pro-search preset
        # Combine query and instructions into the input
        combined_input = query
        if instructions:
            combined_input = f"{instructions}\n\nResearch question: {query}"

        return await self.client.responses.create(
            input=combined_input,
            preset="pro-search",  # Only valid preset for Agentic Research API
            reasoning={"effort": reasoning_effort},
            max_steps=max_steps,
        )

    def _categorize_url(self, url: str) -> str:
        """Categorize a URL by source type.

        Args:
            url: The URL to categorize

        Returns:
            Category string: "academic", "news", "docs", or "other"
        """
        url_lower = url.lower()

        # Academic indicators
        if any(
            domain in url_lower
            for domain in [
                "arxiv.org",
                "doi.org",
                "pubmed",
                "springer.com",
                "nature.com",
                "sciencedirect",
                ".edu/",
                "acm.org",
                "ieee.org",
                "scholar.google",
                "ncbi.nlm.nih",
                "plos.org",
                "frontiersin.org",
                "biorxiv.org",
                "medrxiv.org",
                "researchgate.net",
                "semanticscholar.org",
            ]
        ):
            return "academic"

        # Documentation indicators
        if any(
            domain in url_lower
            for domain in [
                "docs.",
                "/docs/",
                "documentation",
                "readme",
                "github.com",
                "gitlab.com",
                "api.",
                "developer.",
                "devdocs",
            ]
        ):
            return "docs"

        # News indicators
        if any(
            domain in url_lower
            for domain in [
                "techcrunch",
                "wired.com",
                "theverge",
                "arstechnica",
                "bbc.",
                "cnn.",
                "reuters.",
                "nytimes",
                "wsj.com",
                "bloomberg.",
                "/news/",
                "/blog/",
                "medium.com",
                "substack.com",
                "venturebeat",
                "thenextweb",
            ]
        ):
            return "news"

        return "other"

    def _parse_response(self, response: ResponseCreateResponse) -> dict[str, Any]:
        """Parse the typed SDK response into a structured result.

        Args:
            response: Typed ResponseCreateResponse from SDK

        Returns:
            Structured result with content, categorized citations, usage
        """
        result: dict[str, Any] = {
            "content": "",
            "citations": [],
            "usage": {},
            "model": response.model,
            "status": response.status,
        }

        # Check for errors
        if response.error:
            result["error"] = {
                "code": response.error.code,
                "message": response.error.message,
            }

        # Extract output text from typed response
        text_parts: list[str] = []
        citations: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for output_item in response.output:
            # Handle different output item types
            item_type = getattr(output_item, "type", None)

            if item_type == "message":
                # MessageOutputItem has content array
                content_items = getattr(output_item, "content", [])
                for content_item in content_items:
                    content_type = getattr(content_item, "type", None)
                    if content_type in ("output_text", "text"):
                        text = getattr(content_item, "text", "")
                        if text:
                            text_parts.append(text)
                        # Extract annotations/citations (may be None)
                        annotations = getattr(content_item, "annotations", None) or []
                        for annotation in annotations:
                            url = getattr(annotation, "url", None)
                            title = getattr(annotation, "title", url)
                            if url and url not in seen_urls:
                                seen_urls.add(url)
                                citations.append(
                                    {
                                        "url": url,
                                        "title": title
                                        if title and title != url
                                        else "Untitled",
                                        "category": self._categorize_url(url),
                                    }
                                )

            elif item_type == "search_results":
                # Extract URLs from search results
                results = getattr(output_item, "results", [])
                for search_result in results:
                    url = getattr(search_result, "url", None)
                    title = getattr(search_result, "title", None) or getattr(
                        search_result, "name", url
                    )
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        citations.append(
                            {
                                "url": url,
                                "title": title
                                if title and title != url
                                else "Untitled",
                                "category": self._categorize_url(url),
                            }
                        )

            elif item_type == "fetch_url_results":
                # Extract URLs from fetched content
                results = getattr(output_item, "results", [])
                for fetch_result in results:
                    url = getattr(fetch_result, "url", None)
                    title = getattr(fetch_result, "title", None) or url
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        citations.append(
                            {
                                "url": url,
                                "title": title
                                if title and title != url
                                else "Untitled",
                                "category": self._categorize_url(url),
                            }
                        )

        result["content"] = "\n".join(text_parts)
        result["citations"] = citations

        # Extract usage information from typed response
        if response.usage:
            result["usage"] = {
                "input_tokens": response.usage.input_tokens or 0,
                "output_tokens": response.usage.output_tokens or 0,
                "total_tokens": (response.usage.input_tokens or 0)
                + (response.usage.output_tokens or 0),
            }

        return result

    def _format_structured_output(self, result: dict[str, Any]) -> str:
        """Format the parsed result into structured markdown output.

        Groups citations by category and provides a clean format for
        downstream agents to extract URLs.

        Args:
            result: Parsed result from _parse_response

        Returns:
            Formatted markdown string with categorized references
        """
        parts = [result["content"]]

        citations = result.get("citations", [])
        if citations:
            parts.append("\n\n## References\n")

            # Group by category
            by_category: dict[str, list[tuple[int, dict[str, str]]]] = {
                "academic": [],
                "news": [],
                "docs": [],
                "other": [],
            }
            for i, citation in enumerate(citations, 1):
                category = citation.get("category", "other")
                by_category[category].append((i, citation))

            category_names = {
                "academic": "### Academic Sources",
                "news": "### News & Industry",
                "docs": "### Documentation",
                "other": "### Other Sources",
            }

            for category, name in category_names.items():
                if by_category[category]:
                    parts.append(f"\n{name}")
                    for i, citation in by_category[category]:
                        title = citation.get("title", "Untitled")
                        url = citation.get("url", "")
                        if not url:
                            continue  # Skip malformed citations
                        parts.append(f"- [{i}] {title}")
                        parts.append(f"  URL: {url}")

        if result.get("usage"):
            usage = result["usage"]
            parts.append(f"\n\n---\nTokens: {usage.get('total_tokens', 'N/A')}")

        return "\n".join(parts)


async def mount(
    coordinator: ModuleCoordinator, config: dict[str, Any] | None = None
) -> Any:
    """Mount the Perplexity Research Tool into Amplifier.

    Args:
        coordinator: Amplifier module coordinator
        config: Optional configuration dictionary containing:
            - api_key: Perplexity API key (or use PERPLEXITY_API_KEY env var)
            - preset: Default research preset
            - reasoning_effort: Default reasoning depth
            - max_steps: Default max research steps
            - timeout: Request timeout in seconds

    Returns:
        Cleanup function to close HTTP client, or None if mounting failed
    """
    config = config or {}
    api_key = config.get("api_key") or os.environ.get("PERPLEXITY_API_KEY")

    if not api_key:
        logger.warning(
            "Perplexity research tool not mounted: PERPLEXITY_API_KEY not set. "
            "Set the environment variable or provide api_key in config."
        )
        return None

    tool = PerplexityResearchTool(
        api_key=api_key,
        config=config,
        coordinator=coordinator,
    )

    await coordinator.mount("tools", tool, name=tool.name)
    logger.info(f"Perplexity research tool mounted (preset: {tool.preset})")

    async def cleanup() -> None:
        await tool.close()
        logger.debug("Perplexity research tool cleanup complete")

    return cleanup
