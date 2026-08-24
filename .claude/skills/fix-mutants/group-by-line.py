#!/usr/bin/env python3
"""Return the next unresolved line group for a source file.

Usage:
  group-by-line.py <source_file> [--skip-line N ...]

Always returns the full briefing for the LOWEST-numbered line that still has
actionable mutants (survived or no tests) and is not in --skip-line. Calling
this script repeatedly without resolving anything returns the same group — the
only way to advance is to kill the mutants (via verify-mutant.py, which updates
the meta) or mark the line skipped (via --skip-line).

When the user chooses to skip a line (equivalent mutant etc.), pass it as
--skip-line so the next call advances:

  group-by-line.py src/backend_api/mdns.py --skip-line 42

Multiple --skip-line flags are accepted for lines skipped in prior iterations.

Outputs to stdout, when a group remains:

  1. A pre-rendered, user-facing briefing block between
     `=== MUTANT BRIEFING — PASTE TO USER VERBATIM ===` and
     `=== END MUTANT BRIEFING ===` marker lines. It contains the absolute
     path:line, remaining-line count, original source, every mutant's diff,
     and the exercising tests as absolute paths. The agent driving the skill
     pastes this block to the user unchanged before doing anything else.
  2. A `---MACHINE-READABLE---` delimiter line.
  3. The JSON payload:
     {
       "backend_root": "/abs/path/to/folder/containing/pyproject.toml",
       "source_file": "src/backend_api/mdns.py",
       "line": 42,
       "remaining_lines": [42, 67],   # all still-unresolved lines (incl. this one)
       "tests_for_line": ["tests/unit/foo.py::test_x", ...],
       "mutants": [
         {"key": "...__mutmut_1", "status": "survived", "diff": "..."},
         ...
       ]
     }

When all groups are resolved, only the JSON is emitted:

  {
    "backend_root": "/abs/path/to/folder/containing/pyproject.toml",
    "source_file": "src/backend_api/mdns.py",
    "done": true
  }

Reads cached mutants/*.meta — run run-mutmut.py first. Calls mutmut show and
mutmut tests-for-mutant only for mutants on the returned line.
"""

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from utils import ACTIONABLE_STATUSES
from utils import emit
from utils import find_backend_root
from utils import iter_mutant_records
from utils import locate_changed_line
from utils import run_mutmut


def parse_args() -> tuple[str, set[int]]:
    argv = sys.argv[1:]
    if not argv:
        _ = sys.stderr.write("Usage: group-by-line.py <source_file> [--skip-line N ...]\n")
        sys.exit(2)

    source_file = argv[0]
    skip_lines: set[int] = set()

    i = 1
    while i < len(argv):
        if argv[i] == "--skip-line" and i + 1 < len(argv):
            skip_lines.add(int(argv[i + 1]))
            i += 2
        else:
            _ = sys.stderr.write(f"Unknown argument: {argv[i]!r}\n")
            sys.exit(2)

    return source_file, skip_lines


def extract_original_lines(diff: str) -> str:
    removed: list[str] = []
    for diff_line in diff.splitlines():
        if not diff_line.startswith("-"):
            continue
        if diff_line.startswith("---"):
            continue
        removed.append(diff_line[1:])
    return "\n".join(removed)


def render_briefing(
    *,
    location: str,
    remaining_count: int,
    tests: list[str],
    mutants: list[dict[str, str]],
) -> str:
    parts = [
        f"{location} — {len(mutants)} mutant(s)",
        f"({remaining_count} unresolved line(s) remaining in this file, incl. this one)",
        "",
        "Original code on this line:",
        "```python",
        extract_original_lines(mutants[0]["diff"]),
        "```",
    ]
    for index, mutant in enumerate(mutants, start=1):
        parts.extend(
            [
                "",
                f"Mutant {index} — {mutant['key']} (status: {mutant['status']}):",
                "```diff",
                mutant["diff"],
                "```",
            ]
        )
    parts.extend(["", "Currently exercised by:"])
    if tests:
        parts.extend(f"- {test}" for test in tests)
    else:
        parts.append("- no tests")
    return "\n".join(parts)


def main() -> None:
    target, skip_lines = parse_args()
    backend_root = find_backend_root()

    records = [
        r
        for r in iter_mutant_records(backend_root)
        if r["source_file"] == target and r["status"] in ACTIONABLE_STATUSES
    ]

    if not records:
        emit({"backend_root": str(backend_root), "source_file": target, "done": True})
        return

    try:
        source_text = (backend_root / target).read_text(encoding="utf-8")
    except OSError as exc:
        _ = sys.stderr.write(f"Cannot read source file {backend_root / target}: {exc}\n")
        sys.exit(1)

    # First pass: get line number for every record (requires mutmut show).
    keyed: list[tuple[int, dict[str, Any]]] = []
    for record in records:
        show = run_mutmut(["show", record["key"]], backend_root, timeout=120)
        if show.returncode != 0:
            _ = sys.stderr.write(f"`mutmut show {record['key']}` failed:\n{show.stderr}\n")
            sys.exit(1)
        line = locate_changed_line(diff=show.stdout, source_text=source_text)
        keyed.append((line, {"record": record, "diff": show.stdout.rstrip("\n")}))

    all_lines = sorted({line for line, _ in keyed if line not in skip_lines})

    if not all_lines:
        emit({"backend_root": str(backend_root), "source_file": target, "done": True})
        return

    target_line = all_lines[0]

    group_mutants: list[dict[str, str]] = []
    group_tests: set[str] = set()

    for line, data in keyed:
        if line != target_line:
            continue
        record = data["record"]
        diff = data["diff"]
        key = record["key"]

        tests_result = run_mutmut(["tests-for-mutant", key], backend_root, timeout=120)
        tests = [t.strip() for t in tests_result.stdout.splitlines() if "::" in t]

        group_mutants.append({"key": key, "status": record["status"], "diff": diff})
        group_tests.update(tests)

    sorted_tests = sorted(group_tests)
    briefing = render_briefing(
        location=f"{backend_root}/{target}:{target_line}",
        remaining_count=len(all_lines),
        tests=[f"{backend_root}/{test}" for test in sorted_tests],
        mutants=group_mutants,
    )
    _ = sys.stdout.write("=== MUTANT BRIEFING — PASTE TO USER VERBATIM ===\n")
    _ = sys.stdout.write(briefing + "\n")
    _ = sys.stdout.write("=== END MUTANT BRIEFING ===\n")
    _ = sys.stdout.write("---MACHINE-READABLE---\n")
    emit(
        {
            "backend_root": str(backend_root),
            "source_file": target,
            "line": target_line,
            "remaining_lines": all_lines,
            "tests_for_line": sorted_tests,
            "mutants": group_mutants,
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
