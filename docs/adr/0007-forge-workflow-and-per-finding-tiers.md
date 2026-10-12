---
status: accepted
---

# Forge workflow script and per-finding tiers

On 2026-10-12 the maintainer asked for The Forge to run as a Claude Code workflow, invoked from the skill as `/forge fix workflow`, and for models to be picked per agent, like Claude Code's ultracode. A `dynamic` option word was built first; the maintainer then made it the default, since choosing among the tiers is how The Forge should already work.

## Settled design

- `workflow` is an option word like `strict`. The skill does the setup that needs the user, then runs the bundled `skills/forge/workflows/forge.js` through the Workflow tool. The script ships inside the skill, so the skills CLI installs it without extra tooling. Runtimes without the Workflow tool run the same level without it.
- Tiers are set per finding by default, with no option word. The reviewer sets each finding's tier under delegation's planning rule, verification and fixes run at that tier, and failed fixes escalate. The reviewer and complexity reviewer keep the tiers ADR 0003 set.
- Verifier subagents verify findings and return verdicts; the orchestrator makes the final call on each. This replaces the orchestrator verifying each finding itself. In the script, accepted verdicts are fixed within the run, and the orchestrator makes its calls when the run ends.
- The Forge's stall rule comes before delegation's escalation rule. An issue that survives two fixes stops for diagnosis, so an engineer fix never escalates inside a run.
- The script's fixer works in a worker worktree that the orchestrator creates, keeping ADR 0005's rule that every writer gets one. The fixer leaves its changes uncommitted, since one run spans several fix rounds; the orchestrator commits the worktree when the run ends clean, an exception to writers committing their own work. At `build`, the script's fixer replaces routing fixes to implementation owners. Without `workflow`, `build` keeps that routing.
- Each round starts a fresh reviewer, which is stricter than reusing one for focused fixes.
