"""Tests for the Quality Gate (via Claude client)."""

from unittest.mock import patch

from core.claude_client import evaluate_quality


@patch("core.claude_client.call_claude_json")
def test_evaluate_quality_passes(mock_claude):
    mock_claude.return_value = {
        "score": 8.5,
        "passed": True,
        "feedback": {
            "factual": {"score": 2, "notes": "Gut"},
            "seo": {"score": 1.5, "notes": "OK"},
            "readability": {"score": 2, "notes": "Flüssig"},
            "relevance": {"score": 1.5, "notes": "Relevant"},
            "brand": {"score": 1.5, "notes": "Konsistent"},
        },
        "suggestions": [],
        "critical_issues": [],
    }

    result = evaluate_quality("# Test Blog\n\nContent here.", "ki makler")

    assert result["score"] == 8.5
    assert result["passed"] is True
    assert "feedback" in result


@patch("core.claude_client.call_claude_json")
def test_evaluate_quality_fails(mock_claude):
    mock_claude.return_value = {
        "score": 5.0,
        "passed": False,
        "feedback": {
            "factual": {"score": 1, "notes": "Ungenau"},
            "seo": {"score": 1, "notes": "Keyword fehlt"},
            "readability": {"score": 1, "notes": "KI-Phrasen"},
            "relevance": {"score": 1, "notes": "Wenig Bezug"},
            "brand": {"score": 1, "notes": "Tonalität falsch"},
        },
        "suggestions": ["Keyword einbauen", "KI-Phrasen entfernen"],
        "critical_issues": ["Faktenfehler in Absatz 3"],
    }

    result = evaluate_quality("# Bad Blog\n\nIn der heutigen Zeit...", "ki makler")

    assert result["score"] == 5.0
    assert result["passed"] is False
    assert len(result["suggestions"]) == 2
    assert len(result["critical_issues"]) == 1
