"""Sunside AI Content Autopilot — Email Client via Resend."""

import logging
from typing import Optional

import resend

from core.config import RESEND_API_KEY, RESEND_FROM_EMAIL, NOTIFICATION_EMAIL

logger = logging.getLogger(__name__)

resend.api_key = RESEND_API_KEY


def send_email(
    subject: str,
    html_body: str,
    to: Optional[str] = None,
    attachments: Optional[list] = None,
) -> bool:
    """
    Send an email via Resend, optionally with attachments.

    Args:
        subject: Email subject line
        html_body: HTML content
        to: Recipient (defaults to NOTIFICATION_EMAIL)
        attachments: List of dicts with filename, content (base64), type

    Returns:
        True if sent successfully
    """
    recipient = to or NOTIFICATION_EMAIL

    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email")
        return False

    try:
        params = {
            "from": RESEND_FROM_EMAIL,
            "to": [recipient],
            "subject": subject,
            "html": html_body,
        }
        if attachments:
            params["attachments"] = attachments

        resp = resend.Emails.send(params)
        logger.info(f"Email sent: '{subject}' → {recipient} (id: {resp.get('id', '?')})")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
