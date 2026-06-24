# external-memory-directive — Design

## Why a single section in `AGENTS.md` is sufficient

The agent already loads `AGENTS.md` and `CLAUDE.md` (identical content) as the system-prompt overlay for every session. Adding one more `## EXTERNAL MEMORY (PERSISTENT CROSS-SESSION) — OPTIONAL` section there is the lowest-friction way to:

- Make the rule **co-located** with every other behavioral directive (cognitive workflow, identity, architecture principles, etc.) so the agent does not need a second file lookup.
- Keep the rule **out of code** — no Python module to import, no runtime hook to register, no `pyproject.toml` change. The directive is purely about *what the agent should do at session start*.
- Survive the existing `tests/repo/test_gitignore_preserves_harness_and_opsx.py` contract unchanged: `AGENTS.md` and `CLAUDE.md` are already protected by `!AGENTS.md` / `!CLAUDE.md` negations.

A separate file (e.g. `docs/agent/external-memory.md`) would force every harness to add a load step, drift between docs, and break the "two files, identical content" invariant that the project enforces.

## Why no test

Three options were considered and rejected:

1. **Unit test the directive prose.** A test that reads `AGENTS.md` and asserts the section is present would be tautological — the section being there is the test. It would also fail any time we legitimately reword the section.
2. **Integration test that queries a real provider.** Would require a running RetainDB (or mock), making CI non-deterministic and adding a heavy dependency to the test surface for a docs-only change.
3. **Behavior test of the agent.** Not possible in this repo — the agent is a separate runtime (opencode, Claude Code, Codex, Hermes) and the tests run in plain `pytest` with no LLM in the loop.

The directive is a **behavioral contract with the agent runtime, not with the Python codebase**. The right enforcement is the agent obeying the rule on every session; a CI test would test the wrong thing. If a future regression appears (e.g. the agent starts silently dropping memories), it will be visible in any session that uses an external provider, and we can add a guard-rail at that point — likely a small assertion in `tests/repo/` that the section text still contains the required normative verbs (consult, record, conflict, repo-wins).

## Why harness-agnostic

The agent can run in at least four harnesses in this project alone: opencode (this session), Claude Code, Codex CLI, and Hermes. Each surfaces external memory differently:

- opencode: MCP tools with the `mcp__<provider>__*` prefix, plus plugins with a TypeScript export.
- Claude Code: MCP tools with the same prefix convention, but no plugin system.
- Codex: CLI subcommands and env vars; no MCP by default.
- Hermes: a custom hook script convention with a JSON RPC interface.

Hard-coding the RetainDB MCP probe would break the rule for the other three. Instead, the directive enumerates **four interface classes** (MCP / plugin / env vars / CLI-or-hook) and tells the agent to detect the available one. A specific product (RetainDB) is mentioned only as a *worked example* of the health-probe URL, never as a requirement.

## How the directive degrades to project-local memory

The opening paragraph of the section is the kill switch: *"If no such provider is reachable, ignore this entire section."* This is reinforced by:

- The first normative block, `**Detection.**`, ends with *"If the probe fails, fall back to project-local memory only and skip the steps below."*
- The `consult` and `record` blocks use conditional language (*"query the provider"*, *"persist a concise summary"*) that resolves to "no-op" when the provider is absent.
- No rule in the section assumes provider availability. There is no *"always do X with RetainDB"* — every action is gated on the detection step.

The behavior for a dev without any external memory provider is therefore **byte-identical** to the behavior before this change. The cost of the new section is purely a few hundred tokens of system prompt that are never acted on.

## Trade-offs accepted

- **Slight prompt bloat for everyone.** The section adds ~600 tokens to every session's system prompt, even for users who never configure an external provider. This is the price of an "always on" directive; we accepted it because the alternative (a separate docs file the agent must opt into reading) is worse.
- **No automated enforcement.** As above, the right enforcement is at the agent-runtime layer, which is out of scope for this repo.
- **Spec drift risk.** If a future openspec change rewrites the directive prose, the spec (`external-memory-directive/spec.md`) must be updated in the same change. We will rely on the agent reading the directive at session start to catch accidental drift; a `tests/repo/` assertion that the section is present can be added cheaply if drift becomes a real problem.
