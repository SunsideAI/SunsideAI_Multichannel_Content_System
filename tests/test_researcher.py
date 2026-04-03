"""Tests for the Research Agent."""

from unittest.mock import patch, MagicMock

from agents.researcher import (
    fetch_rss_articles,
    match_findings_to_opportunities,
    evaluate_articles,
)


def test_match_findings_to_opportunities():
    findings = [
        {"title": "KI Study", "target_keyword": "ki makler"},
        {"title": "SEO Tips", "target_keyword": "seo immobilien"},
    ]
    opportunities = [
        {"id": "opp-1", "target_keyword": "ki makler"},
        {"id": "opp-2", "target_keyword": "chatbot"},
    ]

    matched = match_findings_to_opportunities(findings, opportunities)

    assert matched[0].get("opportunity_id") == "opp-1"
    assert matched[1].get("opportunity_id") is None


@patch("agents.researcher.feedparser")
def test_fetch_rss_articles(mock_fp):
    mock_fp.parse.return_value = MagicMock(
        entries=[
            MagicMock(title="Article 1", link="https://example.com/1", summary="Summary", published="2026-01-01"),
        ]
    )

    articles = fetch_rss_articles("https://example.com/feed", "Test Feed")
    assert len(articles) == 1
    assert articles[0]["title"] == "Article 1"
    assert articles[0]["source"] == "Test Feed"


@patch("agents.researcher.feedparser")
def test_fetch_rss_articles_error(mock_fp):
    mock_fp.parse.side_effect = Exception("Network error")
    articles = fetch_rss_articles("https://example.com/feed", "Test Feed")
    assert articles == []


@patch("agents.researcher.call_claude_json")
def test_evaluate_articles(mock_claude):
    mock_claude.return_value = [
        {"title": "Relevant Article", "relevance_score": 8, "target_keyword": "ki makler"},
    ]

    articles = [{"title": "Test", "source": "Feed", "url": "https://example.com", "summary": "test", "published": "2026"}]
    result = evaluate_articles(articles, [])

    assert len(result) == 1
    assert result[0]["relevance_score"] == 8
