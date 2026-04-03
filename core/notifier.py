"""Sunside AI Content Autopilot — Notifications (Slack / Email)."""

import json
import logging
from typing import Optional

import requests

from core.config import SLACK_WEBHOOK_URL, NOTIFICATION_EMAIL

logger = logging.getLogger(__name__)


def send_slack(message: str, blocks: Optional[list] = None) -> bool:
    """Send a Slack notification via webhook."""
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set, skipping notification")
        return False
    
    payload = {"text": message}
    if blocks:
        payload["blocks"] = blocks
    
    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
        return False


def send_morning_digest(
    blog_title: str,
    qa_score: float,
    target_keyword: str,
    publish_time: str,
    blog_preview_url: Optional[str] = None,
) -> bool:
    """Send the daily morning digest notification."""
    emoji = "✅" if qa_score >= 7.5 else "⚠️"
    
    message = f"""📝 *Content Autopilot — Heute geplant:*

{emoji} *Blog:* {blog_title}
📊 QA-Score: {qa_score}/10
🔑 Keyword: {target_keyword}
⏰ Auto-Publish: {publish_time} Uhr

{"🔗 Preview: " + blog_preview_url if blog_preview_url else ""}

_⏸ "hold" antworten um zu pausieren_"""

    return send_slack(message)


def send_qa_failure(blog_title: str, qa_score: float, feedback: dict) -> bool:
    """Notify about a QA failure."""
    suggestions = feedback.get("suggestions", [])
    suggestions_text = "\n".join(f"  • {s}" for s in suggestions[:3])
    
    message = f"""🚨 *QA Failed — Manueller Review nötig*

Blog: {blog_title}
Score: {qa_score}/10 (Threshold: 7.5)

Feedback:
{suggestions_text}

_Post wurde zurückgehalten._"""

    return send_slack(message)


def send_publish_success(blog_title: str, blog_url: str) -> bool:
    """Notify about successful blog publication."""
    return send_slack(f"✅ *Published:* {blog_title}\n🔗 {blog_url}")


def send_linkedin_success(blog_title: str, linkedin_url: Optional[str] = None) -> bool:
    """Notify about successful LinkedIn post."""
    return send_slack(f"📣 *LinkedIn posted:* {blog_title}\n{'🔗 ' + linkedin_url if linkedin_url else ''}")


def send_error(agent_name: str, error_message: str) -> bool:
    """Notify about an agent error."""
    return send_slack(f"🔴 *Agent Error — {agent_name}*\n```{error_message[:500]}```")


def send_weekly_research_summary(findings_count: int, opportunities_count: int) -> bool:
    """Notify about weekly research results."""
    return send_slack(
        f"🔬 *Research Complete*\n"
        f"📄 {findings_count} Findings gespeichert\n"
        f"🎯 {opportunities_count} Opportunities identifiziert"
    )
