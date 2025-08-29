#!/usr/bin/env python3
"""
Rollback script for YouTube Disappeared Video Tracker on Fly.io
Usage: python scripts/rollback.py [--version VERSION] [--list-releases]
"""

import argparse
import json
import subprocess
import sys
from typing import Dict, List, Optional


def run_command(cmd: List[str]) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_app_releases() -> List[Dict]:
    """Get list of app releases from Fly.io."""
    code, stdout, stderr = run_command(
        ["flyctl", "releases", "--app", "youtube-tracker", "--json"]
    )

    if code != 0:
        print(f"Error getting releases: {stderr}")
        return []

    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        print("Error parsing releases JSON")
        return []


def list_releases() -> None:
    """List available releases."""
    releases = get_app_releases()

    if not releases:
        print("No releases found")
        return

    print("Available releases:")
    print(
        "Version".ljust(15) + "Status".ljust(12) + "Created".ljust(25) + "Description"
    )
    print("-" * 80)

    for release in releases[:10]:
        version = release.get("version", "unknown")
        status = release.get("status", "unknown")
        created = release.get("created_at", "unknown")[:19].replace("T", " ")
        description = release.get("description", "")[:30]

        print(
            f"{str(version).ljust(15)}{status.ljust(12)}"
            f"{created.ljust(25)}{description}"
        )


def rollback_to_version(version: Optional[str] = None) -> bool:
    """Rollback to specified version or previous version."""
    releases = get_app_releases()

    if not releases:
        print("No releases found")
        return False

    if version:
        target_version = version
    else:
        if len(releases) < 2:
            print("No previous version available for rollback")
            return False
        target_version = str(releases[1]["version"])

    print(f"Rolling back to version {target_version}...")

    code, stdout, stderr = run_command(
        [
            "flyctl",
            "releases",
            "rollback",
            "--app",
            "youtube-tracker",
            "--version",
            target_version,
        ]
    )

    if code != 0:
        print(f"Rollback failed: {stderr}")
        return False

    print(f"Successfully rolled back to version {target_version}")
    print("Checking deployment status...")

    code, stdout, stderr = run_command(["flyctl", "status", "--app", "youtube-tracker"])
    if code == 0:
        print("Deployment status:")
        print(stdout)

    return True


def main():
    parser = argparse.ArgumentParser(description="Rollback YouTube Tracker deployment")
    parser.add_argument("--version", help="Specific version to rollback to")
    parser.add_argument(
        "--list-releases", action="store_true", help="List available releases"
    )

    args = parser.parse_args()

    if args.list_releases:
        list_releases()
        return

    if not rollback_to_version(args.version):
        sys.exit(1)


if __name__ == "__main__":
    main()
