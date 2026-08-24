# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
"""Shared helpers for the fix-mutants skill.

All mutmut state lives under ``<backend_root>/mutants/``:
  - ``<backend_root>/mutants/<src path>.py.meta`` — per-source-file JSON whose
    ``exit_code_by_key`` maps each mutant name to the pytest exit code from its
    last run. The exit code is translated to a status via ``STATUS_BY_EXIT_CODE``.

Scripts in this skill are stdlib-only and run mutmut itself through
``uv run mutmut`` so the project's pinned mutmut (git dependency) is used.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HUNK_RE = re.compile(r"@@ -(\d+)")

# Mirrors mutmut's status_by_exit_code (mutmut/__main__.py). Unknown codes map
# to "suspicious", matching mutmut's defaultdict fallback.
STATUS_BY_EXIT_CODE: dict[int | None, str] = {
    0: "survived",
    1: "killed",
    3: "killed",
    -24: "timeout",
    24: "timeout",
    152: "timeout",
    255: "timeout",
    2: "check was interrupted by user",
    5: "no tests",
    33: "no tests",
    34: "skipped",
    35: "suspicious",
    36: "timeout",
    37: "caught by type check",
    -11: "segfault",
    -9: "segfault",
    None: "not checked",
}

# Statuses that indicate a test gap a human/AI can close by strengthening tests.
ACTIONABLE_STATUSES = ("survived", "no tests")

SUBPROCESS_TIMEOUT_SECONDS = 1800


def emit(obj: Any) -> None:  # noqa: ANN401 — serializes arbitrary JSON-shaped result objects
    """Write a JSON result to stdout (the scripts' machine-readable output)."""
    _ = sys.stdout.write(json.dumps(obj, indent=2) + "\n")


def status_for_exit_code(exit_code: int | None) -> str:
    return STATUS_BY_EXIT_CODE.get(exit_code, "suspicious")


def _original_block(diff: str) -> tuple[list[str], int | None]:
    """Reconstruct the original lines of the first hunk that removes a line.

    Returns the block of original lines (context plus removed) and the index
    of the first removed line within that block, or None if nothing is removed.
    """
    block: list[str] = []
    removed_index: int | None = None
    in_hunk = False
    for diff_line in diff.splitlines():
        if HUNK_RE.match(diff_line):
            if removed_index is not None:
                break
            block = []
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if diff_line.startswith("+"):
            continue
        if diff_line.startswith("-"):
            if removed_index is None:
                removed_index = len(block)
        block.append(diff_line[1:])
    return block, removed_index


def locate_changed_line(*, diff: str, source_text: str) -> int:
    """File line number (1-based) of the first line a mutant diff removes.

    mutmut generates its diff against the extracted function body, so the
    `@@ -N` hunk headers carry function-relative line numbers, not file
    positions. Recover the file position by matching the hunk's original
    lines (context plus removed) against the real source text; fall back to
    matching just the removed line if the full block is not found. Returns 0
    if the diff removes nothing or no match exists.
    """
    block, removed_index = _original_block(diff)
    if removed_index is None:
        return 0

    source_lines = source_text.splitlines()
    for start in range(len(source_lines) - len(block) + 1):
        if source_lines[start : start + len(block)] == block:
            return start + removed_index + 1

    needle = block[removed_index]
    for index, source_line in enumerate(source_lines, start=1):
        if source_line == needle:
            return index
    return 0


def _declares_mutmut(pyproject: Path) -> bool:
    if not pyproject.is_file():
        return False
    try:
        content = pyproject.read_text(encoding="utf-8")
    except OSError:
        return False
    return "[tool.mutmut]" in content


def _mutmut_projects_below(cwd: Path) -> list[Path]:
    matches: list[Path] = []
    for pattern in ("*/pyproject.toml", "*/*/pyproject.toml"):
        for pyproject in cwd.glob(pattern):
            if "mutants" in pyproject.parts:
                continue
            if _declares_mutmut(pyproject):
                matches.append(pyproject.parent)
    return matches


def find_backend_root() -> Path:
    """Locate the directory whose pyproject.toml declares a [tool.mutmut] table.

    Searches upward from cwd first, then downward up to two levels, so the
    scripts can be invoked from either the repo root or inside the backend
    project. mutmut must be run from this directory (it reads ./pyproject.toml
    and writes ./mutants/).
    """
    cwd = Path.cwd()

    for candidate in [cwd, *cwd.parents]:
        if _declares_mutmut(candidate / "pyproject.toml"):
            return candidate

    matches = _mutmut_projects_below(cwd)

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        paths = ", ".join(str(m) for m in matches)
        _ = sys.stderr.write(
            f"Multiple pyproject.toml files with [tool.mutmut] found: {paths}. Run from inside the backend project.\n"
        )
        sys.exit(1)

    _ = sys.stderr.write(
        "Could not find a pyproject.toml with a [tool.mutmut] table in the current directory, any parent, or any subdirectory up to two levels deep.\n"
    )
    sys.exit(1)


def mutants_dir(backend_root: Path) -> Path:
    mutants = backend_root / "mutants"
    if not mutants.is_dir():
        _ = sys.stderr.write(
            f"No mutants/ directory under {backend_root}. Run the mutation suite first (run-mutmut.py).\n"
        )
        sys.exit(1)
    return mutants


def iter_mutant_records(backend_root: Path) -> list[dict[str, Any]]:
    """Read every <file>.meta and flatten to one record per mutant.

    Each record: {"key", "status", "exit_code", "source_file"} where source_file
    is the project-relative path to the original (unmutated) source.
    """
    mutants = mutants_dir(backend_root)
    records: list[dict[str, Any]] = []
    for meta_path in sorted(mutants.rglob("*.py.meta")):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            _ = sys.stderr.write(f"Skipping unreadable meta {meta_path}: {exc}\n")
            continue
        exit_codes = meta.get("exit_code_by_key", {})
        source_rel = meta_path.with_suffix("").relative_to(mutants)
        for key, exit_code in exit_codes.items():
            records.append(
                {
                    "key": key,
                    "status": status_for_exit_code(exit_code),
                    "exit_code": exit_code,
                    "source_file": str(source_rel),
                }
            )
    return records


def run_mutmut(
    args: list[str], backend_root: Path, *, timeout: int = SUBPROCESS_TIMEOUT_SECONDS
) -> subprocess.CompletedProcess[str]:
    """Invoke the project's mutmut via uv, with cwd at the backend root."""
    try:
        return subprocess.run(  # noqa: S603 — args are hardcoded at every call site
            ["uv", "run", "mutmut", *args],  # noqa: S607 — uv is expected on PATH
            cwd=backend_root,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        _ = sys.stderr.write("`uv` not found on PATH. This skill requires uv.\n")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        _ = sys.stderr.write(f"mutmut {' '.join(args)} timed out after {timeout}s.\n")
        sys.exit(1)
