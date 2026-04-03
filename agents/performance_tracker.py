"""Sunside AI Content Autopilot — Performance Tracker Agent.

Collects GSC performance data for published blog posts, detects trends,
and generates a performance summary for the Content Strategist.
Schedule: Sunday 17:00 (BEFORE all other agents).
"""

import logging
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

from core import supabase_client as db
from core.gsc_client import fetch_page_performance, fetch_keywords

logger = logging.getLogger(__name__)


def _slug_from_url(url: str) -> str:
    """Extract blog slug from a full URL."""
    path = urlparse(url).path.rstrip("/")
    if "/blog/" in path:
        return path.split("/blog/")[-1]
    return path


def collect_blog_performance() -> list[dict]:
    """Fetch GSC data for blog posts and match to published posts in DB."""
    # Get all published blog posts from DB
    published = db.get_client().table("blog_posts") \
        .select("id, slug, title, category, target_keyword, published_at") \
        .eq("status", "PUBLISHED") \
        .execute().data

    if not published:
        logger.info("No published posts to track")
        return []

    slug_to_post = {p["slug"]: p for p in published}

    # Fetch page-level GSC data for /blog/
    page_data = fetch_page_performance(url_filter="/blog/", days=28)

    # Fetch keyword data to find top keywords per page
    keyword_data = fetch_keywords(days=28, min_impressions=5)
    page_keywords = defaultdict(list)
    for kw in keyword_data:
        page_url = kw.get("ranking_page", "")
        page_keywords[page_url].append({
            "keyword": kw["keyword"],
            "impressions": kw["impressions"],
            "clicks": kw["clicks"],
            "position": kw["avg_position"],
        })

    # Match GSC data to DB posts
    records = []
    for page in page_data:
        slug = _slug_from_url(page["page"])
        post = slug_to_post.get(slug)
        if not post:
            continue

        # Get top 5 keywords for this page
        top_kws = sorted(
            page_keywords.get(page["page"], []),
            key=lambda k: k["impressions"],
            reverse=True,
        )[:5]

        records.append({
            "blog_post_id": post["id"],
            "impressions": page["impressions"],
            "clicks": page["clicks"],
            "ctr": page["ctr"],
            "avg_position": page["avg_position"],
            "top_keywords": top_kws,
        })

    return records


def build_performance_summary(records: list[dict]) -> dict:
    """Build an aggregated performance summary grouped by category."""
    # Get post metadata for category grouping
    post_ids = [r["blog_post_id"] for r in records]
    if not post_ids:
        return {"categories": {}, "top_posts": [], "trends": []}

    posts = db.get_client().table("blog_posts") \
        .select("id, title, slug, category, target_keyword") \
        .in_("id", post_ids) \
        .execute().data
    post_map = {p["id"]: p for p in posts}

    # Aggregate by category
    cat_stats = defaultdict(lambda: {
        "impressions": 0, "clicks": 0, "ctr_sum": 0, "count": 0, "posts": []
    })

    for r in records:
        post = post_map.get(r["blog_post_id"], {})
        category = post.get("category", "Sonstige")
        stats = cat_stats[category]
        stats["impressions"] += r["impressions"]
        stats["clicks"] += r["clicks"]
        stats["ctr_sum"] += r["ctr"]
        stats["count"] += 1
        stats["posts"].append({
            "title": post.get("title", ""),
            "slug": post.get("slug", ""),
            "impressions": r["impressions"],
            "clicks": r["clicks"],
            "ctr": r["ctr"],
            "avg_position": r["avg_position"],
        })

    categories = {}
    for cat, stats in cat_stats.items():
        avg_ctr = round(stats["ctr_sum"] / stats["count"], 2) if stats["count"] else 0
        avg_impressions = round(stats["impressions"] / stats["count"])
        label = "HIGH PERFORMER" if avg_ctr >= 3.0 and avg_impressions >= 100 else \
                "LOW PERFORMER" if avg_ctr < 1.5 or avg_impressions < 50 else \
                "AVERAGE"
        categories[cat] = {
            "avg_impressions_per_post": avg_impressions,
            "avg_ctr": avg_ctr,
            "total_clicks": stats["clicks"],
            "post_count": stats["count"],
            "label": label,
        }

    # Top posts by impressions
    all_posts = []
    for r in records:
        post = post_map.get(r["blog_post_id"], {})
        all_posts.append({
            "title": post.get("title", ""),
            "keyword": post.get("target_keyword", ""),
            "impressions": r["impressions"],
            "clicks": r["clicks"],
            "ctr": r["ctr"],
            "avg_position": r["avg_position"],
        })
    top_posts = sorted(all_posts, key=lambda p: p["impressions"], reverse=True)[:10]

    # Detect position trends by comparing with historical data
    trends = []
    for r in records:
        post = post_map.get(r["blog_post_id"], {})
        history = db.get_post_performance_trend(r["blog_post_id"], weeks=4)
        if len(history) >= 2:
            prev_pos = history[-2].get("avg_position")
            curr_pos = r["avg_position"]
            if prev_pos and curr_pos and prev_pos - curr_pos >= 2:
                trends.append({
                    "title": post.get("title", ""),
                    "keyword": post.get("target_keyword", ""),
                    "position_change": round(prev_pos - curr_pos, 1),
                    "from_position": prev_pos,
                    "to_position": curr_pos,
                    "direction": "UP",
                })
            elif prev_pos and curr_pos and curr_pos - prev_pos >= 3:
                trends.append({
                    "title": post.get("title", ""),
                    "keyword": post.get("target_keyword", ""),
                    "position_change": round(curr_pos - prev_pos, 1),
                    "from_position": prev_pos,
                    "to_position": curr_pos,
                    "direction": "DOWN",
                })

    return {
        "categories": categories,
        "top_posts": top_posts,
        "trends": trends,
        "measured_at": datetime.utcnow().isoformat(),
    }


def run() -> dict:
    """Run the performance tracker agent."""
    logger.info("Performance Tracker starting...")

    # Step 1: Collect current performance
    records = collect_blog_performance()
    logger.info(f"Collected performance for {len(records)} published posts")

    if not records:
        return {"processed": 0, "created": 0}

    # Step 2: Store performance snapshots
    db.upsert_post_performance(records)

    # Step 3: Build and store summary for strategist
    summary = build_performance_summary(records)
    db.set_config("performance_summary", summary)

    rising = sum(1 for t in summary["trends"] if t["direction"] == "UP")
    falling = sum(1 for t in summary["trends"] if t["direction"] == "DOWN")

    logger.info(
        f"Performance tracking complete: {len(records)} posts tracked, "
        f"{len(summary['categories'])} categories, "
        f"{rising} rising / {falling} falling trends"
    )

    return {
        "processed": len(records),
        "created": len(records),
        "categories": len(summary["categories"]),
        "trends_up": rising,
        "trends_down": falling,
    }
