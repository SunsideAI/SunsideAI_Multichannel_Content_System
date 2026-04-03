"""Sunside AI Content Autopilot — Supabase Client."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from supabase import create_client, Client

from core.config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

_client: Optional[Client] = None


def get_client() -> Client:
    """Get or create the Supabase client."""
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# === Pipeline Config ===

def get_config(key: str, default=None):
    """Get a pipeline config value."""
    resp = get_client().table("pipeline_config").select("value").eq("key", key).execute()
    if resp.data:
        return resp.data[0]["value"]
    return default


def set_config(key: str, value) -> None:
    """Set a pipeline config value."""
    get_client().table("pipeline_config").upsert({
        "key": key, "value": value, "updated_at": datetime.utcnow().isoformat()
    }).execute()


def is_paused() -> bool:
    return get_config("paused", False) is True or get_config("paused", "false") == "true"


def get_qa_threshold() -> float:
    return float(get_config("qa_threshold", 7.5))


# === Content Inventory ===

def upsert_page(page_data: dict) -> None:
    """Insert or update a page in the content inventory."""
    get_client().table("content_inventory").upsert(page_data, on_conflict="url").execute()


def get_all_pages(page_type: Optional[str] = None, status: str = "active") -> list:
    """Get all pages, optionally filtered by type."""
    query = get_client().table("content_inventory").select("*").eq("status", status)
    if page_type:
        query = query.eq("page_type", page_type)
    return query.execute().data


def get_pages_for_linking(limit: int = 50) -> list:
    """Get pages suitable for internal linking (URL, title, keyword)."""
    return get_client().table("content_inventory") \
        .select("url, title, primary_keyword, category") \
        .eq("status", "active") \
        .limit(limit) \
        .execute().data


# === Keywords ===

def upsert_keywords(keywords: list[dict]) -> None:
    """Bulk upsert keywords."""
    if keywords:
        get_client().table("keywords").upsert(
            keywords, on_conflict="keyword,source,period_start"
        ).execute()


def get_keywords(min_impressions: int = 10, limit: int = 500) -> list:
    """Get keywords above minimum impressions."""
    return get_client().table("keywords") \
        .select("*") \
        .gte("impressions", min_impressions) \
        .order("impressions", desc=True) \
        .limit(limit) \
        .execute().data


def get_keywords_by_cluster(cluster_name: str) -> list:
    return get_client().table("keywords") \
        .select("*") \
        .eq("cluster_name", cluster_name) \
        .execute().data


# === Content Opportunities ===

def create_opportunities(opportunities: list[dict]) -> None:
    """Bulk insert content opportunities."""
    if opportunities:
        get_client().table("content_opportunities").insert(opportunities).execute()


def get_open_opportunities(limit: int = 10) -> list:
    """Get open opportunities, highest priority first."""
    return get_client().table("content_opportunities") \
        .select("*") \
        .eq("status", "OPEN") \
        .order("priority_score", desc=True) \
        .limit(limit) \
        .execute().data


def get_opportunities_for_research() -> list:
    """Get opportunities that need research (NEW_POST action)."""
    return get_client().table("content_opportunities") \
        .select("*") \
        .eq("status", "OPEN") \
        .in_("action", ["NEW_POST", "REFRESH_CONTENT"]) \
        .order("priority_score", desc=True) \
        .limit(10) \
        .execute().data


def complete_opportunity(opp_id: str) -> None:
    get_client().table("content_opportunities").update({
        "status": "COMPLETED", "completed_at": datetime.utcnow().isoformat()
    }).eq("id", opp_id).execute()


# === Findings ===

def create_findings(findings: list[dict]) -> None:
    """Bulk insert findings."""
    if findings:
        get_client().table("findings").insert(findings).execute()


def get_next_finding() -> Optional[dict]:
    """Get the next unused finding, preferring those linked to opportunities."""
    # First try opportunity-linked
    resp = get_client().table("findings") \
        .select("*") \
        .eq("status", "RESEARCHED") \
        .not_.is_("opportunity_id", "null") \
        .order("relevance_score", desc=True) \
        .limit(1) \
        .execute()
    if resp.data:
        return resp.data[0]
    
    # Then any finding
    resp = get_client().table("findings") \
        .select("*") \
        .eq("status", "RESEARCHED") \
        .order("relevance_score", desc=True) \
        .limit(1) \
        .execute()
    return resp.data[0] if resp.data else None


def mark_finding_used(finding_id: str) -> None:
    get_client().table("findings").update({
        "status": "USED", "used_at": datetime.utcnow().isoformat()
    }).eq("id", finding_id).execute()


# === Blog Posts ===

def create_blog_post(post_data: dict) -> dict:
    """Insert a new blog post."""
    resp = get_client().table("blog_posts").insert(post_data).execute()
    return resp.data[0] if resp.data else {}


def update_blog_post(post_id: str, updates: dict) -> None:
    get_client().table("blog_posts").update(updates).eq("id", post_id).execute()


def get_posts_to_publish() -> list:
    """Get posts ready to auto-publish (QA passed, delay expired, not on hold)."""
    now = datetime.utcnow().isoformat()
    return get_client().table("blog_posts") \
        .select("*") \
        .eq("status", "QA_PASSED") \
        .lte("scheduled_at", now) \
        .execute().data


def get_posts_to_distribute() -> list:
    """Get published posts that haven't been posted to LinkedIn yet."""
    posted_ids = get_client().table("linkedin_posts") \
        .select("blog_post_id") \
        .execute().data
    posted_blog_ids = [p["blog_post_id"] for p in posted_ids]
    
    query = get_client().table("blog_posts") \
        .select("*") \
        .eq("status", "PUBLISHED")
    
    results = query.execute().data
    return [p for p in results if p["id"] not in posted_blog_ids]


def get_recent_topics(days: int = 30) -> list:
    """Get titles/keywords of recently published posts for dedup."""
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    return get_client().table("blog_posts") \
        .select("title, target_keyword, slug") \
        .gte("created_at", cutoff) \
        .execute().data


def count_posts_this_week() -> int:
    """Count posts created this week."""
    from datetime import date
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    return get_client().table("blog_posts") \
        .select("id", count="exact") \
        .gte("created_at", monday.isoformat()) \
        .execute().count or 0


def count_posts_today() -> int:
    """Count posts created today."""
    today = datetime.utcnow().date().isoformat()
    return get_client().table("blog_posts") \
        .select("id", count="exact") \
        .gte("created_at", today) \
        .execute().count or 0


# === LinkedIn Posts ===

def create_linkedin_post(post_data: dict) -> dict:
    resp = get_client().table("linkedin_posts").insert(post_data).execute()
    return resp.data[0] if resp.data else {}


def update_linkedin_post(post_id: str, updates: dict) -> None:
    get_client().table("linkedin_posts").update(updates).eq("id", post_id).execute()


# === Agent Runs ===

def log_agent_start(agent_name: str) -> str:
    """Log an agent run start. Returns the run ID."""
    resp = get_client().table("agent_runs").insert({
        "agent_name": agent_name, "status": "started"
    }).execute()
    return resp.data[0]["id"]


def log_agent_complete(run_id: str, items_processed: int = 0, items_created: int = 0, metadata: dict = None) -> None:
    from datetime import datetime as dt
    get_client().table("agent_runs").update({
        "status": "completed",
        "completed_at": dt.utcnow().isoformat(),
        "items_processed": items_processed,
        "items_created": items_created,
        "metadata": metadata or {},
    }).eq("id", run_id).execute()


def log_agent_failed(run_id: str, error_message: str) -> None:
    from datetime import datetime as dt
    get_client().table("agent_runs").update({
        "status": "failed",
        "completed_at": dt.utcnow().isoformat(),
        "error_message": error_message,
    }).eq("id", run_id).execute()
