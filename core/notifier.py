"""Sunside AI Content Autopilot — Email Notifications via Resend."""

import logging
from core.email_client import send_email

logger = logging.getLogger(__name__)


def _wrap_email(title: str, body: str) -> str:
    """Wrap content in Sunside AI email template."""
    return f"""
    <div style="max-width:640px;margin:0 auto;font-family:-apple-system,system-ui,sans-serif;color:#1a1a1a;">
      <div style="background:#0F0A15;padding:24px 32px;border-radius:12px 12px 0 0;">
        <span style="color:#9A40C9;font-weight:600;font-size:14px;">SUNSIDE AI</span>
        <span style="color:#666;font-size:14px;margin-left:8px;">Content Autopilot</span>
      </div>
      <div style="border:1px solid #e5e5e5;border-top:none;border-radius:0 0 12px 12px;padding:32px;">
        <h1 style="font-size:20px;margin:0 0 24px;">{title}</h1>
        {body}
      </div>
      <p style="text-align:center;font-size:12px;color:#999;margin-top:16px;">
        Sunside AI GbR — Automatisch generiert
      </p>
    </div>"""


def send_weekly_blog_batch(posts: list[dict]) -> bool:
    """Send all weekly blog posts in one email with .md attachments."""
    if not posts:
        return False

    avg_score = sum(p.get("qa_score", 0) for p in posts) / len(posts)

    rows = ""
    for i, p in enumerate(posts, 1):
        sc = "#22c55e" if p.get("qa_score", 0) >= 7.5 else "#f59e0b"
        rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;">{i}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:14px;">{p.get('title','')}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;text-align:center;">
            <span style="color:{sc};font-weight:600;">{p.get('qa_score','—')}/10</span>
          </td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:13px;color:#666;">{p.get('target_keyword','')}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:13px;color:#666;">{p.get('slug','')}</td>
        </tr>"""

    body = f"""
    <p style="margin:0 0 20px;line-height:1.6;">
      {len(posts)} Blog-Posts erstellt. Durchschnittlicher QA-Score:
      <strong>{avg_score:.1f}/10</strong>.
    </p>
    <table style="width:100%;border-collapse:collapse;margin-bottom:24px;">
      <tr style="background:#f8f8f8;">
        <th style="padding:8px 12px;text-align:left;font-size:12px;color:#666;">#</th>
        <th style="padding:8px 12px;text-align:left;font-size:12px;color:#666;">Titel</th>
        <th style="padding:8px 12px;text-align:center;font-size:12px;color:#666;">QA</th>
        <th style="padding:8px 12px;text-align:left;font-size:12px;color:#666;">Keyword</th>
        <th style="padding:8px 12px;text-align:left;font-size:12px;color:#666;">Slug</th>
      </tr>
      {rows}
    </table>
    <p style="font-size:13px;color:#666;margin:0;">
      Die .md Dateien hängen an dieser Mail. Posts die du publishen willst
      legst du ins Website-Repo unter content/blog/[slug].md —
      LinkedIn postet dann automatisch.
    </p>"""

    import base64
    attachments = []
    for p in posts:
        content = p.get("content", "")
        filename = f"{p.get('slug', 'post')}.md"
        attachments.append({
            "filename": filename,
            "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
            "type": "text/markdown",
        })

    return send_email(
        subject=f"📝 {len(posts)} Blog-Posts zur Review — KW {_calendar_week()}",
        html_body=_wrap_email("Wöchentliche Blog-Posts", body),
        attachments=attachments,
    )


def _calendar_week() -> str:
    """Return current ISO calendar week number."""
    from datetime import date
    return str(date.today().isocalendar()[1])


def send_qa_failure(title: str, qa_score: float, feedback: dict) -> bool:
    """Notify about QA failure after auto-retry also failed."""
    suggestions = feedback.get("suggestions", [])
    items = "".join(f"<li>{s}</li>" for s in suggestions[:5])

    body = f"""
    <p style="margin:0 0 12px;color:#dc2626;font-weight:500;">
      Auto-Retry fehlgeschlagen — manueller Review nötig
    </p>
    <p style="margin:0 0 16px;">
      <strong>{title}</strong> hat auch nach automatischer Überarbeitung
      den QA-Threshold nicht erreicht (Score: {qa_score}/10).
    </p>
    <ul style="margin:0 0 16px;padding-left:20px;color:#666;">{items}</ul>
    <p style="font-size:13px;color:#666;">
      Den Post findest du in Supabase → blog_posts → Status: QA_FAILED
    </p>"""

    return send_email(
        subject=f"⚠️ QA Failed: {title}",
        html_body=_wrap_email("Quality Gate nicht bestanden", body),
    )


def send_linkedin_success(title: str, linkedin_url: str = None) -> bool:
    body = f"""<p>LinkedIn-Post veröffentlicht für: <strong>{title}</strong></p>
    {"<p><a href='" + linkedin_url + "' style='color:#7B3ABF;'>Post ansehen</a></p>" if linkedin_url else ""}"""
    return send_email(
        subject=f"✅ LinkedIn: {title}",
        html_body=_wrap_email("LinkedIn-Post live", body),
    )


def send_error(agent_name: str, error_message: str) -> bool:
    body = f"""
    <p style="color:#dc2626;">Agent <strong>{agent_name}</strong> ist fehlgeschlagen:</p>
    <pre style="background:#f8f8f8;padding:12px;border-radius:6px;font-size:13px;overflow-x:auto;">{error_message[:500]}</pre>"""
    return send_email(
        subject=f"🔴 Agent Error: {agent_name}",
        html_body=_wrap_email("Agent-Fehler", body),
    )


def send_weekly_research_summary(findings_count: int, opportunities_count: int) -> bool:
    body = f"""
    <table style="width:100%;border-collapse:collapse;">
      <tr><td style="padding:8px;background:#f8f8f8;border-radius:6px;text-align:center;">
        <span style="font-size:12px;color:#666;">Findings</span><br>
        <strong style="font-size:24px;">{findings_count}</strong>
      </td>
      <td style="width:12px;"></td>
      <td style="padding:8px;background:#f8f8f8;border-radius:6px;text-align:center;">
        <span style="font-size:12px;color:#666;">Opportunities</span><br>
        <strong style="font-size:24px;">{opportunities_count}</strong>
      </td></tr>
    </table>"""
    return send_email(
        subject=f"🔬 Research: {findings_count} Findings, {opportunities_count} Opportunities",
        html_body=_wrap_email("Wöchentliches Research-Ergebnis", body),
    )
