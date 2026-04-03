"""Tests for the Content Strategist agent."""

from unittest.mock import patch, MagicMock

from agents.content_strategist import build_strategist_context, run


@patch("agents.content_strategist.db")
def test_build_strategist_context(mock_db):
    mock_db.get_all_pages.return_value = [
        {"url": "/blog/test", "page_type": "blog", "primary_keyword": "test", "word_count": 1000, "published_at": "2026-01-01"},
    ]
    mock_db.get_keywords.return_value = [
        {"keyword": "test", "impressions": 100, "clicks": 10, "ctr": 10, "avg_position": 5, "ranking_page": "/blog/test"},
    ]
    mock_db.get_recent_topics.return_value = []
    mock_db.get_open_opportunities.return_value = []

    context = build_strategist_context()

    assert "CONTENT INVENTORY" in context
    assert "KEYWORD DATA" in context
    assert "/blog/test" in context


@patch("agents.content_strategist.db")
@patch("agents.content_strategist.call_claude_json")
def test_run_creates_opportunities(mock_claude, mock_db):
    mock_db.get_all_pages.return_value = []
    mock_db.get_keywords.return_value = []
    mock_db.get_recent_topics.return_value = []
    mock_db.get_open_opportunities.return_value = []

    mock_claude.return_value = [
        {
            "type": "keyword_gap",
            "priority": "HIGH",
            "target_keyword": "ki telefonassistent",
            "action": "NEW_POST",
            "suggested_title": "Test Title",
        }
    ]

    result = run()

    assert result["created"] == 1
    mock_db.create_opportunities.assert_called_once()


@patch("agents.content_strategist.db")
@patch("agents.content_strategist.call_claude_json")
def test_run_handles_api_error(mock_claude, mock_db):
    mock_db.get_all_pages.return_value = []
    mock_db.get_keywords.return_value = []
    mock_db.get_recent_topics.return_value = []
    mock_db.get_open_opportunities.return_value = []
    mock_claude.side_effect = Exception("API error")

    result = run()

    assert result["created"] == 0
