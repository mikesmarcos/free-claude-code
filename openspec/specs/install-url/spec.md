# install-url Specification

## Purpose
TBD - created by archiving change repoint-to-mikesmarcos-fork. Update Purpose after archive.
## Requirements
### Requirement: `REPO_GIT_URL` points at the canonical GitHub fork

The system MUST define `REPO_GIT_URL` (in `scripts/install.sh`) and `$RepoGitUrl` (in `scripts/install.ps1`) as `git+https://github.com/mikesmarcos/free-claude-code.git`. The system MUST fail the install-script URL guard test if either constant drifts to any other value (including the upstream `Alishahryar1` fork or a non-GitHub host).

#### Scenario: `install.sh` URL is the canonical fork
- **WHEN** `scripts/install.sh` line 4 is read
- **THEN** the value is exactly `REPO_GIT_URL="git+https://github.com/mikesmarcos/free-claude-code.git"` (no trailing whitespace, no `ssh://` form, no other host)

#### Scenario: `install.ps1` URL is the canonical fork
- **WHEN** `scripts/install.ps1` line 16 is read
- **THEN** the value is exactly `$RepoGitUrl = "git+https://github.com/mikesmarcos/free-claude-code.git"`

#### Scenario: The install-script URL is the only place `uv tool install` reads the source from
- **WHEN** the user runs `./scripts/install.sh` or `irm ... install.ps1 | iex` without the `--from` flag
- **THEN** `uv tool install --force "$REPO_GIT_URL"` (or the PowerShell equivalent) clones from the canonical fork

### Requirement: README URLs point at the canonical GitHub fork

The system MUST use `github.com/mikesmarcos/free-claude-code` for every link in `README.md` that resolves to a project artifact (badge targets, install/uninstall curl and `irm` snippets, the star-history widget, the issues link, the manual clone line). The system MUST NOT link to `Alishahryar1/free-claude-code` or to a non-GitHub host from `README.md`. A maintainer who wants to re-point the project updates every such URL in the same change; a guard review at PR time catches any drift.

#### Scenario: README badges resolve to the fork
- **WHEN** a badge in `README.md` is hovered
- **THEN** its target is `https://github.com/mikesmarcos/free-claude-code/...` (e.g. the `Tested with Pytest` badge resolves to `https://github.com/mikesmarcos/free-claude-code/actions/workflows/tests.yml`)

#### Scenario: README install snippets resolve to the fork
- **WHEN** a user copies the `curl -fsSL "https://github.com/.../install.sh?raw=1" | sh` line from `README.md` and pastes it into a shell
- **THEN** the `?raw=1` URL resolves to the `mikesmarcos` fork's `scripts/install.sh`, not the upstream

#### Scenario: README issues link resolves to the fork
- **WHEN** a user clicks the "Report bugs" link in `README.md`
- **THEN** the browser opens `https://github.com/mikesmarcos/free-claude-code/issues` (not the upstream's issue tracker)

### Requirement: Uninstall-script fixtures point at the canonical GitHub fork

The system MUST use `mikesmarcos/free-claude-code` in the `tests/scripts/test_uninstallers.py` fixture strings that the uninstall-curl/irm snippets are checked against. The system MUST fail the uninstaller fixture test if either fixture string contains `Alishahryar1` or any other non-canonical owner.

#### Scenario: Uninstall fixture matches the canonical fork
- **WHEN** `tests/scripts/test_uninstallers.py` lines 23 and 27 are read
- **THEN** both fixture strings contain the substring `mikesmarcos/free-claude-code/main/scripts/` (or the equivalent `raw.githubusercontent.com` form)

