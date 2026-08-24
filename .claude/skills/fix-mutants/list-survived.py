#!/usr/bin/env python3
"""List mutants that indicate a test gap, grouped by source file.

Usage:
  list-survived.py [--status survived,no-tests] [--all]

By default lists only actionable statuses (survived + no tests) — the mutants
a stronger test can kill. Pass --all to include every status (killed, timeout,
suspicious, ...) for a full picture.

Outputs JSON to stdout:
  {
    "backend_root": "/abs/path/to/folder/containing/pyproject.toml",
    "total_actionable": N,
    "by_file": {
      "src/backend_api/entrypoint/parser.py": [
        {"key": "...__mutmut_1", "status": "survived", "exit_code": 0}, ...
      ],
      ...
    }
  }

Reads cached mutants/*.meta — run run-mutmut.py first. Does not re-run anything.
"""

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import ACTIONABLE_STATUSES
from utils import emit
from utils import find_backend_root
from utils import iter_mutant_records


def parse_status_filter(argv: list[str]) -> set[str] | None:
    if "--all" in argv:
        return None
    for i, arg in enumerate(argv):
        if arg == "--status" and i + 1 < len(argv):
            return {s.strip().replace("-", " ") for s in argv[i + 1].split(",") if s.strip()}
    return set(ACTIONABLE_STATUSES)


def main() -> None:
    argv = sys.argv[1:]
    wanted = parse_status_filter(argv)
    backend_root = find_backend_root()

    records = iter_mutant_records(backend_root)
    by_file: dict[str, list[dict[str, object]]] = defaultdict(list)
    total = 0
    for record in records:
        if wanted is not None and record["status"] not in wanted:
            continue
        total += 1
        by_file[record["source_file"]].append(
            {"key": record["key"], "status": record["status"], "exit_code": record["exit_code"]}
        )

    emit(
        {
            "backend_root": str(backend_root),
            "total_actionable": total,
            "by_file": dict(sorted(by_file.items())),
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
