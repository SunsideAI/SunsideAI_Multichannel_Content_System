"""Sunside AI Content Autopilot — Content Strategist Agent.

Compares keyword data with content inventory to identify
the best content opportunities for the upcoming week.
Schedule: Sunday 19:30 (after Keyword Researcher).
"""

import logging

from core import supabase_client as db
from core.claude_client import call_claude_json
from core.config import CLAUDE_TEMP_ANALYTICAL, load_prompt

logger = logging.getLogger(__name__)


def build_strategist_context() -> str:
    """Build the context payload for the Content Strategist prompt."""
    # Content inventory
    pages = db.get_all_pages()
    inventory_text = "CONTENT INVENTORY:\n"
    for p in pages:
        inventory_text += (
            f"- {p.get('url', '')} | Type: {p.get('page_type', '')} | "
            f"Keyword: {p.get('primary_keyword', '')} | "
            f"Words: {p.get('word_count', 0)} | "
            f"Published: {p.get('published_at', 'N/A')}\n"
        )

    # Keyword data
    keywords = db.get_keywords(min_impressions=10, limit=200)
    keywords_text = "\nKEYWORD DATA (GSC, last 28 days):\n"
    for k in keywords:
        keywords_text += (
            f"- \"{k.get('keyword', '')}\" | Impressions: {k.get('impressions', 0)} | "
            f"Clicks: {k.get('clicks', 0)} | CTR: {k.get('ctr', 0)}% | "
            f"Pos: {k.get('avg_position', 'N/A')} | Page: {k.get('ranking_page', 'N/A')}\n"
        )

    # Recently planned/created topics
    recent = db.get_recent_topics(days=30)
    recent_text = "\nRECENTLY CREATED/PLANNED TOPICS (last 30 days):\n"
    for r in recent:
        recent_text += f"- {r.get('title', '')} | Keyword: {r.get('target_keyword', '')}\n"

    # Open opportunities already planned
    open_opps = db.get_open_opportunities(limit=20)
    opps_text = "\nALREADY OPEN OPPORTUNITIES:\n"
    for o in open_opps:
        opps_text += f"- {o.get('target_keyword', '')} | {o.get('type', '')} | {o.get('action', '')}\n"

    return f"{inventory_text}\n{keywords_text}\n{recent_text}\n{opps_text}"


def run() -> dict:
    """Run the content strategist agent."""
    logger.info("Content Strategist starting...")

    system_prompt = load_prompt("content-strategist")
    context = build_strategist_context()

    user_msg = f"""Analysiere die folgenden SEO-Daten und identifiziere die besten Content-Opportunities
für die kommende Woche. Maximal 10 Opportunities. Antworte als JSON-Array.

{context}"""

    try:
        opportunities = call_claude_json(
            user_msg,
            system_prompt=system_prompt,
            temperature=CLAUDE_TEMP_ANALYTICAL,
            max_tokens=4096,
        )
    except Exception as e:
        logger.error(f"Content strategy generation failed: {e}")
        return {"processed": 0, "created": 0}

    if not isinstance(opportunities, list):
        logger.error(f"Expected list of opportunities, got {type(opportunities)}")
        return {"processed": 0, "created": 0}

    # Prepare for storage
    opp_records = []
    for opp in opportunities:
        record = {
            "type": opp.get("type", "keyword_gap"),
            "priority": opp.get("priority", "MEDIUM"),
            "priority_score": opp.get("priority_score", 0),
            "target_keyword": opp.get("target_keyword", ""),
            "related_keywords": opp.get("related_keywords", []),
            "action": opp.get("action", "NEW_POST"),
            "suggested_title": opp.get("suggested_title"),
            "research_query": opp.get("research_query"),
            "existing_url": opp.get("existing_url"),
            "current_position": opp.get("current_position"),
            "impressions": opp.get("impressions", 0),
            "current_ctr": opp.get("current_ctr"),
            "suggested_meta_title": opp.get("suggested_meta_title"),
            "suggested_meta_description": opp.get("suggested_meta_description"),
            "existing_content_to_link": opp.get("existing_content_to_link", []),
        }
        opp_records.append(record)

    if opp_records:
        db.create_opportunities(opp_records)
        logger.info(f"Created {len(opp_records)} content opportunities")

    return {"processed": len(opportunities), "created": len(opp_records)}
