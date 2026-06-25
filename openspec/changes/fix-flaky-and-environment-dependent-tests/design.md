# test-isolation — Design

## Why docker isolation is the right fix

The 4 failing tests have a single shared property: they need a machine with **no `fcc-server` (or any `fcc-*` tool) running** and **no `~/.fcc/` state in active use**. The CI runner has that by accident (no one installed `fcc-server` there). A developer's workstation never has that.

The fix is to make the test environment match the CI environment by running the affected tests in a disposable container. The container:

- Starts with no `fcc-server` process and no `~/.fcc/` (or with `~/.fcc/` owned by the container, so the host check cannot fire).
- Has the same Python version, the same `uv` version, the same OS-family as CI.
- Is created per-test-run and torn down after; a flake in one test cannot poison the next.
- Is runnable on a developer's machine with `docker run` (or `distrobox enter`) and on CI via the existing GitHub Actions matrix.

The benefit is not "tests pass on my laptop" (they already pass on CI). The benefit is **"the local signal and the CI signal agree."** Today they disagree, which is the worst shape a test suite can take because the team learns to ignore the local red and trust the green — exactly the policy violation that triggered this change.

## Why we are not implementing it now

Two reasons:

1. **The implementation needs a decision** that is bigger than this change can carry: which container base image (Alpine? Debian? Fedora, because the project is also packaged for Fedora?), how the container reaches the test fixtures, how the local dev-loop runs (interactive `docker exec` vs one-shot `docker run`), and whether `distrobox` is in or out. Those are design decisions a maintainer should make, not a single auto-pilot commit.
2. **The user explicitly asked to mark the failure as TODO for future analysis.** The directive is "do not accept failure, do not fix it now." That maps to "label the failure with a stable requirement name so a future change can pick it up." A 4-comment-line PR is the smallest thing that satisfies the directive without overreaching.

The follow-up change that implements the isolation will live next to this one in `openspec/changes/`, will reference the `test-isolation` spec by name, and will land its own archive when done. At that point, this `fix-flaky-and-environment-dependent-tests` change becomes a pure record of the prior failure mode and can be deleted from `openspec/changes/` (it has no production impact to retire).

## Why a comment-only label beats silencing

The four obviously-shorter alternatives each violate a project policy:

- **`@pytest.mark.xfail`**: would mark the test as "expected to fail" and stop counting it as a failure. This is exactly the "accept failure" pattern the user called out, just dressed up.
- **`@pytest.mark.skip`**: would not run the test at all. Even worse — the regression that the test catches would slip into main unnoticed.
- **`filterwarnings("ignore", ...)`**: irrelevant, the failures are assertion errors not warnings.
- **Commenting out the test bodies**: hides the bug forever. The `fcc-server` process check is a real product behavior; the test is asserting that the uninstaller handles a missing-uv case even when the process check fires. Removing the test removes the protection.

A `# TODO(test-isolation):` comment is a label, not a fix and not a silence. The test still runs, still fails, and still surfaces in the developer's local output — but the comment gives the next reader a stable handle (`test-isolation`, `openspec/changes/fix-flaky-and-environment-dependent-tests`) so they can find the contract that needs to be satisfied before the test is allowed to be silenced. The comment is the smallest possible deviation from "ACCEPT FAILURE is not an option" while still leaving room for the follow-up fix to land cleanly.

## Trade-offs accepted

- **The 4 tests still fail locally.** This is intentional and matches the user's policy: we are not silencing them, we are labeling them. The label is what makes the failure actionable.
- **The open OpenSpec change does not get archived.** This is the first time we have left a change in `openspec/changes/` indefinitely. The `tests/repo/test_gitignore_preserves_harness_and_opsx.py` guard-rail test asserts that `openspec/changes/` is versioned, not that it is empty, so the open change is safe to commit. The follow-up fix will be a normal change that lands, archives, and supersedes this one.
- **The fix path is documented but not committed.** If the team never picks it up, this change becomes permanent documentation of an unfixed failure. That is strictly better than the current state, where the failure is invisible.
