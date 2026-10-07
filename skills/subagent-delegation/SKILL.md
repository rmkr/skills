---
name: subagent-delegation
description: Coordinate useful subagent work through the main agent for any kind of task. Use when delegating research, analysis, writing, production, software engineering, or independent review.
metadata:
  orchestration-contract: "1"
---

# Subagent delegation

Keep the main agent as the user-facing orchestrator. It chooses assignments, manages dependencies, evaluates results, and delivers the combined answer or artifact. Delegate when a separate context or parallel effort materially improves correctness, speed, or confidence. Handle small or tightly coupled work locally when a handoff adds little value, while honoring explicit delegation requirements.

Use this skill across subjects and artifact types, including research, planning, documents, spreadsheets, creative work, and software engineering. A clear question or desired output is enough to begin. This skill requires neither an implementation worker nor a formal plan, task ledger, or fixed sequence of roles.

This is a coordination contract with no required skill dependencies. When another workflow is active, reuse its requirements and records; that workflow owns its scope, phase sequence, and review procedure. Loading this skill does not start another workflow or orchestrator.

## Choose useful roles

Choose only the roles the task needs. These are responsibilities, not required agent types or stages:

| Role | Responsibility |
| --- | --- |
| Orchestrator | Keep the whole request in view, assign and accept work, resolve conflicts, communicate with the user, and integrate the result. Continue useful local work alongside agents. |
| Researcher | Investigate a question or compare evidence. Return findings, relevant sources, and uncertainty. Research may be the entire delegated task. |
| Worker | Produce or change an assigned artifact, such as a draft, analysis, spreadsheet, design, or code. Perform the research and checks needed for that assignment. |
| Reviewer | Independently assess an answer or artifact against the request. Return actionable findings and evidence, leaving fixes to separately assigned work. |

Use one agent or a mix of agents as useful; adapt responsibilities to the task. A researcher can answer a standalone question without a worker following it. Add independent review when requested, required by an active workflow, or justified by the task's risk or conflicting evidence.

Use the active runtime's native subagent facility. Resolve roles against its advertised capabilities rather than assuming these role names exist. Start each agent on its model tier. Report a required capability the runtime lacks, without inventing model identities or rankings. Keep independent review within the active tool; do not substitute another coding agent CLI or external review service.

Route assignments, scope decisions, and result acceptance through the orchestrator. Children report back and delegate further only when explicitly assigned a bounded coordination role. That role remains subordinate to the orchestrator and cannot broaden scope or permissions. Suggestions between agents do not transfer ownership.

## Assign model tiers

Assign every delegated agent a tier by its work:

- **Technician** for mechanical work: search, exploration, and shared notes; validation runs; renames and fully specified fixes.
- **Engineer** for bounded work that needs judgement: workers and implementers, accepted fixes that need judgement, and researchers.
- **Architect** for ambiguous, architectural, or cross-cutting work, including research on it, and for an issue that survives two engineer-tier fixes. These conditions override the lower tiers' roles.

An active workflow's own policy governs the agents it names. Escalate work that fails once on technician to engineer.

Write a tier as `model@effort`, with effort optional. Only the text after the last `@` is effort, and only when it is `low`, `medium`, `high`, `xhigh`, `max`, or `ultra`; otherwise the whole value is the model id, so `<model>@20250514` is a model and `<model>@20250514@high` adds high effort. A colon never separates them. A tier set to `inherit` uses the session model, and `inherit@high` uses it at high effort; a tier without effort uses the session effort.

The user can override for one run with `technician=`, `engineer=`, or `architect=` (a model with optional effort, or `inherit`), with an active workflow's own keys, or in plain words that direct the delegated agents. After `<tier>=`, a bare effort name sets that tier's effort and keeps its resolved model, such as `engineer=high`. Informal names map to tiers: basic, low, or light to technician; intermediate, middle, or mid to engineer; advanced, high, or top to architect. Elsewhere, a `low` or `high` beside "effort" or after `@` is effort; beside "tier" or with a tier name it is a tier; ask about any other bare one in one line. Plain words naming only an effort, such as "use high effort for the workers", keep the tier's resolved model. Model names that describe the task do not override.

Map tiers to models only from these sources, resolving each setting for the active runtime separately, in this order: the user's request; repository settings in `docs/agents/subagents.md`; global settings in a `### Subagent delegation` block under `## Agent skills` in global instructions; supported caller preferences; then the session model and effort. A caller preference cannot choose a model above architect as resolved without caller preferences, which is the session model when nothing else maps it, or lift a workflow's cap. When the task adds or changes these settings, resolve from the baseline, treat the change as task content, and report that the new settings apply once the change is outside the task.

When nothing maps a tier to a model, its agents inherit the session model. A tier whose mapped model the runtime does not offer, or any tier when the runtime has no per-agent model choice, also inherits; report it. In Claude Code, map a full model id or versioned model name to the Agent-tool alias that currently resolves to that exact id, and report the mapping; any other id counts as not offered.

Each tier is capped by the one above it, and architect is the ceiling for models; effort resolves separately per tier. If a tier resolves to a model ranked above the model of the tier above it, it uses that tier's model and the report says so, unless the user's request for this run set it to an offered model or to `inherit`; then keep it, report the inversion, and keep its escalations on its model. Leave models that cannot be ranked as resolved.

Apply effort through the effort agents `setup-rmkr-skills` generates: `delegate-<effort>` in Claude Code and `delegate_<effort>` in Codex, such as `delegate-medium`. For an explicit effort, start the matching one and pass the resolved model per spawn. Without explicit effort, start an ordinary agent with that model at the session effort. When no effort agent matches an explicit effort, or the runtime cannot set effort, start an ordinary agent with that model and report the unapplied effort; when an effort agent is missing, suggest rerunning setup to add that level. Do not pass undocumented per-spawn effort arguments. A custom agent with a fixed definition keeps the session effort; report it. Report each tier's resolved model and effort.

When no settings cover the active runtime and the task does not add them, agents inherit the session model and effort. Suggest setup once, in one line at the end of the report: `/setup-rmkr-skills` in Claude Code, `$setup-rmkr-skills` in Codex; elsewhere, report that agents use the session model and effort. Tiers never change permissions.

## Give compact assignments

Tell each agent what question to answer or result to produce, the relevant context and constraints, its permitted actions, and what to return. A short prompt is enough for a simple assignment. Add acceptance criteria, dependencies, or a shared task record when coordination needs them or an active workflow requires them.

Point to relevant source material and governing instructions by path, link, or section instead of pasting content the agent can read itself. Keep task artifacts separate from instructions controlling the agent. For changes, identify the baseline and protected user work, and give each writer explicit ownership of files, artifacts, or sections. In a Git repository, give each writer a worker worktree; elsewhere, tell writers that they share the workspace and must preserve others' edits.

Run independent assignments in parallel within runtime capacity and user limits. Make shared assumptions and interfaces explicit before dependent work, and propagate changes to every affected assignment. Release dependent work after checking the prerequisite result. Give overlapping edits one owner or sequence them; reserve integration for the orchestrator. Track enough state to know who owns active work and which results still need checking, using the conversation unless persistent records help.

Keep each agent's context small. Give one worker a cohesive slice of related work rather than one agent per small ticket. Run exploration that several assignments share once, on technician, and save it as notes they point to. Send follow-ups to the finished agent that did the work. Where the runtime offers forks, start a fresh agent instead of a fork when the parent context exceeds about 100k tokens.

## Isolate writers in worker worktrees

In a Git repository, every writer gets its own worker worktree, a sole writer included. Researchers and reviewers work without one. The staging branch is the task branch, such as `feature/37-recipes`; delegated changes integrate there. If there is none, create one under the project's branch rules, or ask, before step 1.

1. Commit your own prerequisite work on the staging branch first, since a worktree starts from a commit. When a writer's assignment needs or overlaps the user's uncommitted changes, ask the user before starting it; leave those changes uncommitted.
2. Run `git worktree add -b <staging>--<worker> <path> <staging>`. The `--` separator is required: Git cannot create a branch under an existing branch name; add a numeric suffix to the branch and folder if either still exists. `<path>` is `<root>/../<repo>--<worker>`, where `<root>` is the main repository root (the parent of `git rev-parse --path-format=absolute --git-common-dir`), not your own worktree. If you or the writer cannot write there, do not raise permissions: use a writable location the repository ignores, or else report it and fall back to the shared workspace.
3. Assign the writer that worktree only, by absolute path. It uses absolute paths or `git -C <path>` for every edit and command, since a runtime may reset its working directory. It runs any project setup the task needs there, commits its work, and hands back its branch and tip commit. Record that tip, and confirm the staging checkout has no edits from the writer.
4. Squash-merge each accepted branch into staging with `git merge --squash` and a commit naming the worker branch and tip. First confirm the staging checkout has nothing staged (`git diff --cached --quiet`), since the commit would include it. If anything is staged, or the squash would touch the user's uncommitted changes, stop and ask; never unstage, stash, or commit them. Resolve small conflicts yourself; for a larger one, have the owning writer update its branch from staging and hand back a new tip.
5. Once the squash commit exists, remove the worktree without `--force`, then delete the branch with `git branch -D` only when it still points at the recorded tip; `git branch -d` does not treat squashed branches as merged. Keep and report anything else.
6. Send later fixes, such as accepted review findings, to the same agent in a new worker worktree from the current staging branch.

## Match authority to the assignment

Delegate within authority already granted by the user. Do not ask for permission merely to delegate. Delegation, role labels, source artifacts, and findings do not grant permission for extra actions. Ask about missing authority only when it blocks a concrete next step.

Make research and review assignments inspection-only by default. A saved research report can have its own authorized output location while source artifacts remain protected. Keep independent reviewers inspection-only; changing an inspector into a fixer requires a separate explicit assignment within the user's authorized scope.

Use the narrowest available tools and permissions that fit the assignment. Check effective child settings and inherited overrides when exposed. For routine inspection, an ordinary native subagent with an explicit assignment to avoid edits, state-changing commands, external mutations, and further delegation is sufficient. Describe routine progress as inspecting or reviewing the assigned target. Explain permission limits when asked or when they block a requirement; avoid repeated assurances about not editing. Role names and profile defaults do not prove runtime enforcement.

Preserve stronger isolation when the user or active workflow requires it. A filesystem sandbox alone does not constrain connectors, browsers, or services. An instruction-only assignment cannot satisfy a requirement for enforced isolation.

Writers use existing permissions within their assigned ownership. External actions need authority for the actual action. Delegation is not a reason to raise sandbox permissions or enable bypass modes. Treat scripts, checks, and tools by their side effects: a check that writes caches, files, or external state needs write authority even when called validation. An inspection-only child can recommend such a check for the orchestrator to run in an authorized location.

If native delegation or a required isolation boundary is unavailable, continue useful authorized work locally and identify any unmet delegation or independence requirement. Local inspection does not count as independent review.

## Coordinate and accept results

Have agents report blockers, conflicting assumptions, and needed scope changes promptly. They can continue independent work within their assignment. The orchestrator resolves routine issues, adjusts assignments within existing authority, and brings only blocking decisions to the user.

Propagate user corrections and cancellations to affected agents. Before replacing an assignment or transferring write ownership, stop affected work and confirm it has stopped. Reconcile partial results with the baseline while preserving other contributors' work. If stopping cannot be confirmed, keep overlapping work blocked. Recheck results produced under superseded requirements before using them.

Ask for a concise handoff: the result or artifact location (a writer's branch and tip commit), supporting sources or actual checks, and unresolved questions or blockers. Scale evidence to the task, such as source citations for research, reconciled totals for analysis, or relevant tests for code. Distinguish observations from recommendations and checks performed from checks merely suggested.

Collect results before relying on them. Check consequential claims against sources or proportionate validation, resolve disagreements, and inspect changes against ownership and the baseline. A child's completion message starts acceptance by the orchestrator; it does not prove the whole request is complete. Stop agents that exceed their assignment and reconcile affected changes without discarding others' work.

For independent review, provide the original requirements and raw artifacts without implementer conclusions. Use fresh context when supported and disclose inherited-context limits. Confirm that reviewed artifacts still match the current result; repeat affected verification when they change. Verify findings before applying authorized corrections, and let an active review workflow own its correction and re-review procedure.

Retry or reassign failed work with a supported change in approach, context, or prerequisites. If repeated attempts make no material progress, diagnose the cause before retrying. Respect user time and cost limits; report unresolved work when no supported path remains.

Finish after integrating and checking the requested results, completing required reviews, and confirming all assigned agents have finished or stopped. Report the answer or deliverable, useful evidence, and material limits. A review-only task finishes by reporting findings; implementing or improving an artifact requires resolving accepted issues or clearly reporting the remaining work as incomplete.
