"""Sunside AI Content Autopilot — Research Agent.

Searches RSS feeds, Semantic Scholar, and other sources for relevant
articles and studies, guided by content opportunities.
Schedule: Sunday 20:00 (after Content Strategist).
"""

import logging
import time
from typing import Optional

import feedparser
import requests
import yaml

from core import supabase_client as db
from core.claude_client import call_claude_json
from core.config import FEEDS_FILE, CLAUDE_TEMP_ANALYTICAL, load_prompt

logger = logging.getLogger(__name__)


def load_feed_sources() -> dict:
    """Load feed sources from YAML config."""
    with open(FEEDS_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_rss_articles(feed_url: str, feed_name: str) -> list[dict]:
    """Fetch articles from an RSS feed."""
    try:
        parsed = feedparser.parse(feed_url)
        articles = []
        for entry in parsed.entries[:20]:  # Max 20 per feed
            articles.append({
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "summary": entry.get("summary", "")[:500],
                "published": entry.get("published", ""),
                "source": feed_name,
                "source_type": "rss",
            })
        return articles
    except Exception as e:
        logger.warning(f"Failed to parse RSS feed '{feed_name}': {e}")
        return []


def fetch_scholar_articles(keywords: list[str], max_results: int = 20) -> list[dict]:
    """Fetch articles from Semantic Scholar API."""
    articles = []
    for keyword in keywords[:5]:  # Limit API calls
        try:
            resp = requests.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": keyword, "limit": max_results, "fields": "title,abstract,url,year"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            for paper in data.get("data", []):
                articles.append({
                    "title": paper.get("title", ""),
                    "url": paper.get("url", ""),
                    "summary": (paper.get("abstract") or "")[:500],
                    "published": str(paper.get("year", "")),
                    "source": "Semantic Scholar",
                    "source_type": "scholar",
                })
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            logger.warning(f"Scholar search failed for '{keyword}': {e}")

    return articles


def fetch_all_articles() -> list[dict]:
    """Fetch articles from all configured sources."""
    sources = load_feed_sources()
    all_articles = []

    for feed in sources.get("feeds", []):
        feed_type = feed.get("type", "rss")

        if feed_type == "rss":
            articles = fetch_rss_articles(feed["url"], feed["name"])
            all_articles.extend(articles)
            time.sleep(0.3)

        elif feed_type == "scholar":
            from feeds import keywords as kw_file
            kw_path = FEEDS_FILE.parent / "keywords.yaml"
            with open(kw_path, encoding="utf-8") as f:
                kw_config = yaml.safe_load(f)
            scholar_keywords = kw_config.get("scholar_keywords", [])
            articles = fetch_scholar_articles(scholar_keywords)
            all_articles.extend(articles)

    logger.info(f"Fetched {len(all_articles)} articles from all sources")
    return all_articles


def evaluate_articles(articles: list[dict], opportunities: list[dict]) -> list[dict]:
    """Use Claude to evaluate and filter articles for relevance."""
    system_prompt = load_prompt("research-agent")

    # Build opportunity context
    opp_context = ""
    if opportunities:
        opp_context = "\n\nACTIVE OPPORTUNITIES (prioritize research for these):\n"
        for opp in opportunities:
            opp_context += (
                f"- Keyword: {opp.get('target_keyword', '')} | "
                f"Query: {opp.get('research_query', '')} | "
                f"Title: {opp.get('suggested_title', '')}\n"
            )

    # Batch articles (max ~50 at a time to avoid token limits)
    articles_json = []
    for a in articles[:60]:
        articles_json.append({
            "title": a["title"],
            "source": a["source"],
            "url": a["url"],
            "summary": a["summary"],
            "date": a["published"],
        })

    import json
    user_msg = f"""Bewerte diese Artikel/Studien und filtere die Top-Findings heraus.
{opp_context}

ARTIKEL:
{json.dumps(articles_json, ensure_ascii=False, indent=2)}"""

    try:
        findings = call_claude_json(
            user_msg,
            system_prompt=system_prompt,
            temperature=CLAUDE_TEMP_ANALYTICAL,
            max_tokens=4096,
        )
        return findings if isinstance(findings, list) else []
    except Exception as e:
        logger.error(f"Article evaluation failed: {e}")
        return []


def match_findings_to_opportunities(
    findings: list[dict], opportunities: list[dict]
) -> list[dict]:
    """Match findings to opportunities based on keyword overlap."""
    for finding in findings:
        target_kw = finding.get("target_keyword", "").lower()
        for opp in opportunities:
            opp_kw = opp.get("target_keyword", "").lower()
            if opp_kw and (opp_kw in target_kw or target_kw in opp_kw):
                finding["opportunity_id"] = opp.get("id")
                break
    return findings


def run() -> dict:
    """Run the research agent."""
    logger.info("Research Agent starting...")

    # Load opportunities to guide research
    opportunities = db.get_opportunities_for_research()
    logger.info(f"Found {len(opportunities)} open opportunities for research")

    # Fetch articles from all sources
    articles = fetch_all_articles()

    if not articles:
        logger.warning("No articles fetched — skipping evaluation")
        return {"processed": 0, "created": 0}

    # Evaluate with Claude
    evaluated = evaluate_articles(articles, opportunities)

    if not evaluated:
        logger.warning("No relevant findings after evaluation")
        return {"processed": len(articles), "created": 0}

    # Match to opportunities
    matched = match_findings_to_opportunities(evaluated, opportunities)

    # Store findings
    finding_records = []
    for f in matched:
        record = {
            "title": f.get("title", ""),
            "source_name": f.get("source", ""),
            "source_url": f.get("url", f.get("source_url", "")),
            "key_insight": f.get("key_insight", ""),
            "stats": f.get("stats", ""),
            "relevance_score": f.get("relevance_score", 0),
            "blog_angle": f.get("blog_angle", ""),
            "target_keyword": f.get("target_keyword", ""),
            "opportunity_id": f.get("opportunity_id"),
        }
        finding_records.append(record)

    if finding_records:
        db.create_findings(finding_records)
        logger.info(f"Stored {len(finding_records)} findings")

    from core.notifier import send_weekly_research_summary
    send_weekly_research_summary(len(finding_records), len(opportunities))

    return {
        "processed": len(articles),
        "created": len(finding_records),
        "opportunities_matched": sum(1 for f in matched if f.get("opportunity_id")),
    }
