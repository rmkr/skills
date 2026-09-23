#!/usr/bin/env python3
"""Preview or install the shared GitButler prompt for Codex and Claude Code."""
from __future__ import annotations

import argparse
import difflib
import os
from pathlib import Path
import stat
import sys
import tempfile

START = "<!-- gitbutler-agent-setup:start -->"
END = "<!-- gitbutler-agent-setup:end -->"
SOURCE = Path(__file__).resolve().parents[1] / "prompts/gitbutler.md"
TARGETS = {"codex": ".codex/AGENTS.md", "claude": ".claude/rules/gitbutler.md"}


def merge_prompt(existing: str, prompt: str) -> str:
    if START not in existing and END not in existing:
        return existing + ("\n\n" if existing and not existing.endswith("\n") else "\n" if existing else "") + prompt
    if existing.count(START) != 1 or existing.count(END) != 1:
        raise ValueError("expected exactly one complete GitButler marker block")
    start, end = existing.index(START), existing.index(END)
    if end < start:
        raise ValueError("GitButler markers are reversed")
    return existing[:start] + prompt.rstrip("\n") + existing[end + len(END):]


def replace_file(path: Path, content: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=(*TARGETS, "all"), default="all")
    parser.add_argument("--home", type=Path, default=Path.home(), help="Override installation home for testing or another user directory.")
    parser.add_argument("--apply", action="store_true", help="Write changes; otherwise print a preview only.")
    args = parser.parse_args()
    planned = []
    written = []
    try:
        prompt = SOURCE.read_text(encoding="utf-8")
        if not prompt.startswith(START) or not prompt.rstrip().endswith(END):
            raise ValueError("source must contain only the marked prompt block")
        merge_prompt(prompt, prompt)  # Validate the source marker pair too.
        for target in TARGETS if args.target == "all" else (args.target,):
            path = args.home / TARGETS[target]
            if path.is_symlink():
                raise ValueError(f"refusing symlink destination: {path}")
            before = path.read_bytes() if path.exists() else None
            text = before.decode("utf-8") if before is not None else ""
            after = merge_prompt(text, prompt).encode("utf-8")
            mode = stat.S_IMODE(path.stat().st_mode) if before is not None else 0o600
            if before != after:
                planned.append((path, before, after, mode))
                print("".join(difflib.unified_diff(text.splitlines(keepends=True), after.decode().splitlines(keepends=True), fromfile=str(path), tofile=str(path))), end="")
        if not args.apply:
            print(f"Preview: {len(planned)} file(s) would change. Rerun with --apply to install.")
            return 0
        # Preflight every destination before writing any of them.
        for path, before, after, mode in planned:
            if path.is_symlink() or (path.read_bytes() if path.exists() else None) != before:
                raise ValueError(f"destination changed during preflight: {path}")
        for path, before, after, mode in planned:
            if path.is_symlink() or (path.read_bytes() if path.exists() else None) != before:
                raise ValueError(f"destination changed before replacement: {path}")
            replace_file(path, after, mode)
            written.append((path, before, after, mode))
        print(f"Installed: {len(planned)} file(s) changed.")
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        for path, before, after, mode in reversed(written):
            try:
                if path.is_symlink() or path.read_bytes() != after:
                    print(f"Preserved concurrently changed file during rollback: {path}", file=sys.stderr)
                elif before is None:
                    path.unlink()
                else:
                    replace_file(path, before, mode)
            except OSError as rollback_error:
                print(f"Rollback failed for {path}: {rollback_error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
