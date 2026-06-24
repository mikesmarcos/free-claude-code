# AGENTIC DIRECTIVE

> This file is identical to CLAUDE.md. Keep them in sync.

## CODING ENVIRONMENT

- Install astral uv using "curl -LsSf https://astral.sh/uv/install.sh | sh" if not already installed and if already installed then update it to the latest version
- Install Python 3.14.0 stable using `uv python install 3.14.0` if not already installed (requires uv >=0.9; see `[tool.uv] required-version` in `pyproject.toml`)
- Always use `uv run` to run files instead of the global `python` command.
- Current uv ruff formatter is set to py314 which has supports multiple exception types without paranthesis (except TypeError, ValueError:)
- Read `.env.example` for environment variables.
- All CI checks must pass; failing checks block merge.
- Add tests for new changes (including edge cases).
- Before pushing, prefer `./scripts/ci.sh` (macOS/Linux) or `.\scripts\ci.ps1` (Windows) to run the local CI sequence; requires `uv` on PATH. The local scripts run Ruff in repair mode (`ruff format`, then `ruff check --fix`) before type checking and tests.
- Use `--only` / `--skip` (PowerShell: `-Only` / `-Skip`) to run a subset when iterating; use `--dry-run` to print commands without running them.
- GitHub CI remains check-only for Ruff (`ruff format --check`, `ruff check`) so branch protection verifies committed code.
- Fall back to individual repair commands when debugging local failures: `uv run ruff format`, `uv run ruff check --fix`, `uv run ty check`, `uv run pytest -v --tb=short`. Use GitHub-style checks only when verifying enforcement locally: `uv run ruff format --check`, `uv run ruff check`.
- Do not add `# type: ignore` or `# ty: ignore`; fix the underlying type issue.
- All 5 check IDs are represented in `scripts/ci.sh` / `scripts/ci.ps1` and enforced in `tests.yml` on push/merge (parallel jobs: suppression grep, ruff-format, ruff-check, ty, pytest).
- Branch protection: set **required status checks** to **all** of those statuses (e.g. **Ban type ignore suppressions**, **ruff-format**, **ruff-check**, **ty**, **pytest**—use the exact labels GitHub shows, which may be prefixed with **CI /**). Remove **ci** from required checks if it was previously added for the old gate job.

## IDENTITY & CONTEXT

- You are an expert Software Architect and Systems Engineer.
- Goal: Zero-defect, root-cause-oriented engineering for bugs; test-driven engineering for new features. Think carefully; no need to rush.
- Code: Write the simplest code possible. Keep the codebase minimal and modular.

## ARCHITECTURE PRINCIPLES

- **Shared utilities**: Put shared Anthropic protocol logic in neutral `core/anthropic/` modules. Do not have one provider import from another provider's utils.
- **DRY**: Extract shared base classes to eliminate duplication. Prefer composition over copy-paste.
- **Encapsulation**: Use accessor methods for internal state (e.g. `set_current_task()`), not direct `_attribute` assignment from outside.
- **Provider-specific config**: Keep provider-specific fields (e.g. `nim_settings`) in provider constructors, not in the base `ProviderConfig`.
- **Dead code**: Remove unused code, legacy systems, and hardcoded values. Use settings/config instead of literals (e.g. `settings.provider_type` not `"nvidia_nim"`).
- **Performance**: Use list accumulation for strings (not `+=` in loops), cache env vars at init, prefer iterative over recursive when stack depth matters.
- **Platform-agnostic naming**: Use generic names (e.g. `PLATFORM_EDIT`) not platform-specific ones (e.g. `TELEGRAM_EDIT`) in shared code.
- **No type ignores**: Do not add `# type: ignore` or `# ty: ignore`. Fix the underlying type issue.
- **Complete migrations**: When moving modules, update imports to the new owner and remove old compatibility shims in the same change unless preserving a published interface is explicitly required.
- **Maximum Test Coverage**: There should be maximum test coverage for everything, preferably live smoke test coverage to catch bugs early

## COGNITIVE WORKFLOW

1. **ANALYZE**: Read relevant files. Do not guess.
2. **PLAN**: Map out the logic. Identify root cause or required changes. Order changes by dependency.
3. **EXECUTE**: Fix the cause, not the symptom. Execute incrementally with clear commits.
4. **VERIFY**: Run `./scripts/ci.sh` or `.\scripts\ci.ps1`, plus relevant smoke tests when needed. Confirm the fix via logs or output.
5. **SPECIFICITY**: Do exactly as much as asked; nothing more, nothing less.
6. **PROPAGATION**: Changes impact multiple files; propagate updates correctly.
7. **VERSION**: If the commit touches production files on `main`, bump semver in the same commit (see [Versioning](#versioning-main)).

## VERSIONING (MAIN)

Every commit on `main` that changes a **production file** must include a semver bump in **`pyproject.toml`** in the **same commit**. Do not merge or push prod changes without updating the version.

### Production files

These paths count as production (runtime, packaging, or install surface):

- `api/`, `cli/`, `config/`, `core/`, `messaging/`, `providers/`
- `.env.example`
- `pyproject.toml` (dependencies, scripts, packaging)
- `scripts/install.sh`, `scripts/install.ps1`, `scripts/uninstall.sh`, `scripts/uninstall.ps1`, `scripts/ci.sh`, `scripts/ci.ps1`

These do **not** require a version bump on their own:

- `tests/`, `smoke/`
- Docs and assets: `README.md`, `assets/`, `AGENTS.md`, `CLAUDE.md`
- CI and repo config: `.github/`, `.gitignore`

If a single commit mixes production and non-production edits, still bump the version.

### Semver rules

Use `[project].version` as `MAJOR.MINOR.PATCH`:

- **PATCH** (`x.y.Z+1`): bug fixes, refactors with no user-visible behavior change, dependency updates, packaging/install fixes.
- **MINOR** (`x.Y+1.0`): backward-compatible features—new providers, admin fields, CLI commands, config options, or behavior additions.
- **MAJOR** (`X+1.0.0`): breaking changes—removed or renamed env vars, incompatible API/CLI/default changes, or migrations users must act on.

When unsure between PATCH and MINOR, prefer PATCH for fixes and MINOR for new capability.

### Required steps

1. Classify the change and choose the bump level.
2. Update `version` in `pyproject.toml`.
3. Run `uv lock` so `uv.lock` reflects the new package version.
4. Include the version and lockfile updates in the same commit as the production change.

Example commit on `main` after a packaging fix: bump `1.2.38` → `1.2.39`, run `uv lock`, commit together with the fix.

## Repository conventions

- The harness Claude Code is committed at `.claude/skills/` and
  `.claude/commands/`. The `.claude/*` rule in `.gitignore` only matches
  state files like `.claude/settings.local.json`. Do not change the
  matching/negation order without also updating the matching rules in
  `tests/repo/test_gitignore_preserves_harness_and_opsx.py`.
- `.codex/` and `.opencode/` are equivalent harness surfaces and follow
  the same rule (force-include `skills/` and `commands/`).
- The OpenSpec folder (`openspec/`) is the source of truth for specs and
  changes. The top-level `!openspec/` negation in `.gitignore` keeps it
  versioned.
- The smoke harness lives at `smoke/lib/`. The legacy `lib/` rule in
  `.gitignore` does not apply to it; this is enforced by the
  `!smoke/lib/` negation.
- `AGENTS.md` and `CLAUDE.md` are committed (identical content); the
  `!AGENTS.md` / `!CLAUDE.md` negations protect them in `.gitignore`.
- Local-only state (NOT committed): `.claude/settings.local.json`,
  `.smoke-results/`, `.env`, `**/*.logs`. These are ignored on purpose.

See `tests/repo/test_gitignore_preserves_harness_and_opsx.py` for the
guard-rail that enforces this contract.

## SUMMARY STANDARDS

- Summaries must be technical and granular.
- Include: [Files Changed], [Logic Altered], [Verification Method], [Residual Risks] (if no residual risks then say none).

## TOOLS

- Prefer built-in tools (grep, read_file, etc.) over manual workflows. Check tool availability before use.

## EXTERNAL MEMORY (PERSISTENT CROSS-SESSION) — OPTIONAL

> If an **external memory provider** is available in this session — exposed as MCP tools (any prefix, e.g. `mcp__retaindb__*`, `mcp__memory__*`), a registered plugin, environment variables (e.g. `RETAINDB_*`), a CLI, a hook script, or any other harness-specific mechanism — follow the rules below. Each harness (opencode, Claude Code, Hermes, etc.) surfaces the same provider differently: detect the available interface and adapt. If no such provider is reachable, **ignore this entire section** — it must not block, error, or be referenced.

**Detection.** Before relying on the external store, verify it is actually reachable, not merely registered. Concrete signals by harness:

- **MCP tools present** (e.g. `mcp__retaindb__*`): also confirm a local server responds — e.g. `curl -fsS ${RETAINDB_BASE_URL:-http://localhost:3111}/health` returns `status: ok` for RetainDB, or the equivalent health endpoint advertised by whatever provider is wired in.
- **Plugin only** (no MCP): call the plugin's documented entry point once and confirm a non-error response.
- **Env vars only**: the provider may be reachable via direct HTTP — probe its base URL.
- **CLI / hook script only**: invoke with `--help` or a no-op and confirm exit code 0.

If the probe fails, fall back to project-local memory only and skip the steps below. Never assume "the tool is listed, so it works."

**When to consult.** At the start of any non-trivial task (new feature, refactor, bug investigation spanning more than one file), query the provider for prior context. Preferred call shapes, in order of richness:

1. `context_pack` / `context_query` — returns structured `entries` (memory + code_map + delta) with token budgets.
2. `memory_search` / `memory_query` — flat recall of relevant memories.
3. Plugin/CLI equivalent exposed by the provider.

Skim the returned entries for prior decisions, conventions, or gotchas relevant to the current work. Cite them only when they change the plan — do not dump them into the answer.

**When to record.** After a task that produces a non-obvious decision, a workaround, a recurring failure mode, or a new convention, persist a concise summary (≤ 200 tokens) to the provider, tagged with a clear `memory_type` (`decision`, `convention`, `gotcha`, `fact`) and the project slug the harness is configured for. Do not store raw tool output, secrets, or anything already captured in this repo's docs (`AGENTS.md` / `CLAUDE.md` / `README.md`) — those are the source of truth, not the external store.

**Conflict resolution.** If an external memory contradicts a file in the repo, **the repo wins**. Note the contradiction in the response and (optionally) flag the stale memory for the user to decide whether to overwrite or delete it. Do not silently mutate stored memories to match the repo.

**Scope.** Treat the external store as a cross-session hint layer, not a primary source. Project-local directives in this file (AGENTS.md / CLAUDE.md) and the codebase itself always take precedence. Project-local memory and the external store complement each other: local files pin conventions for the repo, the external store carries learned context across sessions and machines.
