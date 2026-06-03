#!/usr/bin/env python3
"""Delete .rej files whose corresponding source files are unchanged in git.

Typically run after a `copier update` to discard false-positive rejects (hunks that couldn't apply because the target file was already up-to-date).
Exits 0 if no conflicts remain, 1 if any .rej files still exist.
"""

import subprocess
import sys
from pathlib import Path


def _status_paths(*, repo_root: Path) -> list[str]:
    output = subprocess.check_output(
        [  # noqa: S607 # git should always be on PATH
            "git",
            "status",
            "--porcelain",
            "-z",
        ],
        cwd=repo_root,
        text=True,
    )
    return [entry[3:] for entry in output.split("\0") if entry]


if __name__ == "__main__":
    repo_root = Path(
        subprocess.check_output(
            [  # noqa: S607 # git should always be on PATH
                "git",
                "rev-parse",
                "--show-toplevel",
            ],
            text=True,
        ).strip()
    )

    rej_files = [path for path in _status_paths(repo_root=repo_root) if path.endswith(".rej")]

    deleted = 0
    for rej in rej_files:
        source = rej.removesuffix(".rej")
        status = subprocess.check_output(  # noqa: S603 # untrusted input is not a big risk, it's our own repo and this is a manually invoked script
            [  # noqa: S607 # git should always be on PATH
                "git",
                "status",
                "--porcelain",
                "--",
                source,
            ],
            cwd=repo_root,
            text=True,
        ).strip()
        if not status:
            (repo_root / rej).unlink()
            deleted += 1

    remaining = [path for path in _status_paths(repo_root=repo_root) if path.endswith(".rej")]

    print(  # noqa: T201 # we want the script to print to console for easy viewing
        f"Deleted {deleted} .rej file(s)."
    )
    if remaining:
        print(  # noqa: T201 # we want the script to print to console for easy viewing
            "Remaining .rej conflicts:"
        )
        for f in remaining:
            print(  # noqa: T201 # we want the script to print to console for easy viewing
                f"  {f}"
            )

    else:
        print(  # noqa: T201 # we want the script to print to console for easy viewing
            "No .rej conflicts remaining."
        )

    sys.exit(1 if remaining else 0)
