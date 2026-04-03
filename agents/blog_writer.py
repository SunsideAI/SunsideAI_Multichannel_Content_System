"""Sunside AI Content Autopilot — Blog Writer Agent.

Creates SEO-optimized blog posts from research findings,
runs quality gate, and handles auto-publishing.
Schedule: Mon-Fri 06:00 (blog creation), 09:00 (auto-publish).
"""

import logging
import re
from datetime import datetime, timedelta

from core import supabase_client as db
from core.claude_client import generate_blog_post, evaluate_quality, call_claude
from core.github_client import commit_blog_post
from core.config import (
    get_icon_for_category, load_knowledge, is_prompt_placeholder,
    load_prompt, SITE_URL, CLAUDE_TEMP_CREATIVE,
)
from core.notifier import send_blog_for_review, send_qa_failure

logger = logging.getLogger(__name__)


def select_internal_links(pages: list[dict], target_keyword: str, limit: int = 5) -> str:
    """Select relevant internal links for a blog post."""
    keyword_lower = target_keyword.lower()
    scored = []
    for page in pages:
        pk = (page.get("primary_keyword") or "").lower()
        title = (page.get("title") or "").lower()
        score = 0
        if keyword_lower in pk or keyword_lower in title:
            score += 3
        for word in keyword_lower.split():
            if word in pk or word in title:
                score += 1
        scored.append((score, page))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

    lines = []
    for _, page in top:
        url = page.get("url", "")
        title = page.get("title", "")
        lines.append(f"- [{title}]({url})")
    return "\n".join(lines) if lines else "Keine passenden internen Links gefunden."


def load_relevant_knowledge(target_keyword: str) -> dict:
    """Load relevant knowledge base snippets for blog context."""
    context = {}

    # Quellensammlung (trimmed)
    try:
        sources = load_knowledge("quellensammlung.md")
        context["sources"] = sources[:2000]
    except FileNotFoundError:
        context["sources"] = ""

    # Fallstudien (only if relevant)
    try:
        cases = load_knowledge("fallstudien.md")
        keyword_lower = target_keyword.lower()
        relevant_keywords = ["lead", "konversion", "website", "chatbot", "ki", "automatisierung"]
        if any(kw in keyword_lower for kw in relevant_keywords):
            context["case_study"] = cases[:1500]
        else:
            context["case_study"] = ""
    except FileNotFoundError:
        context["case_study"] = ""

    return context


def extract_frontmatter(content: str) -> dict:
    """Extract frontmatter fields from markdown content."""
    fm = {}
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if match:
        for line in match.group(1).split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def run() -> dict:
    """Run the blog writer agent — create a new blog post."""
    logger.info("Blog Writer starting...")

    if is_prompt_placeholder("seo-blog-writer"):
        logger.warning("Prompt file 'seo-blog-writer' is a placeholder, skipping agent")
        return {"processed": 0, "created": 0, "skipped": "placeholder_prompt"}

    # Get next finding
    finding = db.get_next_finding()
    if not finding:
        logger.info("No findings available for blog creation")
        return {"processed": 0, "created": 0}

    target_keyword = finding.get("target_keyword", "")
    logger.info(f"Creating blog for: {finding.get('title', '')} (keyword: {target_keyword})")

    # Load context
    pages = db.get_pages_for_linking()
    internal_links = select_internal_links(pages, target_keyword)
    knowledge = load_relevant_knowledge(target_keyword)

    # Check for existing similar content
    recent = db.get_recent_topics(days=30)
    related_content = ""
    for r in recent:
        if target_keyword.lower() in (r.get("target_keyword", "") or "").lower():
            related_content += f"- {r.get('title', '')} (/{r.get('slug', '')})\n"

    context = {
        "internal_links": internal_links,
        "sources": knowledge.get("sources", ""),
        "case_study": knowledge.get("case_study", ""),
        "related_content": related_content or "Kein ähnlicher Content vorhanden",
    }

    # Optional: refresh GSC data on demand before writing
    from core.config import GSC_REFRESH_ON_DEMAND
    if GSC_REFRESH_ON_DEMAND:
        try:
            from core.gsc_client import fetch_page_performance
            fetch_page_performance(url_filter="/blog/", days=7)
            logger.info("Refreshed GSC data on demand before blog creation")
        except Exception as e:
            logger.warning(f"On-demand GSC refresh failed (non-fatal): {e}")

    # Generate blog post
    blog_content = generate_blog_post(finding, context)
    frontmatter = extract_frontmatter(blog_content)

    slug = frontmatter.get("slug", "")
    title = frontmatter.get("title", finding.get("title", ""))
    category = frontmatter.get("category", "KI & Automatisierung")
    meta_desc = frontmatter.get("description", "")

    # Select blog image
    image_filename = f"{get_icon_for_category(category)}.png"

    # Quality Gate — with auto-retry
    qa_result = evaluate_quality(blog_content, target_keyword)
    qa_score = qa_result.get("score", 0)
    original_qa_score = qa_score
    qa_threshold = db.get_qa_threshold()
    qa_passed = qa_result.get("passed", False) and qa_score >= qa_threshold
    retry_count = 0

    if not qa_passed:
        logger.info(f"QA failed ({qa_score}/10), attempting auto-retry...")
        retry_count = 1

        # Build revision prompt from QA feedback
        suggestions = qa_result.get("suggestions", [])
        feedback = qa_result.get("feedback", {})
        feedback_lines = []
        for criterion, details in feedback.items():
            if isinstance(details, dict):
                feedback_lines.append(f"- {criterion}: {details.get('score', '?')}/2 — {details.get('notes', '')}")

        revision_prompt = f"""Der folgende Blogbeitrag hat die Qualitätsprüfung nicht bestanden (Score: {qa_score}/10).

FEEDBACK:
{chr(10).join(feedback_lines)}

VERBESSERUNGSVORSCHLÄGE:
{chr(10).join(f'- {s}' for s in suggestions)}

Bitte überarbeite den Beitrag und behebe die genannten Punkte.
Behalte Struktur, Keyword-Fokus und Länge bei.

ORIGINALER BEITRAG:
{blog_content}"""

        try:
            system_prompt = load_prompt("seo-blog-writer")
            blog_content = call_claude(
                revision_prompt,
                system_prompt=system_prompt,
                temperature=CLAUDE_TEMP_CREATIVE,
            )
            frontmatter = extract_frontmatter(blog_content)
            slug = frontmatter.get("slug", slug)
            title = frontmatter.get("title", title)
            category = frontmatter.get("category", category)
            meta_desc = frontmatter.get("description", meta_desc)

            # Re-evaluate revised post
            qa_result = evaluate_quality(blog_content, target_keyword)
            qa_score = qa_result.get("score", 0)
            qa_passed = qa_result.get("passed", False) and qa_score >= qa_threshold

            if qa_passed:
                logger.info(f"Auto-retry succeeded: {original_qa_score} → {qa_score}")
            else:
                logger.warning(f"Auto-retry also failed: {qa_score}/10")
        except Exception as e:
            logger.error(f"Auto-retry generation failed: {e}")

    status = "QA_PASSED" if qa_passed else "QA_FAILED"
    scheduled_at = None
    if qa_passed:
        delay = int(db.get_config("delay_hours", 2))
        scheduled_at = (datetime.utcnow() + timedelta(hours=delay)).isoformat()

    # Store in DB
    post_data = {
        "finding_id": finding["id"],
        "opportunity_id": finding.get("opportunity_id"),
        "title": title,
        "slug": slug,
        "meta_description": meta_desc,
        "content": blog_content,
        "category": category,
        "image_filename": image_filename,
        "target_keyword": target_keyword,
        "related_keywords": finding.get("related_keywords", []),
        "internal_links_used": [p["url"] for _, p in zip(range(5), pages)],
        "qa_score": qa_score,
        "qa_feedback": qa_result.get("feedback", {}),
        "retry_count": retry_count,
        "original_qa_score": original_qa_score if retry_count > 0 else None,
        "status": status,
        "scheduled_at": scheduled_at,
    }

    db.create_blog_post(post_data)
    db.mark_finding_used(finding["id"])

    # Complete linked opportunity
    if finding.get("opportunity_id"):
        db.complete_opportunity(finding["opportunity_id"])

    # Notifications — send blog review email or QA failure
    if qa_passed:
        send_blog_for_review(
            title=title, qa_score=qa_score, target_keyword=target_keyword,
            content=blog_content, slug=slug, category=category,
        )
    else:
        qa_result_with_note = dict(qa_result)
        if retry_count > 0:
            qa_result_with_note.setdefault("suggestions", []).insert(
                0, f"Auto-Retry fehlgeschlagen (Original: {original_qa_score}, Retry: {qa_score}). Manueller Review nötig."
            )
        send_qa_failure(title, qa_score, qa_result_with_note)

    logger.info(f"Blog post created: '{title}' — QA: {qa_score}/10 ({status}, retries: {retry_count})")
    return {
        "processed": 1, "created": 1, "qa_score": qa_score, "status": status,
        "retry_count": retry_count, "original_qa_score": original_qa_score,
    }


def run_publish() -> dict:
    """Publish blog posts that passed QA and the review window has expired."""
    logger.info("Publisher starting...")

    posts = db.get_posts_to_publish()
    published = 0

    for post in posts:
        try:
            sha = commit_blog_post(post["slug"], post["content"])
            blog_url = f"{SITE_URL}/blog/{post['slug']}"

            db.update_blog_post(post["id"], {
                "status": "PUBLISHED",
                "published_at": datetime.utcnow().isoformat(),
                "github_commit_sha": sha,
                "blog_url": blog_url,
            })

            published += 1
            logger.info(f"Published: {post['title']}")

        except Exception as e:
            logger.error(f"Publish failed for '{post.get('title', '')}': {e}")
            db.update_blog_post(post["id"], {"status": "REVIEW_HOLD"})

    return {"processed": len(posts), "created": published}
