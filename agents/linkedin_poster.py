"""Sunside AI Content Autopilot — LinkedIn Poster Agent.

Generates LinkedIn post text and infographics for published blog posts,
then posts to LinkedIn via API.
Schedule: Mon-Fri 10:00 (after blog auto-publish).
"""

import logging
import os
from typing import Optional

from core import supabase_client as db
from core.claude_client import generate_linkedin_text
from core.linkedin_client import upload_image, create_post
from core.config import SITE_URL
from core.notifier import send_linkedin_success, send_error

logger = logging.getLogger(__name__)


def extract_key_points(content: str) -> str:
    """Extract key points from blog content for LinkedIn post generation."""
    import re

    # Extract H2 headings as key points
    h2s = re.findall(r"^## (.+)$", content, re.MULTILINE)
    if h2s:
        return "\n".join(f"- {h}" for h in h2s[:5])

    # Fallback: first 3 paragraphs
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip() and not p.startswith("---")]
    return "\n".join(paragraphs[:3])


def extract_stats(content: str) -> str:
    """Extract statistics/numbers from blog content."""
    import re

    # Find sentences containing numbers/percentages
    sentences = content.replace("\n", " ").split(".")
    stat_sentences = []
    for s in sentences:
        if re.search(r"\d+[%,.]?\d*\s*(Prozent|%|Euro|€|Leads|Kunden|Makler)", s):
            stat_sentences.append(s.strip())
            if len(stat_sentences) >= 3:
                break

    return ". ".join(stat_sentences) if stat_sentences else "Keine spezifischen Statistiken"


def run() -> dict:
    """Run the LinkedIn poster agent."""
    logger.info("LinkedIn Poster starting...")

    # Check if auto-posting is enabled
    auto_post = db.get_config("linkedin_auto_post", True)
    if auto_post in (False, "false"):
        logger.info("LinkedIn auto-posting is disabled")
        return {"processed": 0, "created": 0}

    posts = db.get_posts_to_distribute()
    if not posts:
        logger.info("No posts to distribute")
        return {"processed": 0, "created": 0}

    created = 0

    for post in posts:
        try:
            blog_url = f"{SITE_URL}/blog/{post['slug']}"
            key_points = extract_key_points(post.get("content", ""))
            stats = extract_stats(post.get("content", ""))

            # Generate LinkedIn text via Claude
            linkedin_text = generate_linkedin_text(
                blog_title=post["title"],
                blog_url=blog_url,
                key_points=key_points,
                stats=stats,
            )

            # Generate infographic
            image_path = None
            try:
                from agents.image_generator import generate_infographic
                image_path = generate_infographic(
                    title=post["title"],
                    category=post.get("category", "KI & Automatisierung"),
                    bullets=key_points.split("\n")[:3],
                    blog_url=blog_url,
                )
            except Exception as e:
                logger.warning(f"Infographic generation failed, posting without image: {e}")

            # Upload image and create post
            image_urn = None
            if image_path and os.path.exists(image_path):
                image_urn = upload_image(image_path)

            post_urn = create_post(
                text=linkedin_text,
                image_urn=image_urn,
                image_title=post["title"],
            )

            # Store in DB
            db.create_linkedin_post({
                "blog_post_id": post["id"],
                "post_text": linkedin_text,
                "image_path": image_path,
                "linkedin_post_urn": post_urn,
                "posted_at": __import__("datetime").datetime.utcnow().isoformat(),
                "status": "POSTED",
            })

            send_linkedin_success(post["title"], None)
            created += 1
            logger.info(f"LinkedIn post created for: {post['title']}")

        except Exception as e:
            logger.error(f"LinkedIn posting failed for '{post.get('title', '')}': {e}")
            db.create_linkedin_post({
                "blog_post_id": post["id"],
                "post_text": "",
                "status": "FAILED",
            })
            send_error("linkedin_poster", str(e))

    return {"processed": len(posts), "created": created}
