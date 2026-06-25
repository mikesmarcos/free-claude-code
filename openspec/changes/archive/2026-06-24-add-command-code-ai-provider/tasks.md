## 0. Conventions for this change

- **Source of the port**: `origin/migration-from-github` (final, tested state).
- **Prerequisites already landed**: Change 2 (`add-admin-access-controls`, which provides the admin config field pipeline and the `runtime`/`providers`/`smoke` sections).
- **Shared files**: `config/settings.py`, `api/admin_config.py`, `.env.example`, `tests/api/test_admin.py`, and `scripts/install.sh` / `install.ps1` were partly edited by earlier changes. In this change, edit **only the command-code-ai hunks**:
  - `settings.py`: add the `COMMAND_CODE_DEFAULT_BASE` import and the `command_code_*` fields. Do **not** touch `host`/`port`/`allow_admin_from` (Change 2).
  - `admin_config.py`: add the four `COMMAND_CODE_*` / `FCC_SMOKE_MODEL_COMMAND_CODE_AI` rows. Do **not** touch `ALLOW_ADMIN_FROM` (Change 2).
  - `.env.example`: add the `COMMAND_CODE_*` block and update the `Valid providers` comment. Do **not** touch `HOST`/`PORT`/`ALLOW_ADMIN_FROM` (Change 2).
  - `install.sh` / `install.ps1`: add **only** the `--from` / `-From` parsing. The `REPO_GIT_URL` value itself is owned by the leading chore.
- **Atomic commits**: each numbered group is one commit. End messages with the `Co-Authored-By: Claude` trailer.
- **Version bump MINOR** (new provider): `2.4.0` → `2.5.0` in group 11, plus `uv lock`.

## 1. Catalog entry and default base URL

- [x] 1.1 In `config/provider_catalog.py`, add `COMMAND_CODE_DEFAULT_BASE = "https://api.commandcode.ai/provider/v1"` alongside the other `*_DEFAULT_BASE` constants (with the doc comment linking to commandcode.ai/docs/provider).
- [x] 1.2 Add the `"command_code_ai": ProviderDescriptor(...)` entry with `credential_env="COMMAND_CODE_API_KEY"`, `credential_attr="command_code_api_key"`, `base_url_attr="command_code_base_url"`, `proxy_attr="command_code_proxy"`, `default_base_url=COMMAND_CODE_DEFAULT_BASE`, `transport_type="anthropic_messages"`, and capabilities `("chat", "streaming", "tools", "thinking", "rate_limit", "dual_transport")`. Place it before `lmstudio` to match the migration ordering.
- [x] 1.3 Commit: `feat(catalog): add command_code_ai provider descriptor and default base URL`.

## 2. Provider package

- [x] 2.1 Port `providers/command_code_ai/__init__.py` from the migration (exports `CommandCodeAIProvider`).
- [x] 2.2 Port `providers/command_code_ai/request.py` (Anthropic + OpenAI request builders reusing `core/anthropic/build_base_request_body` and the existing OpenAI converter).
- [x] 2.3 Port `providers/command_code_ai/client.py` (`CommandCodeAIProvider` selecting the sub-transport at runtime from the request `model`; `claude-` prefix → `AnthropicMessagesTransport`, else → `OpenAIChatTransport`; both from the same `ProviderConfig`; `Authorization: Bearer` on all requests, `x-api-key` on the Anthropic path; `GET /v1/models` listing).
- [x] 2.4 Run `uv run ty check providers/command_code_ai` and `uv run ruff check providers/command_code_ai` to confirm the port is clean.
- [x] 2.5 Commit: `feat(providers): add command_code_ai dual-transport package`.

## 3. Registry and defaults re-export

- [x] 3.1 In `providers/registry.py`, add `_create_command_code_ai(config, _settings)` (lazy `from providers.command_code_ai import CommandCodeAIProvider`) and register it in `PROVIDER_FACTORIES["command_code_ai"]`.
- [x] 3.2 In `providers/defaults.py`, add `COMMAND_CODE_DEFAULT_BASE` to the import and `__all__`.
- [x] 3.3 Verify the invariant `set(PROVIDER_CATALOG) == set(PROVIDER_FACTORIES) == set(SUPPORTED_PROVIDER_IDS)` holds (boot assertion / contract test).
- [x] 3.4 Commit: `feat(providers): wire command_code_ai into registry and defaults`.

## 4. Settings fields

- [x] 4.1 In `config/settings.py`, add `from .provider_catalog import COMMAND_CODE_DEFAULT_BASE` to the catalog imports.
- [x] 4.2 Add `command_code_api_key` (`validation_alias="COMMAND_CODE_API_KEY"`) and `command_code_base_url` (`validation_alias="COMMAND_CODE_BASE_URL"`, `default=COMMAND_CODE_DEFAULT_BASE`) in the provider config block (after the Z.ai block, before Fireworks).
- [x] 4.3 Add `command_code_proxy` (`validation_alias="COMMAND_CODE_PROXY"`) in the proxies block.
- [x] 4.4 Run `uv run ty check config/settings.py`.
- [x] 4.5 Commit: `feat(settings): add COMMAND_CODE_API_KEY / PROXY / BASE_URL fields`.

## 5. Admin config fields

- [x] 5.1 In `api/admin_config.py`, add the `COMMAND_CODE_API_KEY` `ConfigFieldSpec` (`providers`, `secret`, `secret=True`) and `COMMAND_CODE_BASE_URL` (`providers`, `default=COMMAND_CODE_DEFAULT_BASE`) in the providers section.
- [x] 5.2 Add `COMMAND_CODE_PROXY` (`providers`, `secret`, `secret=True`, `advanced=True`) in the proxies section.
- [x] 5.3 Add `FCC_SMOKE_MODEL_COMMAND_CODE_AI` (`smoke`, `advanced=True`) in the smoke section.
- [x] 5.4 Commit: `feat(admin): expose Command Code AI fields in the admin config manifest`.

## 6. .env.example

- [x] 6.1 Add the `Command Code AI Config` block (`COMMAND_CODE_API_KEY`, `COMMAND_CODE_BASE_URL`, `COMMAND_CODE_PROXY`) with the dual-transport comment.
- [x] 6.2 Update the `Valid providers` comment for `MODEL` to include `command_code_ai` (between `zai` and `lmstudio`).
- [x] 6.3 Add `FCC_SMOKE_MODEL_COMMAND_CODE_AI=` to the smoke-model block.
- [x] 6.4 Commit: `docs(env): document Command Code AI keys and smoke model override`.

## 7. Smoke harness

- [x] 7.1 In `smoke/lib/config.py`, add `"command_code_ai": "command_code_ai/claude-sonnet-4-6"` to `PROVIDER_SMOKE_DEFAULT_MODELS`.
- [x] 7.2 Refactor `has_provider_configuration` to the catalog-driven lookup: `descriptor = PROVIDER_CATALOG.get(provider)`; if `descriptor.credential_attr`, return `bool(getattr(self.settings, descriptor.credential_attr, "").strip())`; elif `descriptor.base_url_attr`, return `bool(getattr(self.settings, descriptor.base_url_attr, "").strip())`; else False. Remove the per-provider `if/elif` chain.
- [x] 7.3 Confirm `FCC_SMOKE_MODEL_COMMAND_CODE_AI` is honored by the existing override resolution (`os.getenv(f"FCC_SMOKE_MODEL_{provider.upper()}")`).
- [x] 7.4 Commit: `refactor(smoke): catalog-driven has_provider_configuration + command_code_ai default model`.

## 8. Install scripts — local source flag

- [x] 8.1 In `scripts/install.sh`, add `--from <path>` and `--from=<path>` parsing; when present, set the spec to the literal path (no `git+` prefix) and call `uv tool install --from "$spec" --force ...`; when absent, preserve the existing `REPO_GIT_URL` behavior.
- [x] 8.2 In `scripts/install.ps1`, add the equivalent `-From <path>` / `-From=<path>` parsing.
- [x] 8.3 Confirm `scripts/uninstall.sh` and `scripts/uninstall.ps1` are unchanged (source-agnostic).
- [x] 8.4 Commit: `feat(install): add --from/-From flag to install from a local repo path`.

## 9. README

- [x] 9.1 In `README.md`, update the "What You Get" provider count `17` → `18` and insert `Command Code AI` in the backend list (after Z.ai).
- [x] 9.2 Add the dual-transport bullet (`Command Code AI dual transport: one COMMAND_CODE_API_KEY serves both /v1/messages for Claude-* and /v1/chat/completions for every other family`).
- [x] 9.3 Commit: `docs(readme): list Command Code AI among supported providers`.

## 10. Tests

- [x] 10.1 Port `tests/providers/test_command_code_ai.py` (model→transport routing, missing-key handling, payload sanitization, model listing, Bearer/x-api-key headers).
- [x] 10.2 Extend `tests/contracts/test_feature_manifest.py` and `tests/contracts/test_provider_catalog_order.py` to include `command_code_ai`.
- [x] 10.3 Extend `tests/contracts/test_smoke_config.py` to cover the catalog-driven `has_provider_configuration` and the `command_code_ai` default model + `FCC_SMOKE_MODEL_COMMAND_CODE_AI` override.
- [x] 10.4 Extend `tests/providers/test_registry.py` (factory present + invariant) and `tests/providers/test_model_validation.py` (`MODEL=command_code_ai/...` validates).
- [x] 10.5 Port the `COMMAND_CODE_*` round-trip hunks of `tests/api/test_admin.py` (do **not** touch the `ALLOW_ADMIN_FROM` hunks).
- [x] 10.6 Extend `tests/config/test_config.py` (env-override sanity for the new fields).
- [x] 10.7 Extend `tests/api/test_dependencies.py` per the migration.
- [x] 10.8 Run `uv run pytest -v --tb=short` and confirm all pass (including the contract and registry invariant tests).
- [x] 10.9 Commit: `test(command-code-ai): routing, manifest, catalog, smoke, and install coverage`.

## 11. Version, CI, smoke, and archive

- [ ] 11.1 Bump `version` in `pyproject.toml` `2.4.0` → `2.5.0` (MINOR) and run `uv lock`.
- [ ] 11.2 Run `openspec validate add-command-code-ai-provider --strict` and resolve any findings.
- [ ] 11.3 Run `./scripts/ci.sh` and confirm all 5 jobs pass.
- [ ] 11.4 Manual smoke: with `COMMAND_CODE_API_KEY` set and `FCC_SMOKE_MODEL_COMMAND_CODE_AI=command_code_ai/claude-sonnet-4-6`, run the smoke `providers` target and confirm the provider is detected and exercised; confirm a Claude model routes to `/v1/messages` and a non-Claude model to `/v1/chat/completions`.
- [ ] 11.5 Run `openspec archive add-command-code-ai-provider -y` to archive and promote the spec to `openspec/specs/command-code-ai-provider/spec.md`.
- [ ] 11.6 Commit the version bump + lockfile + archive: `chore(opsx): archive add-command-code-ai-provider, bump 2.4.0 → 2.5.0`.
