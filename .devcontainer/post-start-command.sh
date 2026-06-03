#!/bin/bash
set -ex

# For some reason the directory is not setup correctly and causes build of devcontainer to fail since
# it doesn't have access to the workspace directory. This can normally be done in post-start-command
script_dir="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)"
repo_root="$(CDPATH='' cd -- "$script_dir/.." && pwd)"
git config --global --add safe.directory "$repo_root"
pre-commit run merge-claude-settings -a
if ! bd ready; then
	echo "It's likely the Dolt server has not yet been initialized to support beads, running that now" # TODO: figure out a better way to match this specific scenario than just a non-zero exit code...but beads still seems like in high flux right now so not sure what to tie it to
    # the 'stealth' flag is just the only way I could figure out how to stop it from modifying AGENTS.md...if there's another way to avoid that, then fine.  Even without the stealth flag though, files inside the .claude/beads directory get modified, so restoring them at the end to what was set in git...these shouldn't really need to change regularly
    # trying to set 'prefix' to nothing doesn't seem to work (it just acts like the prefix flag wasn't there), so just setting to 'work' as an arbitrary name
    # for some reason, the envvar for the server host isn't being picked up normally, so just passing it explicitly here
    rm -rf .claude/.beads && bd init --server-host="$BEADS_DOLT_SERVER_HOST" --database="$BEADS_DOLT_SERVER_DATABASE" --skip-hooks --stealth --prefix=work </dev/null && git -c core.hooksPath=/dev/null restore --source=HEAD --staged --worktree .claude/.beads
fi
