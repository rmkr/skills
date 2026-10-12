from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills/forge/workflows/forge.js"

# Runs the workflow body with scripted agents; prints {result, calls}.
HARNESS = r"""
const fs = require('fs')
const [scriptPath, scenarioJson] = process.argv.slice(1)
const scenario = JSON.parse(scenarioJson)
const body = fs.readFileSync(scriptPath, 'utf8').replace(/^export const meta/m, 'const meta')
const run = new Function('args', 'agent', 'parallel', 'log', 'phase', `return (async () => {${body}\n})()`)
const calls = []
let snaps = 0
async function agent(prompt, opts) {
  calls.push({ label: opts.label, model: opts.model || null })
  const [kind, n] = opts.label.split(':')
  if (kind === 'snapshot' || kind === 'recheck') return { fingerprint: (scenario.fingerprints || [])[snaps++] || 'fp' }
  if (kind === 'review') return scenario.reviews[Number(n) - 1] || { findings: [], open_questions: [], coverage_gaps: [] }
  if (kind === 'verify') return { disposition: (scenario.verdicts || {})[n] || 'accepted', reason: 'checked' }
  if (kind === 'complexity') return { findings: [], open_questions: [], coverage_gaps: [] }
  if (kind === 'fix') return { changed: ['a.py'], checks: [], notes: '' }
}
const parallel = thunks => Promise.all(thunks.map(t => t().catch(() => null)))
run(scenario.args, agent, parallel, () => {}, () => {})
  .then(result => console.log(JSON.stringify({ result, calls })))
"""

TIERS = [
    {"name": "apprentice", "model": "haiku"},
    {"name": "technician", "model": "sonnet"},
    {"name": "engineer", "model": "opus"},
    {"name": "architect", "model": "opus", "effort": "high"},
]


def finding(repeats: str = "", tier: str = "technician") -> dict:
    return {
        "kind": "delivery", "severity": "major", "ref": "a.py:1", "trigger": "t",
        "impact": "i", "correction": "c", "repeats": repeats, "tier": tier,
    }


def review(*findings: dict) -> dict:
    return {"findings": list(findings), "open_questions": [], "coverage_gaps": []}


@unittest.skipUnless(shutil.which("node"), "node is required to run the workflow script")
class ForgeWorkflowTests(unittest.TestCase):
    def run_workflow(self, args: dict, **scenario) -> tuple[dict, list[dict]]:
        base = {"brief": "b", "target": "t", "snapshot": "git diff | sha256sum"}
        payload = json.dumps({"args": {**base, **args}, **scenario})
        out = subprocess.run(
            ["node", "-e", HARNESS, str(SCRIPT), payload],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(out.stdout)
        return data["result"], data["calls"]

    def test_review_reports_without_fixing(self) -> None:
        result, calls = self.run_workflow({"level": "review"}, reviews=[review(finding())])
        self.assertEqual(result["status"], "findings")
        self.assertFalse(any(c["label"].startswith("fix") for c in calls))

    def test_fix_loops_until_clean_review(self) -> None:
        result, _ = self.run_workflow({"level": "fix"}, reviews=[review(finding())])
        self.assertEqual((result["status"], result["rounds"]), ("clean", 2))

    def test_dynamic_escalates_then_stalls(self) -> None:
        result, calls = self.run_workflow(
            {"level": "fix", "dynamic": True, "tiers": TIERS},
            reviews=[review(finding()), review(finding("R1-1")), review(finding("R2-1"))],
        )
        fixers = [c["model"] for c in calls if c["label"].startswith("fix")]
        self.assertEqual(fixers, ["sonnet", "opus"])
        self.assertEqual(result["status"], "stalled")
        self.assertEqual(len(result["escalations"]), 1)

    def test_changed_target_stops_the_loop(self) -> None:
        result, _ = self.run_workflow(
            {"level": "fix"}, reviews=[review(finding())], fingerprints=["one", "two"]
        )
        self.assertEqual(result["status"], "changed")

    def test_missing_brief_is_rejected(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_workflow({"level": "fix", "brief": ""})


if __name__ == "__main__":
    unittest.main()
