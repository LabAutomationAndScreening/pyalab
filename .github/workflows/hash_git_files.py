"""Used typically to calculate if all the files in the context of building a Docker image have changed or not."""

import argparse
import subprocess
import sys
import zlib
from pathlib import Path

DEVCONTAINER_COMMENT_LINE_PREFIX = (
    "  // Devcontainer context hash (do not manually edit this, it's managed by a pre-commit hook): "
)

DEVCONTAINER_COMMENT_LINE_SUFFIX = (
    " # spellchecker:disable-line"  # the typos hook can sometimes mess with the hash without this
)


def get_tracked_files(repo_path: Path) -> list[str]:
    """Return a list of files tracked by Git in the given repository folder, using the 'git ls-files' command."""
    try:
        result = subprocess.run(  # noqa: S603 # there's no concern about executing untrusted input, only we will call this script
            ["git", "-C", str(repo_path), "ls-files"],  # noqa: S607 # yes, this is not using a complete executable path, but it's just git and git should always be present in PATH
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.splitlines()

    except subprocess.CalledProcessError:
        print("Error: The directory does not appear to be a Git repository or Git is not installed.", file=sys.stderr)  # noqa: T201 # this just runs as a simple script, so using print instead of log
        sys.exit(1)


def filter_files_for_devcontainer_context(files: list[str]) -> tuple[list[str], Path]:
    devcontainer_context: list[str] = []
    devcontainer_json_file_path: str | None = None
    for file in files:
        if file.startswith(".devcontainer/"):
            if file.endswith("devcontainer.json"):
                devcontainer_json_file_path = file
                continue
            devcontainer_context.append(file)
        elif file.endswith((".lock", "pnpm-lock.yaml", "hash_git_files.py")) or file == ".pre-commit-config.yaml":
            devcontainer_context.append(file)
    if devcontainer_json_file_path is None:
        raise ValueError("No devcontainer.json file found in the tracked files.")  # noqa: TRY003 # not worth a custom exception for this
    return devcontainer_context, Path(devcontainer_json_file_path)


def compute_adler32(repo_path: Path, files: list[str]) -> int:
    """Compute an overall Adler-32 checksum of the provided files.

    The checksum incorporates both the file names and their contents. Files are processed in sorted order to ensure consistent ordering.
    """
    checksum = 1  # Adler-32 default starting value

    for file in sorted(files):
        file_path = repo_path / file  # Use pathlib to combine paths
        # Update the checksum with the file name (encoded as bytes)
        checksum = zlib.adler32(file.encode("utf-8"), checksum)
        try:
            with file_path.open("rb") as f:
                while True:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    checksum = zlib.adler32(chunk, checksum)
        except Exception as e:
            if "[Errno 21] Is a directory" in str(e):
                # Ignore symlinks that on windows sometimes get confused as being directories
                continue
            print(f"Error reading file {file}: {e}", file=sys.stderr)  # noqa: T201 # this just runs as a simple script, so using print instead of log
            raise

    return checksum


def find_devcontainer_hash_line(lines: list[str]) -> tuple[int, str | None]:
    """Find the line index and current hash in the devcontainer.json file."""
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "}":
            # Check the line above it
            if i > 0:
                above_line = lines[i - 1]
                if above_line.startswith(DEVCONTAINER_COMMENT_LINE_PREFIX):
                    part_after_prefix = above_line.split(": ", 1)[1]
                    part_before_suffix = part_after_prefix.split("#")[0]
                    current_hash = part_before_suffix.strip()
                    return i - 1, current_hash
            return i, None
    return -1, None


def extract_devcontainer_context_hash(devcontainer_json_file: Path) -> str | None:
    """Extract the current devcontainer context hash from the given devcontainer.json file."""
    try:
        with devcontainer_json_file.open("r", encoding="utf-8") as file:
            lines = file.readlines()
    except Exception as e:
        print(f"Error reading file {devcontainer_json_file}: {e}", file=sys.stderr)  # noqa: T201
        raise
    _, current_hash = find_devcontainer_hash_line(lines)
    return current_hash


def update_devcontainer_context_hash(devcontainer_json_file: Path, new_hash: str) -> None:
    """Update the devcontainer.json file with the new context hash."""
    try:
        with devcontainer_json_file.open("r", encoding="utf-8") as file:
            lines = file.readlines()

        line_index, current_hash = find_devcontainer_hash_line(lines)
        new_hash_line = f"{DEVCONTAINER_COMMENT_LINE_PREFIX}{new_hash}{DEVCONTAINER_COMMENT_LINE_SUFFIX}\n"
        if current_hash is not None:
            # Replace the old hash with the new hash
            lines[line_index] = new_hash_line
        else:
            # Insert the new hash line above the closing `}`
            lines.insert(line_index, new_hash_line)

        # Write the updated lines back to the file
        with devcontainer_json_file.open("w", encoding="utf-8") as file:
            file.writelines(lines)

    except Exception as e:
        print(f"Error updating file {devcontainer_json_file}: {e}", file=sys.stderr)  # noqa: T201
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Compute an Adler-32 checksum of all Git-tracked files in the specified folder."
    )
    _ = parser.add_argument("folder", type=Path, help="Path to the Git repository folder")
    _ = parser.add_argument("--debug", action="store_true", help="Print all discovered Git-tracked files")
    _ = parser.add_argument(
        "--for-devcontainer-config-update",
        action="store_true",
        help="Update the hash in the devcontainer.json file based on all files relevant to devcontainer context",
    )
    _ = parser.add_argument("--exit-zero", action="store_true", help="Exit with code 0 even if the hash changes")
    args = parser.parse_args()

    repo_path = args.folder
    if not repo_path.is_dir():
        print(f"Error: {repo_path} is not a valid directory.", file=sys.stderr)  # noqa: T201 # this just runs as a simple script, so using print instead of log
        sys.exit(1)

    # Retrieve the list of Git-tracked files.
    files = get_tracked_files(repo_path)
    devcontainer_json_file: Path | None = None
    if args.for_devcontainer_config_update:
        files, devcontainer_json_file = filter_files_for_devcontainer_context(files)

    # If the debug flag is specified, print out all discovered files.
    if args.debug:
        print("Tracked files discovered:")  # noqa: T201 # this just runs as a simple script, so using print instead of log
        for file in files:
            print(file)  # noqa: T201 # this just runs as a simple script, so using print instead of log

    # Compute the overall Adler-32 checksum.
    overall_checksum = compute_adler32(repo_path, files)
    overall_checksum_str = f"{overall_checksum:08x}"  # Format the checksum as an 8-digit hexadecimal value.
    if args.for_devcontainer_config_update:
        assert devcontainer_json_file is not None, (
            "this should have been set earlier in a similar conditional statement"
        )
        current_hash = extract_devcontainer_context_hash(devcontainer_json_file)
        if current_hash != overall_checksum_str:
            update_devcontainer_context_hash(devcontainer_json_file, overall_checksum_str)
            print(  # noqa: T201
                f"Updated {devcontainer_json_file} with the new hash: {overall_checksum_str}"
            )
            if args.exit_zero:
                sys.exit(0)
            else:
                sys.exit(1)

    else:
        print(overall_checksum_str)  # noqa: T201 # print this so that the value can be picked up via STDOUT when calling this in a CI pipeline or as a subprocess


if __name__ == "__main__":
    main()
