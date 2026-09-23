"""Pull public issues and discussions on Borr1/gtos into queue fields.

Pull requests are skipped. The caller dedups on source_message_id.
"""

from __future__ import annotations

from typing import Any

from src.feedback.http_retry import HttpJson, next_link

REPO = "Borr1/gtos"
API = "https://api.github.com"
GRAPHQL = "https://api.github.com/graphql"


def _headers(token: str) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def issue_fields(issue: dict[str, Any], *, received_at: str) -> dict[str, Any] | None:
    if not isinstance(issue, dict) or "pull_request" in issue:
        return None
    number = issue.get("number")
    if not isinstance(number, int):
        return None
    user = issue.get("user") if isinstance(issue.get("user"), dict) else {}
    title = issue.get("title") or ""
    body = issue.get("body") or ""
    text = title if not body else f"{title}\n\n{body}"
    return {
        "source": "github_issue",
        "received_at": received_at,
        "source_time": issue.get("created_at") or "",
        "sender": user.get("login") or "",
        "text": text,
        "attachments": [],
        "source_message_id": f"github_issue:{number}",
    }


def _is_receipt(text: str) -> bool:
    body = text.strip()
    prefix = "Received fb-"
    return body.startswith(prefix) and body[len(prefix):].isdigit()


def issue_comment_fields(comment: dict[str, Any], *, received_at: str) -> dict[str, Any] | None:
    if not isinstance(comment, dict):
        return None
    if _is_receipt(str(comment.get("body") or "")):
        return None
    cid = comment.get("id")
    if not isinstance(cid, int):
        return None
    user = comment.get("user") if isinstance(comment.get("user"), dict) else {}
    return {
        "source": "github_issue_comment",
        "received_at": received_at,
        "source_time": comment.get("created_at") or "",
        "sender": user.get("login") or "",
        "text": comment.get("body") or "",
        "attachments": [],
        "source_message_id": f"github_issue_comment:{cid}",
    }


def discussion_fields(node: dict[str, Any], *, received_at: str) -> dict[str, Any] | None:
    number = node.get("number")
    if not isinstance(number, int):
        return None
    author = node.get("author") if isinstance(node.get("author"), dict) else {}
    title = node.get("title") or ""
    body = node.get("body") or ""
    text = title if not body else f"{title}\n\n{body}"
    return {
        "source": "github_discussion",
        "received_at": received_at,
        "source_time": node.get("createdAt") or "",
        "sender": author.get("login") or "",
        "text": text,
        "attachments": [],
        "source_message_id": f"github_discussion:{number}",
    }


def discussion_comment_fields(number: int, comment: dict[str, Any], *, received_at: str) -> dict[str, Any] | None:
    cid = comment.get("id")
    if not isinstance(cid, str) or not cid:
        return None
    if _is_receipt(str(comment.get("body") or "")):
        return None
    author = comment.get("author") if isinstance(comment.get("author"), dict) else {}
    return {
        "source": "github_discussion_comment",
        "received_at": received_at,
        "source_time": comment.get("createdAt") or "",
        "sender": author.get("login") or "",
        "text": comment.get("body") or "",
        "attachments": [],
        "source_message_id": f"github_discussion_comment:{cid}",
    }


class GitHubIntake:
    def __init__(self, token: str = "", http: HttpJson | None = None) -> None:
        self._token = token
        self._http = http or HttpJson()

    def _pages(self, url: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        while url and url not in seen:
            seen.add(url)
            result = self._http("GET", url, headers=_headers(self._token), timeout=30)
            batch = result.body
            if not isinstance(batch, list):
                break
            rows.extend(row for row in batch if isinstance(row, dict))
            url = next_link(result.headers)
        return rows

    def issues(self, since: str = "") -> list[dict[str, Any]]:
        url = f"{API}/repos/{REPO}/issues?state=all&per_page=100&sort=created&direction=asc"
        if since:
            url += "&since=" + since
        return self._pages(url)

    def issue_comments(self, since: str = "") -> list[dict[str, Any]]:
        url = f"{API}/repos/{REPO}/issues/comments?per_page=100&sort=created&direction=asc"
        if since:
            url += "&since=" + since
        return self._pages(url)

    def discussions(self) -> list[dict[str, Any]]:
        query = """
        query {
          repository(owner: "Borr1", name: "gtos") {
            discussions(first: 50, orderBy: {field: CREATED_AT, direction: ASC}) {
              nodes {
                number
                title
                body
                createdAt
                author { login }
                comments(first: 50) { nodes { id body createdAt author { login } } }
              }
            }
          }
        }
        """
        result = self._http(
            "POST",
            GRAPHQL,
            headers=_headers(self._token),
            body={"query": query},
            timeout=30,
        )
        body = result.body if isinstance(result.body, dict) else {}
        repo = ((body.get("data") or {}).get("repository") or {})
        nodes = ((repo.get("discussions") or {}).get("nodes") or [])
        return [node for node in nodes if isinstance(node, dict)]

    def comment_on_issue(self, number: int, item_id: str) -> None:
        if not self._token:
            raise RuntimeError("github receipt needs a host-local token")
        self._http(
            "POST",
            f"{API}/repos/{REPO}/issues/{number}/comments",
            headers=_headers(self._token),
            body={"body": f"Received {item_id}"},
            timeout=30,
        )
