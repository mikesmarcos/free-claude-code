# test-isolation Specification

## Purpose

Define the contract that 4 pre-existing tests in the project MUST run in a hermetic, disposable container so they are independent of the developer's local `fcc-*` process state and the `~/.fcc/` filesystem. The 4 tests are environment-dependent today: they pass on a clean CI runner (no `fcc-server` installed) and fail on a developer workstation with `fcc-server` running. The capability exists so the eventual docker-isolation fix can be reviewed against a stable requirement name and so the failure is no longer invisible. The capability does not silence the tests; it specifies how the tests must eventually be made deterministic.

## ADDED Requirements

### Requirement: `test_admin_page_is_loopback_only` runs in a hermetic container

The test `tests/api/test_admin.py::test_admin_page_is_loopback_only` MUST run inside a disposable container that has no live `fcc-server` (or any `fcc-*` tool) and no `~/.fcc/` state owned by the host. The test body MUST NOT be marked `@pytest.mark.xfail`, `@pytest.mark.skip`, commented out, or otherwise silenced. A flake on the developer's local machine MUST be reproducible as a stable pass on the container.

#### Scenario: Local failure mode (pre-fix, observed today)
- **WHEN** the test is run on a developer workstation where `fcc-server` is alive or `~/.fcc/` is in use
- **THEN** the test currently fails because the loopback assertion races with the live server (or with another parallel request)
- **THEN** the failure MUST remain visible in the local test output (no `xfail`, no `skip`, no comment-out) until the hermetic container replaces the host as the test fixture

#### Scenario: Container success mode (post-fix)
- **WHEN** the test is run inside the hermetic container that the fix provides
- **THEN** the test passes deterministically across N ≥ 10 consecutive runs

### Requirement: `test_uninstall_sh_generic_uv_failure_does_not_delete_fcc_home` runs in a hermetic container

The test `tests/scripts/test_uninstallers.py::test_uninstall_sh_generic_uv_failure_does_not_delete_fcc_home` MUST run inside a disposable container where `scripts/uninstall.sh` does not encounter a live `fcc-*` process. The test body MUST NOT be silenced. The container MUST provide the same `uv` semantics (or a deterministic mock thereof) as the CI runner.

#### Scenario: Local failure mode (pre-fix, observed today)
- **WHEN** the test is run on a developer workstation where `fcc-server` is running
- **THEN** the test currently fails because `uninstall.sh` line 1-3 refuses to proceed while `fcc-server` is alive, exiting before the test's mocked "uv failure" branch is reached
- **THEN** the failure MUST remain visible in the local test output until the hermetic container is the test fixture

#### Scenario: Container success mode (post-fix)
- **WHEN** the test is run inside the hermetic container
- **THEN** the script's process-check sees no live `fcc-*` and the test's mocked uv-failure branch runs to completion

### Requirement: `test_uninstall_sh_missing_tool_still_deletes_fcc_home` runs in a hermetic container

The test `tests/scripts/test_uninstallers.py::test_uninstall_sh_missing_tool_still_deletes_fcc_home` MUST run inside a disposable container with no live `fcc-*` processes. The test body MUST NOT be silenced. The container MUST provide a controlled `PATH` so the "tool missing" branch is the only path the test exercises.

#### Scenario: Local failure mode (pre-fix, observed today)
- **WHEN** the test is run on a developer workstation where `fcc-server` is running
- **THEN** the test currently fails because the process check at the top of `uninstall.sh` fires before the test's mocked "tool missing" branch is reached
- **THEN** the failure MUST remain visible in the local test output until the hermetic container is the test fixture

#### Scenario: Container success mode (post-fix)
- **WHEN** the test is run inside the hermetic container
- **THEN** the script's process-check sees no live `fcc-*` and the test's "tool missing" branch runs to completion

### Requirement: `test_uninstall_sh_missing_uv_still_deletes_fcc_home` runs in a hermetic container

The test `tests/scripts/test_uninstallers.py::test_uninstall_sh_missing_uv_still_deletes_fcc_home` MUST run inside a disposable container with no live `fcc-*` processes and a controlled `PATH` that omits `uv`. The test body MUST NOT be silenced.

#### Scenario: Local failure mode (pre-fix, observed today)
- **WHEN** the test is run on a developer workstation where `fcc-server` is running
- **THEN** the test currently fails because the process check at the top of `uninstall.sh` fires before the test's "missing uv" branch is reached
- **THEN** the failure MUST remain visible in the local test output until the hermetic container is the test fixture

#### Scenario: Container success mode (post-fix)
- **WHEN** the test is run inside the hermetic container with `uv` absent from `PATH`
- **THEN** the script's process-check sees no live `fcc-*` and the test's "missing uv" branch runs to completion
