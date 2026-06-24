"""Request builders for Command Code AI dual transport."""

from __future__ import annotations

from typing import Any

from loguru import logger

from config.constants import ANTHROPIC_DEFAULT_MAX_OUTPUT_TOKENS
from core.anthropic import ReasoningReplayMode, build_base_request_body
from core.anthropic.conversion import OpenAIConversionError
from core.anthropic.native_messages_request import (
    build_base_native_anthropic_request_body,
)
from providers.exceptions import InvalidRequestError


def build_anthropic_request_body(request_data: Any, *, thinking_enabled: bool) -> dict:
    """Build JSON for Command Code AI Anthropic-compat POST /v1/messages."""
    logger.debug(
        "COMMAND_CODE_REQUEST: anthropic build model={} msgs={}",
        getattr(request_data, "model", "?"),
        len(getattr(request_data, "messages", [])),
    )
    body = build_base_native_anthropic_request_body(
        request_data,
        default_max_tokens=ANTHROPIC_DEFAULT_MAX_OUTPUT_TOKENS,
        thinking_enabled=thinking_enabled,
    )
    extra = getattr(request_data, "extra_body", None)
    if extra:
        raise InvalidRequestError(
            "Command Code AI Anthropic endpoint does not support extra_body on requests."
        )
    body["stream"] = True
    logger.debug(
        "COMMAND_CODE_REQUEST: anthropic build done model={} msgs={} tools={}",
        body.get("model"),
        len(body.get("messages", [])),
        len(body.get("tools", [])),
    )
    return body


def build_openai_request_body(request_data: Any, *, thinking_enabled: bool) -> dict:
    """Build OpenAI-format JSON for Command Code AI POST /v1/chat/completions."""
    logger.debug(
        "COMMAND_CODE_REQUEST: openai build model={} msgs={}",
        getattr(request_data, "model", "?"),
        len(getattr(request_data, "messages", [])),
    )
    try:
        body = build_base_request_body(
            request_data,
            reasoning_replay=ReasoningReplayMode.REASONING_CONTENT
            if thinking_enabled
            else ReasoningReplayMode.DISABLED,
        )
    except OpenAIConversionError as exc:
        raise InvalidRequestError(str(exc)) from exc
    logger.debug(
        "COMMAND_CODE_REQUEST: openai build done model={} msgs={} tools={}",
        body.get("model"),
        len(body.get("messages", [])),
        len(body.get("tools", [])),
    )
    return body


def select_model_family(model: str) -> str:
    """Return ``"anthropic"`` for Claude-* models, ``"openai"`` otherwise.

    This is a pure routing helper: no I/O, no state. Routing is by model name
    prefix only, matching the Command Code AI provider documentation
    (https://commandcode.ai/docs/provider): Claude-* -> ``/v1/messages``;
    every other family -> ``/v1/chat/completions``.
    """
    return "anthropic" if model.lower().startswith("claude-") else "openai"
