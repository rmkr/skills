from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release

REAL_GITHUB = release.github
COMMIT = "a" * 40
ENDPOINT = "repos/example/skills"
ENVIRONMENT = {
    "GITHUB_REF": "refs/heads/main",
    "GITHUB_EVENT_NAME": "push",
    "GITHUB_SHA": COMMIT,
    "GITHUB_REPOSITORY": "example/skills",
}


class ReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "pyproject.toml").write_text('[project]\nversion = "0.3.4"\n')
        self.enterContext(patch.dict(os.environ, ENVIRONMENT))
        self.enterContext(patch.object(release, "default_repo_root", return_value=self.root))
        self.api = self.enterContext(patch.object(release, "github"))
        self.output = self.enterContext(contextlib.redirect_stdout(io.StringIO()))

    def responses(self, pages: list, references: list | None = None) -> None:
        self.api.side_effect = [
            {"object": {"sha": COMMIT}}, pages,
            [] if references is None else references,
            {"body": "Generated notes"},
            {"html_url": "https://github.com/example/skills/releases/tag/v0.3.4"},
        ]

    def test_new_version_publishes_the_validated_commit(self) -> None:
        self.responses([[]])
        self.assertEqual(release.main(), 0)
        call = self.api.call_args
        self.assertEqual(call.args, ("--method", "POST", f"{ENDPOINT}/releases"))
        self.assertEqual(call.kwargs["data"]["target_commitish"], COMMIT)
        self.assertEqual(call.kwargs["data"]["tag_name"], "v0.3.4")
        self.assertEqual(call.kwargs["data"]["body"], "Generated notes")
        self.assertFalse(call.kwargs["data"]["draft"])

    def test_existing_draft_on_a_later_page_is_published(self) -> None:
        self.responses([[], [{"id": 42, "tag_name": "v0.3.4", "draft": True}]])
        self.assertEqual(release.main(), 0)
        self.assertEqual(
            self.api.call_args.args,
            ("--method", "PATCH", f"{ENDPOINT}/releases/42"),
        )
        self.assertEqual(self.api.call_args.kwargs["data"]["target_commitish"], COMMIT)

    def test_manual_main_run_can_retry_a_draft(self) -> None:
        self.responses([[{"id": 42, "tag_name": "v0.3.4", "draft": True}]])
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch"}):
            self.assertEqual(release.main(), 0)
        self.assertEqual(self.api.call_args.args[1], "PATCH")

    def test_published_version_is_preserved(self) -> None:
        self.responses([[{"id": 42, "tag_name": "v0.3.4", "draft": False}]])
        self.assertEqual(release.main(), 0)
        self.assertEqual(self.api.call_count, 2)

    def test_old_main_run_does_not_publish(self) -> None:
        self.api.return_value = {"object": {"sha": "b" * 40}}
        self.assertEqual(release.main(), 0)
        self.assertEqual(self.api.call_count, 1)

    def test_pull_requests_and_other_branches_cannot_publish(self) -> None:
        for changes in (
            {"GITHUB_EVENT_NAME": "pull_request"},
            {"GITHUB_REF": "refs/heads/feature"},
        ):
            with self.subTest(changes=changes), patch.dict(os.environ, changes):
                with self.assertRaises(SystemExit):
                    release.main()
        self.api.assert_not_called()

    def test_invalid_version_or_commit_stops_before_api_calls(self) -> None:
        with patch.dict(os.environ, {"GITHUB_SHA": "main"}):
            with self.assertRaises(SystemExit):
                release.main()
        (self.root / "pyproject.toml").write_text('[project]\nversion = "0.3.4rc1"\n')
        with self.assertRaises(SystemExit):
            release.main()
        self.api.assert_not_called()

    def test_existing_tag_on_another_commit_is_never_moved(self) -> None:
        self.responses([[]], [{
            "ref": "refs/tags/v0.3.4",
            "object": {"type": "commit", "sha": "b" * 40},
        }])
        with self.assertRaisesRegex(SystemExit, "Refusing to move"):
            release.main()
        self.assertEqual(self.api.call_count, 3)

    def test_matching_annotated_tag_can_be_released(self) -> None:
        self.api.side_effect = [
            {"object": {"sha": COMMIT}}, [[]],
            [{"ref": "refs/tags/v0.3.4", "object": {"type": "tag", "sha": "c" * 40}}],
            {"object": {"type": "commit", "sha": COMMIT}},
            {"body": "Generated notes"}, {"html_url": "release-url"},
        ]
        self.assertEqual(release.main(), 0)
        self.assertEqual(self.api.call_args.args[1], "POST")

    def test_api_failure_does_not_attempt_publication(self) -> None:
        self.api.side_effect = [
            {"object": {"sha": COMMIT}},
            subprocess.CalledProcessError(1, ["gh", "api"]),
        ]
        with self.assertRaises(subprocess.CalledProcessError):
            release.main()
        self.assertEqual(self.api.call_count, 2)

    def test_github_helper_passes_json_without_shell_expansion(self) -> None:
        with patch.object(release.subprocess, "run") as run:
            run.return_value.stdout = '{"id":42}'
            body = {"body": "A literal $value and two\nlines"}
            self.assertEqual(
                REAL_GITHUB("--method", "POST", f"{ENDPOINT}/releases", data=body),
                {"id": 42},
            )
        self.assertEqual(
            run.call_args.args[0],
            ["gh", "api", "--method", "POST", f"{ENDPOINT}/releases", "--input", "-"],
        )
        self.assertEqual(json.loads(run.call_args.kwargs["input"]), body)
        self.assertTrue(run.call_args.kwargs["check"])

if __name__ == "__main__":
    unittest.main()
