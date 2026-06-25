## 0. Conventions for this change

- **Single source of truth for the TODO**: this `proposal.md` and the corresponding `specs/test-isolation/spec.md` are the canonical record. The 4 inline `# TODO(test-isolation):` comments in the test files are pointers, not duplicates of the rationale.
- **Single commit**: the change is small (4 test-comment lines + 4 openspec documents) and the commit is one logical unit ("label the 4 pre-existing failures as TODO"). No sub-steps to split.
- **No test silencing**: do **not** add `@pytest.mark.skip`, `@pytest.mark.xfail`, `pytest.skip(...)`, `filterwarnings("ignore", ...)`, or comment-out the test bodies. The 4 tests must continue to fail in exactly the same way they fail today. The change is about **labeling** the failure, not about making it disappear.
- **No production file edits**: this change touches only `tests/` (with the comment-only edits) and `openspec/` (with the new documents). Per `CLAUDE.md`, both are non-production, so **no version bump**.

## 1. Add the OpenSpec change documents

- [x] 1.1 Create `openspec/changes/fix-flaky-and-environment-dependent-tests/` with `proposal.md` (already in working tree), `design.md` (≤ 60 lines covering: why docker isolation is the right fix, why we are not implementing it now, and why a comment-only label beats silencing), `tasks.md` (this file), and `specs/test-isolation/spec.md` with `## ADDED Requirements` (one Requirement per failing test, two Scenarios each).
- [x] 1.2 Verify the spec uses the **exact** 4 test IDs (`tests/api/test_admin.py::test_admin_page_is_loopback_only`, `tests/scripts/test_uninstallers.py::test_uninstall_sh_generic_uv_failure_does_not_delete_fcc_home`, `...missing_tool_...`, `...missing_uv_...`) so the test names in the spec match the test names in the comment-line edits.
- [x] 1.3 Run `openspec validate fix-flaky-and-environment-dependent-tests --strict` and resolve any findings.
- [x] 1.4 **Do NOT archive this change.** It stays in `openspec/changes/` as an open change until a follow-up change implements the docker isolation. The eventual follow-up lands its own archive commit; the open change here will then be marked done by a separate "mark fix-flaky... as resolved" housekeeping commit, or simply superseded by the follow-up's archive.

## 2. Add the 4 inline `# TODO(test-isolation):` comments

- [x] 2.1 In `tests/api/test_admin.py`, immediately above the line `def test_admin_page_is_loopback_only(`, add a single-line comment: `# TODO(test-isolation): see openspec/changes/fix-flaky-and-environment-dependent-tests — runs only on a clean CI runner; fails on any workstation with a live fcc-server. Fix: hermetic container.`
- [x] 2.2 In `tests/scripts/test_uninstallers.py`, immediately above the line `def test_uninstall_sh_generic_uv_failure_does_not_delete_fcc_home(`, add the analogous comment referencing the same openspec path and naming the failure mode ("script bails on fcc-server process check before the mocked uv-failure branch").
- [x] 2.3 Same as 2.2 for `def test_uninstall_sh_missing_tool_still_deletes_fcc_home(`.
- [x] 2.4 Same as 2.2 for `def test_uninstall_sh_missing_uv_still_deletes_fcc_home(`.
- [x] 2.5 Run `git diff tests/api/test_admin.py tests/scripts/test_uninstallers.py` and confirm exactly 4 comment lines were added (one per test) and that the test bodies are byte-identical otherwise.
- [x] 2.6 Run `uv run pytest tests/api/test_admin.py::test_admin_page_is_loopback_only tests/scripts/test_uninstallers.py::test_uninstall_sh_generic_uv_failure_does_not_delete_fcc_home tests/scripts/test_uninstallers.py::test_uninstall_sh_missing_tool_still_deletes_fcc_home tests/scripts/test_uninstallers.py::test_uninstall_sh_missing_uv_still_deletes_fcc_home` and confirm the same 4 failures (3 on this machine due to fcc-server, 1 flake) — proving we did **not** silence anything.

## 3. Commit

- [x] 3.1 Commit: `docs(opsx): TODO test-isolation for 4 pre-existing environment-dependent tests` with a body that lists the 4 failing test IDs verbatim and the openspec change that owns the eventual fix. End with the `Co-Authored-By: opencode` trailer.

## 4. Push and open PR

- [x] 4.1 Push the branch with `git push -u github docs/todo-flaky-tests`.
- [x] 4.2 Open the PR with `gh pr create --base main --head docs/todo-flaky-tests --title "docs(opsx): TODO 4 environment-dependent pytest failures (test-isolation)" --body-file openspec/changes/fix-flaky-and-environment-dependent-tests/proposal.md`.
- [x] 4.3 Confirm the PR URL and surface it in the final summary.
