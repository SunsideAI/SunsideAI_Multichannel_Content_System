"""Sunside AI Content Autopilot — GitHub API Client."""

import base64
import logging
from typing import Optional

import requests

from core.config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH, BLOG_PATH_IN_REPO

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }


def get_file_sha(path: str) -> Optional[str]:
    """Get the SHA of an existing file (needed for updates)."""
    url = f"{API_BASE}/repos/{GITHUB_REPO}/contents/{path}"
    resp = requests.get(url, headers=_headers(), params={"ref": GITHUB_BRANCH}, timeout=15)
    if resp.status_code == 200:
        return resp.json().get("sha")
    return None


def commit_blog_post(slug: str, content: str, commit_message: Optional[str] = None) -> str:
    """
    Commit a blog post markdown file to the website repo.

    Args:
        slug: The blog post slug (used as filename)
        content: Full markdown content including frontmatter
        commit_message: Optional custom commit message

    Returns:
        The commit SHA
    """
    path = f"{BLOG_PATH_IN_REPO}/{slug}.md"
    message = commit_message or f"feat(blog): add post '{slug}'"

    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    payload = {
        "message": message,
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }

    # Check if file exists (update vs create)
    existing_sha = get_file_sha(path)
    if existing_sha:
        payload["sha"] = existing_sha
        payload["message"] = commit_message or f"feat(blog): update post '{slug}'"

    url = f"{API_BASE}/repos/{GITHUB_REPO}/contents/{path}"
    resp = requests.put(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()

    sha = resp.json().get("commit", {}).get("sha", "")
    logger.info(f"Committed blog post '{slug}' — SHA: {sha}")
    return sha


def update_frontmatter(slug: str, new_frontmatter_fields: dict) -> str:
    """
    Update only the frontmatter of an existing blog post (for CTR optimizations).

    Args:
        slug: Blog post slug
        new_frontmatter_fields: Dict of fields to update (e.g. title, description)

    Returns:
        The commit SHA
    """
    path = f"{BLOG_PATH_IN_REPO}/{slug}.md"
    url = f"{API_BASE}/repos/{GITHUB_REPO}/contents/{path}"

    # Fetch current file
    resp = requests.get(url, headers=_headers(), params={"ref": GITHUB_BRANCH}, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    current_content = base64.b64decode(data["content"]).decode("utf-8")
    sha = data["sha"]

    # Parse and update frontmatter
    updated = _update_frontmatter_in_content(current_content, new_frontmatter_fields)

    encoded = base64.b64encode(updated.encode("utf-8")).decode("utf-8")
    payload = {
        "message": f"fix(seo): update meta for '{slug}'",
        "content": encoded,
        "sha": sha,
        "branch": GITHUB_BRANCH,
    }

    resp = requests.put(url, headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()

    commit_sha = resp.json().get("commit", {}).get("sha", "")
    logger.info(f"Updated frontmatter for '{slug}' — SHA: {commit_sha}")
    return commit_sha


def _update_frontmatter_in_content(content: str, updates: dict) -> str:
    """Replace frontmatter fields in a markdown file."""
    if not content.startswith("---"):
        return content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return content

    fm_lines = parts[1].strip().split("\n")
    updated_keys = set()

    new_lines = []
    for line in fm_lines:
        key = line.split(":")[0].strip() if ":" in line else None
        if key and key in updates:
            new_lines.append(f'{key}: "{updates[key]}"')
            updated_keys.add(key)
        else:
            new_lines.append(line)

    # Add any new keys not already in frontmatter
    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f'{key}: "{value}"')

    return f"---\n{chr(10).join(new_lines)}\n---{parts[2]}"
