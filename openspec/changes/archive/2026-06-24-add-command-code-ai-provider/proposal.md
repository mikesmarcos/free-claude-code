## Why

The `fcc-server` does not yet expose the **Command Code AI** provider (`https://api.commandcode.ai/provider/v1`): there is no catalog entry, no `.env` keys, no Admin UI fields, and no routing for it. The provider is already in operational use by the operator across several models (Claude families plus open-models). Closing this gap lets the same proxy and the `fcc-claude` / `fcc-codex` launchers consume Command Code AI without a parallel proxy.

The provider's documented contract ([commandcode.ai/docs/provider](https://commandcode.ai/docs/provider)) is unusual: a single `Bearer` API key authenticates **two** endpoints — `POST /v1/messages` (Anthropic Messages) and `POST /v1/chat/completions` (OpenAI Chat Completions) — with routing by model family (Claude-* → `/v1/messages`; every other family → `/v1/chat/completions`). Sending Claude to `/chat/completions` or an open-model to `/messages` returns `400 invalid_request_error`. No existing catalog provider exposes the Claude+open-model set on one account, so this requires a **dual-transport** provider — a new pattern — without breaking the registry invariant (`PROVIDER_CATALOG == PROVIDER_FACTORIES == SUPPORTED_PROVIDER_IDS`). The install scripts also need a `--from <path>` flag so local checkouts can be installed for development iteration alongside the canonical Codeberg origin.

This change ports the proven `add-command-code-ai-provider` work from the migration branch. It assumes the leading URL-repoint chore has already repointed `REPO_GIT_URL` to `git+https://codeberg.org/mikek8s/free-claude-code.git`, and that Change 2 (`add-admin-access-controls`) has landed, providing the admin config field pipeline this provider reuses.

## What Changes

- Add the `command_code_ai` provider to the catalog (`config/provider_catalog.py`) with a `dual_transport` capability and `COMMAND_CODE_DEFAULT_BASE`; wire the registry factory (`providers/registry.py::_create_command_code_ai`) and `providers/defaults.py` re-export, preserving the catalog/factory/ids invariant.
- Create the `providers/command_code_ai/` package: `__init__.py`, `client.py` (`CommandCodeAIProvider` selecting the sub-transport at runtime from the request `model`), and `request.py` (Anthropic and OpenAI request builders reusing `core/anthropic/build_base_request_body` and the existing OpenAI converter). Claude-* → `AnthropicMessagesTransport`; other families → `OpenAIChatTransport`; both share one `ProviderConfig` (same key, base URL, proxy, rate limit). `Authorization: Bearer <key>` on all requests; `x-api-key: <key>` additionally on the Anthropic path. Single model-listing endpoint `GET /v1/models`.
- Add the `command_code_api_key`, `command_code_proxy`, and `command_code_base_url` fields to `config/settings.py` (env `COMMAND_CODE_API_KEY` / `COMMAND_CODE_PROXY` / `COMMAND_CODE_BASE_URL`).
- Add the `COMMAND_CODE_API_KEY` (secret), `COMMAND_CODE_BASE_URL`, `COMMAND_CODE_PROXY` (secret/advanced), and `FCC_SMOKE_MODEL_COMMAND_CODE_AI` `ConfigFieldSpec` entries to `api/admin_config.py`.
- Update `.env.example` with the `COMMAND_CODE_*` block and add `command_code_ai` to the `Valid providers` comment for `MODEL`.
- Refactor `smoke/lib/config.py::has_provider_configuration` from the per-provider `if/elif` chain to a catalog-driven lookup (`PROVIDER_CATALOG[provider].credential_attr` / `base_url_attr`), and add `command_code_ai` to `PROVIDER_SMOKE_DEFAULT_MODELS` (default `command_code_ai/claude-sonnet-4-6`), honoring `FCC_SMOKE_MODEL_COMMAND_CODE_AI`.
- Extend `scripts/install.sh` and `scripts/install.ps1` with an optional `--from <path>` / `--from=<path>` flag that installs from a local path (no `git+` prefix) via `uv tool install --from <path>`, preserving the default Codeberg install. Uninstall scripts stay source-agnostic.
- Update `README.md` ("What You Get": 17 → 18 provider backends, add the Command Code AI dual-transport bullet).
- Add tests mirroring the `zai` / `opencode` patterns: model→transport routing, missing-key handling, payload sanitization, model listing, the admin field round-trip, registry/catalog invariant, and contract/manifest updates.
- Version bump MINOR (new provider) `2.4.0` → `2.5.0` per `CLAUDE.md`, plus `uv lock`.

## Capabilities

### New Capabilities

- `command-code-ai-provider`: governs consumption of Command Code AI by the `fcc-server` — dual-transport routing (Claude → `/v1/messages`, other families → `/v1/chat/completions`) under a single `COMMAND_CODE_API_KEY`, configuration persisted via `.env` / Admin UI / managed env, model listing, smoke detection, and the install `--from` flag.

### Modified Capabilities

None. The admin field pipeline this provider reuses is provided by `admin-access-control` (Change 2); adding `COMMAND_CODE_*` rows to the manifest is implementation detail, not a requirement-level change to that capability.

## Impact

- **Production** (version bump MINOR `2.4.0` → `2.5.0` + `uv lock`):
  - `config/provider_catalog.py` (`COMMAND_CODE_DEFAULT_BASE` + `command_code_ai` `ProviderDescriptor`).
  - `config/settings.py` (3 new fields).
  - `providers/command_code_ai/__init__.py`, `client.py`, `request.py` (new package).
  - `providers/registry.py` (factory + invariant), `providers/defaults.py` (re-export).
  - `api/admin_config.py` (4 new `ConfigFieldSpec` entries).
  - `.env.example` (`COMMAND_CODE_*` block + `Valid providers` comment).
  - `scripts/install.sh`, `scripts/install.ps1` (`--from` flag; the Codeberg `REPO_GIT_URL` is assumed already set by the leading chore).
  - `README.md` (provider count 17 → 18 + dual-transport bullet).
  - `pyproject.toml` (version bump) + `uv.lock`.
- **Smoke / tests** (no version bump):
  - `smoke/lib/config.py` (catalog-driven `has_provider_configuration` + default model).
  - `tests/providers/test_command_code_ai.py` (new).
  - `tests/contracts/test_feature_manifest.py`, `test_provider_catalog_order.py`, `test_smoke_config.py` (register/extend).
  - `tests/providers/test_registry.py`, `test_model_validation.py` (extend).
  - `tests/api/test_admin.py` (the `COMMAND_CODE_*` round-trip hunks).
  - `tests/config/test_config.py` (env-override sanity).
  - `tests/api/test_dependencies.py`, `tests/scripts/test_uninstallers.py` (minor updates).
- No new external dependency (HTTPX already covers HTTP). No change to `cli/launchers/*`, `core/anthropic/`, `core/openai_responses/`, or existing transports.
- Non-breaking: no existing env var is renamed/removed; the provider only appears in lists when the key is set.
