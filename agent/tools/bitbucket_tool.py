import httpx
from langchain_core.tools import tool


@tool
async def fetch_bitbucket_pr(workspace: str, repo: str, pr_number: int, token: str = "") -> dict:
    """Fetch a Bitbucket pull request diff and metadata.

    Args:
        workspace: Bitbucket workspace (account or team slug).
        repo: Repository slug.
        pr_number: Pull request ID.
        token: Optional Bitbucket app password or access token.

    Returns:
        Dict with diff, title, author, base_branch, head_branch, additions, deletions, changed_files.
    """
    base = "https://api.bitbucket.org/2.0"
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30) as client:
        # Metadata
        meta_resp = await client.get(
            f"{base}/repositories/{workspace}/{repo}/pullrequests/{pr_number}",
            headers=headers,
        )
        if meta_resp.status_code == 401:
            raise ValueError("Invalid Bitbucket token.")
        if meta_resp.status_code == 404:
            raise ValueError(f"PR #{pr_number} not found in '{workspace}/{repo}'.")
        meta_resp.raise_for_status()
        m = meta_resp.json()

        # Raw diff
        diff_resp = await client.get(
            f"{base}/repositories/{workspace}/{repo}/pullrequests/{pr_number}/diff",
            headers={**headers, "Accept": "text/plain"},
        )
        diff_resp.raise_for_status()
        diff = diff_resp.text

    if len(diff) > 150_000:
        raise ValueError("Diff too large (>150 KB). Paste a smaller portion manually.")

    participants = m.get("participants", [])
    author = m.get("author", {}).get("display_name", "")

    return {
        "diff": diff,
        "title": m.get("title", ""),
        "author": author,
        "base_branch": m.get("destination", {}).get("branch", {}).get("name", ""),
        "head_branch": m.get("source", {}).get("branch", {}).get("name", ""),
        "additions": 0,   # Bitbucket API doesn't return these in metadata
        "deletions": 0,
        "changed_files": 0,
        "body": m.get("description", "") or "",
    }
