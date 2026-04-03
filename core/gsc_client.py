"""Sunside AI Content Autopilot — Google Search Console Client."""

import logging
from datetime import date, timedelta
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build

from core.config import GSC_SERVICE_ACCOUNT_JSON, GSC_SITE_URL

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

_service = None


def _get_service():
    """Get or create the GSC API service."""
    global _service
    if _service is None:
        credentials = service_account.Credentials.from_service_account_file(
            GSC_SERVICE_ACCOUNT_JSON,
            scopes=SCOPES,
        )
        _service = build("searchconsole", "v1", credentials=credentials)
    return _service


def fetch_keywords(
    days: int = 28,
    row_limit: int = 1000,
    min_impressions: int = 10,
) -> list[dict]:
    """
    Fetch keyword performance data from Google Search Console.

    Args:
        days: Number of days to look back
        row_limit: Max rows to return (API max: 25000)
        min_impressions: Filter out keywords below this threshold

    Returns:
        List of dicts with: keyword, page, impressions, clicks, ctr, position
    """
    end_date = date.today() - timedelta(days=3)  # GSC has 2-3 day delay
    start_date = end_date - timedelta(days=days)

    service = _get_service()

    response = service.searchanalytics().query(
        siteUrl=GSC_SITE_URL,
        body={
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "dimensions": ["query", "page"],
            "rowLimit": row_limit,
        },
    ).execute()

    rows = response.get("rows", [])
    results = []

    for row in rows:
        impressions = row.get("impressions", 0)
        if impressions < min_impressions:
            continue

        results.append({
            "keyword": row["keys"][0],
            "ranking_page": row["keys"][1],
            "impressions": impressions,
            "clicks": row.get("clicks", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),  # Convert to percentage
            "avg_position": round(row.get("position", 0), 1),
            "source": "gsc",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
        })

    logger.info(f"Fetched {len(results)} keywords from GSC (filtered from {len(rows)} rows)")
    return results


def fetch_page_performance(
    url_filter: Optional[str] = None,
    days: int = 28,
) -> list[dict]:
    """
    Fetch page-level performance data.

    Args:
        url_filter: Optional URL prefix to filter (e.g. '/blog/')
        days: Number of days to look back

    Returns:
        List of dicts with: page, impressions, clicks, ctr, position
    """
    end_date = date.today() - timedelta(days=3)
    start_date = end_date - timedelta(days=days)

    body = {
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "dimensions": ["page"],
        "rowLimit": 500,
    }

    if url_filter:
        body["dimensionFilterGroups"] = [{
            "filters": [{
                "dimension": "page",
                "operator": "contains",
                "expression": url_filter,
            }]
        }]

    service = _get_service()
    response = service.searchanalytics().query(
        siteUrl=GSC_SITE_URL,
        body=body,
    ).execute()

    results = []
    for row in response.get("rows", []):
        results.append({
            "page": row["keys"][0],
            "impressions": row.get("impressions", 0),
            "clicks": row.get("clicks", 0),
            "ctr": round(row.get("ctr", 0) * 100, 2),
            "avg_position": round(row.get("position", 0), 1),
        })

    logger.info(f"Fetched performance for {len(results)} pages")
    return results
