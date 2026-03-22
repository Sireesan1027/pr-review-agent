"""
PR Review Agent — FastAPI Backend
"""

import asyncio
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()  # reads .env if present
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from agent.graph import stream_review
from agent.llm_factory import PROVIDER_MODELS

app = FastAPI(title="PR Review Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"


# ── Serve UI ───────────────────────────────────────────────────────────────

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok"}


# ── LLM providers metadata (used by frontend to build dropdowns) ───────────

@app.get("/api/providers")
async def providers():
    return PROVIDER_MODELS


# ── Fetch PR ───────────────────────────────────────────────────────────────

class FetchPRRequest(BaseModel):
    host: str          # "github" | "bitbucket"
    token: str = ""
    repo: str          # "owner/repo"  or  "workspace/repo"
    pr_number: int


@app.post("/api/fetch-pr")
async def fetch_pr(req: FetchPRRequest):
    # Use token from request; fall back to env var
    token = req.token.strip() or os.getenv("GITHUB_TOKEN", "")
    headers = {"User-Agent": "pr-review-agent"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=30) as client:
        if req.host == "github":
            meta_url = f"https://api.github.com/repos/{req.repo}/pulls/{req.pr_number}"
            meta_r = await client.get(meta_url, headers=headers)
            _raise_for_git_error(meta_r, "GitHub", req.pr_number, req.repo)
            m = meta_r.json()

            diff_r = await client.get(
                meta_url,
                headers={**headers, "Accept": "application/vnd.github.v3.diff"},
            )
            diff_r.raise_for_status()
            diff = diff_r.text

            return {
                "diff": _check_diff_size(diff),
                "title": m.get("title", ""),
                "author": m.get("user", {}).get("login", ""),
                "base_branch": m.get("base", {}).get("ref", ""),
                "head_branch": m.get("head", {}).get("ref", ""),
                "additions": m.get("additions", 0),
                "deletions": m.get("deletions", 0),
                "changed_files": m.get("changed_files", 0),
                "body": m.get("body", "") or "",
            }

        elif req.host == "bitbucket":
            parts = req.repo.split("/", 1)
            if len(parts) != 2:
                raise HTTPException(400, "Repo must be 'workspace/repo' for Bitbucket.")
            workspace, repo_slug = parts
            base = "https://api.bitbucket.org/2.0"

            meta_r = await client.get(
                f"{base}/repositories/{workspace}/{repo_slug}/pullrequests/{req.pr_number}",
                headers=headers,
            )
            _raise_for_git_error(meta_r, "Bitbucket", req.pr_number, req.repo)
            m = meta_r.json()

            diff_r = await client.get(
                f"{base}/repositories/{workspace}/{repo_slug}/pullrequests/{req.pr_number}/diff",
                headers={**headers, "Accept": "text/plain"},
            )
            diff_r.raise_for_status()
            diff = diff_r.text

            return {
                "diff": _check_diff_size(diff),
                "title": m.get("title", ""),
                "author": m.get("author", {}).get("display_name", ""),
                "base_branch": m.get("destination", {}).get("branch", {}).get("name", ""),
                "head_branch": m.get("source", {}).get("branch", {}).get("name", ""),
                "additions": 0,
                "deletions": 0,
                "changed_files": 0,
                "body": m.get("description", "") or "",
            }

        else:
            raise HTTPException(400, f"Unknown host: {req.host!r}. Use 'github' or 'bitbucket'.")


def _raise_for_git_error(resp: httpx.Response, host: str, pr_number: int, repo: str):
    if resp.status_code == 401:
        raise HTTPException(401, f"Invalid {host} token.")
    if resp.status_code == 403:
        raise HTTPException(403, f"{host} rate limit hit or token lacks required scope.")
    if resp.status_code == 404:
        raise HTTPException(404, f"PR #{pr_number} not found in '{repo}'.")
    resp.raise_for_status()


def _check_diff_size(diff: str) -> str:
    if len(diff) > 150_000:
        raise HTTPException(413, "Diff too large (>150 KB). Paste a smaller portion manually.")
    return diff


# ── Review (SSE stream) ────────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    llm_provider: str
    api_key: str
    model: str
    diff: str
    pr_title: str = ""
    pr_description: str = ""


ENV_KEYS = {
    "groq":     os.getenv("GROQ_API_KEY", ""),
    "openai":   os.getenv("OPENAI_API_KEY", ""),
    "anthropic":os.getenv("ANTHROPIC_API_KEY", ""),
    "gemini":   os.getenv("GOOGLE_API_KEY", ""),
}

@app.get("/api/env-key")
async def env_key(provider: str):
    """Return whether an env key exists for a provider (value hidden)."""
    key = ENV_KEYS.get(provider.lower(), "")
    return {"has_key": bool(key)}

@app.post("/api/review")
async def review(req: ReviewRequest):
    # Fall back to env key if the user left the field blank
    api_key = req.api_key.strip() or ENV_KEYS.get(req.llm_provider.lower(), "")
    if not api_key:
        raise HTTPException(400, "API key is required.")
    if not req.diff.strip():
        raise HTTPException(400, "Diff is required.")

    async def event_stream():
        try:
            async for chunk in stream_review(
                provider=req.llm_provider,
                api_key=api_key,
                model=req.model,
                diff=req.diff,
                pr_title=req.pr_title,
                pr_description=req.pr_description,
            ):
                if chunk:
                    yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
