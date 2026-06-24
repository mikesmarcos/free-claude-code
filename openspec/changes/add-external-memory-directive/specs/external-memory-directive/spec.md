# external-memory-directive Specification

## Purpose

Define how the agent must treat an optional external memory provider in the session — detection by interface, reachability probe, consult cadence, record cadence, conflict resolution, and the repo-wins invariant. The directive is a no-op when no such provider is reachable, and is harness-agnostic: it applies to any MCP server, plugin, env-var-configured service, CLI entry point, or hook script the harness exposes, without naming any specific product.

## Requirements

### Requirement: The directive is opt-in by reachability

The system MUST scope the entire `## EXTERNAL MEMORY (PERSISTENT CROSS-SESSION) — OPTIONAL` block to sessions where an external memory provider is actually reachable. The block MUST NOT block, error, log a warning, or be referenced in agent output when no provider is reachable. The block MUST degrade silently to project-local memory (`AGENTS.md` / `CLAUDE.md` / codebase files) when the reachability probe fails.

#### Scenario: No provider reachable
- **WHEN** the session has no `mcp__<provider>__*` MCP tools, no relevant plugin loaded, no `RETAINDB_*` / equivalent env vars, and no CLI/hook entry point
- **THEN** the agent MUST behave identically to a session before this change was applied — no external memory calls, no mention of the directive in user-facing output

#### Scenario: MCP tools listed but server unreachable
- **WHEN** MCP tools with a memory-provider prefix are listed but the local server health probe returns non-2xx
- **THEN** the agent MUST treat the provider as unavailable and skip all consult/record steps in this session

### Requirement: The directive detects the provider interface, not a specific product

The system MUST identify the provider by **interface class** — MCP tools, plugin, env vars, CLI, or hook script — and MUST NOT hard-code any product name as a requirement. Worked examples (e.g. a RetainDB health URL) are permitted in the directive prose as illustration, but MUST NOT appear as normative requirements in the spec.

#### Scenario: MCP interface is available
- **WHEN** the harness exposes `mcp__<provider>__*` tools
- **THEN** the agent MUST treat that as a provider interface and run a reachability probe against the provider's documented health endpoint

#### Scenario: Plugin-only interface
- **WHEN** no MCP tools are present but a registered plugin exposes a memory-related entry point
- **THEN** the agent MUST invoke the plugin's documented entry point once and confirm a non-error response before relying on it

#### Scenario: Env-var-only interface
- **WHEN** only env vars (e.g. `RETAINDB_BASE_URL`) are set and no MCP or plugin is present
- **THEN** the agent MUST probe the base URL directly with a health-equivalent request and treat a 2xx response as the reachability signal

#### Scenario: CLI or hook-script interface
- **WHEN** only a CLI or hook script is available (no MCP, no plugin, no env var pointing at a live service)
- **THEN** the agent MUST invoke the script with `--help` or a no-op and confirm exit code 0 before relying on it

### Requirement: The agent consults the provider at task boundaries

The system MUST consult the provider at the **start of any non-trivial task** (new feature, refactor, bug investigation spanning more than one file). A trivial task (single-file typo, one-line doc fix) MAY skip the consult step. The consult MUST prefer structured endpoints (`context_pack` / `context_query`) over flat recall (`memory_search` / `memory_query`) when both are available.

#### Scenario: New feature starts
- **WHEN** a non-trivial task begins
- **THEN** the agent MUST issue a context-equivalent query to the provider with a short task description and skim the returned entries for prior decisions, conventions, or gotchas

#### Scenario: Provider returns structured context
- **WHEN** the provider responds with structured `entries` (memory + code_map + delta) under a token budget
- **THEN** the agent MUST skim those entries and cite them only when they change the plan — the agent MUST NOT dump the full response into the user-facing answer

### Requirement: The agent records durable learnings

The system MUST record to the provider after any task that produces a **non-obvious decision, a workaround, a recurring failure mode, or a new convention**. The recorded entry MUST be ≤ 200 tokens, MUST be tagged with a clear `memory_type` (`decision`, `convention`, `gotcha`, `fact`), and MUST be scoped to the project's configured slug. The agent MUST NOT record raw tool output, secrets, or anything already captured in `AGENTS.md` / `CLAUDE.md` / `README.md` of this repo.

#### Scenario: A non-obvious decision is made
- **WHEN** the task closes with a decision that future sessions would benefit from (e.g. "we use X over Y because of constraint Z")
- **THEN** the agent MUST call the provider's write endpoint with a `decision`-typed summary scoped to the project

#### Scenario: An item duplicates repo docs
- **WHEN** the proposed memory entry would duplicate content already in `AGENTS.md` / `CLAUDE.md` / `README.md`
- **THEN** the agent MUST NOT record it — the repo is the source of truth for project conventions

### Requirement: The repo wins on conflict

The system MUST treat `AGENTS.md`, `CLAUDE.md`, `README.md`, and the codebase itself as the source of truth for project conventions. If an external memory entry contradicts any of these, the repo MUST take precedence, the contradiction MUST be surfaced in the agent's response, and the stale memory MUST be flagged for the user (the agent MUST NOT silently overwrite stored memories to match the repo).

#### Scenario: Memory contradicts AGENTS.md
- **WHEN** a stored memory says X and `AGENTS.md` says not-X
- **THEN** the agent MUST follow `AGENTS.md`, MUST surface the contradiction in the response, and MUST suggest the user review the stored memory for deletion or correction

### Requirement: The directive is documented in AGENTS.md and CLAUDE.md

The system MUST keep an `## EXTERNAL MEMORY (PERSISTENT CROSS-SESSION) — OPTIONAL` section in `AGENTS.md` AND MUST mirror the section byte-identical in `CLAUDE.md` (the two files are kept in sync per `CLAUDE.md:1`). Removing the section, breaking the mirror, or rewording any normative verb (consult, record, conflict, repo-wins) is a contract violation that MUST be caught at PR review.

#### Scenario: A future PR drops the section
- **WHEN** a PR removes or substantially rewrites the `## EXTERNAL MEMORY` block in `AGENTS.md` without a corresponding openspec change
- **THEN** the PR MUST be rejected at review and the openspec change `external-memory-directive` MUST be amended or a new change proposed
