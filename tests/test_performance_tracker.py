"""Tests for the Performance Tracker agent."""

from unittest.mock import patch, MagicMock

from agents.performance_tracker import (
    _slug_from_url,
    collect_blog_performance,
    build_performance_summary,
)


def test_slug_from_url():
    assert _slug_from_url("https://sunsideai.de/blog/ki-makler") == "ki-makler"
    assert _slug_from_url("https://sunsideai.de/blog/chatbot-immobilien") == "chatbot-immobilien"
    assert _slug_from_url("https://sunsideai.de/leistungen") == "/leistungen"


def test_slug_from_url_trailing_slash():
    assert _slug_from_url("https://sunsideai.de/blog/ki-makler/") == "ki-makler"


@patch("agents.performance_tracker.db")
@patch("agents.performance_tracker.fetch_page_performance")
@patch("agents.performance_tracker.fetch_keywords")
def test_collect_blog_performance_no_posts(mock_kw, mock_perf, mock_db):
    mock_db.get_client.return_value.table.return_value \
        .select.return_value.eq.return_value.execute.return_value.data = []

    result = collect_blog_performance()
    assert result == []


@patch("agents.performance_tracker.db")
@patch("agents.performance_tracker.fetch_page_performance")
@patch("agents.performance_tracker.fetch_keywords")
def test_collect_blog_performance_matches_posts(mock_kw, mock_perf, mock_db):
    # Published posts in DB
    mock_db.get_client.return_value.table.return_value \
        .select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "post-1", "slug": "ki-makler", "title": "KI Makler", "category": "KI",
         "target_keyword": "ki makler", "published_at": "2026-01-01"},
    ]

    mock_perf.return_value = [
        {"page": "https://sunsideai.de/blog/ki-makler", "impressions": 200,
         "clicks": 15, "ctr": 7.5, "avg_position": 8.3},
        {"page": "https://sunsideai.de/blog/unknown-post", "impressions": 50,
         "clicks": 2, "ctr": 4.0, "avg_position": 20.0},
    ]

    mock_kw.return_value = [
        {"keyword": "ki makler", "impressions": 150, "clicks": 10,
         "avg_position": 8.0, "ranking_page": "https://sunsideai.de/blog/ki-makler"},
    ]

    result = collect_blog_performance()

    assert len(result) == 1
    assert result[0]["blog_post_id"] == "post-1"
    assert result[0]["impressions"] == 200
    assert len(result[0]["top_keywords"]) == 1


def test_build_performance_summary_empty():
    summary = build_performance_summary([])
    assert summary["categories"] == {}
    assert summary["top_posts"] == []
    assert summary["trends"] == []


@patch("agents.performance_tracker.db")
def test_build_performance_summary_categorizes(mock_db):
    mock_db.get_client.return_value.table.return_value \
        .select.return_value.in_.return_value.execute.return_value.data = [
        {"id": "post-1", "title": "KI Makler", "slug": "ki-makler",
         "category": "KI & Automatisierung", "target_keyword": "ki makler"},
        {"id": "post-2", "title": "CRM Test", "slug": "crm-test",
         "category": "Software", "target_keyword": "crm makler"},
    ]

    mock_db.get_post_performance_trend.return_value = []

    records = [
        {"blog_post_id": "post-1", "impressions": 300, "clicks": 20, "ctr": 6.7, "avg_position": 7.0},
        {"blog_post_id": "post-2", "impressions": 30, "clicks": 1, "ctr": 1.0, "avg_position": 25.0},
    ]

    summary = build_performance_summary(records)

    assert "KI & Automatisierung" in summary["categories"]
    assert summary["categories"]["KI & Automatisierung"]["label"] == "HIGH PERFORMER"
    assert "Software" in summary["categories"]
    assert summary["categories"]["Software"]["label"] == "LOW PERFORMER"
    assert len(summary["top_posts"]) == 2
    assert summary["top_posts"][0]["impressions"] == 300


@patch("agents.performance_tracker.db")
def test_build_performance_summary_detects_trends(mock_db):
    mock_db.get_client.return_value.table.return_value \
        .select.return_value.in_.return_value.execute.return_value.data = [
        {"id": "post-1", "title": "Rising Post", "slug": "rising",
         "category": "KI", "target_keyword": "ki makler"},
    ]

    # Historical data shows position dropped from 13 to 8 (= rising)
    mock_db.get_post_performance_trend.return_value = [
        {"measured_at": "2026-03-15", "avg_position": 13.0},
        {"measured_at": "2026-03-22", "avg_position": 10.0},
    ]

    records = [
        {"blog_post_id": "post-1", "impressions": 200, "clicks": 10, "ctr": 5.0, "avg_position": 8.0},
    ]

    summary = build_performance_summary(records)

    assert len(summary["trends"]) == 1
    assert summary["trends"][0]["direction"] == "UP"
    assert summary["trends"][0]["from_position"] == 10.0
    assert summary["trends"][0]["to_position"] == 8.0


@patch("agents.performance_tracker.db")
@patch("agents.performance_tracker.collect_blog_performance")
def test_run_no_records(mock_collect, mock_db):
    mock_collect.return_value = []

    from agents.performance_tracker import run
    result = run()

    assert result["processed"] == 0
    assert result["created"] == 0
