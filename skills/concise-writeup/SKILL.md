---
name: concise-writeup
description: Summarize existing findings into concise, natural write-ups with supporting evidence and optional next steps.
disable-model-invocation: true
compatibility: Explicit-only invocation requires a client that honors disable-model-invocation or the OpenAI allow_implicit_invocation policy.
---

# Concise write-up

Run only when explicitly requested. Turn existing investigation findings, triage notes, or drafts into a concise, evidence-supported write-up for a mixed technical audience. Also support general summaries.

## Establish the point and evidence

1. Identify what readers need to understand or decide. Use the supplied audience, destination, and constraints; otherwise assume technical colleagues outside the immediate specialty. Ask only when a missing detail could materially change the meaning or recommendation.
2. Summarize the findings already available in the conversation and supplied artifacts. Do not restart triage, run diagnostics, or research by default. Investigate or research only when requested; for requested research, prefer authoritative primary sources. Inspect available evidence before citing it and attribute findings you cannot independently verify to the supplied account.
3. Support substantive factual claims with evidence: source documentation, code, test results, measurements, or supplied records. Place concise Markdown links or identifiable artifact references beside the claims they support. When an input has no link, attribute it plainly, such as "According to the supplied test notes." Never invent citations, measurements, or verification.
4. Match each claim's strength and scope to its evidence. Preserve versions, dates, test conditions, and limitations when they affect the conclusion. Distinguish observed results, reported information, and inference; explain the basis of a recommendation. Code inspection alone does not establish measured performance or successful execution.
5. If evidence is missing, inaccessible, or conflicting, qualify the claim and briefly identify the gap. Ask for clarification when the central conclusion depends on it. Do not silently remove a material claim or present an unsupported conclusion as settled.

## Write and format

For an issue, explain what is happening, what should happen, who or what is affected, and the supporting evidence, as available. Distinguish confirmed causes from suspected causes and unknowns. For general summaries, lead with the main point and its practical significance. Choose the structure for the content and destination rather than filling a fixed template.

Include next steps when supplied or requested, such as trying a fix, requesting information, or adding debugging to test a hypothesis. Preserve whether an action is proposed, planned, attempted, or verified. Do not invent a commitment or turn the summary into an implementation plan.

Target 150–300 words by default. Use fewer when sufficient; expand when essential evidence or technical detail requires it. Explicit length and format requests take precedence. Cut repetition before cutting qualifications or evidence.

Sound like a knowledgeable colleague: direct, conversational, and professional. Explain unfamiliar terminology briefly, retain precise technical terms, and replace corporate filler with concrete mechanisms or outcomes. Preserve the author's position, exact quotations, code, commands, identifiers, and technical meaning.

Return paste-ready Markdown. Prefer short paragraphs; use headings, bullets, tables, or code blocks only when they make the content easier to follow or compare. Adapt to a supplied destination such as a message, ticket, or internal document.

## Check and deliver

Compare the write-up against the inputs and inspected sources. Check that substantive factual claims have traceable support or explicit qualification, links support the nearby claims, and compression has preserved meaning and uncertainty.

Return only the finished write-up. Add a short separate note only for unresolved questions or factual concerns; omit an inventory of edits.
