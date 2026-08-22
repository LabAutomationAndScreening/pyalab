#!/usr/bin/env python3
"""Produce a structured, self-contained briefing for one mutant.

Usage:
  show-mutant.py <mutant_name>

Outputs JSON to stdout — everything needed to understand and kill the mutant:
  {
    "key": "<mutant_name>",
    "status": "survived",
    "source_file": "src/backend_api/entrypoint/parser.py",
    "line": 42,
    "diff": "<unified diff: original -> mutated>",
    "tests_for_mutant": ["tests/unit/...::test_x", ...]
  }

The diff comes from `mutmut show` (original vs. this mutant). tests_for_mutant
lists the tests that currently execute the mutated line — the place to add or
strengthen an assertion so the mutant is detected.

Reads cached state — run run-mutmut.py first.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import emit
from utils import find_backend_root
from utils import iter_mutant_records
from utils import locate_changed_line
from utils import run_mutmut

EXPECTED_ARG_COUNT = 2


def main() -> None:
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        _ = sys.stderr.write("Usage: show-mutant.py <mutant_name>\n")
        sys.exit(2)

    key = sys.argv[1]
    backend_root = find_backend_root()

    record = next((r for r in iter_mutant_records(backend_root) if r["key"] == key), None)
    if record is None:
        _ = sys.stderr.write(f"Mutant {key!r} not found in mutants/*.meta. Did you run run-mutmut.py?\n")
        sys.exit(1)

    show = run_mutmut(["show", key], backend_root, timeout=120)
    if show.returncode != 0:
        _ = sys.stderr.write(f"`mutmut show {key}` failed:\n{show.stderr}\n")
        sys.exit(1)

    tests_result = run_mutmut(["tests-for-mutant", key], backend_root, timeout=120)
    tests = [line.strip() for line in tests_result.stdout.splitlines() if "::" in line]

    diff = show.stdout.rstrip("\n")
    try:
        source_text = (backend_root / record["source_file"]).read_text(encoding="utf-8")
    except OSError as exc:
        _ = sys.stderr.write(f"Cannot read source file {backend_root / record['source_file']}: {exc}\n")
        sys.exit(1)
    changed_line = locate_changed_line(diff=diff, source_text=source_text)
    line_number = changed_line or None

    emit(
        {
            "key": key,
            "status": record["status"],
            "source_file": record["source_file"],
            "line": line_number,
            "diff": diff,
            "tests_for_mutant": tests,
        }
    )


if __name__ == "__main__":
    main()

# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
