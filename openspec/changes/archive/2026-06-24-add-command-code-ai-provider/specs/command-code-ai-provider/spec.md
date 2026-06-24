## ADDED Requirements

### Requirement: Command Code AI is listed as a configurable provider

The system MUST include `command_code_ai` in the `SUPPORTED_PROVIDER_IDS` tuple and the `PROVIDER_CATALOG` dict (configured in `config/provider_catalog.py`), with `credential_env="COMMAND_CODE_API_KEY"`, `credential_attr="command_code_api_key"`, `default_base_url="https://api.commandcode.ai/provider/v1"`, and the capability `"dual_transport"` in addition to the standard chat capabilities (`"chat"`, `"streaming"`, `"tools"`). The provider factory MUST be registered in `PROVIDER_FACTORIES` under the key `"command_code_ai"`, and the invariant `set(PROVIDER_CATALOG) == set(PROVIDER_FACTORIES) == set(SUPPORTED_PROVIDER_IDS)` MUST remain valid.

#### Scenario: The catalog contains the provider
- **WHEN** `config.provider_catalog.PROVIDER_CATALOG` is loaded at runtime
- **THEN** the key `"command_code_ai"` is present and the associated `ProviderDescriptor` has `credential_env="COMMAND_CODE_API_KEY"` and `default_base_url` pointing to `https://api.commandcode.ai/provider/v1`

#### Scenario: The registry invariant remains valid
- **WHEN** the server starts
- **THEN** `set(PROVIDER_CATALOG) == set(PROVIDER_FACTORIES) == set(SUPPORTED_PROVIDER_IDS)` (the boot assertion passes)

#### Scenario: `MODEL` accepts the new provider
- **WHEN** `.env` sets `MODEL=command_code_ai/claude-sonnet-4-6`
- **THEN** `Settings()` validates without error and `settings.provider_type == "command_code_ai"`

### Requirement: The provider routes Claude to /v1/messages and other families to /v1/chat/completions

The `CommandCodeAIProvider` class MUST inspect the request `model` at runtime and delegate to the `AnthropicMessagesTransport` sub-transport when the `model` starts with `claude-` (case-insensitive), and to the `OpenAIChatTransport` sub-transport in all other cases. Both sub-transports MUST be instantiated with the same `ProviderConfig` (same key, same `base_url`, same proxy, same rate limit). The routing MUST be transparent to `fcc-claude` (which sends Anthropic-format) and `fcc-codex` (which sends OpenAI Responses, converted internally to Chat Completions by `core/openai_responses/`).

#### Scenario: A Claude request uses /v1/messages
- **WHEN** a request with `model="claude-sonnet-4-6"` is sent to `CommandCodeAIProvider.chat`/`stream`
- **THEN** the provider delegates to `AnthropicMessagesTransport` configured with `base_url=https://api.commandcode.ai/provider/v1` and the request is sent to `POST /v1/messages`

#### Scenario: An open-model request uses /v1/chat/completions
- **WHEN** a request with `model="deepseek/deepseek-v4-flash"` is sent to `CommandCodeAIProvider.chat`/`stream`
- **THEN** the provider delegates to `OpenAIChatTransport` configured with `base_url=https://api.commandcode.ai/provider/v1` and the request is sent to `POST /v1/chat/completions`

#### Scenario: Both sub-transports share the same base URL and key
- **WHEN** the `CommandCodeAIProvider` is constructed
- **THEN** both sub-transport instances share `api_key`, `base_url`, `proxy`, `rate_limit`, `max_concurrency`, and HTTP timeouts from the same `ProviderConfig`

### Requirement: Bearer authentication (and x-api-key for /v1/messages)

The provider MUST send `Authorization: Bearer <COMMAND_CODE_API_KEY>` on every request to Command Code AI. For the Anthropic Messages sub-transport, the provider MUST also send `x-api-key: <COMMAND_CODE_API_KEY>` (the provider accepts both for the `/messages` route). The key MUST never be logged in clear: the `ProviderConfig` reuses the redaction already present in `core.anthropic` and `core.openai_responses`.

#### Scenario: Bearer header is present
- **WHEN** any request (chat, stream, listing) is sent to the provider
- **THEN** the `Authorization: Bearer <key>` header is present

#### Scenario: x-api-key header is present on the Anthropic sub-transport
- **WHEN** a Claude request is routed to `AnthropicMessagesTransport`
- **THEN** the `x-api-key: <key>` header is present in addition to `Authorization`

#### Scenario: The key never appears in payload logs
- **WHEN** `LOG_RAW_API_PAYLOADS=true` is configured
- **THEN** the value of `command_code_api_key` appears redacted (e.g. `"********"`) in any logged payload

### Requirement: Model listing via the unified endpoint

The provider MUST expose model listing via `GET /v1/models` on the configured `base_url` (the `model_list` parameter of `OpenAIChatTransport` or the equivalent sub-transport). The listing MUST return all families supported by the account (Claude, GPT, Gemini, open-models), and each model MUST be exposed on the fcc-server `/v1/models` API in the form `<provider_id>/<model_id>` (e.g. `command_code_ai/claude-sonnet-4-6`).

#### Scenario: Model listing returns the account's models
- **WHEN** `GET https://api.commandcode.ai/provider/v1/models` is called with the `COMMAND_CODE_API_KEY`
- **THEN** the provider parses the response and exposes the models as `command_code_ai/<id>` on the fcc-server `/v1/models`

#### Scenario: Claude-prefixed models remain routable
- **WHEN** the user selects `command_code_ai/claude-sonnet-4-6` in the Claude Code picker
- **THEN** the dual routing selects `AnthropicMessagesTransport` and the request goes to `/v1/messages`

### Requirement: Configuration persisted via .env, managed env, and Admin UI

The system MUST accept `COMMAND_CODE_API_KEY` (required for the provider to function; secret), `COMMAND_CODE_PROXY` (optional; secret/advanced), and `COMMAND_CODE_BASE_URL` (optional; text; default `https://api.commandcode.ai/provider/v1`) as `Settings` fields. The Admin UI MUST display these three fields in the "Providers" section, and `COMMAND_CODE_API_KEY` MUST be stored as `secret=True` and rendered with `MASKED_SECRET` when already configured. The Admin API MUST accept PUT/POST on the config endpoint with these fields and MUST persist them to `~/.fcc/.env` via `write_managed_env`. The Admin API MUST validate that `Settings(**kwargs)` remains valid after the update and MUST reject updates that break invariants (invalid provider, malformed model format).

#### Scenario: The Admin UI displays the provider
- **WHEN** the Admin UI loads `/admin/api/config`
- **THEN** three entries appear in the "Providers" section with `key="COMMAND_CODE_API_KEY"`, `key="COMMAND_CODE_PROXY"`, and `key="COMMAND_CODE_BASE_URL"`

#### Scenario: Key update via the Admin API
- **WHEN** the user saves the form with `COMMAND_CODE_API_KEY=<new-key>`
- **THEN** `~/.fcc/.env` is rewritten atomically containing `COMMAND_CODE_API_KEY=<new-key>` and the field is returned as `MASKED_SECRET` on subsequent reads

#### Scenario: A custom base URL is honored
- **WHEN** `COMMAND_CODE_BASE_URL=https://custom.commandcode.invalid/provider` is configured
- **THEN** the `ProviderConfig` built for `command_code_ai` uses that `base_url` instead of the default

#### Scenario: An invalid base URL is rejected
- **WHEN** the user tries to save `COMMAND_CODE_BASE_URL` to a value that makes `Settings` fail
- **THEN** the Admin API returns 400 with the list of validation errors and no file is rewritten

#### Scenario: Without COMMAND_CODE_API_KEY the provider is not reported as configured
- **WHEN** `COMMAND_CODE_API_KEY` is blank and `MODEL` does not use `command_code_ai`
- **THEN** the Admin API `provider_config_status` reports `command_code_ai` as `"missing_key"` and the server keeps working with the other providers

### Requirement: The smoke harness detects the provider automatically

`smoke/lib/config.py` MUST detect whether `command_code_ai` is configured by consulting the `Settings` attribute indicated by `PROVIDER_CATALOG[provider].credential_attr` instead of maintaining an `if/elif` chain. `PROVIDER_SMOKE_DEFAULT_MODELS` MUST include the key `"command_code_ai"` pointing to a canonical Claude model (suggested default: `command_code_ai/claude-sonnet-4-6`), and the override `FCC_SMOKE_MODEL_COMMAND_CODE_AI` MUST be honored when set. The smoke `providers` target MUST exercise the provider whenever the key is set and a model is resolved.

#### Scenario: has_provider_configuration is generic
- **WHEN** the smoke harness checks `command_code_ai`
- **THEN** it consults `PROVIDER_CATALOG["command_code_ai"].credential_attr == "command_code_api_key"` and reads `settings.command_code_api_key.strip()` — with no provider-specific `if/elif` chain

#### Scenario: The default model appears when no override is given
- **WHEN** `FCC_SMOKE_MODEL_COMMAND_CODE_AI` is not set
- **THEN** the smoke uses `command_code_ai/claude-sonnet-4-6` (the `PROVIDER_SMOKE_DEFAULT_MODELS` default)

#### Scenario: An env-var override is honored
- **WHEN** `FCC_SMOKE_MODEL_COMMAND_CODE_AI=command_code_ai/deepseek-v4-flash`
- **THEN** the smoke uses `command_code_ai/deepseek-v4-flash` instead of the default

### Requirement: Install scripts support the canonical origin and a local repo path

`scripts/install.sh` and `scripts/install.ps1` MUST accept an optional `--from <path>` flag (and the `--from=<path>` / `-From=<path>` form). When `--from` is provided, the package spec MUST be the literal path (no `git+` prefix) and `uv tool install --from <path> --force ...` MUST install from that path. When `--from` is omitted, the current behavior (install from `REPO_GIT_URL` via `git+https`) MUST be preserved. The uninstall scripts (`uninstall.sh` / `uninstall.ps1`) MUST remain unchanged: `uv tool uninstall free-claude-code` is source-agnostic.

#### Scenario: Install from the canonical origin still works
- **WHEN** `curl ... | sh` is run with no arguments
- **THEN** the package is installed from `git+https://codeberg.org/mikek8s/free-claude-code.git` (current behavior preserved)

#### Scenario: Install from a local repo
- **WHEN** `./scripts/install.sh --from /path/to/free-claude-code` is run in a local checkout
- **THEN** `uv tool install --from /path/to/free-claude-code --force ...` is invoked with the local path as the spec

#### Scenario: The `--from=<path>` form is also accepted
- **WHEN** `./scripts/install.sh --from=/path/to/free-claude-code` is run
- **THEN** the behavior is identical to the previous scenario (the `=` form is parsed)

#### Scenario: Uninstall does not need to know the source
- **WHEN** `./scripts/uninstall.sh` is run after a local install
- **THEN** `uv tool uninstall free-claude-code` removes the package normally, without distinguishing canonical vs. local source
