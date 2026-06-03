"""GitHub integration — repos, issues, PRs via REST API."""
import os
import requests

_TOKEN = os.environ.get("GITHUB_TOKEN", "")
_BASE = "https://api.github.com"


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if _TOKEN:
        h["Authorization"] = f"Bearer {_TOKEN}"
    return h


def _get(path: str, params: dict | None = None) -> dict | list:
    resp = requests.get(f"{_BASE}{path}", headers=_headers(), params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ── repos ─────────────────────────────────────────────────────────────────────

def github_repos(user: str = "", max_results: int = 10) -> dict:
    """List GitHub repos for a user (or authenticated user if empty)."""
    if not _TOKEN and not user:
        return {"error": "Imposta GITHUB_TOKEN nel .env o specifica un username."}
    path = f"/users/{user}/repos" if user else "/user/repos"
    data = _get(path, {"per_page": max_results, "sort": "updated", "direction": "desc"})
    repos = [
        {
            "name":        r["name"],
            "full_name":   r["full_name"],
            "description": r.get("description", ""),
            "language":    r.get("language", ""),
            "stars":       r.get("stargazers_count", 0),
            "open_issues": r.get("open_issues_count", 0),
            "updated":     r.get("updated_at", ""),
            "url":         r.get("html_url", ""),
        }
        for r in (data if isinstance(data, list) else [])
    ]
    return {"repos": repos, "count": len(repos)}


# ── issues ────────────────────────────────────────────────────────────────────

def github_issues(repo: str, state: str = "open", max_results: int = 10) -> dict:
    """List issues for a repo. repo format: 'owner/repo-name'."""
    if "/" not in repo:
        return {"error": "Formato repo non valido. Usa 'owner/repo-name'."}
    data = _get(f"/repos/{repo}/issues",
                {"state": state, "per_page": max_results, "sort": "updated"})
    issues = [
        {
            "number":  i["number"],
            "title":   i["title"],
            "state":   i["state"],
            "author":  i["user"]["login"],
            "created": i.get("created_at", ""),
            "labels":  [l["name"] for l in i.get("labels", [])],
            "url":     i.get("html_url", ""),
            "body":    (i.get("body") or "")[:400],
        }
        for i in (data if isinstance(data, list) else [])
        if "pull_request" not in i   # exclude PRs from issues list
    ]
    return {"repo": repo, "state": state, "issues": issues, "count": len(issues)}


# ── pull requests ─────────────────────────────────────────────────────────────

def github_prs(repo: str, state: str = "open", max_results: int = 10) -> dict:
    """List pull requests for a repo."""
    if "/" not in repo:
        return {"error": "Formato repo non valido. Usa 'owner/repo-name'."}
    data = _get(f"/repos/{repo}/pulls",
                {"state": state, "per_page": max_results, "sort": "updated"})
    prs = [
        {
            "number":   p["number"],
            "title":    p["title"],
            "state":    p["state"],
            "author":   p["user"]["login"],
            "branch":   p["head"]["ref"],
            "created":  p.get("created_at", ""),
            "draft":    p.get("draft", False),
            "url":      p.get("html_url", ""),
        }
        for p in (data if isinstance(data, list) else [])
    ]
    return {"repo": repo, "state": state, "prs": prs, "count": len(prs)}


# ── search ────────────────────────────────────────────────────────────────────

def github_search(query: str, kind: str = "repositories", max_results: int = 8) -> dict:
    """Search GitHub. kind: 'repositories', 'issues', 'code', 'users'."""
    data = _get(f"/search/{kind}", {"q": query, "per_page": max_results})
    items = data.get("items", [])
    total = data.get("total_count", 0)
    results = []
    for it in items:
        results.append({
            "name":        it.get("full_name") or it.get("name") or it.get("login", ""),
            "description": it.get("description", ""),
            "url":         it.get("html_url", ""),
            "stars":       it.get("stargazers_count"),
            "language":    it.get("language"),
        })
    return {"query": query, "kind": kind, "total": total, "results": results}
