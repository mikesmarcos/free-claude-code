"""Tests for Command Code AI dual-transport provider."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest

from api.models.anthropic import Message, MessagesRequest
from config.constants import ANTHROPIC_DEFAULT_MAX_OUTPUT_TOKENS
from providers.base import ProviderConfig
from providers.command_code_ai import CommandCodeAIProvider
from providers.command_code_ai.request import select_model_family
from providers.defaults import COMMAND_CODE_DEFAULT_BASE
from providers.exceptions import InvalidRequestError


@pytest.fixture
def command_code_config():
    return ProviderConfig(
        api_key="test_command_code_key",
        base_url=COMMAND_CODE_DEFAULT_BASE,
        rate_limit=10,
        rate_window=60,
        enable_thinking=True,
    )


@pytest.fixture(autouse=True)
def mock_rate_limiter():
    """Stub both Anthropic and OpenAI sub-transport rate limiters."""

    @asynccontextmanager
    async def _slot():
        yield

    with (
        patch(
            "providers.transports.anthropic_messages.transport.GlobalRateLimiter"
        ) as mock_anthropic,
        patch(
            "providers.transports.openai_chat.transport.GlobalRateLimiter"
        ) as mock_openai,
    ):
        for mock in (mock_anthropic, mock_openai):
            instance = mock.get_scoped_instance.return_value

            async def _passthrough(fn, *args, **kwargs):
                return await fn(*args, **kwargs)

            instance.execute_with_retry = AsyncMock(side_effect=_passthrough)
            instance.concurrency_slot.side_effect = _slot
        yield


@pytest.fixture
def command_code_provider(command_code_config):
    return CommandCodeAIProvider(command_code_config)


def test_select_model_family_routes_claude_to_anthropic():
    assert select_model_family("claude-sonnet-4-6") == "anthropic"
    assert select_model_family("Claude-Haiku-4-5") == "anthropic"
    assert select_model_family("claude-3-5-sonnet-latest") == "anthropic"


def test_select_model_family_routes_open_models_to_openai():
    assert select_model_family("deepseek/deepseek-v4-flash") == "openai"
    assert select_model_family("zai-org/GLM-5") == "openai"
    assert select_model_family("Qwen/Qwen3.6-Plus") == "openai"
    assert select_model_family("moonshotai/Kimi-K2.6") == "openai"


def test_init_uses_command_code_base_url(command_code_config):
    with patch("httpx.AsyncClient"):
        provider = CommandCodeAIProvider(command_code_config)
    assert provider._base_url == COMMAND_CODE_DEFAULT_BASE
    assert provider._api_key == "test_command_code_key"
    assert provider._anthropic._base_url == COMMAND_CODE_DEFAULT_BASE
    assert provider._openai._base_url == COMMAND_CODE_DEFAULT_BASE
    assert provider._openai._api_key == "test_command_code_key"


def test_request_build_for_claude_uses_anthropic_builder(command_code_provider):
    request = MessagesRequest(
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[Message(role="user", content="Hi")],
    )
    body = command_code_provider._build_request_body(request)
    assert body["model"] == "claude-sonnet-4-6"
    assert body["stream"] is True
    assert body["max_tokens"] == 100


def test_request_build_for_openai_uses_openai_builder(command_code_provider):
    request = MessagesRequest(
        model="deepseek/deepseek-v4-flash",
        max_tokens=100,
        messages=[Message(role="user", content="Hi")],
    )
    body = command_code_provider._build_request_body(request)
    assert "max_tokens" in body
    assert isinstance(body.get("messages"), list)


def test_request_build_claude_rejects_extra_body(command_code_provider):
    request = MessagesRequest.model_validate(
        {
            "model": "claude-sonnet-4-6",
            "messages": [{"role": "user", "content": "x"}],
            "extra_body": {"x": 1},
        }
    )
    with pytest.raises(InvalidRequestError, match="does not support extra_body"):
        command_code_provider._build_request_body(request)


def test_default_max_tokens_for_claude(command_code_provider):
    request = MessagesRequest(
        model="claude-sonnet-4-6",
        messages=[Message(role="user", content="x")],
    )
    body = command_code_provider._build_request_body(request)
    assert body["max_tokens"] == ANTHROPIC_DEFAULT_MAX_OUTPUT_TOKENS


@pytest.mark.asyncio
async def test_cleanup_calls_both_sub_transports(command_code_provider):
    command_code_provider._anthropic.cleanup = AsyncMock()
    command_code_provider._openai.cleanup = AsyncMock()

    await command_code_provider.cleanup()

    command_code_provider._anthropic.cleanup.assert_awaited_once()
    command_code_provider._openai.cleanup.assert_awaited_once()
