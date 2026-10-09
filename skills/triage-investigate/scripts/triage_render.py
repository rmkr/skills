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
from xml.etree import ElementTree as etree

import markdown
from markdown.treeprocessors import Treeprocessor
from markdown.util import HTML_PLACEHOLDER, HTML_PLACEHOLDER_RE
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
LIGHT = """--ground: #eceef0; --panel: #ffffff; --ink: #15181b; --ink2: #353b41;
  --muted: #4f575e; --rule: #dadee2; --line: #15181b; --accent: #1f4e79; --open: #9a4a00;"""
DARK = """--ground: #12161c; --panel: #1b222b; --ink: #e4e7eb; --ink2: #c3cad1;
  --muted: #a3adb7; --rule: #2c3540; --line: #a3adb7; --accent: #8cc2ff; --open: #f2a65e;"""
CSS = f"""
:root {{ color-scheme: light dark; {LIGHT}
  --serif: Charter, 'Bitstream Charter', 'Iowan Old Style', 'Sitka Text', Cambria, serif;
  --sans: system-ui, -apple-system, 'Segoe UI', sans-serif;
  --mono: ui-monospace, 'SF Mono', Menlo, Consolas, monospace;
  --hl: color-mix(in srgb, var(--open) 16%, var(--panel)); }}
@media (prefers-color-scheme: dark) {{ :root:not(:has(#theme-light:checked)) {{ {DARK} }} }}
:root:has(#theme-light:checked) {{ color-scheme: light; {LIGHT} }}
:root:has(#theme-dark:checked) {{ color-scheme: dark; {DARK} }}
""" + r"""
* { box-sizing: border-box; }
body { margin: 0; background: var(--ground); color: var(--ink); font: 17px/1.6 var(--serif); }
.page { max-width: 1180px; margin: auto; padding: 36px 24px 72px; overflow-wrap: anywhere; }
a { color: var(--accent); text-underline-offset: 3px; }
a:focus-visible, summary:focus-visible { outline: 3px solid var(--accent); outline-offset: 3px; }
.topbar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
  gap: 12px; font: 12px/1.4 var(--sans); letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.masthead { padding: 14px 0 20px; border-bottom: 3px double var(--line); }
h1 { margin: 0; font-size: clamp(1.7rem, 4.5vw, 2.6rem); line-height: 1.12; letter-spacing: -.01em; max-width: 30ch; }
.layout { display: flex; flex-wrap: wrap; gap: 40px; align-items: flex-start; margin-top: 28px; }
.case { flex: 1 1 240px; min-width: 0; display: flex; flex-direction: column; gap: 24px; font: 14px/1.45 var(--sans); }
.main { flex: 999 1 600px; min-width: 0; }
.panel { background: var(--panel); border: 1px solid var(--line); }
.case .label { margin: 0; padding: 10px 0 6px; font: 700 11px/1.4 var(--sans); letter-spacing: .14em; text-transform: uppercase; }
.panel .label { padding: 8px 12px; background: var(--ink); color: var(--panel); }
.facts { margin: 0; display: grid; grid-template-columns: minmax(84px, max-content) minmax(0, 1fr); }
.facts dt, .facts dd { margin: 0; padding: 8px 12px; border-top: 1px solid var(--rule); }
.facts dt:first-of-type, .facts dd:first-of-type { border-top: 0; }
.facts dt { color: var(--muted); font-size: 12px; letter-spacing: .06em; text-transform: uppercase; }
.facts dd { padding-left: 0; }
.case nav, .case .key { border-top: 1px solid var(--line); }
.case ol { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }
.case nav a { text-decoration: none; }
.case nav a:hover { text-decoration: underline; }
.sec-no { font-family: var(--mono); color: var(--muted); }
.case .sec-no { display: inline-block; min-width: 2.4em; }
.key { display: grid; gap: 6px; font-size: 13px; color: var(--muted); }
.key span::before { content: ""; display: inline-block; width: 28px; margin-right: 8px; vertical-align: middle;
  border-top: 2px solid var(--line); }
.key .k-inferred::before { border-top-style: dashed; border-color: var(--accent); }
.key .k-unknown::before { border-top-style: dotted; border-color: var(--open); }
.source { margin: 0; padding-top: 10px; border-top: 1px solid var(--rule); font-size: 12px; color: var(--muted); }
.tag { display: inline-block; padding: 0 6px; border: 1px solid currentColor; font: 700 11px/1.6 var(--sans);
  letter-spacing: .1em; text-transform: uppercase; font-style: normal; text-decoration: none; }
.tag.open { border-style: dashed; color: var(--open); }
.section { margin-bottom: 40px; }
h2 { margin: 0 0 14px; padding-bottom: 6px; border-bottom: 1px solid var(--line); font: 700 14px/1.4 var(--sans);
  letter-spacing: .12em; text-transform: lowercase; font-variant: small-caps; }
h2 .sec-no { margin-right: 12px; font-size: 14px; letter-spacing: 0; font-variant: normal; }
.lead > h2 + p { font-size: 19px; line-height: 1.55; }
h3, h4 { margin: 1.4em 0 .4em; font: 700 15px/1.4 var(--sans); }
p, ul, ol, dl { margin: 0 0 1em; }
li { margin-bottom: .35em; }
ul.evidence { list-style: none; padding: 0; }
.ev { margin-bottom: 12px; padding: 2px 0 2px 14px; border-left: 2px solid var(--line); }
.ev .tag { margin-right: 6px; }
.ev-inferred { border-left-style: dashed; border-color: var(--accent); font-style: italic; }
.ev-inferred .tag { border-style: dashed; color: var(--accent); }
.ev-unknown { border-left-style: dotted; border-color: var(--open); }
.ev-unknown .tag { border-style: dotted; color: var(--open); }
blockquote { margin: 0 0 1em; padding-left: 1rem; border-left: 3px solid var(--rule); color: var(--ink2); }
blockquote.next { padding: 16px 20px; background: var(--panel); border: 2px solid var(--accent);
  color: var(--ink); font-size: 20px; line-height: 1.45; }
blockquote.next > :last-child { margin-bottom: 0; }
.next-label { display: block; margin-bottom: 4px; color: var(--accent); font: 700 12px/1.4 var(--sans);
  letter-spacing: .1em; text-transform: uppercase; }
.exhibit { margin: 0 0 24px; background: var(--panel); border: 1px solid var(--line); }
.exhibit-head { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 16px; padding: 8px 14px;
  border-bottom: 1px solid var(--line); }
.exhibit-head h3 { margin: 0; font: 700 12px/1.5 var(--sans); letter-spacing: .1em; text-transform: uppercase; }
.exhibit-head .tag { margin-left: auto; }
.exhibit > :not(figcaption) { margin: 14px 16px; }
.exhibit > .codehilite { margin: 0; border: 0; }
.exhibit.inferred, .exhibit.inferred .exhibit-head { border-style: dashed; border-color: var(--accent); }
.exhibit.inferred .tag { border-style: dashed; color: var(--accent); }
.tl-key { display: flex; flex-wrap: wrap; gap: 4px 14px; margin: 0 0 8px; font: 12px/1.5 var(--sans); color: var(--muted); }
.tl-basis { margin-right: auto; font-weight: 700; color: var(--ink); }
.tl-key [class^=k-]::before { content: ""; display: inline-block; width: 10px; height: 10px; margin-right: 6px;
  border-radius: 50%; vertical-align: -1px; background: var(--ink); }
.tl-key .k-inferred::before { background: var(--panel); border: 2px solid var(--accent); }
.tl-key .k-gap::before { width: 0; height: 13px; border-radius: 0; background: none; border-left: 2px dashed var(--open); }
ol.timeline { list-style: none; margin: 0 0 1em; padding: 18px 16px 18px 8px; background: var(--panel);
  border: 1px solid var(--line); font: 15px/1.45 var(--sans); }
ol.timeline li { display: grid; grid-template-columns: 7.5em 20px minmax(0, 1fr); gap: 0 12px; margin: 0; }
.tl-time { padding-top: 1px; text-align: right; font: 13px/1.6 var(--mono); color: var(--muted); font-variant-numeric: tabular-nums; }
.tl-mark { display: flex; flex-direction: column; align-items: center; }
.tl-mark::before { content: ""; flex: none; width: 11px; height: 11px; margin-top: 5px; border-radius: 50%; background: var(--ink); }
.tl-mark::after { content: ""; flex: 1; border-left: 1px solid var(--line); }
ol.timeline li:last-child .tl-mark::after { display: none; }
.tl-body { padding-bottom: 20px; }
ol.timeline li:last-child .tl-body { padding-bottom: 0; }
.tl-event { font-weight: 600; }
.tl-source { font: 12px/1.6 var(--mono); color: var(--muted); }
.tl-inferred .tl-time, .tl-inferred .tl-event { color: var(--accent); }
.tl-inferred .tl-event { font-family: var(--serif); font-style: italic; }
.tl-inferred .tl-mark::before { background: var(--panel); border: 2px solid var(--accent); }
.tl-inferred .tl-mark::after { border-left-style: dashed; border-color: var(--accent); }
.tl-gap .tl-time, .tl-gap .tl-event { color: var(--open); }
.tl-gap .tl-mark::before { display: none; }
ol.timeline li.tl-gap .tl-mark::after { display: block; min-height: 64px; border-left: 2px dashed var(--open); }
table { display: block; max-width: 100%; overflow-x: auto; margin: 0 0 1em; border-collapse: collapse;
  background: var(--panel); font: 15px/1.45 var(--sans); }
th, td { padding: 8px 12px; border: 1px solid var(--rule); text-align: left; vertical-align: top; }
th { font-size: 12px; letter-spacing: .06em; text-transform: uppercase; color: var(--muted); }
.status-supported .tag { border-width: 2px; color: var(--accent); }
.status-unresolved .tag { border-style: dashed; color: var(--open); }
.status-contradicted { color: var(--muted); }
.status-contradicted td:not(.status) { text-decoration: line-through; }
ol.handoff { padding-left: 1.6em; }
ol.handoff li { margin-bottom: 10px; }
ol.handoff li::marker { font: 700 14px var(--mono); color: var(--muted); }
pre { margin: 0; padding: 14px 16px; overflow-x: auto; font: 13px/1.7 var(--mono); }
code { font-family: var(--mono); font-size: .88em; }
pre code { font-size: inherit; }
.codehilite { margin: 0 0 1em; border: 1px solid var(--rule); }
.codehilite .hll { display: block; position: relative; outline: 1px solid var(--open); background: var(--hl) !important; }
.codehilite .hll::before { content: "\25B6"; position: absolute; left: -1.5em; color: var(--open); font-weight: 700; }
.codehilite pre:has(.hll) { padding-left: 2.5em; }
details { margin: 0 0 1em; padding: 10px 14px; background: var(--panel); border: 1px solid var(--rule); }
summary { cursor: pointer; font: 700 13px/1.5 var(--sans); letter-spacing: .04em; }
details[open] > summary { margin-bottom: 10px; }
figure { margin: 0 0 1em; overflow-x: auto; }
svg { display: block; width: 100%; height: auto; color: var(--ink); }
svg:not([fill]) { fill: currentColor; }
svg text { font-family: var(--sans); }
figcaption, footer { color: var(--muted); font: 13px/1.5 var(--sans); }
footer { margin-top: 40px; padding-top: 12px; border-top: 1px solid var(--rule); }
footer pre { margin-top: 6px; background: var(--panel); border: 1px solid var(--rule); }
.theme-picker { position: relative; display: flex; margin: 0; padding: 2px; min-inline-size: 0;
  border: 1px solid var(--line); background: var(--panel); }
.theme-picker::before { content: ""; position: absolute; left: 2px; top: 2px; width: 28px; height: 28px;
  background: var(--ink); transform: translateX(28px); }
.theme-picker:has(#theme-light:checked)::before { transform: translateX(0); }
.theme-picker:has(#theme-dark:checked)::before { transform: translateX(56px); }
.theme-picker label { position: relative; display: grid; place-items: center; width: 28px; height: 28px;
  cursor: pointer; color: var(--muted); }
.theme-picker label:has(input:checked) { color: var(--panel); }
.theme-picker label:has(input:focus-visible) { outline: 2px solid var(--accent); outline-offset: 3px; }
.theme-picker legend, .theme-picker input { position: absolute; width: 1px; height: 1px;
  padding: 0; margin: -1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
svg.lucide { display: inline-block; width: 15px; height: 15px; color: inherit; }
@media (forced-colors: active) {
  .theme-picker label:has(input:checked) { outline: 2px solid Highlight; outline-offset: -3px; }
  .theme-picker label:has(input:focus-visible) { outline: 2px dashed Highlight; outline-offset: 2px; }
}
@media (prefers-reduced-motion: no-preference) {
  .theme-picker::before { transition: transform .3s ease, background-color .5s ease; }
  body, body * { transition: background-color .5s ease, color .5s ease, border-color .5s ease, fill .5s ease, stroke .5s ease; }
}
@media (max-width: 600px) {
  .page { padding: 20px 16px 48px; }
  .layout { gap: 28px; }
  ol.timeline { padding: 14px 10px 14px 4px; }
  ol.timeline li { grid-template-columns: 5.6em 14px minmax(0, 1fr); gap: 0 8px; }
  figure svg { min-width: 600px; }
}
@media print {
  .page { max-width: none; padding: 0; }
  .theme-picker { display: none; }
  .exhibit, ol.timeline li, blockquote.next, .panel, details, .codehilite, tr { break-inside: avoid; }
  details::details-content { content-visibility: visible; height: auto; }
}
"""
EVIDENCE = {"observed:": "observed", "supported explanation:": "inferred", "inferred:": "inferred",
            "unresolved:": "unknown", "unknown:": "unknown"}
NOT_FACTS = re.compile(r"(observed|supported explanation|inferred|unresolved|unknown|reproduce|inspect|resolve|verify|next)\b", re.I)
OPEN = re.compile(r"(no|low|unknown|unresolved|proposed|not yet)\b", re.I)
STATUSES = {"supported", "contradicted", "unresolved"}
EXHIBIT_HEADING = re.compile(r"Exhibit ([A-Z])\b[\s:.–—-]*(.*?)\s*(?:\(((?i:observed|inferred))\))?\s*$")
EXHIBIT_REF = re.compile(r"\b(Exhibit ([A-Z]))\b")
RAW_TAG = re.compile(r"<(/?)([a-zA-Z][\w-]*)[^>]*?(/?)>\s*$")
VOID = {"br", "hr", "wbr", "img", "input", "col", "area", "source", "embed", "meta", "link"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def text(element) -> str:
    """Plain text of an element, without stashed raw-HTML placeholders."""
    return HTML_PLACEHOLDER_RE.sub("", "".join(element.itertext())).strip()


def sub(parent, tag: str, content: str | None = None, **attributes):
    child = etree.SubElement(parent, tag, {key.rstrip("_").replace("_", "-"): value for key, value in attributes.items()})
    child.text = content
    return child


def add_class(element, name: str) -> None:
    element.set("class", f"{element.get('class', '')} {name}".strip())


def wrap(element, tag: str, name: str):
    """Move an element's content into a new child wrapper."""
    wrapper = etree.Element(tag, {"class": name})
    wrapper.text, wrapper[:] = element.text, list(element)
    element.text, element[:] = None, [wrapper]
    return wrapper


def lead(element):
    """Return the leading <strong> label of a list item or blockquote, if any."""
    if len(element) and element[0].tag == "p" and not (element.text or "").strip():
        element = element[0]
    if len(element) and element[0].tag == "strong" and not (element.text or "").strip():
        return element[0]
    return None


class Dossier(Treeprocessor):
    """Arrange the parsed report into the case-file layout using the Markdown conventions."""

    def __init__(self, md, source_name: str):
        super().__init__(md)
        self.source_name = source_name

    def run(self, root):
        nodes = list(root)
        for node in nodes:
            root.remove(node)
        self.marked, self.exhibits, self.depth = False, {}, 0
        while nodes and self.is_comment(nodes[0]):
            root.append(nodes.pop(0))
        header = facts = None
        if nodes and nodes[0].tag == "h1":
            header = etree.Element("header", {"class": "masthead"})
            header.append(nodes.pop(0))
            labels = [lead(li) for li in nodes[0]] if nodes and nodes[0].tag == "ul" else []
            if labels and all(label is not None and text(label).endswith(":")
                              and not NOT_FACTS.match(text(label)) for label in labels):
                facts = self.facts(nodes.pop(0))
        nodes = self.group_exhibits(nodes)
        for details in [d for node in nodes for d in node.iter("details")]:
            details[:] = self.group_exhibits(list(details))
        main = etree.Element("div", {"class": "main", "role": "main"})
        sections = []
        current = main
        for node in nodes:
            if node.tag == "h2":
                number = len(sections) + 1
                current = sub(main, "div", class_="section lead" if number == 1 else "section",
                              role="region", aria_labelledby=node.get("id"))
                sections.append((current, node.get("id"), number, text(node)))
                marker = etree.Element("span", {"class": "sec-no"})
                marker.text, marker.tail, node.text = f"§{number}", node.text, None
                node.insert(0, marker)
            current.append(node)
        for section, _, _, title in sections:
            handoff = section.find("ul")
            if title.casefold().startswith("handoff") and handoff is not None:
                handoff.tag = "ol"
                add_class(handoff, "handoff")
        self.annotate(main)
        if self.exhibits:
            self.link(main)
        if header is not None:
            root.append(header)
        layout = sub(root, "div", class_="layout")
        layout.append(self.case_sheet(facts, sections))
        layout.append(main)

    def is_comment(self, node) -> bool:
        match = node.tag == "p" and not len(node) and HTML_PLACEHOLDER_RE.fullmatch((node.text or "").strip())
        raw = match and self.md.htmlStash.rawHtmlBlocks[int(match[1])]
        return isinstance(raw, str) and (not raw.strip() or raw.lstrip().startswith("<!--"))

    def group_exhibits(self, nodes):
        """Fold each `### Exhibit X` heading and the content up to the next heading into a figure."""
        grouped, figure = [], None
        for node in nodes:
            match = node.tag == "h3" and EXHIBIT_HEADING.match(text(node))
            if match and match[1].lower() not in self.exhibits:
                figure = self.exhibit(node, match)
                grouped.append(figure)
            elif figure is not None and node.tag not in HEADINGS:
                figure.append(node)
            else:
                figure = None
                grouped.append(node)
        return grouped

    def facts(self, items):
        sheet = etree.Element("dl", {"class": "facts"})
        for li in items:
            label = lead(li)
            container = li if len(li) and li[0] is label else li[0]
            key = text(label).rstrip(":").strip()
            sub(sheet, "dt", key)
            value = sub(sheet, "dd", (label.tail or "").lstrip())
            value.extend(list(container)[1:] + (list(li)[1:] if container is not li else []))
            if key.casefold() in {"reproduced", "confidence"}:
                wrap(value, "span", "tag open" if OPEN.match(text(value)) else "tag")
        return sheet

    def exhibit(self, heading, match):
        letter, kind = match[1].lower(), (match[3] or "").lower()
        self.exhibits[letter] = match[2] or f"Exhibit {match[1]}"
        figure = etree.Element("figure", {"id": f"exhibit-{letter}", "class": f"exhibit {kind}".strip()})
        caption = sub(figure, "figcaption", class_="exhibit-head")
        heading.attrib.pop("id", None)
        caption.append(heading)
        if kind:
            self.marked = True
            suffix = f"({match[3]})"
            holder = heading[-1] if len(heading) else None
            last = (holder.tail if holder is not None else heading.text) or ""
            if last.rstrip().endswith(suffix):
                last = last.rstrip()[:-len(suffix)].rstrip()
                if holder is not None:
                    holder.tail = last
                else:
                    heading.text = last
            else:  # the kind is wrapped in inline markup; fall back to the plain heading text
                heading.text = f"Exhibit {match[1]}" + (f": {match[2]}" if match[2] else "")
                heading[:] = []
            sub(caption, "span", kind.title(), class_="tag")
        return figure

    def annotate(self, main):
        parents = {child: parent for parent in main.iter() for child in parent}
        for li in main.iter("li"):
            label = lead(li)
            kind = label is not None and EVIDENCE.get(text(label).casefold())
            if kind:
                self.marked = True
                add_class(li, f"ev ev-{kind}")
                label.set("class", "tag")
                if "evidence" not in parents[li].get("class", ""):
                    add_class(parents[li], "evidence")
        for quote_ in main.iter("blockquote"):
            label = lead(quote_)
            if label is not None and text(label).casefold() == "next:":
                quote_.set("class", "next")
                label.set("class", "next-label")
        for table in list(main.iter("table")):
            heads = [text(th) for th in table.iter("th")]
            rows = [tr for tr in table.iter("tr") if tr.find("td") is not None]
            if heads and re.match(r"time\b", heads[0], re.I):
                self.marked = True
                parent = parents[table]
                index = list(parent).index(table)
                parent.remove(table)
                for offset, element in enumerate(self.timeline(heads[0], rows)):
                    parent.insert(index + offset, element)
            elif "status" in (lowered := [head.casefold() for head in heads]):
                column = lowered.index("status")
                for tr in rows:
                    cells = tr.findall("td")
                    if column < len(cells) and (status := text(cells[column]).casefold()) in STATUSES:
                        tr.set("class", f"status-{status}")
                        cells[column].set("class", "status")
                        wrap(cells[column], "span", "tag")

    def timeline(self, basis, rows):
        spine = etree.Element("ol", {"class": "timeline"})
        kinds = set()
        for tr in rows:
            cells = tr.findall("td")
            event = text(cells[1]) if len(cells) > 1 else ""
            kind = ("inferred" if event.startswith("Inferred:")
                    else "gap" if event.startswith(("Unknown:", "Gap:")) else "logged")
            kinds.add(kind)
            li = sub(spine, "li", class_=f"tl-{kind}")
            moved = []
            for index, cell in enumerate(cells):
                target = etree.Element("div", {"class": ("tl-time", "tl-event")[index] if index < 2 else "tl-source"})
                target.text, target[:] = cell.text, list(cell)
                moved.append(target)
            li.append(moved[0])
            sub(li, "span", class_="tl-mark")
            sub(li, "div", class_="tl-body").extend(moved[1:])
        key = etree.Element("p", {"class": "tl-key"})
        sub(key, "span", basis, class_="tl-basis")
        for kind, label in (("logged", "logged"), ("inferred", "inferred"), ("gap", "no data")):
            if kind in kinds:
                sub(key, "span", label, class_=f"k-{kind}")
        return [key, spine]

    def link(self, element):
        """Turn plain-text "Exhibit X" references into links, in document order.

        Inline raw HTML is stashed as one placeholder per tag; self.depth counts open raw
        tags so text inside author markup such as <code> or <a> is never linked.
        """
        if element.tag in {"code", "pre", "a"} or element.get("class") == "exhibit-head":
            return
        element.text, anchors = self.anchors(element.text)
        for offset, anchor in enumerate(anchors):
            element.insert(offset, anchor)
        for child in list(element):
            self.link(child)
            child.tail, anchors = self.anchors(child.tail)
            index = list(element).index(child)
            for offset, anchor in enumerate(anchors, 1):
                element.insert(index + offset, anchor)

    def anchors(self, value):
        lead_text, anchors = "", []

        def emit(piece):
            nonlocal lead_text
            if anchors:
                anchors[-1].tail += piece
            else:
                lead_text += piece

        for position, piece in enumerate(HTML_PLACEHOLDER_RE.split(value or "")):
            if position % 2:
                raw = self.md.htmlStash.rawHtmlBlocks[int(piece)]
                tag = isinstance(raw, str) and RAW_TAG.match(raw)
                if tag and not tag[3] and tag[2].lower() not in VOID:
                    self.depth = max(0, self.depth + (-1 if tag[1] else 1))
                emit(HTML_PLACEHOLDER % piece)
                continue
            if self.depth:
                emit(piece)
                continue
            parts = EXHIBIT_REF.split(piece)
            emit(parts[0])
            for index in range(1, len(parts), 3):
                phrase, letter, after = parts[index:index + 3]
                if letter.lower() in self.exhibits:
                    anchor = etree.Element("a", {"href": f"#exhibit-{letter.lower()}"})
                    anchor.text, anchor.tail = phrase, after
                    anchors.append(anchor)
                else:
                    emit(phrase + after)
        return lead_text, anchors

    def case_sheet(self, facts, sections):
        aside = etree.Element("aside", {"class": "case", "aria-label": "Case sheet"})
        if facts is not None:
            panel = sub(aside, "div", class_="panel")
            sub(panel, "p", "Case sheet", class_="label")
            panel.append(facts)
        if sections:
            nav = sub(aside, "nav", aria_label="Sections")
            sub(nav, "p", "Index", class_="label")
            items = sub(nav, "ol")
            for _, anchor_id, number, title in sections:
                link = sub(sub(items, "li"), "a", href=f"#{anchor_id}")
                sub(link, "span", f"§{number}", class_="sec-no").tail = title
        if self.exhibits:
            nav = sub(aside, "nav", aria_label="Exhibits")
            sub(nav, "p", "Exhibits", class_="label")
            items = sub(nav, "ol")
            for letter, title in sorted(self.exhibits.items()):
                link = sub(sub(items, "li"), "a", href=f"#exhibit-{letter}")
                sub(link, "strong", letter.upper()).tail = f" · {title}"
        if self.marked:
            key = sub(aside, "div", class_="key")
            sub(key, "p", "Key", class_="label")
            for kind, label in (("observed", "Observed"), ("inferred", "Inferred"), ("unknown", "Unknown / open")):
                sub(key, "span", label, class_=f"k-{kind}")
        source = sub(aside, "p", "Generated from ", class_="source")
        sub(source, "a", self.source_name, href=quote(self.source_name)).tail = "."
        return aside


def filter_attribute(tag: str, name: str, value: str) -> str | None:
    # SVG paint references may point only to definitions inside this document.
    if tag in SVG_TAGS and name in {"fill", "stroke", "marker-end", "marker-start"}:
        if "url" in value.lower() and not re.fullmatch(r"url\(#[\w.-]+\)", value):
            return None
    return value


def render(source: str, source_name: str, command: str) -> str:
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "md_in_html", "sane_lists", "toc"],
        extension_configs={"codehilite": {"guess_lang": False, "linenums": False}},
    )
    # After inline parsing (20) and toc ids (5); code is already stashed by then.
    md.treeprocessors.register(Dossier(md, source_name), "dossier", 4)
    body = md.convert(source)
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
<body><div class="page">
<div class="topbar"><span>Case file &middot; bug triage</span>
<fieldset class="theme-picker"><legend>Theme</legend>
<label title="Light"><input type="radio" name="theme" id="theme-light" aria-label="Light">{ICONS["sun"]}</label>
<label title="System"><input type="radio" name="theme" id="theme-system" aria-label="System" checked>{ICONS["monitor"]}</label>
<label title="Dark"><input type="radio" name="theme" id="theme-dark" aria-label="Dark">{ICONS["moon"]}</label>
</fieldset></div>
{body}
<footer>Edit the Markdown and rebuild:<pre><code>{html.escape(command)}</code></pre></footer>
</div></body></html>
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
