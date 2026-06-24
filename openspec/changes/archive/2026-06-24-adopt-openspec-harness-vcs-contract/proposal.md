## Why

The Codeberg fork's `main` (v2.3.14) carries an inherited, generic `Python.gitignore` plus a bare `.claude` rule and a small tail block (`.cursor`, `.serena`, `agent_workspace`, `llama_cache`, `.smoke-results`, `.vscode`). It has **no** rules for `.codex/` or `.opencode/`, **no** `!openspec/` negation, **no** `!AGENTS.md` / `!CLAUDE.md` negations, and **no** `lib/` rule at all. Critically, `main` also tracks **zero** `.claude/` / `.codex/` / `.opencode/` content and has **no** committed OpenSpec framework.

This collides with how the project actually operates:

- The OpenSpec/opsx framework — `openspec/config.yaml` plus the harness skills/commands that implement `/opsx:propose`, `/opsx:apply`, `/opsx:archive`, `/opsx:explore`, `/opsx:sync` — is not committed. In a fresh clone (by any dev, agent, or CI), the harness cannot find those instructions, so the OpenSpec workflow is unavailable.
- The bare `.claude` rule would ignore `.claude/skills/` and `.claude/commands/` even if they were added, unless explicitly carved out.
- `smoke/lib/` (imported by `smoke/conftest.py` and the prereq tests) is currently *not* ignored (there is no `lib/` rule on `main`), but nothing protects it if someone re-adds a `lib/` rule later.
- `AGENTS.md` and `CLAUDE.md` are committed and identical by convention, but nothing prevents someone from ignoring one by accident.

The goal is to make "what is committed" **explicit and testable**: ignore only local state (credentials, caches, smoke results, personal IDE state, `settings.local.json`); commit everything that is source-of-truth for the workflow (harness skills/commands, the `openspec/` folder, `smoke/lib/`, `AGENTS.md` / `CLAUDE.md`). This change also **imports the OpenSpec framework itself** (`openspec/config.yaml` + the 25 harness skill/command files) — the "regras de openspec" the project adopts — and enforces the contract with a guard-rail test.

This is the **foundation change**: it must land before the admin-access and command-code-ai changes so the repo is OpenSpec-capable and the `.gitignore` contract protects the artifacts those changes produce.

## What Changes

- **Port the OpenSpec framework**: `openspec/config.yaml` plus 25 harness instruction files — 5 skills + 5 commands under `.claude/`, 5 skills under `.codex/`, 5 skills + 5 commands under `.opencode/`.
- **Rewrite the `.gitignore` harness block**: replace the bare `.claude` rule with `.claude/*` + `!.claude/skills/` + `!.claude/commands/` + `.claude/settings.local.json` (in that order, so last-match-wins carves out the project-owned subtrees); add `.codex/*` + `!.codex/skills/` + `!.codex/commands/`; add `.opencode/*` + `!.opencode/skills/` + `!.opencode/commands/`; add `!openspec/`, `!AGENTS.md`, `!CLAUDE.md`.
- **Add the `lib/` + `!smoke/lib/` pair** to the Distribution/packaging section. `main` currently has neither; adding both matches the contract and makes the guard-rail's ordering assertion meaningful (and future-proofs `smoke/lib/` against a re-added `lib/` rule).
- **Add the guard-rail test** `tests/repo/test_gitignore_preserves_harness_and_opsx.py` (plus `tests/repo/__init__.py`), ported from the migration branch. It asserts every required negation and ignore rule is present in `.gitignore` text, and checks rule ordering for the `.claude/` block and the `lib/` / `!smoke/lib/` pair.
- **Document the contract** in `CLAUDE.md` and `AGENTS.md` (identical "Repository conventions" block) so the versioning rule is explicit for humans and agents.
- **No version bump**: per the current `CLAUDE.md` production-files list, `.gitignore`, `AGENTS.md`, `CLAUDE.md`, and `tests/` are non-production, and the harness/openspec files are dev infrastructure — so this change touches zero production files. (This differs from the migration branch, which bumped 2.4.0 → 2.4.1 under a stricter reading; we follow the current rules.)

No breaking change. The only observable effect is that `git status` after a clone lists more files (skills/commands, `smoke/lib/`) and no longer mentions `.claude/settings.local.json`.

## Capabilities

### New Capabilities

- `harness-opsx-vcs-contract`: defines the versioning contract between the Claude Code / Codex / OpenCode harness, the OpenSpec/opsx framework, and the `free-claude-code` repository — which artifacts are versioned, which are local, and the invariant that any clone can run `/opsx:*` and the `smoke/` suite without import errors. Enforced by a guard-rail test.

### Modified Capabilities

None. No existing `openspec/specs/` capability exists on `main` yet; this is the bootstrap.

## Impact

- `.gitignore` — rewrite of the harness block + `lib/` / `!smoke/lib/` pair (non-production per `CLAUDE.md`).
- `AGENTS.md` / `CLAUDE.md` — add the "Repository conventions" block, kept identical (non-production per `CLAUDE.md`).
- `tests/repo/__init__.py` + `tests/repo/test_gitignore_preserves_harness_and_opsx.py` — new guard-rail test (non-production).
- `openspec/config.yaml` — new framework config (non-production dev infrastructure).
- `.claude/`, `.codex/`, `.opencode/` skills + commands — 25 new harness instruction files (non-production).
- **No production files touched** (`api/`, `cli/`, `config/`, `core/`, `messaging/`, `providers/`, `.env.example`, `pyproject.toml`, `scripts/`) → **no semver bump** and **no `uv lock` change**.
- No new dependency (the test uses stdlib `re` / `pathlib` against the `.gitignore` text).
- No state migration; no effect on `.env` or managed env.
