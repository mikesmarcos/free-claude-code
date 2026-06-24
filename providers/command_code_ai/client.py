"""Command Code AI provider (Anthropic + OpenAI dual transport)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from providers.defaults import COMMAND_CODE_DEFAULT_BASE
from providers.base import BaseProvider, ProviderConfig
from providers.model_listing import ProviderModelInfo
from providers.transports.anthropic_messages import AnthropicMessagesTransport
from providers.transports.openai_chat import OpenAIChatTransport

from .request import (
    build_anthropic_request_body,
    build_openai_request_body,
    select_model_family,
)

_ANTHROPIC_VERSION = "2023-06-01"


class _CommandCodeAnthropic(AnthropicMessagesTransport):
    """Sub-transport for Claude-* -> POST /v1/messages (Bearer + x-api-key)."""

    def __init__(self, config: ProviderConfig, *, base_url: str):
        super().__init__(
            config,
            provider_name="COMMAND_CODE_ANTHROPIC",
            default_base_url=base_url,
        )

    def _build_request_body(
        self, request: Any, thinking_enabled: bool | None = None
    ) -> dict:
        return build_anthropic_request_body(
            request,
            thinking_enabled=self._is_thinking_enabled(request, thinking_enabled),
        )

    def _request_headers(self) -> dict[str, str]:
        return {
            "Accept": "text/event-stream",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
        }

    def _model_list_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
        }


class _CommandCodeOpenAI(OpenAIChatTransport):
    """Sub-transport for open-models -> POST /v1/chat/completions (Bearer)."""

    def __init__(self, config: ProviderConfig, *, base_url: str, api_key: str):
        super().__init__(
            config,
            provider_name="COMMAND_CODE_OPENAI",
            base_url=base_url,
            api_key=api_key,
        )

    def _build_request_body(
        self, request: Any, thinking_enabled: bool | None = None
    ) -> dict:
        return build_openai_request_body(
            request,
            thinking_enabled=self._is_thinking_enabled(request, thinking_enabled),
        )


class CommandCodeAIProvider(BaseProvider):
    """Command Code AI: dual transport under one Bearer key.

    Claude-* models stream via /v1/messages (Anthropic); every other family
    streams via /v1/chat/completions (OpenAI). Both sub-transports share the
    same ProviderConfig (key, base URL, proxy, rate limits, timeouts).
    See https://commandcode.ai/docs/provider for the routing rules.
    """

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        base_url = (config.base_url or COMMAND_CODE_DEFAULT_BASE).rstrip("/")
        self._base_url = base_url
        self._api_key = config.api_key
        self._anthropic = _CommandCodeAnthropic(config, base_url=base_url)
        self._openai = _CommandCodeOpenAI(
            config, base_url=base_url, api_key=config.api_key
        )

    def _select(self, model: str) -> BaseProvider:
        if select_model_family(model) == "anthropic":
            return self._anthropic
        return self._openai

    def preflight_stream(
        self, request: Any, *, thinking_enabled: bool | None = None
    ) -> None:
        """Delegate preflight to the selected sub-transport so conversion
        errors surface before the SSE stream is opened."""
        self._select(getattr(request, "model", "")).preflight_stream(
            request, thinking_enabled=thinking_enabled
        )

    def _build_request_body(
        self, request: Any, thinking_enabled: bool | None = None
    ) -> dict:
        """Delegate request-body building to the selected sub-transport.

        Mirrors :meth:`preflight_stream`/:meth:`stream_response`: routing is
        by model family, so the correct builder (Anthropic vs OpenAI) is
        selected. Exposed so callers/tests can build a body without streaming.
        """
        if select_model_family(getattr(request, "model", "")) == "anthropic":
            return self._anthropic._build_request_body(
                request, thinking_enabled=thinking_enabled
            )
        return self._openai._build_request_body(
            request, thinking_enabled=thinking_enabled
        )

    async def stream_response(
        self,
        request: Any,
        input_tokens: int = 0,
        *,
        request_id: str | None = None,
        thinking_enabled: bool | None = None,
    ) -> AsyncIterator[str]:
        transport = self._select(getattr(request, "model", ""))
        async for event in transport.stream_response(
            request,
            input_tokens,
            request_id=request_id,
            thinking_enabled=thinking_enabled,
        ):
            yield event

    async def list_model_ids(self) -> frozenset[str]:
        return await self._openai.list_model_ids()

    async def list_model_infos(self) -> frozenset[ProviderModelInfo]:
        return await self._openai.list_model_infos()

    async def cleanup(self) -> None:
        await self._anthropic.cleanup()
        await self._openai.cleanup()
