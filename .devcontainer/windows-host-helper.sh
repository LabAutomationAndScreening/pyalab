#!/bin/bash

# If you are using a Windows host and you initially cloned the repository directly onto your hard drive, you may run into file permission issues when running copier updates. To avoid these, after initially building the devcontainer, run this from the repo root:
# cp .devcontainer/windows-host-helper.sh ../
# cd ..
# bash windows-host-helper.sh <git-url>

# If you're still having issues, make sure in Windows Developer Settings that you enabled Developer Mode, and also that you set your git config to have `core.autocrlf=false` and `core.symlinks=true` globally

set -euo pipefail  # Exit immediately on error

if [ -z "$BASH_VERSION" ]; then
  echo "Error: This script must be run with bash (e.g., 'bash windows-host-helper.sh')." >&2
  exit 1
fi

# Check for the git URL argument
if [ -z "$1" ]; then
    echo "Usage: $0 <git-url>"
    exit 1
fi

gitUrl="$1"

# Extract repository name (removes .git suffix if present)
repoName=$(basename "$gitUrl" .git)

echo "Repo name extracted as '$repoName'"

# Remove any existing subfolder with the repository name and recreate it
rm -rf "./$repoName" || true # sometimes deleting the .venv folder fails
rm -rf "./$repoName/*.md" # for some reason, sometimes md files are left behind
mkdir -p "./$repoName"

# Create a temporary directory for cloning
tmpdir=$(mktemp -d)

# Clone the repository into a subfolder inside the temporary directory.
# This creates "$tmpdir/$repoName" with the repository's contents.
git clone "$gitUrl" "$tmpdir/$repoName"


SRC="$(realpath "$tmpdir/$repoName")"
DST="$(realpath "./$repoName")"

# 1) Recreate directory tree under $DST
while IFS= read -r -d '' dir; do
  rel="${dir#$SRC/}"             # strip leading $SRC/ → e.g. "sub/dir"
  mkdir -p "$DST/$rel"
done < <(find "$SRC" -type d -print0)

# 2) Move all files into that mirror
while IFS= read -r -d '' file; do
  rel="${file#$SRC/}"            # e.g. "sub/dir/file.txt"
  # ensure parent exists (though step 1 already did)
  mkdir -p "$(dirname "$DST/$rel")"
  mv "$file" "$DST/$rel"
done < <(find "$SRC" -type f -print0)

# 3) Clean up now‑empty dirs and the tmp clone
find "$SRC" -depth -type d -empty -delete
rm -rf "$tmpdir"

echo "Repository '$repoName' has been synced into '$DST'."
