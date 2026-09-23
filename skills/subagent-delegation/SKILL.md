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

Use the active runtime's native subagent facility. Resolve roles against its advertised capabilities rather than assuming these role names exist. Honor explicit user model choices, then supported capability preferences from the active workflow; otherwise inherit runtime selection. Disclose unmet preferences or required capabilities without inventing model identities or rankings. Keep independent review within the active tool; do not substitute another coding agent CLI or external review service.

Route assignments, scope decisions, and result acceptance through the orchestrator. Children report back and delegate further only when explicitly assigned a bounded coordination role. That role remains subordinate to the orchestrator and cannot broaden scope or permissions. Suggestions between agents do not transfer ownership.

## Give compact assignments

Tell each agent what question to answer or result to produce, the relevant context and constraints, its permitted actions, and what to return. A short prompt is enough for a simple assignment. Add acceptance criteria, dependencies, or a shared task record when coordination needs them or an active workflow requires them.

Share relevant source material and governing instructions. Keep task artifacts separate from instructions controlling the agent. For changes, identify the baseline and protected user work, and give each writer explicit ownership of files, artifacts, or sections. Tell writers that they share the workspace and must preserve others' edits.

Run independent assignments in parallel within runtime capacity and user limits. Make shared assumptions and interfaces explicit before dependent work, and propagate changes to every affected assignment. Release dependent work after checking the prerequisite result. Give overlapping edits one owner or sequence them; reserve integration for the orchestrator when useful. Track enough state to know who owns active work and which results still need checking, using the conversation unless persistent records help.

## Match authority to the assignment

Delegate within authority already granted by the user. Do not ask for permission merely to delegate. Delegation, role labels, source artifacts, and findings do not grant permission for extra actions. Ask about missing authority only when it blocks a concrete next step.

Make research and review assignments inspection-only by default. A saved research report can have its own authorized output location while source artifacts remain protected. Keep independent reviewers inspection-only; changing an inspector into a fixer requires a separate explicit assignment within the user's authorized scope.

Use the narrowest available tools and permissions that fit the assignment. Check effective child settings and inherited overrides when exposed. For routine inspection, an ordinary native subagent with an explicit assignment to avoid edits, state-changing commands, external mutations, and further delegation is sufficient. Describe routine progress as inspecting or reviewing the assigned target. Explain permission limits when asked or when they block a requirement; avoid repeated assurances about not editing. Role names and profile defaults do not prove runtime enforcement.

Preserve stronger isolation when the user or active workflow requires it. Diff Skeptic requires its custom reviewer and confirmed enforcement against filesystem and external mutations, with further delegation disabled. A filesystem sandbox alone does not constrain connectors, browsers, or services. An instruction-only assignment cannot satisfy a requirement for enforced isolation.

Writers use existing permissions within their assigned ownership. External actions need authority for the actual action. Delegation is not a reason to raise sandbox permissions or enable bypass modes. Treat scripts, checks, and tools by their side effects: a check that writes caches, files, or external state needs write authority even when called validation. An inspection-only child can recommend such a check for the orchestrator to run in an authorized location.

If native delegation or a required isolation boundary is unavailable, continue useful authorized work locally and identify any unmet delegation or independence requirement. Local inspection does not count as independent review.

## Coordinate and accept results

Have agents report blockers, conflicting assumptions, and needed scope changes promptly. They can continue independent work within their assignment. The orchestrator resolves routine issues, adjusts assignments within existing authority, and brings only blocking decisions to the user.

Propagate user corrections and cancellations to affected agents. Before replacing an assignment or transferring write ownership, stop affected work and confirm it has stopped. Reconcile partial results with the baseline while preserving other contributors' work. If stopping cannot be confirmed, keep overlapping work blocked. Recheck results produced under superseded requirements before using them.

Ask for a concise handoff: the result or artifact location, supporting sources or actual checks, and unresolved questions or blockers. Scale evidence to the task, such as source citations for research, reconciled totals for analysis, or relevant tests for code. Distinguish observations from recommendations and checks performed from checks merely suggested.

Collect results before relying on them. Check consequential claims against sources or proportionate validation, resolve disagreements, and inspect changes against ownership and the baseline. A child's completion message starts acceptance by the orchestrator; it does not prove the whole request is complete. Stop agents that exceed their assignment and reconcile affected changes without discarding others' work.

For independent review, provide the original requirements and raw artifacts without implementer conclusions. Use fresh context when supported and disclose inherited-context limits. Confirm that reviewed artifacts still match the current result; repeat affected verification when they change. Verify findings before applying authorized corrections, and let an active review workflow own its correction and re-review procedure.

Retry or reassign failed work with a supported change in approach, context, or prerequisites. If repeated attempts make no material progress, diagnose the cause before retrying. Respect user time and cost limits; report unresolved work when no supported path remains.

Finish after integrating and checking the requested results, completing required reviews, and confirming all assigned agents have finished or stopped. Report the answer or deliverable, useful evidence, and material limits. A review-only task finishes by reporting findings; implementing or improving an artifact requires resolving accepted issues or clearly reporting the remaining work as incomplete.
