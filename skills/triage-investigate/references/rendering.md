# Report source and rendering

Keep all report content in the `.md` file. Render with:

```bash
uvx --from /path/to/triage-investigate triage-render /path/to/report.md
```

The command replaces only the sibling `report.html`. Relative evidence links remain relative to the report directory. The footer links to the Markdown and records the rebuild command. The package requires Python 3.11 or newer; `uvx` installs the declared Python dependencies into its tool environment. The generated page needs no network or JavaScript.

A three-position switch at the upper right offers Light / System / Dark with Lucide icons and a sliding colored thumb. System is selected initially and follows the browser preference. Click an icon, or focus the switch and use arrow keys to select a mode. Theme colors and the thumb animate unless reduced motion is requested. Section headings and expandable evidence also receive decorative inline Lucide icons; report authors do not need to add them.

After editing the renderer itself, add `--no-cache` to the next `uvx` invocation to avoid an older cached tool environment. Ordinary Markdown edits need only the normal command.

Use a Markdown link for the ticket ID in the title, such as `# [ISSUE-123](https://tickets.example/ISSUE-123): Symptom`, substituting the verified ticket URL. Start the report content with its title and a `## TL;DR` paragraph following the skill’s concise write-up guidance. Use ordinary Markdown headings, lists, tables, links, and fenced code. Label code fences with a language such as `python`, `cpp`, `bash`, or `json` for syntax highlighting at generation time. Use `text` for logs; unknown or unlabeled languages remain plain text. Highlight colors follow the selected theme, without highlighting scripts or network requests. Leave a blank line before lists. Put expandable evidence in a block with `markdown="1"` so its body is parsed:

```html
<details markdown="1">
<summary>Evidence and handoff</summary>

**Observed:** quote and cite the decisive log line here.

</details>
```

Put SVG directly in Markdown, outside code fences. Give each graph a unique title/description ID, `viewBox`, axis labels, and text or tabular equivalent. Use explicit `fill`, `stroke`, and font attributes; style attributes and scripts are removed. Supported SVG elements are `svg`, `g`, `title`, `desc`, `rect`, `circle`, `ellipse`, `line`, `polyline`, `polygon`, `path`, `text`, `tspan`, `defs`, `marker`, and `pattern`. Paint references such as `url(#pattern-id)` must refer to this document. Image files and remote resources are not embedded; link to screenshots as evidence instead.

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
