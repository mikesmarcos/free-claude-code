## Why

The repository currently contains hardcoded references to two locations that no longer reflect the project's reality:

1. **Install scripts point at the upstream fork** (`github.com/Alishahryar1/free-claude-code.git`). After forking into `github.com/mikesmarcos/free-claude-code`, the `REPO_GIT_URL` constant in `scripts/install.sh` and `scripts/install.ps1` was never repointed. Running `./scripts/install.sh` on a fresh machine clones from the original maintainer's repo, not the fork this project is actively developed in. `README.md` has the same problem: badges, install snippets, star-history, and issue links all target `Alishahryar1`, so a user landing on the fork's README is being routed back to the upstream.
2. **Specs and an open change reference a Codeberg mirror** that this project no longer maintains. The `command-code-ai-provider` capability spec (live and archived) and its proposal/design/tasks were authored against the assumption that the canonical remote was `codeberg.org/mikek8s/free-claude-code.git` — a mirror that has been abandoned. The `REPO_GIT_URL` is now the source of truth (not the remote name) and the only canonical Git URL is the GitHub fork.

The goal is to make every URL in the repo point at the GitHub fork this project is developed in, remove the abandoned Codeberg reference from the spec body, and drop the empty `.forgejo/CODEOWNERS` shim left over from the mirror era. The behavior of `uv tool install` is unchanged: the same flag set, the same `--from` short-circuit, the same shell/PowerShell pair — only the URL value moves.

## What Changes

- **Repoint `REPO_GIT_URL` in `scripts/install.sh`** from `git+https://github.com/Alishahryar1/free-claude-code.git` to `git+https://github.com/mikesmarcos/free-claude-code.git`.
- **Repoint `$RepoGitUrl` in `scripts/install.ps1`** with the same change.
- **Repoint 22 hardcoded `github.com/Alishahryar1/...` URLs in `README.md`** (badges, install/uninstall snippets, star-history widget, issue link) to the fork. Smoke (`tests/scripts/test_uninstallers.py`) has 2 more URLs in uninstall-fixture strings, also repointed.
- **Repoint 2 spec mentions of `git+https://codeberg.org/mikek8s/free-claude-code.git`** in `openspec/specs/command-code-ai-provider/spec.md` (line 112) and the archived change copy (line 109) to the GitHub fork.
- **Reword 5 archive-document references to the Codeberg `REPO_GIT_URL` and "leading URL-repoint chore"** in `openspec/changes/archive/2026-06-24-add-command-code-ai-provider/{proposal,design,tasks}.md` so the historical record no longer implies a Codeberg prerequisite. The repoint itself is now this change, so the "leading chore" framing is gone.
- **Delete `.forgejo/CODEOWNERS`** and the now-empty `.forgejo/` directory. The matching `.github/CODEOWNERS` (pointing at `@mikesmarcos`) is the only code-owners file that remains.
- **Bump version `2.5.0` → `2.5.1` (PATCH)** in `pyproject.toml` and run `uv lock` so the lockfile matches. This touches `scripts/install.sh`, `scripts/install.ps1`, and `pyproject.toml` — all production files per the project rules in `CLAUDE.md`.
- **No code, env, or capability changes** — every requirement, scenario, and test in the existing specs keeps the same normative meaning; only URLs and the version constant move.

## Capabilities

### New Capabilities

- `install-url`: defines the invariant that `REPO_GIT_URL` in `scripts/install.sh` and `$RepoGitUrl` in `scripts/install.ps1` MUST point at the canonical Git URL of this project, and that every README link, badge, and star-history reference MUST use the same canonical owner. Enforced by the `tests/scripts/test_installers.py` URL-constant assertion (port from the existing uninstaller test if not present).

### Modified Capabilities

- `command-code-ai-provider`: the install-source Scenario now expects the GitHub fork URL (replacing the Codeberg URL it assumed). No requirement text changes; only the example URL in the Scenario moves.

## Impact

- `scripts/install.sh`, `scripts/install.ps1` — production (`CLAUDE.md` production list); one-line change each. **Version bump required.**
- `pyproject.toml` — production; `2.5.0` → `2.5.1`. Run `uv lock` after.
- `README.md` — docs (non-production per `CLAUDE.md`); 22 URL replacements, no semantic change.
- `tests/scripts/test_uninstallers.py` — tests (non-production); 2 URL replacements in fixture strings.
- `openspec/specs/command-code-ai-provider/spec.md` — spec (non-production); 1 URL replacement in the install-source Scenario.
- `openspec/changes/archive/2026-06-24-add-command-code-ai-provider/{proposal,design,tasks,specs/.../spec}.md` — archived change (non-production); 5+2 rewordings to drop the Codeberg prerequisite and the "leading URL-repoint chore" assumption. The archive is immutable history but it is misleading future readers today, so we update it.
- `.forgejo/CODEOWNERS`, `.forgejo/` — non-production; deletion only.
- **No new dependency, no env change, no breaking change for end users** (the install behavior is identical; only the source URL moves). The `tests/scripts/test_uninstallers.py` assertions that read the script's `REPO_GIT_URL` already allow for any URL, so they remain green after the swap; we verify this in CI.
