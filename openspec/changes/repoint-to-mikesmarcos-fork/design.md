# install-url — Design

## Why a single capability is sufficient

The norm this change enforces is narrow: every URL the project publishes to humans (README, install snippet) and to machines (`REPO_GIT_URL` consumed by `uv tool install`) MUST point at the canonical fork. There is exactly one requirement class with three concrete requirements:

1. `REPO_GIT_URL` value in both install scripts.
2. README badge and snippet URLs.
3. A guard test that fails if the URL drifts.

Bundling them into a single `install-url` capability keeps the spec surface small and the rationale coherent. A wider spec like "repository identity" or "fork management" would invent a taxonomy for one requirement.

## Why the archived change prose is updated (not rewritten)

Archive copies under `openspec/changes/archive/2026-06-24-add-command-code-ai-provider/` are immutable history. Strictly, they should be left alone — they record what the project believed at the time. But the archive currently asserts a **prerequisite that never landed** ("the leading URL-repoint chore has already repointed `REPO_GIT_URL` to Codeberg") and a **future-facing plan** ("the leading chore owns the Codeberg repoint") that the project has decided not to execute. Leaving those lines in place would mislead every future reader who walks the archive to understand the install flow.

The compromise: edit the archive to drop the false prerequisite and the dead plan, but keep the surrounding rationale, the task list, the design notes, and the spec body intact. The archive no longer lies about what came before; it also no longer promises a future that will not arrive. The change is small enough to do in one commit and easy to audit (the diff against the original archive is in the commit body if needed).

## Why the install-script URL behavior is unchanged for the user

From the installer's point of view, `uv tool install --force "$REPO_GIT_URL"` is opaque: it shells out to `git+https` cloning. Whether the URL points at the upstream or the fork, the visible behavior (downloading, installing, exposing the `fcc-*` commands on `$PATH`) is identical. The only thing that changes is which Git server the bytes come from. For users who already had the package installed, no action is required — the swap only affects new installs and re-installs.

The `--from <path>` short-circuit is unaffected: when a local path is passed, the spec becomes the literal path and `REPO_GIT_URL` is not consulted. Both branches of the conditional are already covered by `tests/scripts/test_uninstallers.py`; we verify they remain green after the swap.

## Trade-offs accepted

- **Archive rewrite, not pure append.** Updating archive prose is unusual and slightly muddies the "immutable history" rule. We accept the muddiness because the alternative (a `corrections/` subdirectory that supersedes the original archive) adds navigation overhead and is overkill for two sentences.
- **README bulk-rewrite in one commit.** 22 URL replacements look noisy in a diff but are mechanical. Splitting per-section would generate 22 trivial commits with no review value. Single commit, clear message, easy to revert.
- **No smoke change.** We do not add a new smoke test asserting the README URL set, because the README is markdown rendered by GitHub and we have no existing test surface for it. The install-script URL is covered by the existing test.
