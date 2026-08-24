#!/usr/bin/env python3
"""Re-run a single mutant and report whether it is now killed.

Usage:
  verify-mutant.py <mutant_name>

Run after adding/strengthening a test, to confirm the mutant is detected. Only
the named mutant is re-tested (fast), then its fresh status is read back from
its .meta file.

Outputs JSON to stdout:
  {"key": "...", "status": "killed", "exit_code": 1, "killed": true}

Exit code:
  0  mutant is now killed (or no-longer-survived)
  1  mutant still survives / has no tests   (non-zero so a loop can branch on it)
  2  usage / lookup error
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import ACTIONABLE_STATUSES
from utils import emit
from utils import find_backend_root
from utils import iter_mutant_records
from utils import run_mutmut

EXPECTED_ARG_COUNT = 2


def main() -> None:
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        _ = sys.stderr.write("Usage: verify-mutant.py <mutant_name>\n")
        sys.exit(2)

    key = sys.argv[1]
    backend_root = find_backend_root()

    result = run_mutmut(["run", key], backend_root, timeout=600)
    if not (backend_root / "mutants").is_dir():
        _ = sys.stderr.write("mutants/ vanished during re-run.\n" + (result.stdout + result.stderr)[-2000:])
        sys.exit(2)

    record = next((r for r in iter_mutant_records(backend_root) if r["key"] == key), None)
    if record is None:
        _ = sys.stderr.write(f"Mutant {key!r} not found after re-run.\n")
        sys.exit(2)

    killed = record["status"] not in ACTIONABLE_STATUSES
    emit(
        {
            "key": key,
            "status": record["status"],
            "exit_code": record["exit_code"],
            "killed": killed,
        }
    )
    sys.exit(0 if killed else 1)


if __name__ == "__main__":
    main()

# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
