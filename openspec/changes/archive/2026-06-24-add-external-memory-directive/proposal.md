## Why

`AGENTS.md` and `CLAUDE.md` (kept identical by convention, see `CLAUDE.md:1`) currently steer the agent only toward **project-local** sources: the file system (`openspec/`, `tests/`, `smoke/`), the `pyproject.toml` script surface, and the version-control history. There is no rule for the growing class of **external, persistent, cross-session memory providers** (RetainDB, Zep, Mem0, custom REST backends) that the harness in this repo already supports through MCP and plugins.

The result is inconsistent behavior across sessions and across developers:

- A developer who has RetainDB running locally gets *zero* historical context on session start, even though the data is sitting at `http://localhost:3111`.
- A developer without RetainDB never sees any reference to it, so the workflow is invisible and never regresses.
- The agent has no explicit rule for **when to consult**, **when to record**, or **how to resolve conflicts** with the repo's source-of-truth docs (`AGENTS.md` / `CLAUDE.md` / `README.md`).
- Captured memories can quietly drift from reality, because nothing tells the agent to treat the repo as the authority.

The goal is to make the agent's relationship with an optional external memory provider **explicit, harness-agnostic, and self-disabling**. The rule must detect the provider's interface (MCP tools, plugin, env vars, CLI, hook script) instead of hard-coding any product name; must verify reachability before relying on it; must define when to consult, when to record, and how to resolve conflicts; and must degrade silently to project-local memory when no provider is reachable.

This is a docs-only change. It touches no production code, requires no version bump (per `CLAUDE.md` rule: `AGENTS.md` / `CLAUDE.md` are non-production), and ships as an OpenSpec change so the directive is reviewable in the same form as every other capability.

## What Changes

- **Add the `## EXTERNAL MEMORY (PERSISTENT CROSS-SESSION) — OPTIONAL` section** to `AGENTS.md` (after `## TOOLS`), with the same identical content mirrored into `CLAUDE.md` (the two files must stay byte-identical, see `CLAUDE.md:1`).
- **Define a new capability `external-memory-directive`** under `openspec/specs/external-memory-directive/spec.md` that captures the contract: detection by interface, reachability probe, consult cadence, record cadence, conflict resolution, and the repo-wins invariant.
- **Harness-agnostic by design**: the rule detects any of MCP tools, plugins, env vars, CLI entry points, or hook scripts — not any specific product. Example probes use `RETAINDB_BASE_URL` only as illustration.
- **No production files touched** (`api/`, `cli/`, `config/`, `core/`, `messaging/`, `providers/`, `.env.example`, `pyproject.toml`, `scripts/`) → **no semver bump** and **no `uv lock` change**.
- **No new dependency, no state migration, no env changes.** The directive is documentation that the agent reads at session start.
- **No new test.** The directive is behavioral, and a unit test would either flake (external service availability) or test the agent's prompt, not the codebase. Coverage is achieved by the agent itself obeying the rule on every session.

## Capabilities

### New Capabilities

- `external-memory-directive`: defines how the agent must treat an optional external memory provider in the session — detection, reachability probe, consult/record cadence, conflict resolution, and the repo-wins invariant. Provider-agnostic: applies to any MCP server, plugin, env-var-configured service, CLI, or hook script the harness exposes. The directive is a no-op when no such provider is reachable.

### Modified Capabilities

None. `harness-opsx-vcs-contract` (the only existing spec) is unrelated; the agent's harness skills, commands, and `.gitignore` contract are unchanged.

## Impact

- `AGENTS.md` — append the new section (non-production per `CLAUDE.md`).
- `CLAUDE.md` — mirror the new section byte-identical (non-production per `CLAUDE.md`).
- `openspec/specs/external-memory-directive/spec.md` — new spec, promoted from this change at archive time.
- **No production files touched** → **no semver bump**, no `uv lock` change.
- No new dependency. No state migration. No effect on `.env` or managed env.
- No breaking change. Sessions that have no external memory provider see no behavioral difference; sessions that do will see richer context at start and tighter recording after non-trivial work.
