## Context

`server.py` starts Uvicorn with `host`/`port` from `Settings` (`server.py:25-26`, `cli/entrypoints.py:111-112`), and Pydantic Settings already reads these from `HOST` / `PORT` because the field names uppercase-match. But the contract is implicit: no `.env.example` docs, no explicit `validation_alias`, no Admin UI signal.

The admin guard lives in `api/admin_routes.py::require_loopback_admin`, using two private helpers (`_is_loopback_host`, `_origin_is_local`) that reduce the peer and `Origin` hostname to a loopback check. There is no opt-out: any non-loopback client gets `403 Admin UI is local-only`. The `ConfigFieldSpec` manifest has no allow-list row, so the Admin UI cannot persist a relaxed value even if the operator wanted one.

The migration branch shipped a working implementation plus three late fix commits that the original archived `tasks.md` does not capture:
- `6f2ad3a` — resolve the `localhost` hostname in the `Origin` header to loopback addresses, so `http://localhost:8082` matches a loopback allow-list.
- `47dfed5` — a wildcard allow-list (`*` / `0.0.0.0` / `::`) accepts the `Origin` hostname even when it is not parseable as a literal IP (e.g. a Tailscale MagicDNS name), because `ALLOW_ADMIN_FROM` governs *who may reach /admin*, not *which address the server listens on* (that is `HOST`).
- `b70e623` — isolate `GEMINI_API_KEY` from the process env in admin tests so the suite is hermetic.

The shipped `_host_in_networks` also handles IPv4-mapped IPv6 sources matching IPv4 networks. This design adopts the **final shipped behavior**.

## Goals / Non-Goals

**Goals:**

- Make `HOST` / `PORT` first-class, documented, env-controlled bind addresses.
- Add `ALLOW_ADMIN_FROM` (IPs / CIDRs / wildcards) governing `/admin` and the admin API.
- Keep loopback-only as the safe default.
- Validate the allow-list once at `Settings` load time (malformed entries prevent startup).
- Apply the same check to the immediate peer and the `Origin` hostname; resolve `localhost`; let wildcards accept hostnames; handle IPv4-mapped IPv6.
- Surface `ALLOW_ADMIN_FROM` in the Admin UI manifest (`restart_required=True`) and in `admin_status`.

**Non-Goals:**

- Modifying the proxy-level `ANTHROPIC_AUTH_TOKEN` auth path.
- Adding username/password login, OAuth, or session-based admin auth.
- Changing `server.py` / `cli/entrypoints.py` bind logic (already correct).

## Decisions

- **Validate at load time, resolve at request time.** `validate_allow_admin_from` (a `mode="before"` `@field_validator`) normalizes and rejects malformed entries during `Settings` construction, so the server fails fast. `allow_admin_from_networks()` parses the stored string into a `frozenset` of `ipaddress` networks on each call (cheap, and avoids staleness across supervised restarts).
- **`_host_in_networks` semantics** (ported from the shipped code):
  - A wildcard allow-list (any network with `prefixlen == 0`) accepts any source — IP or hostname — because the operator explicitly opened `/admin` to every network.
  - `localhost` resolves to `127.0.0.1` / `::1` so loopback allow-lists match `http://localhost:<port>` Origins.
  - IPv4 addresses are also matched as IPv4-mapped IPv6 (`::ffff:<addr>`); IPv6 addresses with `.ipv4_mapped` are matched against IPv4 networks.
- **`restart_required=True`** for `ALLOW_ADMIN_FROM` because the guard resolves from `Settings` on every admin request; a restart guarantees the new value is loaded through a single, predictable code path.
- **Version bump MINOR** (new config option + first-class env vars), per `CLAUDE.md`. This reconciles the migration's internal inconsistency (its proposal said PATCH, its archive tasks said MINOR); current rules say MINOR.

## Risks / Trade-offs

- **Wildcard exposure** (`*` / `0.0.0.0/0`) opens `/admin` to any reachable client. The `.env.example` and `ConfigFieldSpec` description carry a security warning; safe-by-default (blank → loopback) limits the blast radius.
- **Hostname `Origin` matching** is deliberately permissive only for wildcards and `localhost`; an arbitrary non-IP hostname against a non-wildcard allow-list is rejected (cannot be parsed as an IP), which is the safe failure mode.
- **`restart_required`** means an operator editing `ALLOW_ADMIN_FROM` in the UI must restart for it to take effect — predictable but not instant. Acceptable given the guard reads `Settings` per request.
- **Three test files** (~625 lines) is more coverage than the migration's archive described; this reflects the late fixes and is intentional.
