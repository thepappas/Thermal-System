#!/usr/bin/env python3
"""Check local Markdown links and balanced code fences."""

import pathlib
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = pathlib.Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^ )]+)(?:\s+[^)]*)?\)")


def main():
    errors = []
    for path in ROOT.rglob("*.md"):
        if any(part in {".git", "data", "node_modules", ".esphome"} for part in path.parts):
            continue
        fence = False
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("```"):
                fence = not fence
                continue
            if fence:
                continue
            for match in LINK.finditer(line):
                target = urlsplit(match.group(1))
                if target.scheme or target.netloc or not target.path:
                    continue
                resolved = (path.parent / unquote(target.path)).resolve()
                if not resolved.exists():
                    errors.append(f"{path.relative_to(ROOT)}:{number}: missing {match.group(1)}")
        if fence:
            errors.append(f"{path.relative_to(ROOT)}: unclosed code fence")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Local Markdown links and fences OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
