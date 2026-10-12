---
status: accepted
---

# Forge workflow script and dynamic tiers

On 2026-10-12 the maintainer asked for The Forge to run as a Claude Code workflow, invoked from the skill as `/forge fix workflow`, and for a mode that picks models per agent, like Claude Code's ultracode, usable with or without the workflow.

## Settled design

- `workflow` is an option word like `strict`. The skill does the setup that needs the user, then runs the bundled `skills/forge/workflows/forge.js` through the Workflow tool. The script ships inside the skill, so the skills CLI installs it without extra tooling. Runtimes without the Workflow tool run the same level without it.
- `dynamic` is a general option. The reviewer sets each finding's tier, verification and fixes run at that tier, and failed fixes escalate. The reviewer and complexity reviewer keep the tiers ADR 0003 set.
- Under both options, verifier subagents verify findings and the orchestrator audits their verdicts, an exception to the orchestrator verifying each finding itself.
- In the script, The Forge's stall rule comes before delegation's escalation rule. An issue that survives two fixes stops for diagnosis, so an engineer fix never escalates inside a run.
- The script's fixer works in a worker worktree that the orchestrator creates, keeping ADR 0005's rule that every writer gets one. The fixer leaves its changes uncommitted, since one run spans several fix rounds; the orchestrator commits the worktree when the run ends clean, an exception to writers committing their own work. At `build`, the script's fixer replaces routing fixes to implementation owners. Without `workflow`, `dynamic` keeps that routing.
- Each round starts a fresh reviewer, which is stricter than reusing one for focused fixes.
