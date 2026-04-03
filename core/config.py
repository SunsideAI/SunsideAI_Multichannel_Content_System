"""Sunside AI Content Autopilot — Configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
ASSETS_DIR = BASE_DIR / "assets"
FEEDS_FILE = BASE_DIR / "feeds" / "sources.yaml"

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_TEMP_CREATIVE = 0.7   # Blog-Texte, LinkedIn
CLAUDE_TEMP_ANALYTICAL = 0.3  # Quality Gate, Strategist
CLAUDE_MAX_TOKENS = 4096

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO", "SunsideAI/SunsideAI_Website")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
BLOG_PATH_IN_REPO = "src/content/blog"

# LinkedIn
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_PERSON_ID = os.getenv("LINKEDIN_PERSON_ID")

# Google Search Console
GSC_SERVICE_ACCOUNT_JSON = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "gsc-credentials.json")
GSC_SITE_URL = os.getenv("GSC_SITE_URL", "sc-domain:sunsideai.de")
GSC_REFRESH_ON_DEMAND = os.getenv("GSC_REFRESH_ON_DEMAND", "true").lower() == "true"

# Notifications
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "paul@sunsideai.de")

# Website
SITE_URL = "https://sunsideai.de"
SITEMAP_URL = f"{SITE_URL}/sitemap.xml"

# Scheduling (times in Europe/Berlin)
TIMEZONE = os.getenv("TIMEZONE", "Europe/Berlin")

SCHEDULE = {
    "performance": {"day": "sunday", "time": "17:00"},
    "crawl":      {"day": "sunday",  "time": "18:00"},
    "keywords":   {"day": "sunday",  "time": "19:00"},
    "strategist": {"day": "sunday",  "time": "19:30"},
    "research":   {"day": "sunday",  "time": "20:00"},
    "blog":       {"days": ["monday", "tuesday", "wednesday", "thursday", "friday"], "time": "06:00"},
    "publish":    {"days": ["monday", "tuesday", "wednesday", "thursday", "friday"], "time": "09:00"},
    "linkedin":   {"days": ["monday", "tuesday", "wednesday", "thursday", "friday"], "time": "10:00"},
    "digest":     {"days": ["monday", "tuesday", "wednesday", "thursday", "friday"], "time": "07:00"},
}

# Category → Blog Image Mapping
CATEGORY_ICON_MAP = {
    "KI & Automatisierung": "blog-ki",
    "Chatbot": "blog-chatbot",
    "Telefonassistenz": "blog-telefon",
    "SEO & Sichtbarkeit": "blog-seo",
    "Immobilienmarketing": "blog-immobilie",
    "Analytics & Daten": "blog-analytics",
    "Automatisierung": "blog-automatisierung",
    "E-Mail Marketing": "blog-email",
    "Webdesign": "blog-website",
    "Datenschutz & Recht": "blog-datenschutz",
    "Effizienz": "blog-speed",
    "Teameffizienz": "blog-team",
    "Prozessoptimierung": "blog-schluessel",
    "Zeitmanagement": "blog-zeit",
    "Umsatz & Wachstum": "blog-umsatz",
    "Marketing": "blog-marketing",
    "Exposé & Content": "blog-expose",
    "Bewertung": "blog-bewertung",
    "Zielgruppen": "blog-zielgruppe",
    "Integration": "blog-vernetzung",
}


def load_prompt(name: str) -> str:
    """Load a prompt file from the prompts directory."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def is_prompt_placeholder(name: str) -> bool:
    """Check if a prompt file is still a placeholder (< 50 chars of content)."""
    try:
        content = load_prompt(name)
        return len(content.strip()) < 50
    except FileNotFoundError:
        return True


def load_knowledge(name: str) -> str:
    """Load a knowledge base file."""
    path = KNOWLEDGE_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Knowledge file not found: {path}")
    return path.read_text(encoding="utf-8")


def get_icon_for_category(category: str) -> str:
    """Return the blog image filename for a category."""
    return CATEGORY_ICON_MAP.get(category, "blog-ki")
