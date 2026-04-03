"""Initial full crawl of sunsideai.de — run once during setup."""

import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from agents.content_crawler import run


def main():
    print("Starting initial crawl of sunsideai.de...")
    print("This performs a full sitemap crawl and populates the content_inventory table.\n")

    result = run()

    print(f"\nCrawl complete:")
    print(f"  Pages processed: {result.get('processed', 0)}")
    print(f"  Active pages:    {result.get('created', 0)}")
    print(f"  Errors:          {result.get('errors', 0)}")


if __name__ == "__main__":
    main()
