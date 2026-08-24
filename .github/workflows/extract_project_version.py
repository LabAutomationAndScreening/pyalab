# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
import argparse
import json
import tomllib
from pathlib import Path


def extract_version(file_path: Path | str) -> str:
    path = Path(file_path)

    if path.name == "package.json":
        data = json.loads(path.read_text())
        if version := data.get("version"):
            return version
        raise KeyError(f"No version field found in {path!r}")

    if path.name == "pyproject.toml":
        with path.open("rb") as f:
            data = tomllib.load(f)
        project = data.get("project", {})
        if version := project.get("version"):
            return version
        tool = data.get("tool", {})
        if version := tool.get("poetry", {}).get("version"):
            return version
        raise KeyError(f"No version field found in {path!r}")

    raise ValueError(f"Unsupported file type {path.name!r}; expected pyproject.toml or package.json")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract the version from a pyproject.toml or package.json file and print it."
    )
    _ = parser.add_argument(
        "file",
        nargs="?",
        default="pyproject.toml",
        help="Path to pyproject.toml or package.json (default: pyproject.toml)",
    )
    args = parser.parse_args()

    print(extract_version(args.file))  # noqa: T201 # specifically printing this out so CI pipelines can read the value from stdout


if __name__ == "__main__":
    main()
