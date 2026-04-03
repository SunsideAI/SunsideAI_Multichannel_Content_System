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
) -> bool:
    """
    Send an email via Resend.

    Args:
        subject: Email subject line
        html_body: HTML content
        to: Recipient (defaults to NOTIFICATION_EMAIL)

    Returns:
        True if sent successfully
    """
    recipient = to or NOTIFICATION_EMAIL

    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email")
        return False

    try:
        resp = resend.Emails.send({
            "from": RESEND_FROM_EMAIL,
            "to": [recipient],
            "subject": subject,
            "html": html_body,
        })
        logger.info(f"Email sent: '{subject}' → {recipient} (id: {resp.get('id', '?')})")
        return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False
