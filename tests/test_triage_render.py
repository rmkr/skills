import contextlib
from html.parser import HTMLParser
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from triage_render import main, render


class Elements(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class TriageRenderTests(unittest.TestCase):
    def test_markdown_graph_and_safe_markup_survive_rebuild(self):
        source = '''# Boot delay

| Phase | Seconds |
| --- | --- |
| Compile | 2 |

[Evidence](logs/boot.txt#L4)

<details markdown="1">
<summary>Evidence</summary>

**Observed:** two seconds.

</details>

<figure>
<svg viewBox="0 0 600 100" role="img" aria-labelledby="graph-title">
<title id="graph-title">Compile duration</title>
<defs><pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse">
<rect width="5" height="5" fill="#176a80"/></pattern></defs>
<rect width="200" height="30" fill="url(#hatch)"/>
<text x="10" y="65">Compile: 2 seconds</text>
</svg>
<figcaption>See evidence above.</figcaption>
</figure>

```text
<script>quoted log text</script>
```

<script>alert('bad')</script>
<a href="javascript:alert(1)" onclick="alert(1)">unsafe link</a>
<img src="https://example.com/tracker">
<svg onload="alert(1)"><rect fill="url(https://example.com/x)"/></svg>
'''
        output = render(source, 'a & b.md')
        self.assertEqual(output, render(source, 'a & b.md'))
        tags = Elements(output).tags
        self.assertTrue({'table', 'details', 'summary', 'svg', 'figcaption', 'strong'} <= {t for t, _ in tags})
        self.assertIn(('svg', {'viewbox': '0 0 600 100', 'role': 'img', 'aria-labelledby': 'graph-title'}), tags)
        self.assertTrue(any(t == 'rect' and a.get('fill') == 'url(#hatch)' for t, a in tags))
        self.assertTrue(any(t == 'a' and a.get('href') == 'logs/boot.txt#L4' for t, a in tags))
        self.assertIn('a%20%26%20b.md', output)
        self.assertIn('&lt;script&gt;quoted log text&lt;/script&gt;', output)
        self.assertNotIn('<script>', output)
        self.assertNotIn("alert('bad')", output)
        for tag, attrs in tags:
            self.assertNotIn(tag, {'img', 'iframe', 'foreignobject'})
            self.assertFalse(any(key.startswith('on') for key in attrs))
            self.assertFalse(any('javascript:' in value or 'https://example.com' in value for value in attrs.values() if value is not None))

    def test_highlighting_icons_and_plain_text_fallback(self):
        source = """# [ISSUE-123](https://tickets.example/ISSUE-123): Investigation

## TL;DR
A short explanation with uncertainty.

## Evidence
```python
def check():
    return "<script>example</script>"
```

```unknown-language
<unsafe> & plain
```

```
def unchanged(): pass
```

<details markdown="1">
<summary>Handoff</summary>

Next check.

</details>
"""
        output = render(source, 'report.md')
        tags = Elements(output).tags
        self.assertTrue(any(t == 'span' and a.get('class') == 'k' for t, a in tags))
        self.assertIn('&lt;unsafe&gt; &amp; plain', output)
        self.assertIn('def unchanged(): pass', output)
        self.assertIn('A short explanation with uncertainty.', output)
        self.assertTrue(any(t == 'a' and a.get('href') == 'https://tickets.example/ISSUE-123' for t, a in tags))
        icons = [a for t, a in tags if t == 'svg' and a.get('class') == 'lucide']
        self.assertEqual(len(icons), 3)  # theme switch only; headings use section numbers
        self.assertTrue(all(a.get('aria-hidden') == 'true' and a.get('focusable') == 'false' for a in icons))
        radios = [a for t, a in tags if t == 'input' and a.get('type') == 'radio']
        self.assertEqual([a['aria-label'] for a in radios], ['Light', 'System', 'Dark'])
        self.assertEqual([a['id'] for a in radios if 'checked' in a], ['theme-system'])
        self.assertIn(':root:has(#theme-dark:checked) .codehilite', output)
        self.assertIn('Lucide Icons and Contributors', output)
        self.assertFalse(any(t == 'link' for t, _ in tags))
        self.assertNotIn('<script>', output)

    def test_case_file_conventions(self):
        source = """# Checkout 502s

- **Build:** 2.41.0
- **Reproduced:** No

## Finding
See Exhibit A; `Exhibit A` in code stays plain.
Raw <kbd>Exhibit A</kbd> and <a href="https://x.example">Exhibit A</a> stay plain too. Open <span>unclosed.

Later Exhibit A and Exhibit B still link.

> **Next:** Replay traffic.

| Timeout (ms) | Count |
| --- | --- |
| 30 | 2 |

## Timeline

| Time (UTC) | Event | Source |
| --- | --- | --- |
| 14:05 | Deploy | deploy.log |
| 14:06 | Inferred: pool cold | lb.log |
| 14:20 | Gap: no logs | app.log |

### Exhibit A: First failure (observed)

```text hl_lines="1"
ERROR reset
```

## Q&amp;A &lt;hypotheses&gt;

| Hypothesis | Status |
| --- | --- |
| DB lock | Contradicted |

<details markdown="1">
<summary>More</summary>

### Exhibit B: Config diff

body

</details>
"""
        output = render(source, 'r.md')
        tags = Elements(output).tags
        classes = [a.get('class') for _, a in tags]
        self.assertIn(('dt', {}), tags)
        self.assertIn('tag open', classes)
        self.assertIn(('a', {'href': '#finding', 'rel': 'noopener noreferrer'}), tags)
        self.assertIn('§2', output)
        self.assertIn('next', classes)
        self.assertEqual([c for c in classes if c and c.startswith('tl-') and c[3:] in {'logged', 'inferred', 'gap'}],
                         ['tl-logged', 'tl-inferred', 'tl-gap'])
        self.assertNotIn('<th>Time (UTC)</th>', output)
        self.assertIn(('figure', {'class': 'exhibit observed', 'id': 'exhibit-a'}), tags)
        # body text, the later paragraph past an unclosed raw <span>, and the index
        self.assertEqual(sum(1 for t, a in tags if t == 'a' and a.get('href') == '#exhibit-a'), 3)
        self.assertIn(('figure', {'class': 'exhibit', 'id': 'exhibit-b'}), tags)  # inside <details>
        self.assertEqual(sum(1 for t, a in tags if t == 'a' and a.get('href') == '#exhibit-b'), 2)
        self.assertIn('</span>Q&amp;A &lt;hypotheses&gt;</a>', output)  # entities kept in the index
        self.assertIn('<code>Exhibit A</code>', output)
        self.assertIn('<kbd>Exhibit A</kbd> and <a href="https://x.example" rel="noopener noreferrer">Exhibit A</a>', output)
        self.assertIn('<th>Timeout (ms)</th>', output)  # only a whole-word "Time" header makes a timeline
        self.assertIn('hll', classes)
        self.assertIn('status-contradicted', classes)

    def test_cli_preserves_source_and_rebuilds_sibling(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'report with spaces.md'
            source.write_text('# First\n\nEvidence.', encoding='utf-8')
            with patch('sys.argv', ['triage-render', str(source)]), contextlib.redirect_stdout(io.StringIO()):
                main()
            output = source.with_suffix('.html')
            self.assertIn('<h1 id="first">First</h1>', output.read_text())
            self.assertEqual(source.read_text(), '# First\n\nEvidence.')
            source.write_text('# Revised\n\nNew evidence.', encoding='utf-8')
            with patch('sys.argv', ['triage-render', str(source)]), contextlib.redirect_stdout(io.StringIO()):
                main()
            self.assertIn('New evidence.', output.read_text())
            self.assertNotIn('<h1 id="first">', output.read_text())
            output.unlink()
            output.symlink_to(source)
            with patch('sys.argv', ['triage-render', str(source)]), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main()
            self.assertEqual(source.read_text(), '# Revised\n\nNew evidence.')


if __name__ == '__main__':
    unittest.main()
