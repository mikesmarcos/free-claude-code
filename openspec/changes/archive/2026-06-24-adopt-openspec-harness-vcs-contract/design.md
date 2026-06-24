## Context

`main` (Codeberg fork, v2.3.14) inherits a generic `Python.gitignore` plus a bare `.claude` rule and a tail block. It has no `.codex/` / `.opencode/` rules, no `!openspec/`, no `!AGENTS.md` / `!CLAUDE.md`, and no `lib/` rule. It tracks zero `.claude/` / `.codex/` / `.opencode/` content and has no committed OpenSpec framework (`openspec/config.yaml` or skills/commands).

The migration branch already proved a working contract + guard-rail + framework. This change **adopts that proven state**, reconciled for `main`'s starting point. The reconciliation differences are:

1. `main` has **no `lib/` rule** (the migration's `.gitignore` inherited one from `Python.gitignore`). We **add** the `lib/` + `!smoke/lib/` pair so the contract and guard-rail match the migration exactly, and so `smoke/lib/` is defended against a future re-added `lib/` rule.
2. `main` has **no tracked harness files**. We port all 25 skills/commands + `openspec/config.yaml` as net-new files.
3. `main` has a **bare `.claude`** rule (ignores the whole dir). We replace it with `.claude/*` + carved-out negations + `.claude/settings.local.json`, so the project-owned subtrees are tracked while local state stays ignored.
4. Per the **current** `CLAUDE.md`, this change touches no production files → **no version bump**. (The migration bumped 2.4.0 → 2.4.1 under a stricter reading; we follow the rules as written today.)

The guard-rail test strategy (ported verbatim from the migration) tests the `.gitignore` **text directly** rather than `git check-ignore` at runtime: `git check-ignore` reports exit 1 for already-tracked files regardless of rules, and a scratch dir inherits the parent's ignore rules. Asserting the rule lines are present (and ordered) is exactly what the contract requires and is robust across environments.

## Goals / Non-Goals

**Goals:**

- Make the versioning contract explicit and testable: ignore only local state; commit harness skills/commands, `openspec/`, `smoke/lib/`, `AGENTS.md` / `CLAUDE.md`.
- Import the OpenSpec framework (`openspec/config.yaml` + 25 skills/commands) so any clone can run `/opsx:*` and the `smoke/` suite.
- Guard-rail test that fails if someone re-adds `.claude/`, removes a `!` negation, or removes `!smoke/lib/`.
- Keep secrets and local state ignored (`.env`, `*.logs`, `.smoke-results`, `.claude/settings.local.json`).

**Non-Goals:**

- Do not migrate `.codex/` → `.claude/` (equivalent harness surfaces for different harnesses; keep both).
- Do not introduce pre-commit hooks or external tooling.
- Do not change runtime production code.
- Do not bump the version (no production files touched).

## Decisions

- **Reuse the migration's guard-rail test verbatim.** It tests `.gitignore` text directly, which is environment-independent and exactly matches the contract.
- **Add the `lib/` + `!smoke/lib/` pair** even though `main` lacks `lib/`. This matches the migration's contract, makes the guard-rail's `lib/` < `!smoke/lib/` ordering assertion meaningful, and defends `smoke/lib/` against a future re-added `lib/` rule. Adding `lib/` newly ignores a root `lib/` dir, but the project has none, so it is harmless.
- **`.claude/*` + carved negations** instead of bare `.claude`. Last-match-wins means the negations must come *after* the broad ignore, in the order: `.claude/*`, `!.claude/skills/`, `!.claude/commands/`, `.claude/settings.local.json`. The guard-rail enforces this order.
- **Generalize the spec scenarios**: drop migration-specific line numbers (e.g. "linha 17", "linha 224") and the specific archive path (`2026-06-22-host-and-admin-access-controls/...`) in favor of rule-name and `openspec/changes/`-relative references, so the contract is repo-state-independent.
- **No version bump** per current `CLAUDE.md` production-files rules.

## Risks / Trade-offs

- **Adding a `lib/` rule** newly ignores a root-level `lib/` directory if one existed. The project has none, so the risk is theoretical; the guard-rail's `lib/` < `!smoke/lib/` ordering check is the payoff.
- **Canonical path list in the guard-rail** covers only the paths currently used by the project. A new harness surface (e.g. `.gemini/skills/`) would require updating the list — this is by design (it makes omission explicit and fails loudly).
- **25 new committed files** increase repo size trivially and appear in `git status` after clone — the intended, visible signal that the harness is now versioned.
- **No runtime behavior change**, so no smoke-test regression risk from this change alone.
