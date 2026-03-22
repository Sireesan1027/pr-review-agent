import httpx
from langchain_core.tools import tool


@tool
async def fetch_github_pr(repo: str, pr_number: int, token: str = "") -> dict:
    """Fetch a GitHub pull request diff and metadata.

    Args:
        repo: Repository in 'owner/repo' format.
        pr_number: Pull request number.
        token: Optional GitHub personal access token (for private repos).

    Returns:
        Dict with diff, title, author, base_branch, head_branch, additions, deletions, changed_files.
    """
    headers = {"User-Agent": "pr-review-agent"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30) as client:
        # Metadata
        meta_resp = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
            headers=headers,
        )
        if meta_resp.status_code == 401:
            raise ValueError("Invalid GitHub token.")
        if meta_resp.status_code == 403:
            raise ValueError("GitHub rate limit hit or token lacks 'repo' scope.")
        if meta_resp.status_code == 404:
            raise ValueError(f"PR #{pr_number} not found in '{repo}'.")
        meta_resp.raise_for_status()
        m = meta_resp.json()

        # Raw diff
        diff_resp = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}",
            headers={**headers, "Accept": "application/vnd.github.v3.diff"},
        )
        diff_resp.raise_for_status()
        diff = diff_resp.text

    if len(diff) > 150_000:
        raise ValueError("Diff too large (>150 KB). Paste a smaller portion manually.")

    return {
        "diff": diff,
        "title": m.get("title", ""),
        "author": m.get("user", {}).get("login", ""),
        "base_branch": m.get("base", {}).get("ref", ""),
        "head_branch": m.get("head", {}).get("ref", ""),
        "additions": m.get("additions", 0),
        "deletions": m.get("deletions", 0),
        "changed_files": m.get("changed_files", 0),
        "body": m.get("body", "") or "",
    }
