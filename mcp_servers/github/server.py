from __future__ import annotations
from dotenv import load_dotenv


import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from mcp.server.fastmcp import FastMCP

load_dotenv()
mcp = FastMCP("devrescue-github")

GITHUB_API = "https://api.github.com"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "DevRescue",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    return headers


def _request(
    path: str,
    params: dict[str, Any] | None = None,
) -> Any:
    url = f"{GITHUB_API}{path}"

    if params:
        query = urllib.parse.urlencode(
            {
                key: value
                for key, value in params.items()
                if value is not None
            }
        )
        if query:
            url = f"{url}?{query}"

    request = urllib.request.Request(
        url,
        headers=_headers(),
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)

    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")

        try:
            details = json.loads(body)
        except json.JSONDecodeError:
            details = body

        return {
            "status": "error",
            "http_status": exc.code,
            "error": details,
        }

    except urllib.error.URLError as exc:
        return {
            "status": "error",
            "error": str(exc.reason),
        }

    except TimeoutError:
        return {
            "status": "error",
            "error": "GitHub API request timed out.",
        }


def _repository(
    owner: str | None,
    repository: str | None,
) -> tuple[str, str]:
    resolved_owner = owner or GITHUB_OWNER
    resolved_repository = repository or GITHUB_REPOSITORY

    if not resolved_owner:
        raise ValueError(
            "GitHub owner is required. "
            "Set GITHUB_OWNER or provide owner."
        )

    if not resolved_repository:
        raise ValueError(
            "GitHub repository is required. "
            "Set GITHUB_REPOSITORY or provide repository."
        )

    return resolved_owner, resolved_repository


@mcp.tool()
def get_repository(
    owner: str | None = None,
    repository: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve metadata for a GitHub repository.
    """

    owner, repository = _repository(
        owner,
        repository,
    )

    result = _request(
        f"/repos/{owner}/{repository}"
    )

    if isinstance(result, dict) and result.get("status") == "error":
        return result

    return {
        "status": "success",
        "repository": {
            "id": result.get("id"),
            "full_name": result.get("full_name"),
            "name": result.get("name"),
            "owner": result.get("owner", {}).get("login"),
            "private": result.get("private"),
            "default_branch": result.get("default_branch"),
            "description": result.get("description"),
            "language": result.get("language"),
            "html_url": result.get("html_url"),
        },
    }


@mcp.tool()
def get_file(
    path: str,
    owner: str | None = None,
    repository: str | None = None,
    ref: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve a file from a GitHub repository.

    The returned content is decoded from GitHub's base64 representation.
    """

    owner, repository = _repository(
        owner,
        repository,
    )

    result = _request(
        f"/repos/{owner}/{repository}/contents/{path}",
        params={"ref": ref},
    )

    if isinstance(result, dict) and result.get("status") == "error":
        return result

    if isinstance(result, list):
        return {
            "status": "error",
            "error": "The requested path is a directory, not a file.",
        }

    encoded_content = result.get("content", "")

    try:
        content = base64.b64decode(
            encoded_content.replace("\n", "")
        ).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        return {
            "status": "error",
            "error": f"Unable to decode file content: {exc}",
        }

    return {
        "status": "success",
        "file": {
            "path": result.get("path"),
            "name": result.get("name"),
            "sha": result.get("sha"),
            "size": result.get("size"),
            "html_url": result.get("html_url"),
            "download_url": result.get("download_url"),
            "content": content,
        },
    }


@mcp.tool()
def search_code(
    query: str,
    owner: str | None = None,
    repository: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Search source code in a GitHub repository.

    The repository is automatically scoped to the supplied repository.
    """

    owner, repository = _repository(
        owner,
        repository,
    )

    if not query.strip():
        return {
            "status": "error",
            "error": "Search query cannot be empty.",
        }

    scoped_query = (
        f"{query} repo:{owner}/{repository}"
    )

    result = _request(
        "/search/code",
        params={
            "q": scoped_query,
            "per_page": min(max(limit, 1), 100),
        },
    )

    if isinstance(result, dict) and result.get("status") == "error":
        return result

    items = []

    for item in result.get("items", []):
        items.append(
            {
                "name": item.get("name"),
                "path": item.get("path"),
                "sha": item.get("sha"),
                "html_url": item.get("html_url"),
                "repository": item.get(
                    "repository",
                    {},
                ).get("full_name"),
            }
        )

    return {
        "status": "success",
        "query": query,
        "repository": f"{owner}/{repository}",
        "total_count": result.get(
            "total_count",
            len(items),
        ),
        "results": items,
    }


@mcp.tool()
def list_commits(
    owner: str | None = None,
    repository: str | None = None,
    branch: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Retrieve recent commits from a GitHub repository.
    """

    owner, repository = _repository(
        owner,
        repository,
    )

    result = _request(
        f"/repos/{owner}/{repository}/commits",
        params={
            "sha": branch,
            "per_page": min(max(limit, 1), 100),
        },
    )

    if isinstance(result, dict) and result.get("status") == "error":
        return result

    commits = []

    for commit in result:
        commits.append(
            {
                "sha": commit.get("sha"),
                "message": (
                    commit.get("commit", {})
                    .get("message")
                ),
                "author": (
                    commit.get("commit", {})
                    .get("author", {})
                    .get("name")
                ),
                "timestamp": (
                    commit.get("commit", {})
                    .get("author", {})
                    .get("date")
                ),
                "html_url": commit.get("html_url"),
            }
        )

    return {
        "status": "success",
        "repository": f"{owner}/{repository}",
        "branch": branch,
        "results": commits,
    }


@mcp.tool()
def get_commit(
    sha: str,
    owner: str | None = None,
    repository: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve detailed metadata for a GitHub commit.
    """

    owner, repository = _repository(
        owner,
        repository,
    )

    result = _request(
        f"/repos/{owner}/{repository}/commits/{sha}"
    )

    if isinstance(result, dict) and result.get("status") == "error":
        return result

    return {
        "status": "success",
        "commit": {
            "sha": result.get("sha"),
            "message": (
                result.get("commit", {})
                .get("message")
            ),
            "author": (
                result.get("commit", {})
                .get("author", {})
            ),
            "committer": (
                result.get("commit", {})
                .get("committer", {})
            ),
            "html_url": result.get("html_url"),
            "stats": result.get("stats"),
            "files": [
                {
                    "filename": item.get("filename"),
                    "status": item.get("status"),
                    "additions": item.get("additions"),
                    "deletions": item.get("deletions"),
                    "changes": item.get("changes"),
                }
                for item in result.get("files", [])
            ],
        },
    }


@mcp.tool()
def get_diff(
    sha: str,
    owner: str | None = None,
    repository: str | None = None,
) -> dict[str, Any]:
    """
    Retrieve the patch/diff associated with a GitHub commit.
    """

    owner, repository = _repository(
        owner,
        repository,
    )

    result = _request(
        f"/repos/{owner}/{repository}/commits/{sha}"
    )

    if isinstance(result, dict) and result.get("status") == "error":
        return result

    files = []

    for item in result.get("files", []):
        files.append(
            {
                "filename": item.get("filename"),
                "status": item.get("status"),
                "additions": item.get("additions"),
                "deletions": item.get("deletions"),
                "changes": item.get("changes"),
                "patch": item.get("patch"),
            }
        )

    return {
        "status": "success",
        "repository": f"{owner}/{repository}",
        "commit": {
            "sha": result.get("sha"),
            "message": (
                result.get("commit", {})
                .get("message")
            ),
        },
        "files": files,
    }


if __name__ == "__main__":
    mcp.run()