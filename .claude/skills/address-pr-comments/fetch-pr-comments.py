#!/usr/bin/env python3
"""Fetch and group PR comments into threads for the address-pr-comments skill.

Usage: fetch-pr-comments.py <pr_number>

Outputs JSON array of actionable comment threads to stdout. Each entry:
  {
    "id": <root comment id>,
    "type": "pulls/comments" | "issues/comments",
    "author": "<login>",
    "body": "<text>",
    "created_at": "<iso8601>",
    "path": "<file path, pulls/comments only>",
    "line": <line number, pulls/comments only>,
    "replies": [{"id", "author", "body", "created_at"}, ...]
  }

Filtered out:
  - Resolved threads
  - Bot summary/walkthrough comments
  - Threads whose most recent comment is by the current user (already addressed)
  - Top-level PR comments authored by the current user
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from utils import owner_repo_from_remote

EXPECTED_ARG_COUNT = 2
GH_TIMEOUT_SECONDS = 30

# Fetches only what we need to determine resolution: the root comment URL.
# We intentionally do NOT use databaseId here — it does not match the REST
# pulls/comments id that the replies endpoint requires.
RESOLVED_THREAD_URLS_QUERY = """
query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          isResolved
          comments(first: 1) {
            nodes {
              url
            }
          }
        }
      }
    }
  }
}
"""


def gh_rest(*args: str) -> Any:  # noqa: ANN401 — return type is genuinely unknown JSON
    # --paginate emits one JSON doc per page; --slurp wraps them into a single array.
    # Each page is itself an array, so we flatten the resulting array-of-arrays.
    paginating = "--paginate" in args
    call_args = [*args, "--slurp"] if paginating else list(args)
    result = subprocess.run(  # noqa: S603 — args are hardcoded at every call site
        ["gh", *call_args],  # noqa: S607 — gh is expected on PATH
        capture_output=True,
        text=True,
        check=True,
        timeout=GH_TIMEOUT_SECONDS,
    )
    data = json.loads(result.stdout)
    if not paginating:
        return data
    # --slurp wraps each page (a list) into an outer list; flatten to a single list.
    # All --paginate call sites query list endpoints, so data is list[list[Any]].
    return [item for page in data for item in page]


def gh_graphql(query: str, variables: dict[str, str | int]) -> Any:  # noqa: ANN401
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        # -F for integers (GraphQL Int), -f for strings
        flag = "-F" if isinstance(value, int) else "-f"
        args += [flag, f"{key}={value}"]
    result = subprocess.run(  # noqa: S603
        args,
        capture_output=True,
        text=True,
        check=True,
        timeout=GH_TIMEOUT_SECONDS,
    )
    data = json.loads(result.stdout)
    if errors := data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {errors}")
    return data["data"]


def fetch_current_user_login() -> str:
    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],  # noqa: S607 — gh is expected on PATH
        capture_output=True,
        text=True,
        check=True,
        timeout=GH_TIMEOUT_SECONDS,
    )
    return result.stdout.strip()


_BOT_LOGINS = frozenset({"coderabbitai[bot]", "copilot-pull-request-reviewer[bot]", "Copilot"})


def _login_from_comment(c: dict[str, Any]) -> str:
    user = c.get("user")
    if user is None:
        return "ghost"
    login = user.get("login")
    if not isinstance(login, str):
        return "ghost"
    return login


def is_bot_pr_body_comment(c: dict[str, Any]) -> bool:
    if "user" not in c or c["user"] is None:
        return False
    return c["user"].get("login", "") in _BOT_LOGINS


def fetch_resolved_html_urls(*, owner: str, repo: str, pr_number: int) -> set[str]:
    """Return the HTML URL of the root comment from each resolved review thread.

    We match resolved threads to REST comments via html_url rather than by ID
    because GraphQL databaseId does not equal the REST pulls/comments id field,
    so ID-based matching produces 404s on the replies endpoint.
    """
    resolved: set[str] = set()
    after: str | None = None
    while True:
        variables: dict[str, str | int] = {"owner": owner, "repo": repo, "number": pr_number}
        if after is not None:
            variables["after"] = after
        data = gh_graphql(RESOLVED_THREAD_URLS_QUERY, variables)
        page = data["repository"]["pullRequest"]["reviewThreads"]
        for node in page["nodes"]:
            if node["isResolved"]:
                comments = node["comments"]["nodes"]
                if comments:
                    resolved.add(comments[0]["url"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        after = page["pageInfo"]["endCursor"]
    return resolved


def _last_author(thread: dict[str, Any]) -> str:
    replies: list[dict[str, Any]] = thread["replies"]
    if replies:
        return replies[-1]["author"]
    return thread["author"]


def _collect_thread_roots(pulls_raw: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Return root comments (no in_reply_to_id) keyed by id, with empty replies lists."""
    roots: dict[int, dict[str, Any]] = {}
    for c in pulls_raw:
        if c.get("in_reply_to_id") is None:
            roots[c["id"]] = {
                "id": c["id"],
                "type": "pulls/comments",
                "author": _login_from_comment(c),
                "body": c["body"],
                "created_at": c["created_at"],
                "path": c.get("path"),
                "line": c.get("line") or c.get("original_line"),
                "_html_url": c.get("html_url", ""),
                "replies": [],
            }
    return roots


def _resolve_root_id(
    parent_id: int,
    roots: dict[int, dict[str, Any]],
    all_pulls: dict[int, dict[str, Any]],
) -> int | None:
    """Walk up the in_reply_to_id chain until a known root is found. Return None if broken."""
    root_id = parent_id
    seen: set[int] = set()
    while root_id not in roots and root_id not in seen:
        seen.add(root_id)
        parent = all_pulls.get(root_id)
        if parent is None:
            return None
        root_id = parent.get("in_reply_to_id", root_id)
    return root_id if root_id in roots else None


def _attach_replies(pulls_raw: list[dict[str, Any]], roots: dict[int, dict[str, Any]]) -> None:
    """Append each non-root comment as a reply on its thread root."""
    all_pulls: dict[int, dict[str, Any]] = {c["id"]: c for c in pulls_raw}
    for c in pulls_raw:
        parent_id = c.get("in_reply_to_id")
        if parent_id is None:
            continue
        root_id = _resolve_root_id(parent_id, roots, all_pulls)
        if root_id is None:
            continue
        roots[root_id]["replies"].append(
            {
                "id": c["id"],
                "author": _login_from_comment(c),
                "body": c["body"],
                "created_at": c["created_at"],
            }
        )
    for t in roots.values():
        replies: list[dict[str, Any]] = t["replies"]
        replies.sort(key=lambda r: r["created_at"])


def _build_pulls_threads(
    pulls_raw: list[dict[str, Any]],
    resolved_urls: set[str],
    current_user: str,
) -> list[dict[str, Any]]:
    """Group inline review comments into threads, filtering resolved + already-addressed."""
    roots = _collect_thread_roots(pulls_raw)
    _attach_replies(pulls_raw, roots)

    threads: list[dict[str, Any]] = []
    for t in roots.values():
        if t["_html_url"] in resolved_urls:
            continue
        if _last_author(t) == current_user:
            continue
        threads.append({k: v for k, v in t.items() if k != "_html_url"})
    return threads


def _build_flat_issues(issues_raw: list[dict[str, Any]], current_user: str) -> list[dict[str, Any]]:
    """Project top-level PR comments, filtering bot summaries + current-user comments."""
    flat: list[dict[str, Any]] = []
    for c in issues_raw:
        if is_bot_pr_body_comment(c):
            continue
        if _login_from_comment(c) == current_user:
            continue
        flat.append(
            {
                "id": c["id"],
                "type": "issues/comments",
                "author": _login_from_comment(c),
                "body": c["body"],
                "created_at": c["created_at"],
                "path": None,
                "line": None,
                "replies": [],
            }
        )
    return flat


def fetch(*, owner: str, repo: str, pr_number: int, current_user: str) -> list[dict[str, Any]]:
    # GitHub exposes two separate comment APIs for pull requests:
    #
    # - pulls/comments: inline review comments attached to specific lines of code.
    #   These can form threads — a root comment plus replies. Each reply carries
    #   an `in_reply_to_id` pointing to its parent.
    #   Resolved threads are excluded using GraphQL reviewThreads.isResolved, since
    #   the REST API does not expose thread resolution status. We use REST IDs for
    #   the thread structure because they are what the replies endpoint accepts.
    #
    # - issues/comments: general comments on the PR conversation (not tied to a
    #   line). These are flat — GitHub has no threading or resolved concept for them.
    resolved_urls = fetch_resolved_html_urls(owner=owner, repo=repo, pr_number=pr_number)

    pulls_raw: list[dict[str, Any]] = gh_rest("api", f"repos/{owner}/{repo}/pulls/{pr_number}/comments", "--paginate")
    issues_raw: list[dict[str, Any]] = gh_rest("api", f"repos/{owner}/{repo}/issues/{pr_number}/comments", "--paginate")

    threads = _build_pulls_threads(pulls_raw, resolved_urls, current_user)
    flat = _build_flat_issues(issues_raw, current_user)

    combined = threads + flat
    combined.sort(key=lambda x: x["created_at"])
    return combined


def main() -> None:
    if len(sys.argv) != EXPECTED_ARG_COUNT:
        _ = sys.stderr.write(f"Usage: {sys.argv[0]} <pr_number>\n")
        sys.exit(1)

    pr_number_raw = sys.argv[1].strip().lstrip("#")
    try:
        pr_number = int(pr_number_raw)
    except ValueError:
        _ = sys.stderr.write(f"Invalid PR number: {pr_number_raw}\n")
        sys.exit(1)

    owner, repo = owner_repo_from_remote()

    try:
        current_user = fetch_current_user_login()
        comments = fetch(owner=owner, repo=repo, pr_number=pr_number, current_user=current_user)
        _ = sys.stdout.write(json.dumps(comments, indent=2) + "\n")
    except subprocess.CalledProcessError as e:
        _ = sys.stderr.write(f"gh api error: {e.stderr}\n")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        _ = sys.stderr.write(f"gh api timed out after {GH_TIMEOUT_SECONDS}s\n")
        sys.exit(1)
    except RuntimeError as e:
        _ = sys.stderr.write(f"{e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
