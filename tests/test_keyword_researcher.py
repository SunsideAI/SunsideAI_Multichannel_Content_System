"""Tests for the Keyword Researcher agent."""

from unittest.mock import patch, MagicMock

from agents.keyword_researcher import fetch_and_store_gsc_keywords, fetch_autocomplete_suggestions


@patch("agents.keyword_researcher.db")
@patch("agents.keyword_researcher.fetch_keywords")
def test_fetch_and_store_gsc_keywords(mock_fetch, mock_db):
    mock_fetch.return_value = [
        {"keyword": "ki makler", "impressions": 100, "clicks": 10},
        {"keyword": "chatbot immobilien", "impressions": 50, "clicks": 5},
    ]

    result = fetch_and_store_gsc_keywords()

    assert len(result) == 2
    mock_db.upsert_keywords.assert_called_once()


@patch("agents.keyword_researcher.db")
@patch("agents.keyword_researcher.expand_keywords")
def test_fetch_autocomplete_suggestions(mock_expand, mock_db):
    gsc_keywords = [
        {"keyword": "ki makler", "impressions": 100},
    ]
    mock_expand.return_value = {
        "ki makler": ["ki makler kosten", "ki makler erfahrungen"],
    }

    result = fetch_autocomplete_suggestions(gsc_keywords)

    assert len(result) == 2
    mock_db.upsert_keywords.assert_called_once()


@patch("agents.keyword_researcher.db")
@patch("agents.keyword_researcher.fetch_keywords")
def test_no_gsc_keywords(mock_fetch, mock_db):
    mock_fetch.return_value = []

    result = fetch_and_store_gsc_keywords()

    assert result == []
    mock_db.upsert_keywords.assert_not_called()
