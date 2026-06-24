## 0. Conventions for this change

- **Source of truth for the port**: every file below already exists, tested, on `origin/migration-from-github`. Port it verbatim with `git checkout origin/migration-from-github -- <path>` (or `git show origin/migration-from-github:<path> > <path>` for new files), then verify with `git diff --stat`.
- **Atomic commits**: each numbered group below is **one commit**. Sub-steps within a group are staged together. Commit messages follow the repo convention (see `CLAUDE.md`); end with the `Co-Authored-By: Claude` trailer.
- **No version bump** in this change — it touches no production files (per `CLAUDE.md`). Do **not** edit `pyproject.toml` or `uv.lock` here.
- **No code edits beyond porting** — do not refactor the ported files; adopt them as-is.

## 1. Port the OpenSpec framework config

- [x] 1.1 Ensure `openspec/config.yaml` on disk matches `origin/migration-from-github:openspec/config.yaml` (it is currently untracked in the working tree — verify byte-identical, stage it).
- [x] 1.2 Commit: `chore(opsx): adopt openspec/config.yaml as framework config`.

## 2. Port the harness skills and commands

- [x] 2.1 Port the 5 `.claude/skills/openspec-*/SKILL.md` files (`openspec-apply-change`, `openspec-archive-change`, `openspec-explore`, `openspec-propose`, `openspec-sync-specs`).
- [x] 2.2 Port the 5 `.claude/commands/opsx/*.md` files (`apply`, `archive`, `explore`, `propose`, `sync`).
- [x] 2.3 Port the 5 `.codex/skills/openspec-*/SKILL.md` files.
- [x] 2.4 Port the 5 `.opencode/skills/openspec-*/SKILL.md` files.
- [x] 2.5 Port the 5 `.opencode/commands/opsx-*.md` files (`opsx-apply`, `opsx-archive`, `opsx-explore`, `opsx-propose`, `opsx-sync`).
- [x] 2.6 Verify the 25 files match the migration with `git diff origin/migration-from-github -- .claude .codex .opencode` (expect empty diff after staging).
- [x] 2.7 Commit (one per harness surface, or one combined — recommended one combined): `chore(harness): adopt Claude Code / Codex / OpenCode skills and commands`.

## 3. Establish the .gitignore VCS contract

- [x] 3.1 Replace the bare `.claude` rule with the carved block, in this exact order: `.claude/*`, `!.claude/skills/`, `!.claude/commands/`, `.claude/settings.local.json` (with the explanatory comment from the migration).
- [x] 3.2 Add the Codex block: `.codex/*`, `!.codex/skills/`, `!.codex/commands/`.
- [x] 3.3 Add the OpenCode block: `.opencode/*`, `!.opencode/skills/`, `!.opencode/commands/`.
- [x] 3.4 Add `!openspec/` (with the "OpenSpec / opsx — versioned source of truth" comment).
- [x] 3.5 Add `!AGENTS.md` and `!CLAUDE.md` (with the "committed (identical content); explicit negations protect them" comment).
- [x] 3.6 In the Distribution/packaging section, add `lib/` and, immediately after it, `!smoke/lib/` with the "Provider source lives at smoke/lib/ — force-include despite the legacy lib/ rule" comment. (`main` currently has neither; we add both to match the contract.)
- [x] 3.7 Confirm `git check-ignore -v .claude/skills/openspec-propose/SKILL.md` returns exit 1 (not ignored) and `git check-ignore -v .claude/settings.local.json` returns exit 0 (ignored).
- [x] 3.8 Commit: `feat(gitignore): adopt harness + openspec + smoke/lib VCS contract`.

## 4. Add the guard-rail test

- [x] 4.1 Add `tests/repo/__init__.py` (empty, ported from the migration).
- [x] 4.2 Add `tests/repo/test_gitignore_preserves_harness_and_opsx.py` ported verbatim from the migration.
- [x] 4.3 Run `uv run pytest tests/repo/test_gitignore_preserves_harness_and_opsx.py -v` and confirm every parametrized case passes (negations present, ignores present, `.claude/` block ordered, `lib/` < `!smoke/lib/` ordered). If any fails, the `.gitignore` edits in group 3 are incomplete — fix the rules, not the test.
- [x] 4.4 Commit: `test(repo): guard-rail for .gitignore preserving harness and opsx`.

## 5. Document the contract in identity docs

- [x] 5.1 Add the "Repository conventions" block to `CLAUDE.md` (after the "VERSIONING (MAIN)" section, before "SUMMARY STANDARDS"), ported from the migration.
- [x] 5.2 Mirror the **identical** block into `AGENTS.md` (the two files must stay in sync — see `CLAUDE.md:1`).
- [x] 5.3 Commit: `docs(agents): document harness + openspec versioning convention`.

## 6. Validate, run CI, and archive

- [x] 6.1 Run `openspec validate adopt-openspec-harness-vcs-contract --strict` and resolve any findings.
- [x] 6.2 Run `./scripts/ci.sh` (or `.\scripts\ci.ps1` on Windows) and confirm all 5 jobs pass (suppression grep, ruff-format, ruff-check, ty, pytest). Use `--only ruff-format,ruff-check,ty,pytest` while iterating if needed.
- [x] 6.3 Run `openspec archive adopt-openspec-harness-vcs-contract -y` to archive the change and promote the spec to `openspec/specs/harness-opsx-vcs-contract/spec.md`.
- [x] 6.4 Commit the archive: `chore(opsx): archive adopt-openspec-harness-vcs-contract and promote spec`.
