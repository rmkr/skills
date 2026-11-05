from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class PluginTests(unittest.TestCase):
    def test_plugin_tracks_collection_version_and_skill_root(self) -> None:
        manifest = json.loads((REPO_ROOT / "plugin.json").read_text())
        project = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
        self.assertEqual(manifest["name"], "rmkr")
        self.assertEqual(manifest["version"], project["project"]["version"])
        self.assertEqual(
            manifest["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        catalog = json.loads(
            (REPO_ROOT / ".agents/plugins/marketplace.json").read_text()
        )
        self.assertEqual(catalog["name"], "rmkr-skills")
        self.assertEqual(len(catalog["plugins"]), 1)
        plugin = catalog["plugins"][0]
        self.assertEqual(plugin["name"], manifest["name"])
        self.assertEqual(plugin["source"], {"source": "local", "path": "./"})
        self.assertEqual(plugin["policy"]["installation"], "AVAILABLE")
        self.assertTrue((REPO_ROOT / plugin["source"]["path"] / "skills").is_dir())

    def test_claude_plugin_shares_metadata_and_skill_root(self) -> None:
        manifest = json.loads((REPO_ROOT / ".claude-plugin/plugin.json").read_text())
        shared = json.loads((REPO_ROOT / "plugin.json").read_text())
        for field in ("name", "version", "description", "repository", "license"):
            with self.subTest(field=field):
                self.assertEqual(manifest[field], shared[field])
        self.assertNotIn("$schema", manifest)
        self.assertNotIn("skills", manifest)
        self.assertEqual(manifest["agents"], [])

        catalog = json.loads(
            (REPO_ROOT / ".claude-plugin/marketplace.json").read_text()
        )
        self.assertEqual(catalog["name"], "rmkr-skills")
        self.assertEqual(catalog["owner"]["name"], manifest["author"]["name"])
        self.assertEqual(
            catalog["plugins"], [{"name": manifest["name"], "source": "./"}]
        )
        plugin_root = REPO_ROOT / catalog["plugins"][0]["source"]
        self.assertTrue((plugin_root / "skills").is_dir())


if __name__ == "__main__":
    unittest.main()
