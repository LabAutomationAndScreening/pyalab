import argparse
import subprocess
import tomllib
from pathlib import Path


def extract_version(toml_path: Path | str) -> str:
    """Load toml_path and return the version string.

    Checks [project].version (PEP 621) first, then [tool.poetry].version. Raises KeyError if no version field is found.
    """
    path = Path(toml_path)
    with path.open("rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    if version := project.get("version"):
        return version

    tool = data.get("tool", {})
    poetry = tool.get("poetry", {})
    if version := poetry.get("version"):
        return version

    raise KeyError(f"No version field found in {path!r}")  # noqa: TRY003 # not worth a custom exception


def ensure_tag_not_present(tag: str, remote: str) -> None:
    try:
        _ = subprocess.run(  # noqa: S603 # this is trusted input, it's our own arguments being passed in
            ["git", "ls-remote", "--exit-code", "--tags", remote, f"refs/tags/{tag}"],  # noqa: S607 # if `git` isn't in PATH already, then there are bigger problems to solve
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        raise Exception(f"Error: tag '{tag}' exists on remote '{remote}'")  # noqa: TRY002,TRY003 # not worth a custom exception
    except subprocess.CalledProcessError:
        # tag not present, continue
        return


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extract the version from a pyproject.toml file, "
            "confirm that git tag v<version> is not present, or "
            "create and push the tag to a remote."
        )
    )
    _ = parser.add_argument(
        "file",
        nargs="?",
        default="pyproject.toml",
        help="Path to pyproject.toml (default: pyproject.toml)",
    )
    _ = parser.add_argument(
        "--confirm-tag-not-present",
        action="store_true",
        help=("Check that git tag v<version> is NOT present on the remote. If the tag exists, exit with an error."),
    )
    _ = parser.add_argument(
        "--push-tag-to-remote",
        action="store_true",
        help=(
            "Create git tag v<version> locally and push it to the remote. "
            "Internally confirms the tag is not already present."
        ),
    )
    _ = parser.add_argument(
        "--remote",
        default="origin",
        help="Name of git remote to query/push (default: origin)",
    )
    args = parser.parse_args()

    ver = extract_version(args.file)

    tag = f"v{ver}"

    if args.push_tag_to_remote:
        ensure_tag_not_present(tag, args.remote)
        _ = subprocess.run(["git", "tag", tag], check=True)  # noqa: S603,S607 # this is trusted input, it's our own pyproject.toml file. and if `git` isn't in PATH, then there are larger problems anyway
        _ = subprocess.run(["git", "push", args.remote, tag], check=True)  # noqa: S603,S607 # this is trusted input, it's our own pyproject.toml file. and if `git` isn't in PATH, then there are larger problems anyway
        return

    if args.confirm_tag_not_present:
        ensure_tag_not_present(tag, args.remote)
        return

    # Default behavior: just print the version
    print(ver)  # noqa: T201 # specifically printing this out so CI pipelines can read the value from stdout


if __name__ == "__main__":
    main()
