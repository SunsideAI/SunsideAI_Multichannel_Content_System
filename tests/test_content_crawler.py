"""Tests for the Content Crawler agent."""

from unittest.mock import patch, MagicMock

from agents.content_crawler import (
    classify_page_type,
    extract_page_data,
    fetch_sitemap_urls,
)


def test_classify_page_type_blog():
    assert classify_page_type("https://sunsideai.de/blog/ki-makler") == "blog"


def test_classify_page_type_landing():
    assert classify_page_type("https://sunsideai.de/") == "landing"


def test_classify_page_type_service():
    assert classify_page_type("https://sunsideai.de/leistungen") == "service"


def test_classify_page_type_legal():
    assert classify_page_type("https://sunsideai.de/datenschutz") == "legal"


def test_classify_page_type_other():
    assert classify_page_type("https://sunsideai.de/ueber-uns") == "other"


def test_extract_page_data():
    html = """
    <html>
    <head>
        <title>Test Page | Sunside AI</title>
        <meta name="description" content="Test description">
    </head>
    <body>
        <main>
            <h1>Test Heading</h1>
            <h2>Section One</h2>
            <p>Some content here with words.</p>
            <h2>Section Two</h2>
            <a href="/blog/other-post">Link</a>
        </main>
    </body>
    </html>
    """
    data = extract_page_data("https://sunsideai.de/blog/test", html)

    assert data["title"] == "Test Page | Sunside AI"
    assert data["meta_description"] == "Test description"
    assert data["h1"] == "Test Heading"
    assert len(data["h2s"]) == 2
    assert data["word_count"] > 0
    assert data["page_type"] == "blog"
    assert data["status"] == "active"


@patch("agents.content_crawler.requests.get")
def test_fetch_sitemap_urls_empty(mock_get):
    mock_get.side_effect = Exception("Network error")
    urls = fetch_sitemap_urls()
    assert urls == []
