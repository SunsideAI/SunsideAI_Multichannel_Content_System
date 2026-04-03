"""Sunside AI Content Autopilot — LinkedIn API v2 Client."""

import logging
from typing import Optional

import requests

from core.config import LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_ID

logger = logging.getLogger(__name__)

API_BASE = "https://api.linkedin.com/v2"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def upload_image(image_path: str) -> Optional[str]:
    """
    Upload an image to LinkedIn and return the media URN.

    Args:
        image_path: Local path to the image file

    Returns:
        The uploaded image URN (e.g. "urn:li:digitalmediaAsset:xxx")
    """
    author = f"urn:li:person:{LINKEDIN_PERSON_ID}"

    # Step 1: Register upload
    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": author,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent",
            }],
        }
    }

    resp = requests.post(
        f"{API_BASE}/assets?action=registerUpload",
        headers=_headers(),
        json=register_payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    upload_url = data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset = data["value"]["asset"]

    # Step 2: Upload binary
    with open(image_path, "rb") as f:
        upload_resp = requests.put(
            upload_url,
            headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}"},
            data=f,
            timeout=60,
        )
        upload_resp.raise_for_status()

    logger.info(f"Uploaded image to LinkedIn: {asset}")
    return asset


def create_post(
    text: str,
    image_urn: Optional[str] = None,
    image_title: Optional[str] = None,
) -> str:
    """
    Create a LinkedIn UGC post.

    Args:
        text: The post text
        image_urn: Optional media URN from upload_image()
        image_title: Optional title for the image

    Returns:
        The LinkedIn post URN
    """
    author = f"urn:li:person:{LINKEDIN_PERSON_ID}"

    share_content = {
        "shareCommentary": {"text": text},
    }

    if image_urn:
        share_content["shareMediaCategory"] = "IMAGE"
        share_content["media"] = [{
            "status": "READY",
            "media": image_urn,
            "title": {"text": image_title or ""},
        }]
    else:
        share_content["shareMediaCategory"] = "NONE"

    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": share_content,
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
        },
    }

    resp = requests.post(
        f"{API_BASE}/ugcPosts",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()

    post_urn = resp.json().get("id", "")
    logger.info(f"Created LinkedIn post: {post_urn}")
    return post_urn


def check_token_expiry() -> Optional[int]:
    """
    Check remaining days until token expires.
    Returns None if unable to determine.
    """
    try:
        resp = requests.get(
            f"{API_BASE}/me",
            headers=_headers(),
            timeout=10,
        )
        if resp.status_code == 401:
            logger.warning("LinkedIn token expired or invalid")
            return 0
        resp.raise_for_status()
        return None  # Token is valid but expiry date not available via this endpoint
    except Exception as e:
        logger.error(f"Failed to check LinkedIn token: {e}")
        return None
