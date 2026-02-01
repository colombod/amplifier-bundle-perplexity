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

Cost: ~$5 per research task. Returns structured output with citations."""

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
                "preset": {
                    "type": "string",
                    "enum": ["pro-search", "sonar-pro", "sonar-reasoning"],
                    "description": "Research preset. pro-search=balanced, sonar-pro=deeper, sonar-reasoning=with reasoning steps",
                },
                "reasoning_effort": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Depth of reasoning. Higher = more thorough but slower",
                },
                "max_steps": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Maximum research loop steps (1-10)",
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
        """Execute a research query using Perplexity's Agentic Research API.

        Args:
            input: Dictionary containing:
                - query (required): Research question or topic
                - preset: Research preset (pro-search, sonar-pro, sonar-reasoning)
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

        preset = input.get("preset") or self.preset
        reasoning_effort = input.get("reasoning_effort") or self.reasoning_effort
        max_steps = input.get("max_steps") or self.max_steps
        instructions = input.get("instructions") or (
            "Provide thorough, well-researched answers with citations."
        )

        # Execute request using SDK's high-level method
        try:
            logger.debug(f"Executing Perplexity research: {query[:100]}...")

            response = await self._make_request(
                query=query,
                preset=preset,
                reasoning_effort=reasoning_effort,
                max_steps=max_steps,
                instructions=instructions,
            )

            # Parse typed response
            result = self._parse_response(response)

            # Format output for LLM consumption
            output_parts = [result["content"]]

            if result.get("citations"):
                output_parts.append("\n\n## Citations")
                for i, citation in enumerate(result["citations"], 1):
                    output_parts.append(f"[{i}] {citation}")

            if result.get("usage"):
                usage = result["usage"]
                output_parts.append(
                    f"\n\n---\nTokens: {usage.get('total_tokens', 'N/A')}"
                )

            return ToolResult(
                success=True,
                output="\n".join(output_parts),
            )

        except perplexity.RateLimitError as e:
            return ToolResult(
                success=False,
                output="",
                error={"message": f"Rate limited: {e.message}"},
            )
        except perplexity.APITimeoutError:
            return ToolResult(
                success=False,
                output="",
                error={"message": f"Research request timed out after {self.timeout}s"},
            )
        except perplexity.APIStatusError as e:
            error_msg = f"API error: {e.status_code}"
            if e.message:
                error_msg = f"{error_msg} - {e.message}"
            return ToolResult(
                success=False,
                output="",
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

    async def _make_request(
        self,
        query: str,
        preset: str,
        reasoning_effort: str,
        max_steps: int,
        instructions: str,
    ) -> ResponseCreateResponse:
        """Make request to Perplexity's Agentic Research API.

        Uses the SDK's high-level client.responses.create() method which provides:
        - Type safety with ResponseCreateResponse
        - Built-in retry logic
        - Proper error handling

        Args:
            query: Research question
            preset: Research preset
            reasoning_effort: Reasoning depth
            max_steps: Max research steps
            instructions: Additional instructions

        Returns:
            Typed ResponseCreateResponse from SDK

        Raises:
            perplexity.APIError: On API errors
        """
        return await self.client.responses.create(
            input=query,
            preset=preset,
            reasoning={"effort": reasoning_effort},
            max_steps=max_steps,
            tools=[{"type": "web_search"}, {"type": "fetch_url"}],
            instructions=instructions,
        )

    def _parse_response(self, response: ResponseCreateResponse) -> dict[str, Any]:
        """Parse the typed SDK response into a structured result.

        Args:
            response: Typed ResponseCreateResponse from SDK

        Returns:
            Structured result with content, citations, usage
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
        citations: list[str] = []
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
                                if title and title != url:
                                    citations.append(f"{title}: {url}")
                                else:
                                    citations.append(url)

            elif item_type == "search_results":
                # SearchResultsOutputItem - could extract search results
                pass

            elif item_type == "fetch_url_results":
                # FetchURLResultsOutputItem - could extract fetched content
                pass

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
