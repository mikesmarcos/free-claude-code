## Why

The Free Claude Code proxy hardcodes the Admin UI (`/admin`) to loopback-only via `require_loopback_admin`, with no configuration knob. The `HOST` and `PORT` fields already exist on `Settings` and are read by Pydantic Settings from the `HOST` / `PORT` env vars (and `server.py` / `cli/entrypoints.py` already bind Uvicorn to `settings.host` / `settings.port`), but the contract is implicit: the env vars are not documented in `.env.example`, `Settings` declares no explicit `validation_alias`, and the admin manifest does not surface them as user-editable. Operators who want to expose the admin UI on a private LAN, a custom interface, or accept connections from a specific set of remote IPs have no supported path — the loopback check rejects any non-loopback client unconditionally.

This change ports the proven `host-and-admin-access-controls` work from the migration branch, **reconciled against the final shipped code**. The migration's archived OpenSpec artifacts predate three late fix commits (Origin `localhost` hostname resolution, wildcard allow-list accepting a non-IP Origin hostname such as a Tailscale MagicDNS name, IPv4-mapped IPv6 matching, and `GEMINI_API_KEY` test isolation) that landed after that archive was written and are not reflected in its `tasks.md`. The spec and tasks below describe the **actual shipped behavior**, not the stale archive.

## What Changes

- **Promote `HOST` and `PORT` to first-class, documented env vars.** Add explicit `validation_alias="HOST"` / `validation_alias="PORT"` to the existing `host` / `port` fields in `config/settings.py`; document them in `.env.example`. `server.py` and `cli/entrypoints.py` already consume `settings.host` / `settings.port`, so no entry-point change is required.
- **Introduce `ALLOW_ADMIN_FROM`** — a new env var listing the source IPs / CIDR ranges that may reach `/admin` and the admin API. Accepted forms:
  - Blank or unset → restrict to loopback (`127.0.0.0/8` + `::1/128`); preserves the existing safety posture.
  - Comma-separated list of IPv4 / IPv6 addresses or CIDR blocks (e.g. `127.0.0.1,10.0.0.0/24,::1`).
  - The literal `*` (or `0.0.0.0` / `::`) → accept any source.
- **Replace the hardcoded loopback check** in `api/admin_routes.py::require_loopback_admin` with a configurable allow-list resolver. The check operates on the request's immediate peer (`request.client.host`) **and** the `Origin` header hostname, both evaluated against `settings.allow_admin_from_networks()`. The resolver (`_host_in_networks`) handles: wildcard allow-lists accept any source (IP or hostname); the `localhost` hostname resolves to `127.0.0.1` / `::1`; IPv4-mapped IPv6 addresses match IPv4 networks. Remove the now-unused `_is_loopback_host` and `_origin_is_local` helpers.
- **Expose the effective allow-list** in the `admin_status` response (`allow_admin_from` string + `allow_admin_from_networks` sorted list) so the Admin UI can display it.
- **Persist the setting through the Admin UI.** Register `ALLOW_ADMIN_FROM` as a `ConfigFieldSpec` in `api/admin_config.py` (`runtime` section, `restart_required=True`).
- **Update `.env.example`** to document `HOST`, `PORT`, and `ALLOW_ADMIN_FROM` with usage notes and a security warning for the wildcard forms.
- **Tests** — port the three shipped test files covering: default loopback allow/reject; explicit CIDR allow/reject; comma-separated mixed v4/v6; IPv6; wildcards `*` / `0.0.0.0` / `::`; `localhost` Origin resolution; wildcard accepting a hostname Origin; IPv4-mapped IPv6; the `Origin` header path; admin API uses the same guard; the `ConfigFieldSpec` round-trip; settings parsing/validation (blank → loopback, wildcards normalize, malformed → `ValueError`, `HOST`/`PORT` aliases).

Non-breaking: the default (loopback-only) is identical to current behavior; `HOST`/`PORT` already exist. `ANTHROPIC_AUTH_TOKEN` proxy auth is out of scope.

## Capabilities

### New Capabilities

- `admin-access-control`: governs which source addresses may reach `/admin` and the admin API, safe-by-default with explicit operator opt-in for non-loopback exposure; also covers the first-class `HOST` / `PORT` bind settings.

### Modified Capabilities

None. No `openspec/specs/` capability on `main` requires requirement-level changes; this is a net-new surface.

## Impact

- `config/settings.py` — add `allow_admin_from` field; add explicit `validation_alias` for `host` / `port`; add `validate_allow_admin_from` `@field_validator` and `allow_admin_from_networks()` method (production).
- `api/admin_routes.py` — replace `require_loopback_admin` with the allow-list resolver; add `_host_in_networks`; remove `_is_loopback_host` / `_origin_is_local`; extend `admin_status` (production).
- `api/admin_config.py` — add the `ALLOW_ADMIN_FROM` `ConfigFieldSpec` (`runtime`, `restart_required=True`) (production).
- `.env.example` — document `HOST`, `PORT`, `ALLOW_ADMIN_FROM` (production).
- `tests/api/test_admin_access_control.py`, `tests/api/test_admin_config_access_control.py`, `tests/config/test_admin_access_control_settings.py` — port the three shipped test files (non-production).
- `tests/api/test_admin.py` — extend with the `ALLOW_ADMIN_FROM` round-trip coverage shipped on the migration branch (non-production).
- **Version bump MINOR** per `CLAUDE.md` (new config option `ALLOW_ADMIN_FROM` + first-class `HOST`/`PORT`): `2.3.15` → `2.4.0` (assumes the leading URL-repoint chore landed at `2.3.15`), plus `uv lock`.
- No new dependency (`ipaddress` is stdlib). No `server.py` / `cli/entrypoints.py` change (they already bind `settings.host` / `settings.port`).
