"""Sunside AI Content Autopilot — Claude API Client."""

import json
import time
import logging
from typing import Optional

import anthropic

from core.config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS,
    CLAUDE_TEMP_CREATIVE, CLAUDE_TEMP_ANALYTICAL, load_prompt
)

logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def call_claude(
    user_message: str,
    system_prompt: Optional[str] = None,
    prompt_file: Optional[str] = None,
    temperature: float = CLAUDE_TEMP_CREATIVE,
    max_tokens: int = CLAUDE_MAX_TOKENS,
    max_retries: int = 3,
) -> str:
    """
    Call Claude API with retry logic.
    
    Args:
        user_message: The user message to send
        system_prompt: Direct system prompt string (takes precedence)
        prompt_file: Name of prompt file to load (e.g. "research-agent")
        temperature: 0.7 for creative, 0.3 for analytical
        max_tokens: Max response tokens
        max_retries: Number of retries on failure
    
    Returns:
        Claude's text response
    """
    if system_prompt is None and prompt_file:
        system_prompt = load_prompt(prompt_file)
    
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": CLAUDE_MODEL,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": user_message}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = client.messages.create(**kwargs)
            return response.content[0].text
            
        except anthropic.RateLimitError:
            wait = 2 ** (attempt + 1)
            logger.warning(f"Rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})")
            time.sleep(wait)
        except anthropic.APIError as e:
            logger.error(f"API error: {e} (attempt {attempt + 1}/{max_retries})")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
    
    raise RuntimeError(f"Claude API failed after {max_retries} retries")


def call_claude_json(
    user_message: str,
    system_prompt: Optional[str] = None,
    prompt_file: Optional[str] = None,
    temperature: float = CLAUDE_TEMP_ANALYTICAL,
    max_tokens: int = CLAUDE_MAX_TOKENS,
) -> dict | list:
    """
    Call Claude and parse the response as JSON.
    Strips markdown code fences if present.
    """
    raw = call_claude(
        user_message=user_message,
        system_prompt=system_prompt,
        prompt_file=prompt_file,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    
    # Strip markdown code fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e}\nRaw response: {raw[:500]}")
        raise ValueError(f"Claude returned invalid JSON: {e}")


def generate_blog_post(finding: dict, context: dict) -> str:
    """
    Generate a blog post from a finding with full context.
    
    Args:
        finding: Dict with title, key_insight, stats, source, target_keyword, blog_angle
        context: Dict with internal_links, related_content, sources, case_study
    """
    system = load_prompt("seo-blog-writer")
    
    user_msg = f"""Erstelle einen SEO-Blogbeitrag basierend auf:

Thema: {finding.get('title', '')}
Kernaussage: {finding.get('key_insight', '')}
Statistiken: {finding.get('stats', '')}
Quelle: {finding.get('source_name', '')} — {finding.get('source_url', '')}
Ziel-Keyword: {finding.get('target_keyword', '')}
Verwandte Keywords (natürlich einbauen): {', '.join(finding.get('related_keywords', []))}
Blog-Winkel: {finding.get('blog_angle', '')}

INTERNE VERLINKUNG — Baue 3-5 dieser Links natürlich in den Text ein:
{context.get('internal_links', 'Keine internen Links verfügbar')}

QUELLEN — Bevorzuge diese geprüften Quellen wenn thematisch passend:
{context.get('sources', '')}

FALLSTUDIE — Falls thematisch passend, baue diese Praxisdaten natürlich ein:
{context.get('case_study', 'Keine Fallstudie für dieses Thema')}

BESTEHENDER CONTENT — Stelle sicher dass dein Beitrag einen neuen Winkel bietet:
{context.get('related_content', 'Kein ähnlicher Content vorhanden')}
"""
    
    return call_claude(user_msg, system_prompt=system, temperature=CLAUDE_TEMP_CREATIVE)


def evaluate_quality(blog_content: str, target_keyword: str) -> dict:
    """Run the quality gate on a blog post. Returns parsed JSON with score."""
    user_msg = f"""Bewerte diesen Blogbeitrag:

Ziel-Keyword: {target_keyword}

--- BLOGBEITRAG START ---
{blog_content}
--- BLOGBEITRAG ENDE ---
"""
    return call_claude_json(user_msg, prompt_file="quality-gate")


def generate_linkedin_text(blog_title: str, blog_url: str, key_points: str, stats: str) -> str:
    """Generate a LinkedIn post text for a published blog."""
    system = load_prompt("linkedin-creator")
    
    user_msg = f"""Erstelle einen LinkedIn-Post für diesen Blogbeitrag:

Blog-Titel: {blog_title}
Blog-URL: {blog_url}
Kernaussagen: {key_points}
Statistiken: {stats}
"""
    return call_claude(user_msg, system_prompt=system, temperature=CLAUDE_TEMP_CREATIVE)
