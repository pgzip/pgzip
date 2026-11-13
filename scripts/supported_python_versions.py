# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomlkit",
# ]
# ///
"""Discover currently supported (non-EOL) and pre-release Python versions for CI."""

import argparse
import datetime
import json
import re
import sys
import tomllib
import urllib.request

EOL_API_URL = "https://endoflife.date/api/python.json"
MANIFEST_URL = "https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json"


def parse_version(version: str) -> tuple[int, ...]:
    """Parse a 'major.minor' string into an integer tuple for comparison."""
    return tuple(int(part) for part in version.split("."))


def get_min_python_version(pyproject_path: str = "pyproject.toml") -> tuple[int, ...]:
    """Read the minimum Python version from pyproject.toml's requires-python."""
    with open(pyproject_path, "rb") as f:
        requires_python = tomllib.load(f).get("project", {}).get("requires-python", "")
    match = re.search(r">=\s*(\d+\.\d+)", requires_python)
    if match:
        return parse_version(match.group(1))
    return (3, 10)


def fetch_supported_versions(min_version: tuple[int, ...]) -> list[str]:
    """Fetch active, non-EOL Python minor versions from endoflife.date."""
    today = datetime.date.today().isoformat()
    req = urllib.request.Request(EOL_API_URL, headers={"User-Agent": "pgzip-ci"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        cycles = json.loads(resp.read().decode("utf-8"))

    versions: list[str] = []
    for entry in cycles:
        cycle = entry.get("cycle", "")
        if not re.fullmatch(r"\d+\.\d+", cycle):
            continue
        release_date = entry.get("releaseDate")
        if isinstance(release_date, str) and release_date > today:
            continue
        eol = entry.get("eol")
        is_supported = eol is False or (isinstance(eol, str) and eol >= today)
        if is_supported and parse_version(cycle) >= min_version:
            versions.append(cycle)

    versions.sort(key=parse_version)
    if not versions:
        raise RuntimeError(f"No supported Python versions found from {EOL_API_URL}")
    return versions


def fetch_prerelease_versions(min_exclusive: tuple[int, ...]) -> list[str]:
    """Fetch pre-release major.minor versions newer than min_exclusive from setup-python's manifest."""
    req = urllib.request.Request(MANIFEST_URL, headers={"User-Agent": "pgzip-ci"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        entries = json.loads(resp.read().decode("utf-8"))

    prereleases: set[str] = set()
    for entry in entries:
        if entry.get("stable", True):
            continue
        match = re.match(r"^(\d+\.\d+)\.\d+-", entry.get("version", ""))
        if not match:
            continue
        minor_version = match.group(1)
        if parse_version(minor_version) > min_exclusive:
            prereleases.add(minor_version)

    return sorted(prereleases, key=parse_version)


def update_pyproject(
    versions: list[str], pyproject_path: str = "pyproject.toml"
) -> bool:
    """Update [[tool.hatch.envs.all.matrix]] python list in pyproject.toml."""
    import tomlkit

    with open(pyproject_path, "r", encoding="utf-8") as f:
        doc = tomlkit.parse(f.read())

    matrix = doc["tool"]["hatch"]["envs"]["all"]["matrix"]
    if not matrix:
        raise RuntimeError(
            f"Could not find [[tool.hatch.envs.all.matrix]] in {pyproject_path}"
        )

    entry = matrix[0]
    if list(entry.get("python", [])) == versions:
        return False

    arr = tomlkit.array()
    arr.extend(versions)
    entry["python"] = arr

    with open(pyproject_path, "w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(doc))
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover currently supported and pre-release Python versions."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output discovered versions as JSON to stdout.",
    )
    parser.add_argument(
        "--update-pyproject",
        action="store_true",
        help="Update [[tool.hatch.envs.all.matrix]] in pyproject.toml with supported stable versions.",
    )
    args = parser.parse_args()

    min_version = get_min_python_version()
    stable_versions = fetch_supported_versions(min_version)
    latest_stable = stable_versions[-1]
    prerelease_versions = fetch_prerelease_versions(parse_version(latest_stable))

    if args.update_pyproject:
        changed = update_pyproject(stable_versions)
        status = "Updated" if changed else "Already up to date:"
        stream = sys.stderr if args.json else sys.stdout
        print(
            f"{status} tool.hatch.envs.all.matrix in pyproject.toml -> {stable_versions}",
            file=stream,
        )

    if args.json:
        print(
            json.dumps(
                {
                    "supported": stable_versions,
                    "prerelease": prerelease_versions,
                    "latest_stable": latest_stable,
                }
            )
        )
    else:
        print(f"Supported Python versions: {stable_versions}")
        print(f"Pre-release Python versions: {prerelease_versions}")
        print(f"Latest stable Python version: {latest_stable}")


if __name__ == "__main__":
    main()
