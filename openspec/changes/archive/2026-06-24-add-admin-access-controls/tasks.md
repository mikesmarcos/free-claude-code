## 0. Conventions for this change

- **Source of the port**: `origin/migration-from-github`. The shipped code there is the final, tested behavior — including three late fix commits (`6f2ad3a` Origin `localhost`, `47dfed5` wildcard-accepts-hostname, `b70e623` GEMINI isolation) that the migration's archived `tasks.md` missed. Port the **final** state.
- **Shared files**: `config/settings.py`, `api/admin_config.py`, `.env.example`, and `tests/api/test_admin.py` are also touched by Change 3 (`add-command-code-ai-provider`). In this change, edit **only the admin-access hunks**:
  - `settings.py`: add `import ipaddress`; add `validation_alias` to `host`/`port`; add the `allow_admin_from` field + `validate_allow_admin_from` validator + `allow_admin_from_networks()` method. Do **not** add the `COMMAND_CODE_DEFAULT_BASE` import or any `command_code_*` field (those are Change 3).
  - `admin_config.py`: add **only** the `ALLOW_ADMIN_FROM` `ConfigFieldSpec`. Do **not** add the `COMMAND_CODE_*` or `FCC_SMOKE_MODEL_COMMAND_CODE_AI` fields (Change 3).
  - `.env.example`: add **only** the `HOST` / `PORT` / `ALLOW_ADMIN_FROM` block. Do **not** add the `COMMAND_CODE_*` block or update the `Valid providers` comment (Change 3).
- **Atomic commits**: each numbered group is one commit. End messages with the `Co-Authored-By: Claude` trailer.
- **Version bump MINOR** (new config option + first-class env vars): `2.3.15` → `2.4.0` in group 6 (assumes the leading URL-repoint chore landed at `2.3.15` and Change 1 did not bump).

## 1. Settings — HOST/PORT aliases and allow_admin_from

- [x] 1.1 In `config/settings.py`, add `import ipaddress` to the stdlib imports.
- [x] 1.2 Add `validation_alias="HOST"` to the existing `host` field and `validation_alias="PORT"` to the existing `port` field; keep defaults `"0.0.0.0"` and `8082`.
- [x] 1.3 Add `allow_admin_from: str = Field(default="", validation_alias="ALLOW_ADMIN_FROM")` directly under `anthropic_auth_token` in the `Server` block, with the doc comment about loopback default and wildcards.
- [x] 1.4 Add `validate_allow_admin_from` (`@field_validator("allow_admin_from", mode="before")`) that splits on commas, trims, ignores empties, accepts `*` / `0.0.0.0` / `::`, validates the rest with `ipaddress.ip_network(entry, strict=False)`, raises `ValueError` referencing the offending entry on failure, and returns the canonical comma-joined form.
- [x] 1.5 Add `allow_admin_from_networks() -> frozenset[ipaddress.IPv4Network | ipaddress.IPv6Network]` returning the parsed networks (blank → `127.0.0.0/8` + `::1/128`; `*` / `0.0.0.0` → `0.0.0.0/0`; `::` → `::/0`).
- [x] 1.6 Run `uv run pytest tests/config/test_admin_access_control_settings.py -v` (after group 5) — for now, run `uv run ty check config/settings.py` to confirm types.
- [x] 1.7 Commit: `feat(settings): add HOST/PORT aliases and ALLOW_ADMIN_FROM allow-list`.

## 2. Admin guard

- [x] 2.1 In `api/admin_routes.py`, add `_host_in_networks(host, networks) -> bool` with the shipped semantics: `None` → False; any network with `prefixlen == 0` → True (wildcard accepts any source, IP or hostname); `localhost` → matches `127.0.0.1` / `::1` against the networks; otherwise parse as IP and test membership, plus IPv4-mapped-IPv6 (`::ffff:<addr>`) and `.ipv4_mapped` handling.
- [x] 2.2 Add `is_admin_request_allowed(request, settings) -> bool` that resolves `networks = settings.allow_admin_from_networks()`, checks the peer (`request.client.host`), then the `Origin` hostname (`urlsplit(origin).hostname`) when `Origin` is present; both must pass.
- [x] 2.3 Replace the body of `require_loopback_admin` to call `is_admin_request_allowed(request, get_cached_settings())` and raise `HTTPException(403, "Admin UI is local-only")` when it returns False. Delete `_is_loopback_host` and `_origin_is_local` (no other consumers).
- [x] 2.4 Extend the `admin_status` response with `"allow_admin_from": settings.allow_admin_from` and `"allow_admin_from_networks": [str(net) for net in sorted(settings.allow_admin_from_networks(), key=str)]`.
- [x] 2.5 Commit: `feat(admin): replace loopback check with configurable ALLOW_ADMIN_FROM guard`.

## 3. Admin manifest

- [x] 3.1 In `api/admin_config.py`, add the `ALLOW_ADMIN_FROM` `ConfigFieldSpec` in the `runtime` section: `settings_attr="allow_admin_from"`, `default="127.0.0.1"`, `restart_required=True`, with the description warning about `*` and `0.0.0.0/0`. (Port the exact spec from the migration.)
- [x] 3.2 Confirm `_target_values_with_updates`, `validate_updates`, and `write_managed_env` round-trip the field via the existing manifest flow (no code change expected).
- [x] 3.3 Commit: `feat(admin): register ALLOW_ADMIN_FROM in the admin config manifest`.

## 4. .env.example

- [x] 4.1 In `.env.example`, add the `Server bind address and port` section documenting `HOST="0.0.0.0"`, `PORT="8082"`, and `ALLOW_ADMIN_FROM="127.0.0.1"` with the security warning for `*` / `0.0.0.0/0`. Place it adjacent to the existing `ANTHROPIC_AUTH_TOKEN` block.
- [x] 4.2 Commit: `docs(env): document HOST, PORT, and ALLOW_ADMIN_FROM`.

## 5. Tests

- [x] 5.1 Port `tests/api/test_admin_access_control.py` from the migration (covers default loopback allow/reject, CIDR allow/reject, comma-separated mixed v4/v6, IPv6, wildcards, `localhost` Origin, wildcard accepting a hostname Origin, IPv4-mapped IPv6, `Origin` header, admin API same guard).
- [x] 5.2 Port `tests/api/test_admin_config_access_control.py` from the migration (the `ConfigFieldSpec` round-trip + validate/apply coverage).
- [x] 5.3 Port `tests/config/test_admin_access_control_settings.py` from the migration (blank → loopback, wildcards normalize, malformed → `ValueError`, `HOST`/`PORT` aliases read from env).
- [x] 5.4 Port the `ALLOW_ADMIN_FROM`-related hunks of `tests/api/test_admin.py` from the migration (the admin round-trip). Do **not** port the `COMMAND_CODE_*` hunks (Change 3).
- [x] 5.5 Ensure the `GEMINI_API_KEY` isolation (`b70e623`) is present in the ported admin tests (e.g. `monkeypatch.delenv` / `unset` of `GEMINI_API_KEY` so the suite is hermetic). Verify against the migration's final test files.
- [x] 5.6 Run `uv run pytest tests/api/test_admin_access_control.py tests/api/test_admin_config_access_control.py tests/config/test_admin_access_control_settings.py tests/api/test_admin.py -v --tb=short` and confirm all pass.
- [x] 5.7 Commit: `test(admin): cover ALLOW_ADMIN_FROM guard, manifest round-trip, and settings parsing`.

## 6. Version, CI, smoke, and archive

- [x] 6.1 Bump `version` in `pyproject.toml` `2.3.15` → `2.4.0` (MINOR) and run `uv lock` so `uv.lock` reflects the new package version.
- [x] 6.2 Run `openspec validate add-admin-access-controls --strict` and resolve any findings.
- [x] 6.3 Run `./scripts/ci.sh` and confirm all 5 jobs pass (suppression grep, ruff-format, ruff-check, ty, pytest).
- [x] 6.4 Manual smoke: start the server with `ALLOW_ADMIN_FROM=10.0.0.0/24` and confirm `/admin` returns 200 from a peer in that range and 403 from a peer outside it; unset `ALLOW_ADMIN_FROM` and confirm the loopback default is restored.
- [x] 6.5 Run `openspec archive add-admin-access-controls -y` to archive and promote the spec to `openspec/specs/admin-access-control/spec.md`.
- [ ] 6.6 Commit the version bump + lockfile + archive: `chore(opsx): archive add-admin-access-controls, bump 2.3.15 → 2.4.0`.
