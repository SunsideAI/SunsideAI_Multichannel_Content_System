"""Sunside AI Content Autopilot — Content Crawler Agent.

Crawls sunsideai.de and builds/updates the content inventory in Supabase.
Schedule: Sunday 18:00 (first agent in the weekly cycle).
"""

import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from core.config import SITE_URL, SITEMAP_URL
from core import supabase_client as db

logger = logging.getLogger(__name__)

CRAWL_DELAY = 0.5  # seconds between requests (max 2 req/s)
REQUEST_TIMEOUT = 15


def fetch_sitemap_urls() -> list[str]:
    """Fetch all URLs from the sitemap."""
    try:
        resp = requests.get(SITEMAP_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except Exception:
        # Fallback: try sitemap-0.xml (Next.js pattern)
        try:
            resp = requests.get(f"{SITE_URL}/sitemap-0.xml", timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Could not fetch sitemap: {e}")
            return []

    root = ET.fromstring(resp.content)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = []
    # Handle sitemap index
    for sitemap in root.findall("sm:sitemap", ns):
        loc = sitemap.find("sm:loc", ns)
        if loc is not None and loc.text:
            try:
                sub_resp = requests.get(loc.text, timeout=REQUEST_TIMEOUT)
                sub_resp.raise_for_status()
                sub_root = ET.fromstring(sub_resp.content)
                for url_elem in sub_root.findall("sm:url/sm:loc", ns):
                    if url_elem.text:
                        urls.append(url_elem.text)
                time.sleep(CRAWL_DELAY)
            except Exception as e:
                logger.warning(f"Failed to fetch sub-sitemap {loc.text}: {e}")

    # Handle regular sitemap
    for url_elem in root.findall("sm:url/sm:loc", ns):
        if url_elem.text:
            urls.append(url_elem.text)

    logger.info(f"Found {len(urls)} URLs in sitemap")
    return urls


def classify_page_type(url: str) -> str:
    """Classify a URL into a page type."""
    path = urlparse(url).path.rstrip("/")
    if "/blog/" in path:
        return "blog"
    if path in ("/", ""):
        return "landing"
    if any(p in path for p in ("/leistungen", "/services", "/preise", "/pricing")):
        return "service"
    if any(p in path for p in ("/impressum", "/datenschutz", "/agb")):
        return "legal"
    return "other"


def extract_page_data(url: str, html: str) -> dict:
    """Extract structured data from a page's HTML."""
    soup = BeautifulSoup(html, "html.parser")

    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "")

    h1 = ""
    h1_tag = soup.find("h1")
    if h1_tag:
        h1 = h1_tag.get_text(strip=True)

    h2s = [h2.get_text(strip=True) for h2 in soup.find_all("h2")]

    # Word count from main content
    body = soup.find("main") or soup.find("article") or soup.find("body")
    text = body.get_text(separator=" ", strip=True) if body else ""
    word_count = len(text.split())

    # Internal links
    internal_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(url, href)
        if urlparse(full_url).netloc == urlparse(SITE_URL).netloc:
            internal_links.append(full_url)
    internal_links = list(set(internal_links))

    # Primary keyword estimation from title + h1
    primary_keyword = h1 if h1 else title.split("|")[0].strip() if title else ""

    # Blog-specific: category, author
    page_type = classify_page_type(url)
    category = None
    author = None
    published_at = None

    if page_type == "blog":
        # Try to extract from meta tags or structured data
        cat_meta = soup.find("meta", attrs={"property": "article:section"})
        if cat_meta:
            category = cat_meta.get("content")

        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta:
            author = author_meta.get("content")

        date_meta = soup.find("meta", attrs={"property": "article:published_time"})
        if date_meta:
            published_at = date_meta.get("content")

    return {
        "url": url,
        "page_type": page_type,
        "title": title[:500] if title else None,
        "meta_description": meta_desc[:500] if meta_desc else None,
        "h1": h1[:500] if h1 else None,
        "h2s": h2s[:20],
        "word_count": word_count,
        "internal_links": internal_links[:50],
        "primary_keyword": primary_keyword[:200] if primary_keyword else None,
        "category": category,
        "author": author,
        "published_at": published_at,
        "last_crawled_at": datetime.utcnow().isoformat(),
        "status": "active",
    }


def crawl_url(url: str) -> Optional[dict]:
    """Crawl a single URL and return extracted data."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        if resp.status_code == 404:
            return {"url": url, "status": "deleted", "last_crawled_at": datetime.utcnow().isoformat()}
        if resp.status_code >= 400:
            logger.warning(f"HTTP {resp.status_code} for {url}")
            return {"url": url, "status": "error", "last_crawled_at": datetime.utcnow().isoformat()}
        resp.raise_for_status()
        return extract_page_data(url, resp.text)
    except Exception as e:
        logger.error(f"Crawl failed for {url}: {e}")
        return {"url": url, "status": "error", "last_crawled_at": datetime.utcnow().isoformat()}


def run() -> dict:
    """Run the content crawler agent."""
    logger.info("Content Crawler starting...")

    urls = fetch_sitemap_urls()
    if not urls:
        logger.warning("No URLs found in sitemap")
        return {"processed": 0, "created": 0}

    processed = 0
    created = 0
    errors = 0

    for url in urls:
        page_data = crawl_url(url)
        if page_data:
            try:
                db.upsert_page(page_data)
                processed += 1
                if page_data.get("status") == "active":
                    created += 1
            except Exception as e:
                logger.error(f"DB upsert failed for {url}: {e}")
                errors += 1
        time.sleep(CRAWL_DELAY)

    # Mark pages not in sitemap as deleted
    existing_pages = db.get_all_pages()
    sitemap_urls = set(urls)
    for page in existing_pages:
        if page["url"] not in sitemap_urls:
            db.upsert_page({
                "url": page["url"],
                "status": "deleted",
                "last_crawled_at": datetime.utcnow().isoformat(),
            })

    logger.info(f"Crawl complete: {processed} processed, {created} active, {errors} errors")
    return {"processed": processed, "created": created, "errors": errors}
