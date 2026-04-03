"""Sunside AI Content Autopilot — Image Generator.

Generates LinkedIn infographics in the Sunside AI design style.
Output: 1200x1200px PNG with dark background, gradient, title, bullets.
"""

import logging
import os
import textwrap
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from core.config import ASSETS_DIR, BASE_DIR

logger = logging.getLogger(__name__)

# Design System Colors
PRIMARY = "#7B3ABF"
SECONDARY = "#5E2C8C"
TERTIARY = "#9A40C9"
BACKGROUND = "#0F0A15"
WHITE = "#FFFFFF"
WHITE_80 = (255, 255, 255, 204)  # 80% opacity

# Dimensions
WIDTH = 1200
HEIGHT = 1200

# Font paths
FONTS_DIR = ASSETS_DIR / "fonts"


def _hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load Inter or Poppins font, falling back to default."""
    font_names = [
        "Inter-Bold.ttf" if bold else "Inter-Regular.ttf",
        "Poppins-Bold.ttf" if bold else "Poppins-Regular.ttf",
    ]

    for font_name in font_names:
        font_path = FONTS_DIR / font_name
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size)

    # Try system fonts
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/inter/Inter-Regular.ttf", size)
    except OSError:
        pass

    return ImageFont.load_default()


def generate_infographic(
    title: str,
    category: str,
    bullets: list[str],
    blog_url: str,
    output_dir: Optional[str] = None,
) -> str:
    """
    Generate a LinkedIn infographic.

    Args:
        title: Blog post title
        category: Content category (for tag)
        bullets: 3 key bullet points
        blog_url: URL to the blog post

    Returns:
        Path to the generated PNG file
    """
    img = Image.new("RGBA", (WIDTH, HEIGHT), _hex_to_rgb(BACKGROUND) + (255,))
    draw = ImageDraw.Draw(img)

    # Draw dot grid pattern (subtle)
    dot_color = (*_hex_to_rgb(PRIMARY), 25)  # 10% opacity
    for x in range(0, WIDTH, 40):
        for y in range(0, HEIGHT // 2, 40):
            draw.ellipse([x-1, y-1, x+1, y+1], fill=dot_color)

    # Glow effect in center-top (simulated with gradient circles)
    for r in range(200, 0, -5):
        alpha = int(15 * (r / 200))
        glow_color = (*_hex_to_rgb(PRIMARY), alpha)
        draw.ellipse(
            [WIDTH//2 - r, 200 - r//2, WIDTH//2 + r, 200 + r//2],
            fill=glow_color,
        )

    # Gradient overlay in bottom 60%
    gradient_start_y = int(HEIGHT * 0.4)
    for y in range(gradient_start_y, HEIGHT):
        alpha = int(200 * ((y - gradient_start_y) / (HEIGHT - gradient_start_y)))
        draw.line([(0, y), (WIDTH, y)], fill=(*_hex_to_rgb(SECONDARY), alpha))

    # Category tag
    font_tag = _load_font(24, bold=False)
    tag_text = category.upper()
    tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
    tag_w = tag_bbox[2] - tag_bbox[0] + 30
    tag_h = tag_bbox[3] - tag_bbox[1] + 16

    tag_x = 60
    tag_y = HEIGHT - 550
    draw.rounded_rectangle(
        [tag_x, tag_y, tag_x + tag_w, tag_y + tag_h],
        radius=8,
        fill=_hex_to_rgb(SECONDARY),
    )
    draw.text((tag_x + 15, tag_y + 5), tag_text, fill=WHITE, font=font_tag)

    # Title
    font_title = _load_font(48, bold=True)
    title_y = tag_y + tag_h + 20
    wrapped_title = textwrap.fill(title, width=28)
    draw.multiline_text((60, title_y), wrapped_title, fill=WHITE, font=font_title, spacing=8)

    # Bullet points
    font_bullet = _load_font(28, bold=False)
    bullet_y = title_y + 180
    for bullet in bullets[:3]:
        bullet_text = bullet.strip().lstrip("- ")
        if len(bullet_text) > 60:
            bullet_text = bullet_text[:57] + "..."
        draw.text((80, bullet_y), f"→  {bullet_text}", fill=WHITE_80, font=font_bullet)
        bullet_y += 50

    # Separator line
    sep_y = HEIGHT - 100
    separator_color = (*_hex_to_rgb(PRIMARY), 38)  # 15% opacity
    draw.line([(60, sep_y), (WIDTH - 60, sep_y)], fill=separator_color, width=1)

    # Bottom bar
    font_bottom = _load_font(22, bold=True)
    draw.text((60, sep_y + 20), "SUNSIDE AI", fill=WHITE, font=font_bottom)

    font_url = _load_font(20, bold=False)
    url_short = blog_url.replace("https://", "").replace("http://", "")
    url_text = f"{url_short} >>"
    url_bbox = draw.textbbox((0, 0), url_text, font=font_url)
    url_w = url_bbox[2] - url_bbox[0]
    draw.text((WIDTH - 60 - url_w, sep_y + 22), url_text, fill=WHITE_80, font=font_url)

    # Save
    if output_dir is None:
        output_dir = str(BASE_DIR / "assets" / "generated")
    os.makedirs(output_dir, exist_ok=True)

    slug = title.lower().replace(" ", "-")[:50]
    output_path = os.path.join(output_dir, f"linkedin-{slug}.png")

    img = img.convert("RGB")
    img.save(output_path, "PNG", quality=95)
    logger.info(f"Generated infographic: {output_path}")

    return output_path
