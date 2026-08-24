#!/usr/bin/env python3
"""Check whether mutmut has any existing results.

Usage:
  check-results.py

Runs `mutmut results` and checks whether it produced any output. Empty stdout
means mutmut has never been run (or the mutants/ directory was wiped).

Outputs JSON to stdout:
  {
    "has_results": true | false,
    "backend_root": "/abs/path/to/folder/containing/pyproject.toml"
  }
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import emit
from utils import find_backend_root
from utils import run_mutmut


def main() -> None:
    backend_root = find_backend_root()
    result = run_mutmut(["results"], backend_root, timeout=30)
    has_results = bool(result.stdout.strip())
    emit({"has_results": has_results, "backend_root": str(backend_root)})


if __name__ == "__main__":
    main()

# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
