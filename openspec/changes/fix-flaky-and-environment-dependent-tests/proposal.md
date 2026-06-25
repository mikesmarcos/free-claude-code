## Why

`uv run pytest` on a developer workstation that has the `fcc-server` process running (or any `fcc-*` tool) fails **4 pre-existing tests** that the project has been accepting as "known flakes" instead of fixing. This is a policy violation per `AGENTS.md` ("Add tests for new changes (including edge cases)" and "All CI checks must pass; failing checks block merge"):

1. `tests/api/test_admin.py::test_admin_page_is_loopback_only` — fails on the developer's machine when the loopback check races with a parallel request, but passes in CI (the GitHub runner has no live admin server). CI sees green; the developer sees red. The "fix" of "rerun until it passes" is exactly the "accept failure" anti-pattern.
2. `tests/scripts/test_uninstallers.py::test_uninstall_sh_generic_uv_failure_does_not_delete_fcc_home` — fails when `fcc-server` is running because `scripts/uninstall.sh` line 1-3 explicitly refuses to delete `~/.fcc/` while any of the four `fcc-*` processes is alive. The test wants to assert "uninstall proceeds even when uv is broken," but the script bails out on the process check first.
3. `tests/scripts/test_uninstallers.py::test_uninstall_sh_missing_tool_still_deletes_fcc_home` — same root cause: the process check at the top of `uninstall.sh` fires before the test's mocked "tool missing" branch is reached.
4. `tests/scripts/test_uninstallers.py::test_uninstall_sh_missing_uv_still_deletes_fcc_home` — same root cause as 2 and 3.

The 4 tests share a single environmental assumption: they want a clean machine where `fcc-server` is not running and `~/.fcc/` is not actively in use. Real workstations do not look like that. The CI runner does, by accident (it has no `fcc-server` because nothing installed it). The result is a permanent false-negative on every developer's laptop and a permanent false-positive on CI — the worst possible shape for a test suite, because it trains the team to ignore red on the local machine and trust green on CI even when they disagree.

The user policy ("ACCEPT FAILURE is not an option") requires these 4 tests to be made deterministic. The proposed solution is to run the affected tests inside a disposable container (Docker or `distrobox`) so each test starts from a known-clean `fcc-*` state. The container provides a hermetic, reproducible environment that matches the CI runner's, removing the environmental dependency from the test entirely.

This change is **documentation of the problem + a proposed fix path**; it does not implement the docker isolation. The reason to land it as an open OpenSpec change (rather than a free-floating `TODO.md`) is so the contract for the future fix is reviewable now, and so the test suite is annotated with a stable requirement name that the eventual fix can satisfy.

## What Changes

- **Add a new capability `test-isolation`** that captures the four pre-existing test failures as 4 ADDED Requirements, one per test. Each Requirement has 2 Scenarios: (a) the failure mode observed today and (b) the success mode once the test runs inside a hermetic container. The requirements are written so the eventual fix lands in a single follow-up change.
- **Add 4 `# TODO(test-isolation):` comments** inline in the four affected test files, pointing at the new `test-isolation` spec and at the open change. The comments make the "TODO is here, not just in a doc" intent obvious to anyone debugging the failures later.
- **No production code changes.** This change touches only test files, openspec documents, and one comment line per affected test. The 4 tests still fail in the same way they do today; we are not silencing them, we are labeling them.
- **No version bump.** Per `CLAUDE.md` production list, `tests/`, `openspec/`, and this kind of doc-only change are non-production.
- **No CI changes.** The CI continues to run the 4 tests; on the GitHub runner they still pass (the runner has no `fcc-server`), and on a developer's machine they still fail in the same way. The point of this change is to **stop pretending the failure is normal**.

## Capabilities

### New Capabilities

- `test-isolation`: defines that 4 pre-existing tests in `tests/api/test_admin.py` and `tests/scripts/test_uninstallers.py` MUST run in a hermetic, disposable container so they are independent of the developer's local `fcc-*` process state. Each test gets a Requirement with a Scenario describing today's failure mode and a Scenario describing the success mode once the container is in place. The container is the test fixture; the test bodies stay the same.

### Modified Capabilities

None. No existing spec is changed; we are adding a new spec that documents a fix path.

## Impact

- `tests/api/test_admin.py` — non-production; one comment line added near the affected test.
- `tests/scripts/test_uninstallers.py` — non-production; three comment lines added (one per failing test).
- `openspec/changes/fix-flaky-and-environment-dependent-tests/{proposal,design,tasks,specs/test-isolation/spec}.md` — non-production; documents the 4 failures and the proposed fix.
- **No production files touched** (`api/`, `cli/`, `config/`, `core/`, `messaging/`, `providers/`, `.env.example`, `pyproject.toml`, `scripts/`) → **no semver bump** and **no `uv lock` change**.
- **No new dependency.** The eventual fix will add `docker` / `distrobox` to the dev-dependency surface, but that lands in the follow-up change, not here.
- **No CI change.** The CI continues to run the same 4 tests against the same Python on the same runner. On the runner the tests already pass; on a workstation they still fail. The change is purely about **labeling** the failure as a known TODO, not about silencing it.
- **No test silencing.** No `pytest.skip`, no `xfail`, no `filterwarnings ignore`, no comment-out. The 4 tests still fail; we just stop pretending the failure is acceptable.
