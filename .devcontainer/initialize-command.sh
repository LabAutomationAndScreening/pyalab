# CodeSpaces build environments get cluttered and need to be pruned https://github.com/orgs/community/discussions/50403
# There was an error encountered during the codespace build using `docker system prune`, so switched to `docker image prune`: Error: The expected container does not exist.
set -ex

printenv
if [ -n "$CODESPACES" ] && [ "$CODESPACES" = "true" ]; then
    docker image prune --all --force
fi

# ============== WARNING ==============================================================================
# File is managed by copier template: gh:LabAutomationAndScreening/copier-base-template.git
# See .config/.copier-managed-files.json for details.
#
# You are welcome to make changes to this file in your repo if they are custom to your project,
# but if the change should be shared with other projects, please backport it to the template repo.
# =====================================================================================================
