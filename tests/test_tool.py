"""Unit tests for PerplexityResearchTool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from perplexity import AsyncPerplexity

from amplifier_core import ToolResult
from amplifier_module_tool_perplexity_search import PerplexityResearchTool


@pytest.fixture
def tool():
    """Shared sync fixture for tests that only need a PerplexityResearchTool instance."""
    return PerplexityResearchTool(api_key="test-key")


class TestInputSchema:
    """Tests for input_schema validation."""

    def test_schema_has_required_properties(self, tool):
        """Input schema should define all expected properties."""
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "mode" in schema["properties"]
        assert "model" in schema["properties"]
        assert "reasoning_effort" in schema["properties"]
        assert "max_steps" in schema["properties"]
        assert "instructions" in schema["properties"]

    def test_query_is_required(self, tool):
        """Query should be the only required field."""
        schema = tool.input_schema

        assert schema["required"] == ["query"]

    def test_mode_enum_values(self, tool):
        """Mode should have valid enum values."""
        schema = tool.input_schema

        mode_schema = schema["properties"]["mode"]
        assert mode_schema["enum"] == ["auto", "research", "chat"]

    def test_model_enum_values(self, tool):
        """Model should have valid enum values."""
        schema = tool.input_schema

        model_schema = schema["properties"]["model"]
        assert model_schema["enum"] == ["sonar-pro", "sonar", "sonar-reasoning"]

    def test_reasoning_effort_enum_values(self, tool):
        """Reasoning effort should have valid enum values."""
        schema = tool.input_schema

        effort_schema = schema["properties"]["reasoning_effort"]
        assert effort_schema["enum"] == ["low", "medium", "high"]

    def test_max_steps_constraints(self, tool):
        """Max steps should have min/max constraints."""
        schema = tool.input_schema

        steps_schema = schema["properties"]["max_steps"]
        assert steps_schema["minimum"] == 1
        assert steps_schema["maximum"] == 10


class TestResponseParsing:
    """Tests for _parse_response method with typed SDK responses."""

    def _create_mock_response(
        self,
        output_items=None,
        model="sonar",
        status="completed",
        usage=None,
        error=None,
    ):
        """Create a mock ResponseCreateResponse."""
        mock_response = MagicMock()
        mock_response.model = model
        mock_response.status = status
        mock_response.output = output_items or []
        mock_response.error = error

        if usage:
            mock_response.usage = MagicMock()
            mock_response.usage.input_tokens = usage.get("input_tokens", 0)
            mock_response.usage.output_tokens = usage.get("output_tokens", 0)
        else:
            mock_response.usage = None

        return mock_response

    def _create_message_output(self, text, annotations=None):
        """Create a mock message output item."""
        content_item = MagicMock()
        content_item.type = "output_text"
        content_item.text = text
        content_item.annotations = annotations or []

        message = MagicMock()
        message.type = "message"
        message.content = [content_item]
        return message

    def test_parse_simple_message(self, tool):
        """Simple message output should be extracted."""
        response = self._create_mock_response(
            output_items=[self._create_message_output("Research result text.")],
            model="sonar-pro",
        )
        result = tool._parse_response(response)

        assert result["content"] == "Research result text."
        assert result["model"] == "sonar-pro"
        assert result["status"] == "completed"

    def test_parse_multiple_messages(self, tool):
        """Multiple message blocks should be concatenated."""
        response = self._create_mock_response(
            output_items=[
                self._create_message_output("First paragraph."),
                self._create_message_output("Second paragraph."),
            ],
        )
        result = tool._parse_response(response)

        assert "First paragraph." in result["content"]
        assert "Second paragraph." in result["content"]

    def test_parse_annotations_as_citations(self, tool):
        """Annotations should be extracted as citations."""
        annotation1 = MagicMock()
        annotation1.url = "https://example.com/paper1"
        annotation1.title = "Paper 1"

        annotation2 = MagicMock()
        annotation2.url = "https://example.com/paper2"
        annotation2.title = "Paper 2"

        response = self._create_mock_response(
            output_items=[
                self._create_message_output(
                    "Research findings.", annotations=[annotation1, annotation2]
                )
            ],
        )
        result = tool._parse_response(response)

        assert len(result["citations"]) == 2
        assert result["citations"][0] == {
            "url": "https://example.com/paper1",
            "title": "Paper 1",
            "category": "other",
        }
        assert result["citations"][1] == {
            "url": "https://example.com/paper2",
            "title": "Paper 2",
            "category": "other",
        }

    def test_parse_deduplicates_citations(self, tool):
        """Duplicate URLs should be deduplicated."""
        annotation1 = MagicMock()
        annotation1.url = "https://example.com/same"
        annotation1.title = "Same URL"

        annotation2 = MagicMock()
        annotation2.url = "https://example.com/same"
        annotation2.title = "Same URL Again"

        response = self._create_mock_response(
            output_items=[
                self._create_message_output("Text 1.", annotations=[annotation1]),
                self._create_message_output("Text 2.", annotations=[annotation2]),
            ],
        )
        result = tool._parse_response(response)

        assert len(result["citations"]) == 1

    def test_parse_usage_information(self, tool):
        """Usage information should be extracted."""
        response = self._create_mock_response(
            output_items=[self._create_message_output("Result")],
            usage={"input_tokens": 100, "output_tokens": 200},
        )
        result = tool._parse_response(response)

        assert result["usage"]["input_tokens"] == 100
        assert result["usage"]["output_tokens"] == 200
        assert result["usage"]["total_tokens"] == 300

    def test_parse_empty_output(self, tool):
        """Empty output should return empty content."""
        response = self._create_mock_response(output_items=[])
        result = tool._parse_response(response)

        assert result["content"] == ""

    def test_parse_error_response(self, tool):
        """Error in response should be captured."""
        error = MagicMock()
        error.code = "rate_limit"
        error.message = "Rate limit exceeded"

        response = self._create_mock_response(
            output_items=[], status="failed", error=error
        )
        result = tool._parse_response(response)

        assert result["status"] == "failed"
        assert result["error"]["code"] == "rate_limit"
        assert result["error"]["message"] == "Rate limit exceeded"


class TestToolExecution:
    """Tests for execute method with mocked SDK."""

    @pytest.fixture
    async def tool(self):
        t = PerplexityResearchTool(api_key="test-key")
        yield t
        await t.close()

    async def test_execute_success(self, tool):
        """Successful execution should return ToolResult with content."""
        with patch.object(
            tool, "_execute_research", new_callable=AsyncMock
        ) as mock_research:
            mock_research.return_value = ToolResult(
                success=True,
                output="Result content",
            )

            result = await tool.execute({"query": "What is AI?", "mode": "research"})

            assert result.success is True
            assert "Result content" in result.output
            mock_research.assert_called_once()

    async def test_execute_with_citations(self, tool):
        """Execution should include citations in output."""
        with patch.object(
            tool, "_execute_research", new_callable=AsyncMock
        ) as mock_research:
            mock_research.return_value = ToolResult(
                success=True,
                output=(
                    "AI research findings.\n\n## References\n\n"
                    "### Academic Sources\n"
                    "- [1] AI Paper\n"
                    "  URL: https://arxiv.org/paper1"
                ),
            )

            result = await tool.execute({"query": "AI research", "mode": "research"})

            assert result.success is True
            assert "References" in result.output
            assert "AI Paper" in result.output

    async def test_execute_missing_query(self, tool):
        """Execution without query should fail."""
        result = await tool.execute({})

        assert result.success is False
        assert "Missing required parameter: query" in result.error["message"]

    async def test_execute_api_error(self, tool):
        """API errors should return failed ToolResult."""
        with patch.object(
            tool, "_execute_research", new_callable=AsyncMock
        ) as mock_research:
            mock_research.return_value = ToolResult(
                success=False,
                output="API error 500: Internal server error",
                error={"message": "API error 500: Internal server error"},
            )

            result = await tool.execute({"query": "Test query", "mode": "research"})

            assert result.success is False
            assert "API error" in result.error["message"]

    async def test_execute_timeout(self):
        """Timeout should return failed ToolResult."""
        tool = PerplexityResearchTool(api_key="test-key", config={"timeout": 5.0})

        with patch.object(
            tool, "_execute_research", new_callable=AsyncMock
        ) as mock_research:
            mock_research.return_value = ToolResult(
                success=False,
                output="Research request timed out after 5.0s",
                error={"message": "Research request timed out after 5.0s"},
            )

            result = await tool.execute({"query": "Test query", "mode": "research"})

            assert result.success is False
            assert "timed out" in result.error["message"]

        await tool.close()

    async def test_execute_rate_limit(self, tool):
        """Rate limit errors should return failed ToolResult."""
        with patch.object(
            tool, "_execute_research", new_callable=AsyncMock
        ) as mock_research:
            mock_research.return_value = ToolResult(
                success=False,
                output="Rate limited: Rate limit exceeded",
                error={"message": "Rate limited: Rate limit exceeded"},
            )

            result = await tool.execute({"query": "Test query", "mode": "research"})

            assert result.success is False
            assert "Rate limited" in result.error["message"]


class TestToolResult:
    """Tests for ToolResult structure."""

    @pytest.fixture
    async def tool(self):
        t = PerplexityResearchTool(api_key="test-key")
        yield t
        await t.close()

    async def test_result_has_expected_fields(self, tool):
        """ToolResult should have success, output, and error fields."""
        with patch.object(
            tool, "_execute_research", new_callable=AsyncMock
        ) as mock_research:
            mock_research.return_value = ToolResult(
                success=True,
                output="Result content",
            )

            result = await tool.execute({"query": "Test", "mode": "research"})

            # Check ToolResult structure
            assert hasattr(result, "success")
            assert hasattr(result, "output")
            assert hasattr(result, "error")

            assert isinstance(result.success, bool)
            assert isinstance(result.output, str)
            assert result.success is True
            assert "Result content" in result.output


class TestClientInitialization:
    """Tests for SDK client initialization."""

    def test_client_not_initialized_on_construction(self):
        """Client should not be initialized until accessed."""
        tool = PerplexityResearchTool(api_key="test-key")
        assert tool._client is None

    def test_client_requires_api_key(self):
        """Accessing client without API key should raise ValueError."""
        tool = PerplexityResearchTool(api_key=None)
        with pytest.raises(ValueError, match="api_key must be provided"):
            _ = tool.client

    def test_client_lazy_initialization(self):
        """Client should be created on first access."""
        tool = PerplexityResearchTool(api_key="test-key")
        client = tool.client
        assert client is not None
        assert isinstance(client, AsyncPerplexity)

    def test_client_reused_on_subsequent_access(self):
        """Same client instance should be returned on subsequent access."""
        tool = PerplexityResearchTool(api_key="test-key")
        client1 = tool.client
        client2 = tool.client
        assert client1 is client2

    async def test_close_method(self):
        """Close method should cleanup client."""
        tool = PerplexityResearchTool(api_key="test-key")
        _ = tool.client  # Initialize
        assert tool._client is not None

        await tool.close()
        assert tool._client is None

    async def test_context_manager(self):
        """Context manager should cleanup on exit."""
        async with PerplexityResearchTool(api_key="test-key") as tool:
            _ = tool.client
            assert tool._client is not None

        assert tool._client is None


class TestConfiguration:
    """Tests for tool configuration."""

    def test_default_configuration(self, tool):
        """Tool should use sensible defaults."""
        assert tool.preset == "pro-search"
        assert tool.reasoning_effort == "medium"
        assert tool.max_steps == 5
        assert tool.timeout == 120.0
        assert tool.max_retries == 2

    def test_custom_configuration(self):
        """Tool should accept custom configuration."""
        config = {
            "preset": "sonar-pro",
            "reasoning_effort": "high",
            "max_steps": 8,
            "timeout": 180.0,
            "max_retries": 5,
        }
        tool = PerplexityResearchTool(api_key="test-key", config=config)

        assert tool.preset == "sonar-pro"
        assert tool.reasoning_effort == "high"
        assert tool.max_steps == 8
        assert tool.timeout == 180.0
        assert tool.max_retries == 5


class TestDescription:
    """Tests for tool description."""

    def test_description_mentions_cost(self, tool):
        """Description should mention the cost."""
        assert "Token-based" in tool.description

    def test_description_mentions_citations(self, tool):
        """Description should mention citations."""
        assert "citation" in tool.description.lower()

    def test_description_mentions_web_search_alternative(self, tool):
        """Description should mention web_search as free alternative."""
        assert "web_search" in tool.description


class TestMakeResearchRequest:
    """Tests for _make_research_request method."""

    async def test_make_research_request_calls_sdk_method(self):
        """_make_research_request should call client.responses.create()."""
        tool = PerplexityResearchTool(api_key="test-key")

        mock_response = MagicMock()
        mock_responses = MagicMock()
        mock_responses.create = AsyncMock(return_value=mock_response)

        with patch.object(tool, "_client", create=True) as mock_client:
            mock_client.responses = mock_responses

            result = await tool._make_research_request(
                query="Test query",
                reasoning_effort="medium",
                max_steps=5,
                instructions="Test instructions",
            )

            mock_responses.create.assert_called_once_with(
                input="Test instructions\n\nResearch question: Test query",
                preset="pro-search",
                reasoning={"effort": "medium"},
                max_steps=5,
            )
            assert result == mock_response

        await tool.close()


class TestMount:
    """Test the mount() function."""

    async def test_mount_with_api_key_env(self, monkeypatch):
        """Mount should work with API key from environment."""
        monkeypatch.setenv("PERPLEXITY_API_KEY", "test-key-from-env")

        from amplifier_core import TestCoordinator

        from amplifier_module_tool_perplexity_search import mount

        coordinator = TestCoordinator()
        cleanup = await mount(coordinator, {})

        assert cleanup is not None
        # Verify tool was mounted
        assert any(
            entry.get("name") == "perplexity_research"
            for entry in coordinator.mount_history
            if entry.get("mount_point") == "tools"
        )

        # Cleanup
        await cleanup()

    async def test_mount_without_api_key_returns_none(self, monkeypatch):
        """Mount should return None if no API key available."""
        monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)

        from amplifier_core import TestCoordinator

        from amplifier_module_tool_perplexity_search import mount

        coordinator = TestCoordinator()
        result = await mount(coordinator, {})

        assert result is None
