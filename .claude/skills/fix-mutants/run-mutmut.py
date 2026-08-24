#!/usr/bin/env python3
"""Run the full mutation suite, then report a status breakdown.

Usage:
  run-mutmut.py [--clean]

Options:
  --clean   Delete mutants/ before running, forcing a fresh mutant generation
            and a clean re-test of every mutant. Without it, mutmut reuses the
            cached mutants/ and only re-tests what changed.

Outputs JSON to stdout:
  {
    "generated": "<mutmut's 'done in ...' summary line, or null>",
    "counts": {"survived": N, "killed": N, ...},
    "total": N,
    "actionable": N        # survived + no tests
  }

A non-zero mutation result (surviving mutants) is NOT a script error — the
script exits 0 as long as mutmut ran. It exits 1 only on infrastructure
failure (mutmut crashed before producing meta files).
"""

import re
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import ACTIONABLE_STATUSES
from utils import emit
from utils import find_backend_root
from utils import iter_mutant_records
from utils import run_mutmut

GENERATION_SUMMARY_RE = re.compile(r"done in .*?\(.*?\)")
COMPLETION_RE = re.compile(r"\d+(?:\.\d+)? mutations/second")


def main() -> None:
    clean = "--clean" in sys.argv[1:]
    backend_root = find_backend_root()

    if clean:
        shutil.rmtree(backend_root / "mutants", ignore_errors=True)

    result = run_mutmut(["run"], backend_root)
    combined = result.stdout + result.stderr

    if not (backend_root / "mutants").is_dir():
        _ = sys.stderr.write("mutmut run did not produce a mutants/ directory. Output:\n" + combined[-4000:] + "\n")
        sys.exit(1)

    if not COMPLETION_RE.search(combined):
        _ = sys.stderr.write(
            "mutmut did not reach the mutation testing phase (no 'mutations/second' line). Output:\n"
            + combined[-4000:]
            + "\n"
        )
        sys.exit(1)

    done_match = GENERATION_SUMMARY_RE.search(combined)
    records = iter_mutant_records(backend_root)
    counts = Counter(r["status"] for r in records)
    actionable = sum(counts[s] for s in ACTIONABLE_STATUSES)

    emit(
        {
            "generated": done_match.group(0) if done_match else None,
            "counts": dict(sorted(counts.items())),
            "total": len(records),
            "actionable": actionable,
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
