from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib

from _shared import default_repo_root


def github(*arguments: str, data: dict | None = None):
    command = ["gh", "api", *arguments]
    if data is not None:
        command.extend(["--input", "-"])
    result = subprocess.run(
        command,
        input=json.dumps(data) if data is not None else None,
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    if os.environ.get("GITHUB_REF") != "refs/heads/main" or os.environ.get(
        "GITHUB_EVENT_NAME"
    ) not in {"push", "workflow_dispatch"}:
        raise SystemExit("Release publication requires a main push or manual run.")

    version = tomllib.loads(
        (default_repo_root() / "pyproject.toml").read_text()
    )["project"]["version"]
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise SystemExit("The collection release version must have three numeric parts.")
    commit = os.environ["GITHUB_SHA"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit("GITHUB_SHA must identify the validated commit.")
    endpoint = f"repos/{os.environ['GITHUB_REPOSITORY']}"
    if github(f"{endpoint}/git/ref/heads/main")["object"]["sha"] != commit:
        print("Skipped release because main has advanced beyond this run.")
        return 0

    tag = f"v{version}"
    pages = github("--paginate", "--slurp", f"{endpoint}/releases?per_page=100")
    existing = next(
        (item for page in pages for item in page if item["tag_name"] == tag), None
    )
    if existing is not None and not existing["draft"]:
        print(f"Release {tag} is already published.")
        return 0

    for reference in github(f"{endpoint}/git/matching-refs/tags/{tag}"):
        if reference["ref"] != f"refs/tags/{tag}":
            continue
        target = reference["object"]
        while target["type"] == "tag":
            target = github(f"{endpoint}/git/tags/{target['sha']}")["object"]
        if target["type"] != "commit" or target["sha"] != commit:
            raise SystemExit(f"Refusing to move existing tag {tag} to another commit.")

    notes = github(
        "--method", "POST", f"{endpoint}/releases/generate-notes",
        data={"tag_name": tag, "target_commitish": commit},
    )
    data = {
        "tag_name": tag,
        "target_commitish": commit,
        "name": tag,
        "body": notes["body"],
        "draft": False,
        "prerelease": False,
        "make_latest": "true",
    }
    if existing is None:
        result = github("--method", "POST", f"{endpoint}/releases", data=data)
    else:
        result = github(
            "--method", "PATCH", f"{endpoint}/releases/{existing['id']}", data=data
        )
    print(result["html_url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
