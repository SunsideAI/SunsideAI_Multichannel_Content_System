"""Seed initial feed sources — validates RSS URLs and reports status."""

import sys
import yaml
import feedparser
import requests

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from core.config import FEEDS_FILE


def main():
    with open(FEEDS_FILE, encoding="utf-8") as f:
        sources = yaml.safe_load(f)

    feeds = sources.get("feeds", [])
    print(f"Checking {len(feeds)} feed sources...\n")

    ok = 0
    failed = 0

    for feed in feeds:
        name = feed["name"]
        url = feed["url"]
        feed_type = feed.get("type", "rss")

        if feed_type == "rss":
            try:
                parsed = feedparser.parse(url)
                count = len(parsed.entries)
                if count > 0:
                    print(f"  ✓ {name}: {count} entries")
                    ok += 1
                else:
                    print(f"  ⚠ {name}: 0 entries (feed may be empty or URL wrong)")
                    failed += 1
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                failed += 1

        elif feed_type in ("scrape", "scholar"):
            try:
                resp = requests.head(url, timeout=10, allow_redirects=True)
                print(f"  ✓ {name}: HTTP {resp.status_code}")
                ok += 1
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                failed += 1

    print(f"\nResults: {ok} OK, {failed} failed out of {len(feeds)} sources")


if __name__ == "__main__":
    main()
