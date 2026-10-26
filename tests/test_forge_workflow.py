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
const run = new Function('args', 'agent', 'parallel', 'log', 'phase', 'budget', `return (async () => {${body}\n})()`)
const calls = []
let snaps = 0
async function agent(prompt, opts) {
  const ids = opts.schema?.properties?.verdicts?.items?.properties?.id?.enum || []
  calls.push({ label: opts.label, model: opts.model || null, ids, prompt, schema: opts.schema, agentType: opts.agentType || null })
  if (opts.label === scenario.throw_at) { left = 0; throw new Error('budget spent') }
  if (opts.label === scenario.error_at) { left = 100; throw new Error('schema rejected') }
  const [kind, n] = opts.label.split(':')
  if (['snapshot', 'recheck', 'after-review'].includes(kind)) {
    const fp = (scenario.fingerprints || [])[snaps++]
    return fp === null ? null : { fingerprint: fp || 'fp' }
  }
  if (kind === 'review') return (scenario.reviews || [])[Number(n) - 1] || { findings: [], open_questions: [], coverage_gaps: [] }
  if (kind === 'verify') {
    if (Object.hasOwn(scenario.verifier_responses || {}, opts.label)) return scenario.verifier_responses[opts.label]
    return { verdicts: ids.map(id => ({ id, disposition: (scenario.verdicts || {})[id] || 'accepted', reason: `checked ${id}` })) }
  }
  if (kind === 'complexity') return { findings: [], open_questions: [], coverage_gaps: [] }
  if (kind === 'fix') return { changed: ['a.py'], checks: [], notes: '' }
}
const parallel = thunks => Promise.all(thunks.map(t => t().catch(() => null)))
let left = scenario.budget_remaining
const budget = { total: left === undefined ? null : 1e6, remaining: () => left }
run(scenario.args, agent, parallel, () => {}, () => {}, budget)
  .then(result => console.log(JSON.stringify({ result, calls })))
"""

TIERS = [
    {"name": "apprentice", "model": "haiku"},
    {"name": "technician", "model": "sonnet"},
    {"name": "engineer", "model": "opus"},
    {"name": "architect", "model": "opus", "effort": "high"},
]


def finding(repeats: str = "", tier: str = "technician", group: str = "") -> dict:
    return {
        "kind": "delivery", "severity": "major", "ref": "a.py:1", "trigger": "t",
        "impact": "i", "correction": "c", "repeats": repeats, "tier": tier,
        "verification_group": group,
    }


def review(*findings: dict) -> dict:
    return {"findings": list(findings), "open_questions": [], "coverage_gaps": []}


@unittest.skipUnless(shutil.which("node"), "node is required to run the workflow script")
class ForgeWorkflowTests(unittest.TestCase):
    def run_workflow(self, args: dict, **scenario) -> tuple[dict, list[dict]]:
        base = {"brief": "b", "target": "t", "snapshot": "sha256sum t", "tiers": TIERS}
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

    def test_failed_fix_escalates_then_stalls(self) -> None:
        result, calls = self.run_workflow(
            {"level": "fix"},
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

    def test_unresolved_finding_blocks_a_later_clean_round(self) -> None:
        result, _ = self.run_workflow(
            {"level": "fix"}, reviews=[review(finding(), finding())], verdicts={"R1-2": "unresolved"}
        )
        self.assertEqual(result["status"], "unresolved")

    def test_settled_repeat_clears_an_unresolved_finding(self) -> None:
        result, _ = self.run_workflow(
            {"level": "fix"},
            reviews=[review(finding(), finding()), review(finding("R1-2"))],
            verdicts={"R1-2": "unresolved"},
        )
        self.assertEqual(result["status"], "clean")

    def test_settled_repeat_chain_clears_an_unresolved_finding(self) -> None:
        result, _ = self.run_workflow(
            {"level": "fix"},
            reviews=[
                review(finding(), finding()),
                review(finding("R1-2"), finding()),
                review(finding("R2-1")),
            ],
            verdicts={"R1-2": "unresolved", "R2-1": "unresolved"},
        )
        self.assertEqual((result["status"], result["rounds"]), ("clean", 4))

    def test_real_error_under_budget_is_not_a_budget_stop(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_workflow({"level": "fix"}, budget_remaining=1e6, error_at="review:1")

    def test_strict_change_keeps_the_unverified_findings(self) -> None:
        result, _ = self.run_workflow(
            {"level": "fix", "strict": True}, reviews=[review(finding())], fingerprints=["fp", "other"]
        )
        self.assertEqual(result["status"], "changed")
        self.assertEqual([f["disposition"] for f in result["ledger"]], ["unresolved"])

    def test_budget_spent_mid_round_returns_the_ledger(self) -> None:
        result, _ = self.run_workflow(
            {"level": "fix"}, reviews=[review(finding())], budget_remaining=1e6, throw_at="fix:1"
        )
        self.assertEqual(result["status"], "budget")
        self.assertEqual(len(result["ledger"]), 1)

    def test_split_repeat_counts_once_per_round(self) -> None:
        result, calls = self.run_workflow(
            {"level": "fix"},
            reviews=[review(finding()), review(finding("R1-1"), finding("R1-1"))],
        )
        self.assertEqual(result["status"], "clean")
        self.assertEqual(sum(c["label"].startswith("fix") for c in calls), 2)

    def test_failed_recheck_is_not_a_change(self) -> None:
        result, _ = self.run_workflow({"level": "review"}, fingerprints=["fp", None])
        self.assertEqual(result["status"], "snapshot-failed")

    def test_spent_budget_returns_the_ledger(self) -> None:
        result, _ = self.run_workflow({"level": "fix"}, budget_remaining=0)
        self.assertEqual((result["status"], result["ledger"]), ("budget", []))

    def test_related_findings_share_inspection_and_keep_individual_verdicts(self) -> None:
        result, calls = self.run_workflow(
            {"level": "review"},
            reviews=[review(finding(group="parser"), finding(group="parser"))],
            verifier_responses={"verify:R1-1": {"verdicts": [
                {"id": "R1-2", "disposition": "rejected", "reason": "guard handles this input"},
                {"id": "R1-1", "disposition": "accepted", "reason": "reproduced empty input failure"},
            ]}},
        )
        verifiers = [c for c in calls if c["label"].startswith("verify:")]
        self.assertEqual([c["ids"] for c in verifiers], [["R1-1", "R1-2"]])
        self.assertEqual([f["disposition"] for f in result["ledger"]], ["accepted", "rejected"])
        self.assertEqual(result["ledger"][0]["reason"], "reproduced empty input failure")

    def test_shared_context_keeps_different_tiers_separate(self) -> None:
        _, calls = self.run_workflow(
            {"level": "review"},
            reviews=[review(finding(group="parser"), finding(tier="engineer", group="parser"))],
        )
        verifiers = [c for c in calls if c["label"].startswith("verify:")]
        self.assertEqual([c["model"] for c in verifiers], ["sonnet", "opus"])
        self.assertEqual([c["ids"] for c in verifiers], [["R1-1"], ["R1-2"]])

    def test_unrelated_findings_stay_separate(self) -> None:
        for groups in (("", ""), ("parser", "storage"), ("R1-2", "")):
            with self.subTest(groups=groups):
                _, calls = self.run_workflow(
                    {"level": "review"}, reviews=[review(*(finding(group=g) for g in groups))],
                )
                self.assertEqual(sum(c["label"].startswith("verify:") for c in calls), 2)

    def test_missing_duplicate_and_invalid_verdicts_remain_unresolved(self) -> None:
        valid = {"id": "R1-1", "disposition": "accepted", "reason": "reproduced"}
        for response in (
            {"verdicts": [valid]},
            {"verdicts": [valid, {**valid, "id": "unknown"}]},
            {"verdicts": [valid, {**valid, "id": "R1-2", "disposition": "clean"}]},
            {"verdicts": [valid, {**valid, "id": "R1-2", "reason": ""}]},
            {"verdicts": [valid, {**valid, "id": "R1-2"}, {**valid, "id": "R1-2"}]},
        ):
            with self.subTest(response=response):
                result, _ = self.run_workflow(
                    {"level": "fix"},
                    reviews=[review(finding(group="parser"), finding(group="parser"))],
                    verifier_responses={"verify:R1-1": response},
                )
                self.assertEqual(result["status"], "unresolved")
                self.assertEqual([f["id"] for f in result["ledger"]], ["R1-1", "R1-2"])
                self.assertEqual([f["disposition"] for f in result["ledger"]], ["accepted", "unresolved"])

    def test_failed_verifier_leaves_its_whole_group_unresolved(self) -> None:
        result, _ = self.run_workflow(
            {"level": "fix"}, reviews=[review(finding(group="parser"), finding(group="parser"))],
            verifier_responses={"verify:R1-1": None},
        )
        self.assertEqual(result["status"], "unresolved")
        self.assertEqual([f["disposition"] for f in result["ledger"]], ["unresolved", "unresolved"])

    def test_clean_review_needs_no_verifier_and_strict_keeps_its_reviewer(self) -> None:
        result, calls = self.run_workflow({"level": "review", "strict": True})
        self.assertEqual(result["status"], "clean")
        self.assertFalse(any(c["label"].startswith("verify:") for c in calls))
        self.assertEqual(next(c["agentType"] for c in calls if c["label"] == "review:1"), "forge-strict-reviewer")

    def test_reusable_verifier_cases_preserve_all_outcomes_with_fewer_calls(self) -> None:
        fixture = json.loads((Path(__file__).parent / "fixtures/skill-evals.json").read_text())
        cases = fixture["cases"]
        verdicts = {f"R1-{i}": case["expected"]["disposition"] for i, case in enumerate(cases, 1)}
        grouped, calls = self.run_workflow(
            {"level": "review"}, reviews=[review(*(case["finding"] for case in cases))], verdicts=verdicts,
        )
        ungrouped, baseline_calls = self.run_workflow(
            {"level": "review"},
            reviews=[review(*({**case["finding"], "verification_group": ""} for case in cases))],
            verdicts=verdicts,
        )
        expected = [case["expected"]["disposition"] for case in cases]
        self.assertEqual([f["disposition"] for f in grouped["ledger"]], expected)
        self.assertEqual([f["disposition"] for f in ungrouped["ledger"]], expected)
        self.assertEqual(sum(c["label"].startswith("verify:") for c in calls), 5)
        self.assertEqual(sum(c["label"].startswith("verify:") for c in baseline_calls), 10)

    def test_missing_brief_is_rejected(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError):
            self.run_workflow({"level": "fix", "brief": ""})


if __name__ == "__main__":
    unittest.main()
