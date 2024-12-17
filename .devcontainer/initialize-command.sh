# CodeSpaces build environments get cluttered and need to be pruned https://github.com/orgs/community/discussions/50403
# There was an error encountered during the codespace build using `docker system prune`, so switched to `docker image prune`: Error: The expected container does not exist.
set -ex

printenv
if [ -n "$CODESPACES" ] && [ "$CODESPACES" = "true" ]; then
    docker image prune --all --force
fi
