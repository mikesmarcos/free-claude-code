## 0. Conventions for this change

- **Single source of truth for the directive text**: the section body lives in `AGENTS.md` (and is mirrored to `CLAUDE.md` with `cp`, since the two must stay byte-identical per `CLAUDE.md:1`). The `proposal.md` and `spec.md` only reference it; they do not duplicate the prose.
- **Atomic commits**: each numbered group below is **one commit**. Commit messages follow the repo convention (see `CLAUDE.md`); end with the `Co-Authored-By: opencode` trailer (this branch was authored through the opencode harness).
- **No version bump** in this change — it touches no production files (per `CLAUDE.md`). Do **not** edit `pyproject.toml` or `uv.lock` here.
- **No code edits beyond the directive** — do not refactor unrelated sections of `AGENTS.md` / `CLAUDE.md` in the same commit.

## 1. Add the OpenSpec change skeleton

- [x] 1.1 Create `openspec/changes/add-external-memory-directive/` with `proposal.md` (already in working tree) and the empty `specs/external-memory-directive/` directory.
- [x] 1.2 Create `openspec/changes/add-external-memory-directive/design.md` (≤ 80 lines) covering: why a single section in `AGENTS.md` is sufficient, why no test, why harness-agnostic, and how the directive degrades to project-local memory.
- [x] 1.3 Create `openspec/changes/add-external-memory-directive/tasks.md` (this file).
- [x] 1.4 Commit: `docs(opsx): add external-memory-directive change skeleton`.

## 2. Author the capability spec

- [x] 2.1 Create `openspec/changes/add-external-memory-directive/specs/external-memory-directive/spec.md` with the sections `## Purpose` and `## Requirements`, capturing the five normative rules (detection, reachability, consult cadence, record cadence, conflict resolution) as `### Requirement:` blocks and one `#### Scenario:` per rule.
- [x] 2.2 Verify the spec does not mention any specific product (no `RetainDB`, `Zep`, `Mem0` as requirements — only as illustrative probes in the directive prose, never in the spec).
- [x] 2.3 Commit: `docs(opsx): add external-memory-directive capability spec`.

## 3. Add the directive to AGENTS.md and mirror to CLAUDE.md

- [x] 3.1 Append the `## EXTERNAL MEMORY (PERSISTENT CROSS-SESSION) — OPTIONAL` section to `AGENTS.md` (after the `## TOOLS` section, before any trailing content).
- [x] 3.2 Mirror byte-identical with `cp AGENTS.md CLAUDE.md`.
- [x] 3.3 Confirm with `diff AGENTS.md CLAUDE.md` (expect empty) and `wc -l AGENTS.md CLAUDE.md` (expect equal).
- [x] 3.4 Commit: `docs(agents): add external memory directive (harness-agnostic, optional)`.

## 4. Validate, run CI, and archive

- [x] 4.1 Run `openspec validate add-external-memory-directive --strict` and resolve any findings.
- [x] 4.2 Run `./scripts/ci.sh --only ruff-format,ruff-check,ty,pytest` (macOS/Linux) or `.\scripts\ci.ps1 -Only ruff-format,ruff-check,ty,pytest` (Windows) and confirm all 4 jobs pass. The `suppression grep` job is omitted because this change touches no Python files, but include it if any flagged path was edited by accident.
- [x] 4.3 Run `openspec archive add-external-memory-directive -y` to archive the change and promote the spec to `openspec/specs/external-memory-directive/spec.md`.
- [x] 4.4 Commit the archive: `chore(opsx): archive add-external-memory-directive and promote spec`.

## 5. Push and open PR

- [x] 5.1 Push the branch with `git push -u github docs/external-memory-directive` (or `origin` if Codeberg is the canonical remote — confirm with the user if unclear).
- [x] 5.2 Open the PR with `gh pr create --base main --head docs/external-memory-directive --title "docs(agents): add external memory directive (harness-agnostic, optional)" --body-file openspec/changes/add-external-memory-directive/proposal.md` (or paste the proposal body if `gh` is not configured for the remote).
- [x] 5.3 Confirm the PR URL and surface it in the final summary.
