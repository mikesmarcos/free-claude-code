## Context

The `fcc-server` routes `/v1/messages` (Anthropic, consumed by `fcc-claude` and Claude Code) and `/v1/responses` (OpenAI Responses, consumed by `fcc-codex`) to providers via `config/provider_catalog.py::PROVIDER_CATALOG` (one `TransportType` per provider: `openai_chat` or `anthropic_messages`) and `providers/registry.py::PROVIDER_FACTORIES`. The sub-transports (`AnthropicMessagesTransport`, `OpenAIChatTransport`) concentrate the HTTP lifecycle, headers, model listing, retry, and rate limit; each concrete provider is essentially a `ProviderConfig` + a `_build_request_body`.

Command Code AI does not fit that single-transport model: it publishes **two** endpoints under one `Bearer` key, routed by model family (Claude → `/v1/messages`; other families → `/v1/chat/completions`). We need a **dual-transport** provider without breaking the registry invariant (`PROVIDER_CATALOG == PROVIDER_FACTORIES == SUPPORTED_PROVIDER_IDS`) or the existing sub-transports.

Persistence is already consolidated: everything the Admin UI writes goes to `~/.fcc/.env` (managed env) via `api/admin_config.py::write_managed_env`, with `Settings` (Pydantic) as the schema. New fields are additions to `BaseSettings`, the admin `FIELDS` tuple, and `.env.example`. The install scripts fix `REPO_GIT_URL` as the single source (`uv tool install --force "$REPO_GIT_URL"`), which blocks local-checkout iteration; the `--from` flag adds a local-install path alongside it.

This change assumes Change 2 (`add-admin-access-controls`) has landed, so the admin config field pipeline and the `runtime` / `providers` / `smoke` sections already exist as targets for the new `ConfigFieldSpec` rows. It also assumes the leading URL-repoint chore set `REPO_GIT_URL` to the Codeberg origin.

## Goals / Non-Goals

**Goals:**

- Expose Command Code AI as a selectable provider in `MODEL` / `MODEL_OPUS` / `MODEL_SONNET` / `MODEL_HAIKU` (format `command_code_ai/<model>`).
- Preserve `fcc-claude` → `/v1/messages` (Anthropic) and `fcc-codex` → `/v1/responses` (OpenAI Responses) end-to-end.
- Dual routing within one Command Code account: Claude-* via `AnthropicMessagesTransport`; other families via `OpenAIChatTransport`; both authenticated by the same `COMMAND_CODE_API_KEY` against the same base URL.
- Persist config via `.env` / managed env / Admin UI like the other providers; mask the key in the UI.
- Support local install (`--from <path>`) and the default Codeberg install, with source-agnostic uninstall.
- Test coverage equivalent to `zai` / `opencode`; smoke harness detects the provider automatically from the catalog (no hardcoded `if/elif`).

**Non-Goals:**

- No extra auth (OAuth, refresh tokens) — the key is `Bearer` in an env var like the other providers.
- No automatic fallback between Command Code and other providers (that stays a `MODEL_*` decision).
- No caching, queuing, batching, or new HTTP dependencies.
- No changes to existing transports or the OpenAI Responses ↔ Chat Completions conversion in `core/openai_responses/`.
- No change to the `REPO_GIT_URL` value itself (the leading chore owns the Codeberg repoint).

## Decisions

- **Dual transport by model-family prefix at runtime.** `CommandCodeAIProvider` inspects the request `model`: `claude-` prefix (case-insensitive) → `AnthropicMessagesTransport`; otherwise → `OpenAIChatTransport`. Both sub-transports are built from the same `ProviderConfig` so key, base URL, proxy, rate limit, and timeouts are shared.
- **Catalog descriptor marks `dual_transport`** alongside the standard chat capabilities (`chat`, `streaming`, `tools`, `thinking`, `rate_limit`). The descriptor's `transport_type` stays `anthropic_messages` as the primary; `dual_transport` signals the runtime split. The registry invariant is preserved by adding the matching `_create_command_code_ai` factory and the `command_code_ai` id.
- **Auth headers**: `Authorization: Bearer <key>` on every request; `x-api-key: <key>` additionally on the Anthropic path (the provider accepts both for `/messages`). The key is never logged in clear — redaction reuses `core.anthropic` / `core.openai_responses`.
- **Smoke detection becomes catalog-driven.** `has_provider_configuration` reads `PROVIDER_CATALOG[provider].credential_attr` (then `base_url_attr`) via `getattr`, eliminating the per-provider `if/elif` chain so future providers are detected automatically. `command_code_ai` gets a default smoke model (`command_code_ai/claude-sonnet-4-6`) and honors `FCC_SMOKE_MODEL_COMMAND_CODE_AI`.
- **Install `--from` parsing** accepts both `--from <path>` and `--from=<path>`; when present, the spec is the literal path (no `git+` prefix) and `uv tool install --from <path>` is used; when absent, the existing `REPO_GIT_URL` behavior is preserved. Uninstall remains `uv tool uninstall free-claude-code` (source-agnostic).
- **Version bump MINOR** (new provider) `2.4.0` → `2.5.0`, per `CLAUDE.md`.

## Risks / Trade-offs

- **Dual transport is a new pattern.** A bug in the model-family routing (e.g. misclassifying a Claude model) would send a request to the wrong endpoint and get a `400`. Mitigated by a dedicated routing unit test (`claude-` → Anthropic; non-Claude → OpenAI) and by keeping the prefix rule simple and documented.
- **The smoke refactor changes behavior for all providers** (removes the `if/elif` chain). It is behavior-preserving (each provider still checked via its catalog `credential_attr`), but it must be verified against the existing contract tests (`test_smoke_config.py`, `test_provider_catalog_order.py`).
- **`--from` local install** bypasses the `git+` fetch, so a stale local checkout could be installed. That is the intended dev-iteration behavior; the default (no `--from`) remains the Codeberg origin.
- **Secret masking** depends on the existing redaction path; the `COMMAND_CODE_API_KEY` field is `secret=True` and rendered as `MASKED_SECRET` when set, matching the other provider keys.
