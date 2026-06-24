## ADDED Requirements

### Requirement: Harness skills and commands are versioned

The system MUST version every file under `.claude/skills/`, `.claude/commands/`, `.codex/skills/`, `.codex/commands/`, `.opencode/skills/`, and `.opencode/commands/`. `.gitignore` MUST contain explicit negations `!.claude/skills/`, `!.claude/commands/`, `!.codex/skills/`, `!.codex/commands/`, `!.opencode/skills/`, and `!.opencode/commands/` that override any ancestral ignore rule. The system MUST fail the guard-rail test if any of these negations is removed.

#### Scenario: A harness skill is committed
- **WHEN** `git check-ignore -v .claude/skills/openspec-propose/SKILL.md` is run
- **THEN** the command returns exit code 1 (the file is NOT ignored) and stdout is empty

#### Scenario: A harness command is committed
- **WHEN** `git check-ignore -v .claude/commands/opsx/propose.md` is run
- **THEN** the command returns exit code 1

#### Scenario: A Codex skill is committed
- **WHEN** `git check-ignore -v .codex/skills/openspec-apply-change/SKILL.md` is run
- **THEN** the command returns exit code 1

#### Scenario: An OpenCode command is committed
- **WHEN** `git check-ignore -v .opencode/commands/opsx-apply.md` is run
- **THEN** the command returns exit code 1

#### Scenario: Removing the `.claude/skills/` negation fails the test
- **WHEN** someone edits `.gitignore` to remove the `!.claude/skills/` line and commits
- **THEN** the test `tests/repo/test_gitignore_preserves_harness_and_opsx.py` fails with a message referencing the missing path

### Requirement: The OpenSpec folder is versioned

The system MUST version `openspec/` (including `openspec/config.yaml`, `openspec/specs/`, `openspec/changes/`, and `openspec/changes/archive/`). `.gitignore` MUST contain the negation `!openspec/` that overrides any ancestral ignore rule. The system MUST fail the guard-rail test if the negation is removed.

#### Scenario: `openspec/config.yaml` is committed
- **WHEN** `git check-ignore -v openspec/config.yaml` is run
- **THEN** the command returns exit code 1

#### Scenario: `openspec/specs/` is committed
- **WHEN** `git check-ignore -v openspec/specs/admin-access-control/spec.md` is run
- **THEN** the command returns exit code 1

#### Scenario: `openspec/changes/archive/` is committed
- **WHEN** `git check-ignore -v openspec/changes/archive/<any-change>/proposal.md` is run
- **THEN** the command returns exit code 1

### Requirement: `smoke/lib/` is versioned

The system MUST version every file under `smoke/lib/`. `.gitignore` MUST contain the negation `!smoke/lib/` that overrides the `lib/` rule, and the `lib/` rule MUST appear before the `!smoke/lib/` negation so git honors it. The system MUST fail the guard-rail test if the negation is removed or if the ordering is wrong.

#### Scenario: `smoke/lib/config.py` is committed
- **WHEN** `git check-ignore -v smoke/lib/config.py` is run
- **THEN** the command returns exit code 1 (the `lib/` rule does not apply to this path because of the `!smoke/lib/` negation)

#### Scenario: An arbitrary subpath of `smoke/lib/` is committed
- **WHEN** `git check-ignore -v smoke/lib/utils/helpers.py` is run (a hypothetical future path)
- **THEN** the command returns exit code 1 (the `!smoke/lib/` negation is recursive)

#### Scenario: A real root-level `lib/` stays ignored
- **WHEN** a file `lib/foo.py` is created at the repo root (hypothetical, unused by the project)
- **THEN** `git check-ignore -v lib/foo.py` returns exit code 0 and indicates `.gitignore` as the source via the `lib/` rule

### Requirement: `AGENTS.md` and `CLAUDE.md` are versioned

The system MUST version `AGENTS.md` and `CLAUDE.md` (identical by project convention). `.gitignore` MUST contain explicit negations `!AGENTS.md` and `!CLAUDE.md` that override any ancestral ignore rule (including a future `*.md` rule in a subfolder). The system MUST fail the guard-rail test if either negation is removed.

#### Scenario: `AGENTS.md` is committed
- **WHEN** `git check-ignore -v AGENTS.md` is run
- **THEN** the command returns exit code 1

#### Scenario: `CLAUDE.md` is committed
- **WHEN** `git check-ignore -v CLAUDE.md` is run
- **THEN** the command returns exit code 1

### Requirement: Harness local state is NOT versioned

The system MUST ignore `.claude/settings.local.json` (machine/user-specific permissions). `.gitignore` MUST contain a `.claude/settings.local.json` rule (without negation). The system MUST fail the guard-rail test if the rule is removed (e.g. someone makes it a negation by mistake, or omits it and the file leaks into `git status`).

#### Scenario: `settings.local.json` is ignored
- **WHEN** `git check-ignore -v .claude/settings.local.json` is run
- **THEN** the command returns exit code 0 and stdout indicates `.gitignore` as the source

#### Scenario: Other files under `.claude/` stay ignored by default
- **WHEN** an arbitrary file `.claude/foo.json` is created
- **THEN** `git check-ignore -v .claude/foo.json` returns exit code 0 (the ancestral `.claude/*` rule still holds; only `skills/` and `commands/` were explicitly negated)

### Requirement: Smoke state is NOT versioned

The system MUST ignore the `.smoke-results/` directory (smoke-suite run artifacts). The `.smoke-results` rule MUST be present in `.gitignore` and MUST NOT be negated. The system MUST fail the guard-rail test if the rule is removed.

#### Scenario: A smoke artifact is ignored
- **WHEN** a file `.smoke-results/run-<timestamp>.json` is created
- **THEN** `git check-ignore -v .smoke-results/run-<timestamp>.json` returns exit code 0

### Requirement: A guard-rail test detects regression

The system MUST have a pytest module at `tests/repo/test_gitignore_preserves_harness_and_opsx.py` that:
- Asserts every required negation rule is present in `.gitignore` text (for the canonical list of versioned paths).
- Asserts every required ignore rule is present (for the canonical list of local-state paths).
- Asserts the `.claude/` block rule ordering: `.claude/*` before `!.claude/skills/` before `!.claude/commands/` before `.claude/settings.local.json`.
- Asserts the `lib/` rule appears before `!smoke/lib/`.
- Runs in any environment where the `.gitignore` file is readable (no network, no git runtime behavior dependency).
- Is part of the `pytest` CI job (no new job required).

#### Scenario: Reintroducing `.claude/` without negation breaks the test
- **WHEN** someone adds `.claude/` at the top of `.gitignore` (without the corresponding negations)
- **THEN** the test fails with an `AssertionError` referencing `.claude/skills/openspec-propose/SKILL.md` and the rule that ignored it

#### Scenario: Removing `!smoke/lib/` breaks the test
- **WHEN** someone removes the `!smoke/lib/` line from `.gitignore`
- **THEN** the test fails with an `AssertionError` referencing `smoke/lib/config.py`

#### Scenario: Adding a new harness surface without a negation breaks the test
- **WHEN** someone adds `.gemini/skills/` to `.gitignore` without adding `!.gemini/skills/`
- **THEN** the test does not cover it (the canonical list covers only currently-used paths; new paths require updating the canonical list, which is the point — omission becomes explicit)

#### Scenario: The test runs in CI
- **WHEN** `./scripts/ci.sh` is run in any clean clone
- **THEN** the `pytest` job includes and passes `test_gitignore_preserves_harness_and_opsx.py`
