"""
Sunside AI Content Autopilot — Main Orchestrator

Usage:
    python main.py                  # Run scheduled (daemon mode)
    python main.py --run performance # Run performance tracker
    python main.py --run crawl      # Run single agent
    python main.py --run research
    python main.py --run strategy
    python main.py --run blog
    python main.py --run publish
    python main.py --run linkedin
    python main.py --run batch      # Create 5 blog posts + summary email
    python main.py --run all        # Run full pipeline once
"""

import argparse
import logging
import sys
from datetime import datetime

import pytz

from core.config import TIMEZONE
from core import supabase_client as db
from core.notifier import send_error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("autopilot")

tz = pytz.timezone(TIMEZONE)


def run_agent(agent_name: str) -> None:
    """Run a single agent with logging and error handling."""
    if db.is_paused():
        logger.info(f"Pipeline paused, skipping {agent_name}")
        return
    
    run_id = db.log_agent_start(agent_name)
    logger.info(f"Starting agent: {agent_name}")
    
    try:
        if agent_name == "performance":
            from agents.performance_tracker import run
        elif agent_name == "crawl":
            from agents.content_crawler import run
        elif agent_name == "keywords":
            from agents.keyword_researcher import run
        elif agent_name == "strategy":
            from agents.content_strategist import run
        elif agent_name == "research":
            from agents.researcher import run
        elif agent_name == "blog":
            from agents.blog_writer import run
        elif agent_name == "publish":
            from agents.blog_writer import run_publish as run
        elif agent_name == "linkedin":
            from agents.linkedin_poster import run
        else:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        result = run()
        
        db.log_agent_complete(
            run_id,
            items_processed=result.get("processed", 0),
            items_created=result.get("created", 0),
            metadata=result,
        )
        logger.info(f"Agent {agent_name} completed: {result}")
        
    except Exception as e:
        error_msg = str(e)
        db.log_agent_failed(run_id, error_msg)
        logger.error(f"Agent {agent_name} failed: {error_msg}")
        send_error(agent_name, error_msg)
        raise


def run_sunday_pipeline() -> None:
    """Run the full Sunday pipeline (SEO Intelligence + Research)."""
    logger.info("=== Sunday Pipeline ===")
    run_agent("performance")
    run_agent("crawl")
    run_agent("keywords")
    run_agent("strategy")
    run_agent("research")
    logger.info("=== Sunday Pipeline Complete ===")


def run_weekday_pipeline() -> None:
    """Run the weekday pipeline (Blog + Publish + LinkedIn)."""
    logger.info("=== Weekday Pipeline ===")
    
    # Check limits
    max_per_day = int(db.get_config("max_posts_per_day", 1))
    max_per_week = int(db.get_config("max_posts_per_week", 5))
    
    if db.count_posts_today() >= max_per_day:
        logger.info(f"Daily limit reached ({max_per_day}), skipping blog creation")
    elif db.count_posts_this_week() >= max_per_week:
        logger.info(f"Weekly limit reached ({max_per_week}), skipping blog creation")
    else:
        run_agent("blog")
    
    # Always check for posts to publish and distribute
    run_agent("publish")
    run_agent("linkedin")
    
    logger.info("=== Weekday Pipeline Complete ===")


def run_weekly_blog_batch() -> None:
    """Create up to 5 blog posts and send each + summary via email."""
    logger.info("=== Weekly Blog Batch ===")
    created_posts = []

    for i in range(5):
        finding = db.get_next_finding()
        if not finding:
            logger.info(f"No more findings after {i} posts")
            break

        try:
            run_agent("blog")
            post = db.get_blog_post_by_finding(finding["id"])
            if post:
                created_posts.append(post)
        except Exception as e:
            logger.error(f"Blog batch post {i+1} failed: {e}")

    if created_posts:
        from core.notifier import send_weekly_batch_summary
        send_weekly_batch_summary(created_posts)
        logger.info(f"Batch complete: {len(created_posts)} posts created, summary sent")
    else:
        logger.info("No posts created in batch")

    logger.info("=== Weekly Blog Batch Complete ===")


def run_full_pipeline() -> None:
    """Run everything once (for testing)."""
    run_sunday_pipeline()
    run_weekday_pipeline()


def main():
    parser = argparse.ArgumentParser(description="Sunside AI Content Autopilot")
    parser.add_argument("--run", type=str, help="Run a specific agent or 'all'/'sunday'/'weekday'")
    args = parser.parse_args()
    
    if args.run:
        if args.run == "all":
            run_full_pipeline()
        elif args.run == "sunday":
            run_sunday_pipeline()
        elif args.run == "weekday":
            run_weekday_pipeline()
        elif args.run == "batch":
            run_weekly_blog_batch()
        else:
            run_agent(args.run)
    else:
        # Daemon mode with schedule
        try:
            import schedule
            import time
            
            now = datetime.now(tz)
            logger.info(f"Starting scheduler (timezone: {TIMEZONE}, current time: {now.strftime('%H:%M')})")
            
            # Sunday: Performance tracking at 17:00, then SEO Intelligence + Research at 18:00
            schedule.every().sunday.at("17:00").do(run_sunday_pipeline)
            
            # Weekdays: Blog + Publish + LinkedIn
            for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                getattr(schedule.every(), day).at("06:00").do(run_weekday_pipeline)
            
            logger.info("Scheduler running. Press Ctrl+C to stop.")
            while True:
                schedule.run_pending()
                time.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
