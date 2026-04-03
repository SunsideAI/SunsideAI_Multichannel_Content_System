"""Tests for the LinkedIn Poster agent."""

from agents.linkedin_poster import extract_key_points, extract_stats


def test_extract_key_points_from_h2s():
    content = """# Main Title

## Warum KI für Makler wichtig ist

Some text here.

## Die besten Tools im Vergleich

More text.

## Fazit und nächste Schritte

Conclusion.
"""
    result = extract_key_points(content)

    assert "Warum KI für Makler wichtig ist" in result
    assert "Die besten Tools im Vergleich" in result
    assert "Fazit und nächste Schritte" in result


def test_extract_key_points_fallback():
    content = """First paragraph of content.

Second paragraph of content.

Third paragraph of content.

Fourth paragraph.
"""
    result = extract_key_points(content)
    assert "First paragraph" in result


def test_extract_stats():
    content = """
Eine aktuelle Studie zeigt: 67% der Makler nutzen bereits KI-Tools.
Die Konversionsrate stieg um 15,8 Prozent.
Insgesamt wurden 30 Leads generiert.
Keine weiteren Zahlen hier.
"""
    result = extract_stats(content)
    assert "67%" in result or "15,8 Prozent" in result or "30 Leads" in result


def test_extract_stats_no_numbers():
    content = "Dieser Text enthält keine relevanten Statistiken oder Zahlen."
    result = extract_stats(content)
    assert result == "Keine spezifischen Statistiken"
