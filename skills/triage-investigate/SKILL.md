---
name: triage-investigate
description: Triage a reported bug using available logs and source code, then produce a concise evidence-backed HTML report with useful graphs and a Markdown handoff for further investigation or repair. Use for understanding a bug and recommending next steps; implementation is a separate task.
---

# Triage investigate

Requires uv and Python 3.11 or newer for the bundled renderer.

Produce a short decision brief with enough evidence for a person or another coding tool to continue. Stop at triage and recommendations. Leave application code and external tickets unchanged.

## Investigate

1. Establish the reported behavior, expected behavior, reproduction steps, affected build, and incident window from the supplied ticket or artifacts. Treat prior reports and ticket theories as leads to verify. Use available authorized sources before asking for missing inputs; report inaccessible sources explicitly.
2. Inspect the raw logs around the symptom. Identify the device or session, build, time range, timezone, rotation boundaries, and capture gaps needed to interpret the event. Correlate timestamps or request identifiers before combining sources. Check stale crash records and extractor classifications against originals. Absence from incomplete logs is not proof that an event never happened.
3. Trace relevant log emitters into source, including the conditions, callers, and state transitions that explain the observed sequence. Record the inspected revision and its relationship to the incident build. A search miss means the source was not located in the searched scope; it does not establish that the code is absent. Missing or mismatched source limits the conclusion.
4. Test the leading explanation against contrary evidence and relevant alternatives. Compare like-for-like builds, variants, sessions, and measurement boundaries. Distinguish a measured delay from a demonstrated regression. Use a safe existing reproduction or check when available; record whether it was performed, failed to reproduce, or remains proposed. Do not modify a live system to obtain proof.
5. Stop when the evidence supports a useful decision or a specific missing artifact blocks further progress. Recommend the smallest next check that could confirm or falsify the explanation. Keep unrelated findings separate and brief.

## Evidence standard

- **Observed:** directly established by a cited log, inspected code, or performed check. State what each source proves. Code showing a possible path does not prove that the incident took it.
- **Supported explanation:** logs and code connect the symptom to a mechanism, with remaining assumptions named. Call the incident's root cause confirmed only when the causal chain is established for the affected build, including any reproduction or discriminating check needed to resolve competing explanations.
- **Unresolved:** evidence is missing, conflicting, or insufficient. Label hypotheses as hypotheses and name what would distinguish them. Preserve contradictions in the summary when they affect the decision.

Attach citations to consequential claims: log artifact plus line range and timestamp/session; source repository, revision, file and line range; or command, environment and actual result. Quote only the decisive excerpt. For derived measurements, retain the endpoints and calculation. Use resolvable paths or links, never invented or abbreviated paths that hide the source.

When only logs or only code are available, report useful observations and the missing half of the causal chain. Do not turn a plausible fix, repository name, repeated timing, or confident earlier report into proof. Redact secrets and unnecessary personal identifiers from excerpts.

## Deliver a concise report and handoff

Link the ticket ID in the report title to its verified URL from the supplied ticket or authorized source. If only an ID is available, ask for the ticket URL; keep the ID as plain text until it is known rather than guessing a server or URL.

Write `<issue-or-short-name>-triage.md` beside the investigation artifacts or in the user's chosen output location. Make Markdown the canonical report and handoff, and generate the self-contained HTML from it with a repeatable rendering command. Revise the source and re-render rather than editing report content separately in HTML. Honor a request for Markdown only. Place a TL;DR directly below the report title: one plain-language paragraph of roughly 80–120 words that someone can reuse to explain the issue to a mixed technical/nontechnical audience. Cover the problem, supported impact, known or suspected cause, and next step with its actual status. Preserve material uncertainty; define essential jargon and leave detailed citations and excerpts in the evidence section. Put only decision-relevant evidence below it, linking to raw artifacts instead of copying dumps.

Keep graphs as inline SVG in the Markdown, with a nearby text equivalent or data table for coding tools. Use the bundled renderer, resolving `<skill-directory>` to this skill's installed directory:

```bash
uvx --from <skill-directory> triage-render <issue-or-short-name>-triage.md
```

This writes a sibling `.html` file with inline styling and a source/rebuild link. Python dependencies are declared in `pyproject.toml`; no package publication is needed. For authoring syntax, read [references/rendering.md](references/rendering.md). Run the command to produce the delivered HTML and confirm that rebuilding preserves the report and graphs. A separately authored HTML page checked against Markdown does not satisfy this requirement.

```markdown
# [<Issue>](<verified-ticket-url>): <plain-language symptom>

## TL;DR
<One shareable paragraph: problem, supported impact, assessment with uncertainty, and next step. Distinguish reported behavior from verification and proposed actions from completed work.>

## Evidence
The shortest causal sequence the artifacts support, with log and code citations beside each claim. Mark inferred links and contradictions explicitly.

## Handoff
- **Reproduce:** inputs, environment and steps; distinguish reported steps from attempts performed and their results.
- **Inspect:** relevant source locations and revision, linked evidence artifacts, and access requirements or missing sources.
- **Resolve:** the remaining question and the smallest discriminating check, including what each outcome would mean.
- **Verify a future fix:** observable expected behavior and relevant regression checks; mark these as proposed until run.
```

The handoff must stand alone without chat history and preserve the assessment's uncertainty. Direct the fixing tool to verify the hypothesis before editing; identify candidate change locations only when supported by inspected code. Omit empty or redundant bullets. Keep this in the same report unless the user requests a separate handoff; if split, link the evidence report and retain its limitations instead of duplicating the investigation.


## Make the HTML easy to scan

Keep the summary, assessment, material uncertainty, and next action visible at the top. Follow with one useful graph when the evidence supports it: a timeline for ordering, a duration chart for measured delays, or a small sequence diagram connecting logs to code. Skip graphs that add no information.

Use inline SVG and CSS without remote scripts, fonts, or dependencies. Label units, time basis, builds, and data sources. Distinguish observed steps from inferred links with text and line style, not color alone; retain gaps and contradictory evidence. Never invent timings, imply causation with an unlabeled arrow, or turn unmatched comparisons into a regression chart. Include a short text equivalent and evidence links near the graphic.

Keep detailed excerpts and the handoff in clearly labeled expandable sections. Avoid dashboards, repeated verdicts, and full log dumps. Make the page readable on narrow screens and with keyboard navigation. Escape artifact text before embedding it as HTML. Check that HTML and Markdown agree on conclusions, limitations, values, and citations, then open the HTML to check readability, graph labels, and links before delivery. If visual inspection is unavailable, disclose that limitation.
