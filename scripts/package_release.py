#!/usr/bin/env python3
"""Build a versioned archive from a Git commit, without local deployment data."""

import argparse
import gzip
import hashlib
import re
import subprocess
from pathlib import Path


VERSION = re.compile(
    r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?\Z"
)


def valid_tag(tag):
    match = VERSION.fullmatch(tag)
    if not match:
        return False
    prerelease = match.group(4)
    return not prerelease or all(
        not (part.isdigit() and len(part) > 1 and part.startswith("0"))
        for part in prerelease.split(".")
    )


def package(tag, commit, output_dir):
    if not valid_tag(tag):
        raise ValueError(f"Not a v-prefixed semantic version: {tag}")
    resolved = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{commit}^{{commit}}"], text=True
    ).strip()
    if resolved != commit:
        raise ValueError("Commit must be a full Git commit ID")
    name = f"thermal-system-{tag}"
    archive = subprocess.check_output(
        ["git", "archive", "--format=tar", f"--prefix={name}/", resolved]
    )
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle = output_dir / f"{name}.tar.gz"
    bundle.write_bytes(gzip.compress(archive, mtime=0))
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    (output_dir / "SHA256SUMS").write_text(f"{digest}  {bundle.name}\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("commit", help="full commit ID to archive")
    parser.add_argument("output_dir")
    args = parser.parse_args()
    package(args.tag, args.commit, args.output_dir)


if __name__ == "__main__":
    main()
