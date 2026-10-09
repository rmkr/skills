# Report source and rendering

Keep all report content in the `.md` file. Render with:

```bash
uvx --from /path/to/triage-investigate triage-render /path/to/report.md
```

The command replaces only the sibling `report.html`. Relative evidence links remain relative to the report directory. The case sheet links to the Markdown and the footer records the rebuild command. The package requires Python 3.11 or newer; `uvx` installs the declared Python dependencies into its tool environment. The generated page needs no network or JavaScript.

The page is laid out as a case file: the title under a double rule, a case sheet column (facts, section index, exhibit index, line-style key) that stacks above the report on narrow screens, and §-numbered sections. A Light / System / Dark switch sits at the upper right; System follows the browser preference.

## Conventions

All are optional and stay readable as plain Markdown; a report that uses none still renders.

- **Facts:** a list directly after the title whose every item starts with `**Key:**` moves into the case sheet. A `Reproduced` or `Confidence` value starting with No, Low, Unknown, or Unresolved is boxed as open.
- **Next action:** a blockquote starting `**Next:**` becomes the next-action panel.
- **Sections:** every `##` heading is numbered and indexed.
- **Timeline:** a table whose first header starts with `Time` becomes a vertical timeline (time, event, source). An event starting `Inferred:` gets a hollow ring and dashed line; `Unknown:` or `Gap:` gets a dashed no-data segment; anything else is logged. Put the time basis in the header, such as `Time (UTC)`.
- **Evidence:** list items starting `**Observed:**`, `**Supported explanation:**` / `**Inferred:**`, or `**Unresolved:**` / `**Unknown:**` get solid, dashed, or dotted rules beside the visible label.
- **Exhibits:** `### Exhibit A: Title`, optionally ending `(observed)` or `(inferred)`, plus everything up to the next heading becomes a framed exhibit (solid or dashed border with a text label). End an exhibit with a heading. Plain text "Exhibit A" elsewhere links to it.
- **Hypotheses:** in a table with a `Status` column, cells `Supported`, `Contradicted`, or `Unresolved` get status labels; contradicted rows are struck through.
- **Logs:** ```` ```text hl_lines="1" ```` marks decisive lines with ▶ and an outline.
- **Handoff:** the first bullet list under `## Handoff` is numbered.

````markdown
# [ISSUE-123](https://tickets.example/ISSUE-123): Symptom

- **Build:** 2.41.0
- **Reproduced:** No, proposed

## TL;DR
One paragraph; the first failure is Exhibit A.

> **Next:** The smallest discriminating check.

## Timeline

| Time (UTC) | Event | Source |
| --- | --- | --- |
| 14:05:02 | Deploy begins | [deploy.log L12](logs/deploy.log#L12) |
| 14:06–14:52 | Inferred: new pods fail until warm | [lb.log L412](logs/lb.log#L412) |
| 14:20–14:35 | Gap: no app logs | app.log |

## Evidence

- **Observed:** cited fact.

### Exhibit A: First failure (observed)

```text hl_lines="1"
14:06:11 ERROR decisive line
```
````

After editing the renderer itself, add `--no-cache` to the next `uvx` invocation to avoid an older cached tool environment. Ordinary Markdown edits need only the normal command.

Use a Markdown link for the ticket ID in the title, such as `# [ISSUE-123](https://tickets.example/ISSUE-123): Symptom`, substituting the verified ticket URL. Start the report content with its title and a `## TL;DR` paragraph following the skill’s concise write-up guidance. Use ordinary Markdown headings, lists, tables, links, and fenced code. Label code fences with a language such as `python`, `cpp`, `bash`, or `json` for syntax highlighting at generation time. Use `text` for logs; unknown or unlabeled languages remain plain text. Highlight colors follow the selected theme, without highlighting scripts or network requests. Leave a blank line before lists. Put expandable evidence in a block with `markdown="1"` so its body is parsed:

```html
<details markdown="1">
<summary>Evidence and handoff</summary>

**Observed:** quote and cite the decisive log line here.

</details>
```

Use the timeline table rather than drawing a timeline. For other graphs, put SVG directly in Markdown, outside code fences. Give each graph a unique title/description ID, `viewBox`, axis labels, and text or tabular equivalent. Use explicit `fill`, `stroke`, and font attributes; style attributes and scripts are removed. Supported SVG elements are `svg`, `g`, `title`, `desc`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `path`, `text`, `tspan`, `defs`, `marker`, and `pattern`. Paint references such as `url(#pattern-id)` must refer to this document. Image files and remote resources are not embedded; link to screenshots as evidence instead.

For example, this is illustrative syntax, not measured incident data:

```html
<figure>
<svg viewBox="0 0 600 100" role="img" aria-labelledby="latency-title latency-desc">
  <title id="latency-title">Example duration</title>
  <desc id="latency-desc">An illustrative phase takes two seconds.</desc>
  <rect x="10" y="10" width="200" height="30" fill="#176a80"/>
  <text x="10" y="65">Example phase: 2 seconds</text>
</svg>
<figcaption>Replace with a measured value and its evidence citation.</figcaption>
</figure>
```

Escape raw log text or put it in code fences. The renderer sanitizes embedded markup as a second safeguard. Inspect the generated page after rendering: unsupported HTML is stripped, and graph readability still depends on the source geometry. On narrow screens, wide graphs scroll horizontally to keep labels legible.
