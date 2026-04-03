"""Manually trigger individual agents for testing."""

import argparse
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from main import run_agent, run_sunday_pipeline, run_weekday_pipeline, run_full_pipeline


AGENTS = ["crawl", "keywords", "strategy", "research", "blog", "publish", "linkedin"]


def main():
    parser = argparse.ArgumentParser(description="Manually trigger Sunside AI agents")
    parser.add_argument(
        "agent",
        choices=AGENTS + ["sunday", "weekday", "all"],
        help="Which agent or pipeline to run",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore pipeline pause state",
    )
    args = parser.parse_args()

    if args.force:
        from core import supabase_client as db
        was_paused = db.is_paused()
        if was_paused:
            db.set_config("paused", False)
            print("Pipeline was paused — temporarily unpausing for this run")

    try:
        if args.agent == "sunday":
            run_sunday_pipeline()
        elif args.agent == "weekday":
            run_weekday_pipeline()
        elif args.agent == "all":
            run_full_pipeline()
        else:
            run_agent(args.agent)
        print(f"\n✓ {args.agent} completed successfully")
    except Exception as e:
        print(f"\n✗ {args.agent} failed: {e}")
        sys.exit(1)
    finally:
        if args.force and was_paused:
            db.set_config("paused", True)
            print("Re-paused pipeline")


if __name__ == "__main__":
    main()
