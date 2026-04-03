"""Sunside AI Content Autopilot — Keyword Researcher Agent.

Collects keyword data from Google Search Console, expands with
Google Autocomplete, and clusters via Claude API.
Schedule: Sunday 19:00 (after Content Crawler).
"""

import logging

from core import supabase_client as db
from core.gsc_client import fetch_keywords
from core.autocomplete_client import expand_keywords, DEFAULT_SEEDS
from core.claude_client import call_claude_json
from core.config import CLAUDE_TEMP_ANALYTICAL

logger = logging.getLogger(__name__)


def fetch_and_store_gsc_keywords() -> list[dict]:
    """Step 1: Fetch keywords from Google Search Console and store them."""
    logger.info("Fetching GSC keywords...")
    keywords = fetch_keywords(days=28, min_impressions=10)

    if keywords:
        db.upsert_keywords(keywords)
        logger.info(f"Stored {len(keywords)} GSC keywords")
    else:
        logger.warning("No keywords returned from GSC")

    return keywords


def fetch_autocomplete_suggestions(gsc_keywords: list[dict]) -> list[dict]:
    """Step 2: Expand top GSC keywords + seeds with autocomplete."""
    logger.info("Fetching autocomplete suggestions...")

    # Top 20 GSC keywords by impressions
    top_gsc = sorted(gsc_keywords, key=lambda k: k.get("impressions", 0), reverse=True)[:20]
    seed_keywords = [k["keyword"] for k in top_gsc] + DEFAULT_SEEDS

    # Deduplicate
    seed_keywords = list(dict.fromkeys(seed_keywords))

    suggestions_map = expand_keywords(seed_keywords)

    # Flatten and prepare for storage
    new_keywords = []
    for seed, suggestions in suggestions_map.items():
        for suggestion in suggestions:
            new_keywords.append({
                "keyword": suggestion,
                "source": "autocomplete",
                "impressions": 0,
                "clicks": 0,
                "ctr": 0,
                "avg_position": None,
            })

    if new_keywords:
        db.upsert_keywords(new_keywords)
        logger.info(f"Stored {len(new_keywords)} autocomplete keywords")

    return new_keywords


def cluster_keywords(all_keywords: list[dict]) -> list[dict]:
    """Step 3: Cluster keywords via Claude API."""
    logger.info("Clustering keywords via Claude...")

    keyword_list = [k["keyword"] for k in all_keywords[:200]]  # Limit for API

    user_msg = f"""Gruppiere diese Keywords in thematische Cluster.
Für jeden Cluster bestimme:
- cluster_name: Kurzer Name des Clusters
- main_keyword: Das Haupt-Keyword (höchstes Suchvolumen-Potenzial)
- related: Liste der verwandten Keywords
- intent: informational, transactional oder navigational

Keywords:
{chr(10).join(f'- {kw}' for kw in keyword_list)}

Antworte als JSON-Array. Nur valides JSON, keine Codeblöcke."""

    try:
        clusters = call_claude_json(user_msg, temperature=CLAUDE_TEMP_ANALYTICAL)

        # Update keywords with cluster assignments
        updates = []
        for cluster in clusters:
            cluster_name = cluster.get("cluster_name", "")
            intent = cluster.get("intent", "unknown")
            for kw in [cluster.get("main_keyword", "")] + cluster.get("related", []):
                if kw:
                    updates.append({
                        "keyword": kw,
                        "cluster_name": cluster_name,
                        "search_intent": intent,
                        "source": "clustering",
                    })

        if updates:
            db.upsert_keywords(updates)
            logger.info(f"Updated {len(updates)} keywords with cluster info")

        return clusters

    except Exception as e:
        logger.error(f"Keyword clustering failed: {e}")
        return []


def run() -> dict:
    """Run the keyword researcher agent."""
    logger.info("Keyword Researcher starting...")

    # Step 1: GSC data
    gsc_keywords = fetch_and_store_gsc_keywords()

    # Step 2: Autocomplete expansion
    autocomplete_keywords = fetch_autocomplete_suggestions(gsc_keywords)

    # Step 3: Clustering
    all_keywords = gsc_keywords + autocomplete_keywords
    clusters = cluster_keywords(all_keywords)

    total_keywords = len(gsc_keywords) + len(autocomplete_keywords)
    logger.info(
        f"Keyword research complete: {len(gsc_keywords)} GSC, "
        f"{len(autocomplete_keywords)} autocomplete, {len(clusters)} clusters"
    )

    return {
        "processed": total_keywords,
        "created": total_keywords,
        "gsc_count": len(gsc_keywords),
        "autocomplete_count": len(autocomplete_keywords),
        "cluster_count": len(clusters),
    }
