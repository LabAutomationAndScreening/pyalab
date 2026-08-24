# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
import re
import subprocess
import sys


def run_cmd(
    cmd: list[str],
    *,
    timeout: int,
    timeout_msg: str,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(  # noqa: S603 — callers are responsible for only passing safe commands
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        _ = sys.stderr.write(f"{timeout_msg}\n")
        sys.exit(1)


def owner_repo_from_remote() -> tuple[str, str]:
    try:
        result = run_cmd(
            ["git", "remote", "get-url", "origin"],
            timeout=15,
            timeout_msg="Timed out reading git remote 'origin'.",
        )
    except subprocess.CalledProcessError:
        _ = sys.stderr.write("Cannot read git remote 'origin'. Ensure it exists and points to GitHub.\n")
        sys.exit(1)
    url = result.stdout.strip()
    match = re.fullmatch(
        r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+)/([^/]+?)(?:\.git)?/?",
        url,
    )
    if not match:
        _ = sys.stderr.write(f"Cannot parse GitHub owner/repo from remote: {url}\n")
        sys.exit(1)
    return match.group(1), match.group(2)
