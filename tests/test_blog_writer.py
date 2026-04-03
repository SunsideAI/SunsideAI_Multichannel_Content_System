"""Tests for the Blog Writer agent."""

from unittest.mock import patch

from agents.blog_writer import (
    select_internal_links,
    extract_frontmatter,
    load_relevant_knowledge,
)


def test_select_internal_links():
    pages = [
        {"url": "/blog/ki-makler", "title": "KI für Makler", "primary_keyword": "ki makler", "category": "KI"},
        {"url": "/blog/seo-tipps", "title": "SEO Tipps", "primary_keyword": "seo tipps", "category": "SEO"},
        {"url": "/leistungen", "title": "Leistungen", "primary_keyword": "chatbot makler", "category": ""},
    ]

    result = select_internal_links(pages, "ki makler", limit=2)

    assert "ki-makler" in result
    assert result.count("[") <= 2


def test_extract_frontmatter():
    content = """---
title: "Test Post"
description: "A test description"
slug: "test-post"
date: "2026-04-01"
author: "Paul Probodziak"
category: "KI & Automatisierung"
---

# Test Post

Content here.
"""
    fm = extract_frontmatter(content)

    assert fm["title"] == "Test Post"
    assert fm["slug"] == "test-post"
    assert fm["category"] == "KI & Automatisierung"
    assert fm["author"] == "Paul Probodziak"


def test_extract_frontmatter_empty():
    fm = extract_frontmatter("No frontmatter here")
    assert fm == {}


@patch("agents.blog_writer.load_knowledge")
def test_load_relevant_knowledge_with_ki_keyword(mock_load):
    mock_load.return_value = "Some knowledge content"

    result = load_relevant_knowledge("ki chatbot makler")

    assert "sources" in result
    assert "case_study" in result
    assert result["case_study"] != ""  # Should include case study for KI topic


@patch("agents.blog_writer.load_knowledge")
def test_load_relevant_knowledge_without_relevant_keyword(mock_load):
    mock_load.return_value = "Some knowledge content"

    result = load_relevant_knowledge("datenschutz immobilien")

    assert "sources" in result
    assert result["case_study"] == ""  # Should not include case study
