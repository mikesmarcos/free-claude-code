## 0. Conventions for this change

- **Atomic commits**: each numbered group below is **one commit**. Commit messages follow the repo convention (see `CLAUDE.md`); end with the `Co-Authored-By: opencode` trailer.
- **Version bump required**: this change touches `scripts/install.sh`, `scripts/install.ps1`, and `pyproject.toml` — all production files per `CLAUDE.md`. Bump `2.5.0` → `2.5.1` (PATCH) in the same commit that updates `pyproject.toml`, and run `uv lock` so the lockfile matches.
- **No code edits beyond the URL swaps and version bump** — do not refactor `install.sh` / `install.ps1` body, do not change `tests/scripts/test_uninstallers.py` semantics, do not rewrite `README.md` prose.

## 1. Add the OpenSpec change skeleton

- [x] 1.1 Create `openspec/changes/repoint-to-mikesmarcos-fork/` with `proposal.md` (already in working tree), `design.md` (≤ 60 lines, already in working tree), `tasks.md` (this file), and `specs/install-url/spec.md` (with `## ADDED Requirements` covering `REPO_GIT_URL`, README URLs, and the uninstaller fixture test).
- [x] 1.2 Commit: `docs(opsx): add repoint-to-mikesmarcos-fork change skeleton`.

## 2. Repoint `REPO_GIT_URL` in install scripts

- [x] 2.1 In `scripts/install.sh` line 4, replace `git+https://github.com/Alishahryar1/free-claude-code.git` with `git+https://github.com/mikesmarcos/free-claude-code.git`. Do not touch any other line.
- [x] 2.2 In `scripts/install.ps1` line 16, replace `$RepoGitUrl = "git+https://github.com/Alishahryar1/free-claude-code.git"` with `$RepoGitUrl = "git+https://github.com/mikesmarcos/free-claude-code.git"`. Do not touch any other line.
- [x] 2.3 Commit: `fix(install): point REPO_GIT_URL at mikesmarcos/free-claude-code fork`.

## 3. Repoint the 22 README URLs and 2 test-fixture URLs

- [x] 3.1 In `README.md`, replace every occurrence of `github.com/Alishahryar1/free-claude-code` with `github.com/mikesmarcos/free-claude-code` (badges, install snippets, uninstall snippets, star-history, issue link, manual clone line). Do not touch prose; the URLs are mechanical replacements.
- [x] 3.2 In `tests/scripts/test_uninstallers.py` lines 23 and 27, replace `Alishahryar1/free-claude-code` with `mikesmarcos/free-claude-code` in the fixture strings.
- [x] 3.3 Run `git grep -n Alishahryar1` and confirm zero matches remain outside the openspec archive copies handled in step 4.
- [x] 3.4 Commit: `docs(readme): repoint install/uninstall links and badges to mikesmarcos fork`.

## 4. Drop the Codeberg reference from the command-code-ai spec and its archive

- [x] 4.1 In `openspec/specs/command-code-ai-provider/spec.md` line 112, replace `git+https://codeberg.org/mikek8s/free-claude-code.git (current behavior preserved)` with `git+https://github.com/mikesmarcos/free-claude-code.git (current behavior preserved)`.
- [x] 4.2 In `openspec/changes/archive/2026-06-24-add-command-code-ai-provider/specs/command-code-ai-provider/spec.md` line 109, same swap.
- [x] 4.3 In `openspec/changes/archive/2026-06-24-add-command-code-ai-provider/proposal.md` line 7, drop the "It assumes the leading URL-repoint chore has already repointed `REPO_GIT_URL` to `git+https://codeberg.org/mikek8s/free-claude-code.git`" sentence. Keep the rest of the line.
- [x] 4.4 In `openspec/changes/archive/2026-06-24-add-command-code-ai-provider/design.md` line 9, drop the "It also assumes the leading URL-repoint chore set `REPO_GIT_URL` to the Codeberg origin." sentence. Keep the rest of the line.
- [x] 4.5 In `openspec/changes/archive/2026-06-24-add-command-code-ai-provider/design.md` line 28, drop the "No change to the `REPO_GIT_URL` value itself (the leading chore owns the Codeberg repoint)." entry. Keep the rest of the list.
- [x] 4.6 In `openspec/changes/archive/2026-06-24-add-command-code-ai-provider/tasks.md` line 4, drop the "`REPO_GIT_URL` → Codeberg" phrase from the prerequisites line. Keep the rest.
- [x] 4.7 Run `git grep -n codeberg.org` and confirm zero matches remain.
- [x] 4.8 Commit: `docs(opsx): drop Codeberg reference from command-code-ai spec and archive`.

## 5. Drop the `.forgejo/` directory

- [x] 5.1 Delete `.forgejo/CODEOWNERS` and the empty `.forgejo/` directory. The matching `.github/CODEOWNERS` (pointing at `@mikesmarcos`) is the only code-owners file that remains.
- [x] 5.2 Run `git check-ignore -v .forgejo/CODEOWNERS` (expect: not ignored, no output) and `ls -la .forgejo/` (expect: No such file or directory) to confirm the directory is fully gone from the working tree.
- [x] 5.3 Commit: `chore(config): drop .forgejo/CODEOWNERS (no longer maintaining Codeberg mirror)`.

## 6. Version bump and lockfile

- [x] 6.1 In `pyproject.toml`, bump `version = "2.5.0"` to `version = "2.5.1"`. Do not touch any other line.
- [x] 6.2 Run `uv lock` to refresh `uv.lock` so it reflects the new package version. The lockfile should be the only other file changed.
- [x] 6.3 Commit: `chore(release): bump 2.5.0 → 2.5.1 (repoint to mikesmarcos fork)`.

## 7. Validate, run CI, and archive

- [x] 7.1 Run `openspec validate repoint-to-mikesmarcos-fork --strict` and resolve any findings.
- [x] 7.2 Run `./scripts/ci.sh` (or `.\scripts\ci.ps1` on Windows) and confirm all 5 jobs pass. Use `--only ruff-format,ruff-check,ty,pytest` while iterating if needed.
- [x] 7.3 Run `openspec archive repoint-to-mikesmarcos-fork -y` to archive the change and promote the spec to `openspec/specs/install-url/spec.md`.
- [x] 7.4 Commit the archive: `chore(opsx): archive repoint-to-mikesmarcos-fork and promote spec`.

## 8. Push and open PR

- [x] 8.1 Push the branch with `git push -u github docs/repoint-to-mikesmarcos-fork` (or whatever the local branch name is).
- [x] 8.2 Open the PR with `gh pr create --base main --head <branch> --title "fix(install): repoint REPO_GIT_URL to mikesmarcos/free-claude-code fork" --body-file openspec/changes/repoint-to-mikesmarcos-fork/proposal.md`.
- [x] 8.3 Confirm the PR URL and surface it in the final summary.
