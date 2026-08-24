# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
import argparse
import subprocess


def ensure_tag_not_present(tag: str, remote: str) -> None:
    no_matching_refs_return_code = 2
    result = subprocess.run(  # noqa: S603 # this is trusted input, it's our own arguments being passed in
        ["git", "ls-remote", "--exit-code", "--tags", remote, f"refs/tags/{tag}"],  # noqa: S607 # if `git` isn't in PATH already, then there are bigger problems to solve
        stdout=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0:
        raise Exception(f"Error: tag '{tag}' exists on remote '{remote}'")  # noqa: TRY002 # not worth a custom exception
    if (
        result.returncode != no_matching_refs_return_code
    ):  # anything else is a real error (bad remote, auth failure, network)
        raise Exception(f"git ls-remote exited with code {result.returncode} (remote={remote!r})")  # noqa: TRY002 # not worth a custom exception


def main() -> None:
    parser = argparse.ArgumentParser(
        description=("Confirm that git tag v<version> is not present on a remote, or create and push the tag.")
    )
    _ = parser.add_argument(
        "--version",
        required=True,
        help="Version string (e.g. 1.0.6 or v1.0.6); the tag will always be v<version>",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    _ = mode.add_argument(
        "--confirm-tag-not-present",
        action="store_true",
        help="Check that git tag v<version> is NOT present on the remote. If the tag exists, exit with an error.",
    )
    _ = mode.add_argument(
        "--push-tag-to-remote",
        action="store_true",
        help="Create git tag v<version> locally and push it to the remote. Internally confirms the tag is not already present.",
    )
    _ = parser.add_argument(
        "--remote",
        default="origin",
        help="Name of git remote to query/push (default: origin)",
    )
    args = parser.parse_args()

    tag = args.version if args.version.startswith("v") else f"v{args.version}"

    if args.push_tag_to_remote:
        ensure_tag_not_present(tag, args.remote)
        _ = subprocess.run(["git", "tag", tag], check=True)  # noqa: S603,S607 # this is trusted input, it's our own version string. and if `git` isn't in PATH, then there are larger problems anyway
        _ = subprocess.run(["git", "push", args.remote, tag], check=True)  # noqa: S603,S607 # this is trusted input, it's our own version string. and if `git` isn't in PATH, then there are larger problems anyway
        return

    if args.confirm_tag_not_present:
        ensure_tag_not_present(tag, args.remote)


if __name__ == "__main__":
    main()
