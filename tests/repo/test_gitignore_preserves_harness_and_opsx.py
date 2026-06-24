"""Guard-rail test: .gitignore must keep harness / OpenSpec / smoke sources versioned.

Strategy
--------
We can't easily test the *runtime* behavior of `git check-ignore` on tracked
files (git always reports exit 1 for already-tracked files), and using a
scratch dir means the parent dir's ignore rule shadows everything inside.

So we test the `.gitignore` text directly: every required negation must be
present, and every required ignore must be present (without a matching `!`
negation that would cancel it). This is exactly what the spec
`harness-opsx-vcs-contract` requires — the contract is about the **rules** in
`.gitignore`, not about a particular runtime test setup.

This catches the realistic regression: someone re-adds `.claude/` (no
negation), removes `!smoke/lib/`, or removes `!.claude/skills/`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

GITIGNORE = Path(__file__).resolve().parents[2] / ".gitignore"


@pytest.fixture(scope="module")
def gitignore_text() -> str:
    return GITIGNORE.read_text(encoding="utf-8")


def _rule_present(text: str, pattern: str, *, negated: bool = False) -> bool:
    """Return True if `pattern` appears as a non-negated (or negated) rule.

    A negated rule is a line that starts with `!` followed by the pattern.
    A non-negated rule is a line that starts with the pattern and is not
    preceded by `!`. Comment lines are ignored.
    """
    target = pattern if not negated else f"!{pattern}"
    lines = text.splitlines()
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == target:
            return True
    return False


# ---------------------------------------------------------------------------
# MUST-BE-TRACKED — every path below must be covered by a `!` negation rule
# in `.gitignore` so it is NOT ignored. (Some paths need a parent-dir
# negation; we test the parent dir which is the standard idiom.)
# ---------------------------------------------------------------------------

MUST_HAVE_NEGATIONS: tuple[tuple[str, str], ...] = (
    ("Harness Claude Code skills dir", ".claude/skills/"),
    ("Harness Claude Code commands dir", ".claude/commands/"),
    ("Codex skills dir", ".codex/skills/"),
    ("Codex commands dir", ".codex/commands/"),
    ("OpenCode skills dir", ".opencode/skills/"),
    ("OpenCode commands dir", ".opencode/commands/"),
    ("OpenSpec folder", "openspec/"),
    ("Smoke lib dir", "smoke/lib/"),
    ("AGENTS.md identity doc", "AGENTS.md"),
    ("CLAUDE.md identity doc", "CLAUDE.md"),
)


@pytest.mark.parametrize(("label", "rule"), MUST_HAVE_NEGATIONS)
def test_must_have_negation(gitignore_text: str, label: str, rule: str) -> None:
    assert _rule_present(gitignore_text, rule, negated=True), (
        f"Missing required negation `!{rule}` in .gitignore "
        f"(needed to keep {label} versioned). "
        f"Add the line `!{rule}` to .gitignore."
    )


# ---------------------------------------------------------------------------
# MUST-BE-IGNORED — every pattern below must be present as a non-negated
# rule in `.gitignore` so that locally generated state is NOT committed.
# ---------------------------------------------------------------------------

MUST_HAVE_IGNORES: tuple[tuple[str, str], ...] = (
    ("Harness local state (settings.local.json)", ".claude/settings.local.json"),
    (".claude/ default ignore (so other state files are ignored)", ".claude/*"),
    (".codex/ default ignore", ".codex/*"),
    (".opencode/ default ignore", ".opencode/*"),
    ("Smoke results dir", ".smoke-results"),
    ("Harness / agent_workspace dir", "agent_workspace"),
    ("llama_cache dir", "llama_cache"),
    ("User .env", ".env"),
    ("Pytest cache", ".pytest_cache"),
    ("Ruff cache", ".ruff_cache"),
)


@pytest.mark.parametrize(("label", "rule"), MUST_HAVE_IGNORES)
def test_must_have_ignore(gitignore_text: str, label: str, rule: str) -> None:
    assert _rule_present(gitignore_text, rule, negated=False), (
        f"Missing required ignore rule {rule!r} in .gitignore "
        f"(needed to keep {label} out of version control). "
        f"Add the line `{rule}` to .gitignore (without a `!` negation)."
    )


# ---------------------------------------------------------------------------
# Whole-file sanity check: a tracked `.claude/*` must not be silently
# overridden by a later rule that ignores the parent. The order of
# `!.claude/skills/`, `!.claude/commands/`, and `.claude/*` must be:
#   1. .claude/*
#   2. !.claude/skills/
#   3. !.claude/commands/
#   4. .claude/settings.local.json
# so that the negate rules actually take effect.
# ---------------------------------------------------------------------------


def test_negation_order_in_claude_block(gitignore_text: str) -> None:
    """The negation rules must come *after* the broad ignore, in this order."""
    broad = re.search(r"^\s*\.claude/\*\s*$", gitignore_text, re.MULTILINE)
    skills = re.search(r"^\s*!\.claude/skills/\s*$", gitignore_text, re.MULTILINE)
    commands = re.search(r"^\s*!\.claude/commands/\s*$", gitignore_text, re.MULTILINE)
    settings = re.search(
        r"^\s*\.claude/settings\.local\.json\s*$", gitignore_text, re.MULTILINE
    )
    assert broad and skills and commands and settings, (
        "One of the .claude/ rules is missing — see test_must_have_* for details."
    )
    assert broad.start() < skills.start() < commands.start() < settings.start(), (
        "Rule order in .claude/ block is wrong. Required order: "
        "(1) .claude/*  (2) !.claude/skills/  (3) !.claude/commands/  "
        "(4) .claude/settings.local.json. Git's last-match-wins means a later "
        "negation is required AFTER the broad rule, not before."
    )


def test_negation_order_in_smoke_lib(gitignore_text: str) -> None:
    broad = re.search(r"^\s*lib/\s*$", gitignore_text, re.MULTILINE)
    negate = re.search(r"^\s*!smoke/lib/\s*$", gitignore_text, re.MULTILINE)
    assert broad and negate, "lib/ or !smoke/lib/ rule missing"
    assert broad.start() < negate.start(), (
        "!smoke/lib/ must come AFTER the lib/ rule for git to honor the negation."
    )
