"""Render Markdown and inline SVG without executing report content."""

import argparse
import html
from importlib.metadata import distribution
import json
import os
from pathlib import Path
import re
import shlex
import tempfile
from urllib.parse import quote, unquote, urlsplit

import markdown
import nh3
from pygments.formatters import HtmlFormatter


# SVGs from https://github.com/lucide-icons/lucide; license retained in every report.
LUCIDE_LICENSE = """ISC License

Copyright (c) 2026 Lucide Icons and Contributors

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

---

The following Lucide icons are derived from the Feather project:

airplay, alert-circle, alert-octagon, alert-triangle, aperture, arrow-down-circle, arrow-down-left, arrow-down-right, arrow-down, arrow-left-circle, arrow-left, arrow-right-circle, arrow-right, arrow-up-circle, arrow-up-left, arrow-up-right, arrow-up, at-sign, calendar, cast, check, chevron-down, chevron-left, chevron-right, chevron-up, chevrons-down, chevrons-left, chevrons-right, chevrons-up, circle, clipboard, clock, code, columns, command, compass, corner-down-left, corner-down-right, corner-left-down, corner-left-up, corner-right-down, corner-right-up, corner-up-left, corner-up-right, crosshair, database, divide-circle, divide-square, dollar-sign, download, external-link, feather, frown, hash, headphones, help-circle, info, italic, key, layout, life-buoy, link-2, link, loader, lock, log-in, log-out, maximize, meh, minimize, minimize-2, minus-circle, minus-square, minus, monitor, moon, more-horizontal, more-vertical, move, music, navigation-2, navigation, octagon, pause-circle, percent, plus-circle, plus-square, plus, power, radio, rss, search, server, share, shopping-bag, sidebar, smartphone, smile, square, table-2, tablet, target, terminal, trash-2, trash, triangle, tv, type, upload, x-circle, x-octagon, x-square, x, zoom-in, zoom-out

The MIT License (MIT) (for the icons listed above)

Copyright (c) 2013-present Cole Bemis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
ICONS = {
    "sun": '''<svg class="lucide" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="4" />
  <path d="M12 2v2" />
  <path d="M12 20v2" />
  <path d="m4.93 4.93 1.41 1.41" />
  <path d="m17.66 17.66 1.41 1.41" />
  <path d="M2 12h2" />
  <path d="M20 12h2" />
  <path d="m6.34 17.66-1.41 1.41" />
  <path d="m19.07 4.93-1.41 1.41" />
</svg>''',
    "moon": '''<svg class="lucide" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401" />
</svg>''',
    "monitor": '''<svg class="lucide" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect width="20" height="14" x="2" y="3" rx="2" />
  <line x1="8" x2="16" y1="21" y2="21" />
  <line x1="12" x2="12" y1="17" y2="21" />
</svg>''',
    "file-text": '''<svg class="lucide" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z" />
  <path d="M14 2v5a1 1 0 0 0 1 1h5" />
  <path d="M10 9H8" />
  <path d="M16 13H8" />
  <path d="M16 17H8" />
</svg>''',
    "search": '''<svg class="lucide" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <path d="m21 21-4.34-4.34" />
  <circle cx="11" cy="11" r="8" />
</svg>''',
    "clipboard-list": '''<svg class="lucide" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <rect width="8" height="4" x="8" y="2" rx="1" ry="1" />
  <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
  <path d="M12 11h4" />
  <path d="M12 16h4" />
  <path d="M8 11h.01" />
  <path d="M8 16h.01" />
</svg>''',
}

SVG_TAGS = {
    "svg", "g", "title", "desc", "rect", "circle", "ellipse", "line",
    "polyline", "polygon", "path", "text", "tspan", "defs", "marker", "pattern",
}
SVG_ATTRIBUTES = {
    "viewBox", "viewbox", "preserveAspectRatio", "preserveaspectratio",
    "x", "y", "x1", "x2", "y1", "y2", "dx", "dy", "cx", "cy", "r", "rx", "ry",
    "width", "height", "d", "points", "transform", "fill", "stroke", "stroke-width",
    "stroke-dasharray", "stroke-linecap", "stroke-linejoin", "opacity", "fill-opacity",
    "stroke-opacity", "text-anchor", "dominant-baseline", "font-size", "font-weight",
    "marker-end", "marker-start", "markerWidth", "markerHeight", "refX", "refY",
    "orient", "markerUnits", "patternUnits", "patternTransform",
}
CSS = """
:root { color-scheme: light dark; --paper: #faf9f6; --ink: #252c32;
  --muted: #58636c; --rule: #cbd1d4; --obs: #176a80; --flat: #68737d; }
:root:has(#theme-light:checked) { color-scheme: light; --paper: #faf9f6; --ink: #252c32;
  --muted: #58636c; --rule: #cbd1d4; --obs: #176a80; --flat: #68737d; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink);
  font: 16px/1.6 system-ui, sans-serif; }
main { max-width: 960px; margin: auto; padding: 32px 24px 64px; overflow-wrap: anywhere; }
h1 { font-size: clamp(1.6rem, 4vw, 2.2rem); line-height: 1.2; }
h2 { margin-top: 2rem; border-bottom: 1px solid var(--rule); padding-bottom: .35rem; }
h3 { margin-bottom: .4rem; }
a { color: var(--obs); text-underline-offset: 3px; }
a:focus-visible, summary:focus-visible { outline: 3px solid var(--obs); outline-offset: 4px; }
pre { padding: 1rem; border: 1px solid var(--rule); overflow-x: auto; }
code { font: .88em ui-monospace, monospace; }
table { display: block; max-width: 100%; overflow-x: auto; border-collapse: collapse; }
th, td { padding: .5rem .7rem; border: 1px solid var(--rule); text-align: left; }
blockquote { margin-left: 0; border-left: 3px solid var(--rule); padding-left: 1rem; }
details { margin: 1rem 0; padding: .75rem 1rem; border: 1px solid var(--rule); border-radius: 6px; }
summary { cursor: pointer; font-weight: 600; }
figure { margin: 1.5rem 0; overflow-x: auto; }
svg { display: block; width: 100%; height: auto; color: var(--ink); }
svg:not([fill]) { fill: currentColor; }
svg text { font-family: system-ui, sans-serif; }
.svgmuted { fill: var(--muted); font-size: 12px; } .svgbold { font-weight: 600; }
figcaption, footer { color: var(--muted); font-size: .85rem; }
footer { border-top: 1px solid var(--rule); margin-top: 2rem; padding-top: 1rem; }
@media (prefers-color-scheme: dark) { :root:not(:has(#theme-light:checked)) { --paper: #192126; --ink: #e4e9ec;
  --muted: #b2bec6; --rule: #4d5b65; --obs: #78c5db; --flat: #9aabb6; } }
:root:has(#theme-dark:checked) { color-scheme: dark; --paper: #192126; --ink: #e4e9ec;
  --muted: #b2bec6; --rule: #4d5b65; --obs: #78c5db; --flat: #9aabb6; }
.theme-toolbar { float: right; margin: .15rem 0 .75rem 1.5rem; }
.theme-toolbar + h1 { display: flow-root; margin-top: 0; }
.theme-toolbar + h1 + * { clear: both; }
.theme-picker { position: relative; display: flex; margin: 0; padding: 3px;
  min-inline-size: 0; border: 1px solid var(--rule); border-radius: 999px;
  background: color-mix(in srgb, var(--ink) 4%, var(--paper)); }
.theme-picker::before { content: ""; position: absolute; left: 3px; top: 3px;
  width: 32px; height: 32px; border-radius: 50%; background: var(--obs);
  transform: translateX(32px); }
.theme-picker:has(#theme-light:checked)::before { transform: translateX(0); }
.theme-picker:has(#theme-dark:checked)::before { transform: translateX(64px); }
.theme-picker label { position: relative; display: grid; place-items: center;
  width: 32px; height: 32px; border-radius: 50%; cursor: pointer; color: var(--muted); }
.theme-picker label:has(input:checked) { color: var(--paper); }
.theme-picker label:has(input:focus-visible) { outline: 2px solid var(--obs); outline-offset: 3px; }
.theme-picker legend, .theme-picker input { position: absolute; width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.theme-picker .lucide { color: inherit; width: 16px; height: 16px; }
@media (forced-colors: active) {
  .theme-picker label:has(input:checked) { outline: 2px solid Highlight; outline-offset: -3px; }
  .theme-picker label:has(input:focus-visible) { outline: 2px dashed Highlight; outline-offset: 2px; }
}
@media (prefers-reduced-motion: no-preference) {
  .theme-picker::before { transition: transform .4s ease, background-color .65s ease; }
  body, body * { transition: background-color .65s ease, color .65s ease,
    border-color .65s ease, fill .65s ease, stroke .65s ease; }
}
svg.lucide { display: inline-block; width: 1.1em; height: 1.1em; min-width: 0;
  vertical-align: -.15em; flex-shrink: 0; }
h2 .lucide, h3 .lucide, summary .lucide { margin-right: .4em; color: var(--obs); }
@media (max-width: 600px) {
  .theme-toolbar { float: none; width: fit-content; margin: 0 0 .75rem auto; }
  main { padding: 20px 16px; } figure svg { min-width: 600px; } }
@media print { main { max-width: none; padding: 0; } .theme-toolbar { display: none; } }
"""


def filter_attribute(tag: str, name: str, value: str) -> str | None:
    # SVG paint references may point only to definitions inside this document.
    if tag in SVG_TAGS and name in {"fill", "stroke", "marker-end", "marker-start"}:
        if "url" in value.lower() and not re.fullmatch(r"url\(#[\w.-]+\)", value):
            return None
    return value


def render(source: str, source_name: str, command: str) -> str:
    body = markdown.markdown(
        source,
        extensions=["tables", "fenced_code", "codehilite", "md_in_html", "sane_lists", "toc"],
        extension_configs={"codehilite": {"guess_lang": False, "linenums": False}},
    )
    attributes = {tag: set(values) for tag, values in nh3.ALLOWED_ATTRIBUTES.items()}
    attributes["*"] = {"id", "class", "role", "aria-label", "aria-labelledby", "aria-describedby"}
    attributes.update({tag: SVG_ATTRIBUTES for tag in SVG_TAGS})
    attributes["details"] = {"open"}
    # Inline SVG is the supported image format; no remote or file image loading.
    body = nh3.clean(
        body,
        tags=(nh3.ALLOWED_TAGS - {"img"}) | SVG_TAGS | {"details", "summary", "figure", "figcaption"},
        attributes=attributes,
        attribute_filter=filter_attribute,
        url_schemes={"http", "https", "mailto"},
    )
    # Decorate sanitized headings; code examples remain escaped and untouched.
    body = re.sub(
        r"(<(?:h2|h3|summary)\b[^>]*>)(.*?)(</(?:h2|h3|summary)>)",
        lambda match: match[1] + ICONS[{
            "evidence": "search", "handoff": "clipboard-list",
        }.get(match[2].strip().casefold(), "file-text")] + match[2] + match[3],
        body,
        flags=re.DOTALL,
    )
    light_code = HtmlFormatter(style="default").get_style_defs(".codehilite")
    dark_override = HtmlFormatter(style="github-dark").get_style_defs(':root:has(#theme-dark:checked) .codehilite')
    system_dark = HtmlFormatter(style="github-dark").get_style_defs(':root:not(:has(#theme-light:checked)) .codehilite')
    heading = re.search(r"^#\s+(.+)$", source, re.MULTILINE)
    title = heading[1] if heading else Path(source_name).stem
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{html.escape(title)}</title><style>{CSS}
{light_code}
@media (prefers-color-scheme: dark) {{ {system_dark} }}
{dark_override}
</style><!-- {html.escape(LUCIDE_LICENSE)} --></head>
<body><main>
<div class="theme-toolbar">
<fieldset class="theme-picker"><legend>Theme</legend>
<label title="Light"><input type="radio" name="theme" id="theme-light" aria-label="Light">{ICONS["sun"]}</label>
<label title="System"><input type="radio" name="theme" id="theme-system" aria-label="System" checked>{ICONS["monitor"]}</label>
<label title="Dark"><input type="radio" name="theme" id="theme-dark" aria-label="Dark">{ICONS["moon"]}</label>
</fieldset></div>
{body}
<footer>Generated from <a href="{quote(source_name)}">{html.escape(source_name)}</a>.
Edit the Markdown and rebuild:<pre><code>{html.escape(command)}</code></pre></footer>
</main></body></html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Markdown report; writes a sibling .html file")
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    if source.suffix.lower() != ".md":
        parser.error("source must be a .md file")
    destination = source.with_suffix(".html")
    package = distribution("rmkr-triage-render")
    origin = json.loads(package.read_text("direct_url.json") or "{}")
    location = origin.get("url", "rmkr-triage-render==" + package.version)
    if location.startswith("file:"):
        location = unquote(urlsplit(location).path)
    command = shlex.join(["uvx", "--from", location, "triage-render", str(source)])
    temporary = None
    try:
        output = render(source.read_text(encoding="utf-8"), source.name, command)
        if destination.is_symlink():
            raise ValueError("refusing to replace an output symlink")
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=source.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(output)
        os.replace(temporary, destination)
    except (OSError, UnicodeError, ValueError) as error:
        parser.exit(1, f"triage-render: {error}\n")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(destination)


if __name__ == "__main__":
    main()
