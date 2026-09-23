#!/usr/bin/env python3
"""Choose skill collections to install for your coding agents."""
from __future__ import annotations

import argparse
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import questionary

# Common skills CLI agent IDs; --target also accepts other upstream agent IDs.
TARGETS = {
    "codex": "Codex",
    "claude-code": "Claude Code",
    "cursor": "Cursor",
    "github-copilot": "GitHub Copilot",
    "gemini-cli": "Gemini CLI",
    "opencode": "OpenCode",
    "windsurf": "Windsurf",
    "cline": "Cline",
    "roo": "Roo Code",
    "amp": "Amp",
    "goose": "Goose",
    "pi": "Pi",
    "continue": "Continue",
}
COMMANDS = {
    "codex": "codex", "claude-code": "claude", "cursor": "cursor",
    "github-copilot": "copilot", "gemini-cli": "gemini", "opencode": "opencode",
    "windsurf": "windsurf", "amp": "amp", "goose": "goose", "pi": "pi",
}
MAC_APPS = {
    "codex": "Codex.app", "cursor": "Cursor.app",
    "windsurf": "Windsurf.app",
}
EXTENSIONS = {
    "github-copilot": "github.copilot", "cline": "saoudrizwan.claude-dev",
    "roo": "rooveterinaryinc.roo-cline", "continue": "continue.continue",
}
MANIFEST = Path(__file__).resolve().parent / "preferred-skills.json"


def installed_targets() -> list[str]:
    home = Path.home()
    extension_roots = [
        home / editor / "extensions"
        for editor in (".vscode", ".vscode-insiders", ".cursor", ".windsurf")
    ]
    return [name for name in TARGETS if (
        (name in COMMANDS and shutil.which(COMMANDS[name]))
        or (sys.platform == "darwin" and name in MAC_APPS and any(
            (root / MAC_APPS[name] / "Contents" / "MacOS").is_dir()
            for root in (Path("/Applications"), home / "Applications")
        ))
        or (name in EXTENSIONS and any(
            manifest.is_file()
            for root in extension_roots
            for manifest in root.glob(f"{EXTENSIONS[name]}-*/package.json")
        ))
    )]


def read_manifest(path: Path) -> list[dict]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        raise ValueError("preferred skills must be a nonempty list")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("each preference must be an object")
        if set(entry) - {"skills"} != {"id", "repository"}:
            raise ValueError("preferences support only id, repository, and optional skills")
        if "skills" in entry and (
            not isinstance(entry["skills"], list) or not entry["skills"] or any(
                not isinstance(s, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", s)
                for s in entry["skills"]
            )
        ):
            raise ValueError("skills must contain explicit skill names")
        name, repo = entry["id"], entry["repository"]
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name):
            raise ValueError("invalid preference id")
        if not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-][A-Za-z0-9_.-]*", repo):
            raise ValueError("repository must be a GitHub owner/repo")
        if name in seen:
            raise ValueError(f"duplicate preference: {name}")
        seen.add(name)
    return entries


def multiselect(message: str, choices: list[questionary.Choice]) -> list[str]:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError("interactive selection requires a terminal; supply --item and --target")
    return questionary.checkbox(
        message, choices=choices,
        instruction="(↑/↓ move, Space toggle, a select all, Enter continue, Ctrl+C cancel)",
    ).ask() or []


def choose(entries: list[dict], requested: list[str] | None) -> list[dict]:
    if requested is None:
        requested = multiselect("What would you like to install?", [
            questionary.Choice(e["id"], value=e["id"])
            for e in entries
        ])
    if "all" in requested:
        requested = [e["id"] for e in entries] + [r for r in requested if r != "all"]
    unknown = set(requested) - {e["id"] for e in entries}
    if unknown:
        raise ValueError(f"unknown preferences: {', '.join(sorted(unknown))}")
    return [e for e in entries if e["id"] in requested]


def choose_targets(requested: list[str] | None) -> list[str]:
    available = installed_targets() if requested is None or "all" in requested else []
    if not available and (requested is None or requested == ["all"]):
        print("No installed agents detected; use --target AGENT_ID for a custom installation.")
        return []
    if requested is None:
        requested = multiselect("Which agents should receive them?", [
            questionary.Choice(TARGETS[name], value=name) for name in available
        ])
    if "all" in requested:
        requested = available + [t for t in requested if t != "all"]
    targets = list(dict.fromkeys("claude-code" if t == "claude" else t for t in requested))
    if any(not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", t) for t in targets):
        raise ValueError("invalid agent ID")
    return targets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", action="append", help="Explicit agent ID (bypasses detection); repeat, or all for detected agents.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--item", action="append", help="Preference ID; repeat to select more, or all.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without installing.")
    args = parser.parse_args(argv)
    executing = False
    try:
        entries = choose(read_manifest(args.manifest), args.item)
        if not entries:
            print("Nothing selected.")
            return 0
        targets = choose_targets(args.target)
        if not targets:
            print("No agents selected.")
            return 0
        if not args.dry_run and not shutil.which("bunx"):
            raise ValueError("bunx is not on PATH; install Bun first")
        commands = []
        for entry in entries:
            command = ["bunx", "skills", "add", entry["repository"], "--global", "--agent", *targets]
            if "skills" in entry:
                command += ["--skill", *entry["skills"]]
            commands.append(command)
        for command in commands:
            print(shlex.join(command), flush=True)
            if not args.dry_run:
                executing = True
                subprocess.run(command, check=True)
        return 0
    except (EOFError, OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        print("Earlier commands may have completed; rerun after resolving the error." if executing else "No installation changes made.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
