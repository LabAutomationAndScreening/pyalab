#!/usr/bin/env python3
"""Ensure the AI attribution footer is present in a reply file.

Usage: check-footer.py <file>

Checks whether the footer is already in the file. If missing, appends it
with a blank line separator. Prints "present" or "added" to stdout.
"""

import sys
from pathlib import Path

EXPECTED_ARG_COUNT = 2

FOOTER = "*Reply drafted by AI (Claude), reviewed and approved by the author before posting.*"


def main() -> None:
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        _ = sys.stderr.write(f"Usage: {sys.argv[0]} <file>\n")
        sys.exit(1)

    path = Path(sys.argv[1])
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as e:
        _ = sys.stderr.write(f"File error for {path}: {e}\n")
        sys.exit(1)

    non_empty_lines = [line.strip() for line in content.splitlines() if line.strip()]
    if non_empty_lines and non_empty_lines[-1] == FOOTER:
        _ = sys.stdout.write("present\n")
        return

    # Ensure a blank line before the footer, then append.
    suffix = "\n" if content.endswith("\n") else "\n\n"
    try:
        _ = path.write_text(content + suffix + FOOTER + "\n", encoding="utf-8")
    except OSError as e:
        _ = sys.stderr.write(f"File error for {path}: {e}\n")
        sys.exit(1)
    _ = sys.stdout.write("added\n")


if __name__ == "__main__":
    main()
