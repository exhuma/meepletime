#!/usr/bin/env python3
"""Bump the project version across both package manifests.

MeepleTime keeps its version in two ecosystem-native forms that must
stay in lockstep:

- ``frontend/package.json`` — semver (e.g. ``2026.6.15-alpha.3``)
- ``backend/pyproject.toml`` — PEP440 (e.g. ``2026.6.15a3``)

The base is calendar versioning (``YYYY.M.D``, no zero-padding). A
qualifier selects the release channel and its pre-release suffix:

- ``alpha`` -> ``-alpha.N`` / ``aN``
- ``beta``  -> ``-beta.N``  / ``bN``
- ``stable`` -> no suffix (final release)

The counter ``N`` continues only while the calver base and channel are
unchanged; a new day or a channel change resets it to ``1`` (so
``alpha.3`` becomes ``beta.1``).

After writing both files the script commits them and creates a
``vX`` git tag (it does not push). Pushing the tag with
``git push --follow-tags`` is what triggers the CI image build.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_JSON = REPO_ROOT / "frontend" / "package.json"
PYPROJECT_TOML = REPO_ROOT / "backend" / "pyproject.toml"

# Channel -> PEP440 pre-release marker. ``stable`` has no marker.
PEP440_MARKER = {"alpha": "a", "beta": "b"}

SEMVER_RE = re.compile(
    r"^(\d+\.\d+\.\d+)(?:-(alpha|beta)\.(\d+))?$",
)


def calver_base(today: date) -> str:
    """Return today's calver base ``YYYY.M.D`` without zero-padding."""
    return f"{today.year}.{today.month}.{today.day}"


def read_current_semver() -> str:
    """Read the semver string currently in ``package.json``."""
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    return str(data["version"])


def compute_versions(
    qualifier: str, today: date, current_semver: str
) -> tuple[str, str]:
    """Return the new ``(semver, pep440)`` pair for *qualifier*."""
    base = calver_base(today)

    if qualifier == "stable":
        return base, base

    match = SEMVER_RE.match(current_semver)
    cur_base = match.group(1) if match else None
    cur_channel = match.group(2) if match else None
    cur_n = int(match.group(3)) if match and match.group(3) else 0

    if cur_base == base and cur_channel == qualifier:
        n = cur_n + 1
    else:
        n = 1

    semver = f"{base}-{qualifier}.{n}"
    pep440 = f"{base}{PEP440_MARKER[qualifier]}{n}"
    return semver, pep440


def write_package_json(semver: str) -> None:
    """Rewrite ``package.json`` with *semver*, preserving formatting."""
    data = json.loads(PACKAGE_JSON.read_text(encoding="utf-8"))
    data["version"] = semver
    PACKAGE_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_pyproject_toml(pep440: str) -> None:
    """Rewrite the project ``version`` line in ``pyproject.toml``."""
    text = PYPROJECT_TOML.read_text(encoding="utf-8")
    new_text, count = re.subn(
        r'(?m)^version = "[^"]*"',
        f'version = "{pep440}"',
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit(
            f"could not find a 'version = \"...\"' line in "
            f"{PYPROJECT_TOML}"
        )
    PYPROJECT_TOML.write_text(new_text, encoding="utf-8")


def git(*args: str) -> None:
    """Run a git command rooted at the repository, raising on error."""
    subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        check=True,
    )


def commit_and_tag(semver: str) -> str:
    """Commit the two manifests and create a ``vX`` tag (no push)."""
    tag = f"v{semver}"
    git(
        "add",
        "frontend/package.json",
        "backend/pyproject.toml",
    )
    git("commit", "-m", f"Bump version to {semver}")
    git("tag", tag)
    return tag


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bump the version in both package manifests.",
    )
    parser.add_argument(
        "qualifier",
        choices=("alpha", "beta", "stable"),
        help="release channel for the new version",
    )
    args = parser.parse_args(argv)

    semver, pep440 = compute_versions(
        args.qualifier, date.today(), read_current_semver()
    )

    write_package_json(semver)
    write_pyproject_toml(pep440)
    tag = commit_and_tag(semver)

    print(f"Bumped to {semver} (pyproject: {pep440})")
    print(f"Created tag {tag}")
    print("Run 'git push --follow-tags' to trigger the CI build.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
