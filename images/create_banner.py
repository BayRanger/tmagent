#!/usr/bin/env python3
"""
Create a cool post image for TM-Agent.
Design philosophy: Digital Essence - minimalism meets AI
"""

from PIL import Image, ImageDraw, ImageFont
import math
import random

# Configuration
WIDTH = 1200
HEIGHT = 630  # Social media friendly ratio
OUTPUT_PATH = "tmagent/images/tmagent_banner.png"

# Color palette - Digital Essence
COLORS = {
    "bg_dark": "#0a0a0f",
    "bg_gradient_start": "#0d1117",
    "bg_gradient_end": "#161b22",
    "accent": "#58a6ff",      # Electric blue
    "accent_secondary": "#7ee787",  # Green
    "accent_tertiary": "#f778ba",   # Pink
    "text_primary": "#f0f6fc",
    "text_secondary": "#8b949e",
    "grid": "#21262d",
}


def create_gradient_background():
    """Create a subtle gradient background."""
    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["bg_dark"])
    draw = ImageDraw.Draw(img)
    
    # Create vertical gradient effect with lines
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        # Interpolate between gradient colors
        r = int(int(COLORS["bg_gradient_start"][1:3], 16) * (1 - ratio) + 
                int(COLORS["bg_gradient_end"][1:3], 16) * ratio)
        g = int(int(COLORS["bg_gradient_start"][3:5], 16) * (1 - ratio) + 
                int(COLORS["bg_gradient_end"][3:5], 16) * ratio)
        b = int(int(COLORS["bg_gradient_start"][5:7], 16) * (1 - ratio) + 
                int(COLORS["bg_gradient_end"][5:7], 16) * ratio)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    
    return img


def draw_grid_pattern(draw):
    """Draw a subtle grid pattern in background."""
    spacing = 40
    
    # Vertical lines
    for x in range(0, WIDTH, spacing):
        # Vary opacity based on position
        opacity = 20 if x % (spacing * 4) == 0 else 8
        draw.line([(x, 0), (x, HEIGHT)], fill=COLORS["grid"], width=1)
    
    # Horizontal lines
    for y in range(0, HEIGHT, spacing):
        opacity = 20 if y % (spacing * 4) == 0 else 8
        draw.line([(0, y), (WIDTH, y)], fill=COLORS["grid"], width=1)


def draw_circuit_pattern(draw):
    """Draw subtle circuit/node connections."""
    # Create geometric nodes and connections
    nodes = [
        (150, 150), (200, 300), (150, 450),
        (WIDTH - 150, 150), (WIDTH - 200, 300), (WIDTH - 150, 450),
        (WIDTH // 2, 100), (WIDTH // 2, HEIGHT - 100),
    ]
    
    # Draw connections
    for i, (x1, y1) in enumerate(nodes):
        for x2, y2 in nodes[i+1:]:
            # Only connect nearby nodes
            dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if dist < 300:
                draw.line([(x1, y1), (x2, y2)], fill=COLORS["grid"], width=1)
    
    # Draw nodes
    for x, y in nodes:
        draw.ellipse([x-3, y-3, x+3, y+3], fill=COLORS["grid"])


def draw_central_orb(draw):
    """Draw a glowing orb in the center representing AI."""
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    base_radius = 120
    
    # Draw multiple rings for glow effect
    for i in range(20, 0, -1):
        radius = base_radius + i * 8
        opacity = int(255 * (1 - i/20) * 0.15)
        color = (
            int(int(COLORS["accent"][1:3], 16) * (1 - i/40)),
            int(int(COLORS["accent"][3:5], 16) * (1 - i/40)),
            int(int(COLORS["accent"][5:7], 16) * (1 - i/40)),
            opacity
        )
        # Draw ellipse for perspective
        draw.ellipse(
            [center_x - radius, center_y - radius//2, center_x + radius, center_y + radius//2],
            outline=color
        )
    
    # Core circle
    draw.ellipse(
        [center_x - 30, center_y - 15, center_x + 30, center_y + 15],
        fill=COLORS["accent"]
    )


def draw_function_call_indicators(draw):
    """Draw function call indicators around the central orb."""
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    
    # Function indicators - radiating from center
    angles = [0, 60, 120, 180, 240, 300]
    colors = [COLORS["accent"], COLORS["accent_secondary"], COLORS["accent_tertiary"]] * 2
    
    for i, angle in enumerate(angles):
        rad = math.radians(angle)
        # Outer point
        x_outer = center_x + int(200 * math.cos(rad))
        y_outer = center_y + int(100 * math.sin(rad))
        # Inner point
        x_inner = center_x + int(140 * math.cos(rad))
        y_inner = center_y + int(70 * math.sin(rad))
        
        # Draw line
        draw.line([(x_inner, y_inner), (x_outer, y_outer)], fill=colors[i], width=2)
        
        # Draw node at outer end
        draw.ellipse([x_outer-6, y_outer-6, x_outer+6, y_outer+6], fill=colors[i])
        
        # Draw small dots along the line
        for t in [0.25, 0.5, 0.75]:
            x_dot = x_inner + int((x_outer - x_inner) * t)
            y_dot = y_inner + int((y_outer - y_inner) * t)
            draw.ellipse([x_dot-2, y_dot-2, x_dot+2, y_dot+2], fill=colors[i])


def draw_text_elements(draw, font_large, font_small):
    """Draw text elements."""
    center_x = WIDTH // 2
    
    # Main title
    title = "TM-Agent"
    bbox = draw.textbbox((0, 0), title, font=font_large)
    title_width = bbox[2] - bbox[0]
    draw.text((center_x - title_width // 2, HEIGHT - 120), title, font=font_large, fill=COLORS["text_primary"])
    
    # Subtitle
    subtitle = "Minimal AI Agent with Function Calling"
    bbox = draw.textbbox((0, 0), subtitle, font=font_small)
    subtitle_width = bbox[2] - bbox[0]
    draw.text((center_x - subtitle_width // 2, HEIGHT - 70), subtitle, font=font_small, fill=COLORS["text_secondary"])
    
    # Top tagline
    tagline = "Intelligent · Minimal · Powerful"
    bbox = draw.textbbox((0, 0), tagline, font=font_small)
    tagline_width = bbox[2] - bbox[0]
    draw.text((center_x - tagline_width // 2, 40), tagline, font=font_small, fill=COLORS["accent"])


def draw_corner_elements(draw, font_tiny):
    """Draw decorative corner elements."""
    # Top left - version info
    draw.text((30, 30), "v0.1.0", font=font_tiny, fill=COLORS["text_secondary"])
    
    # Top right - "Open Source"
    draw.text((WIDTH - 100, 30), "Open Source", font=font_tiny, fill=COLORS["text_secondary"])
    
    # Bottom left - GitHub style decoration
    draw.text((30, HEIGHT - 40), "◆", font=font_tiny, fill=COLORS["accent_secondary"])
    
    # Bottom right
    bbox = draw.textbbox((0, 0), "Built with Python", font=font_tiny)
    text_width = bbox[2] - bbox[0]
    draw.text((WIDTH - text_width - 30, HEIGHT - 40), "Built with Python", font=font_tiny, fill=COLORS["text_secondary"])


def create_banner():
    """Create the main banner image."""
    print("Creating TM-Agent banner image...")
    
    # Create base image with gradient
    img = create_gradient_background()
    draw = ImageDraw.Draw(img)
    
    # Add grid pattern
    draw_grid_pattern(draw)
    
    # Add circuit pattern
    draw_circuit_pattern(draw)
    
    # Load fonts (try to use a nice font, fallback to default)
    try:
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        font_tiny = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny = ImageFont.load_default()
    
    # Draw central orb (AI representation)
    draw_central_orb(draw)
    
    # Draw function call indicators
    draw_function_call_indicators(draw)
    
    # Draw text
    draw_text_elements(draw, font_large, font_small)
    
    # Draw corner elements
    draw_corner_elements(draw, font_tiny)
    
    # Save
    img.save(OUTPUT_PATH, "PNG", quality=95)
    print(f"Banner saved to: {OUTPUT_PATH}")
    
    # Also create a square version for badges/icons
    create_square_badge()
    
    return img


def create_square_badge():
    """Create a square badge version."""
    SIZE = 400
    OUTPUT_SQUARE = "tmagent/images/tmagent_badge.png"
    
    # Create dark background
    img = Image.new("RGB", (SIZE, SIZE), COLORS["bg_dark"])
    draw = ImageDraw.Draw(img)
    
    # Draw grid
    spacing = 20
    for x in range(0, SIZE, spacing):
        opacity = 30 if x % (spacing * 4) == 0 else 12
        draw.line([(x, 0), (x, SIZE)], fill=COLORS["grid"], width=1)
    for y in range(0, SIZE, spacing):
        opacity = 30 if y % (spacing * 4) == 0 else 12
        draw.line([(0, y), (SIZE, y)], fill=COLORS["grid"], width=1)
    
    # Draw central orb
    center = SIZE // 2
    base_radius = 60
    
    # Glow rings
    for i in range(15, 0, -1):
        radius = base_radius + i * 6
        opacity = int(255 * (1 - i/15) * 0.12)
        color = (
            int(int(COLORS["accent"][1:3], 16) * (1 - i/30)),
            int(int(COLORS["accent"][3:5], 16) * (1 - i/30)),
            int(int(COLORS["accent"][5:7], 16) * (1 - i/30))
        )
        draw.ellipse(
            [center - radius, center - radius//2, center + radius, center + radius//2],
            outline=color
        )
    
    # Core
    draw.ellipse(
        [center - 15, center - 8, center + 15, center + 8],
        fill=COLORS["accent"]
    )
    
    # Function indicators
    angles = [0, 90, 180, 270]
    for i, angle in enumerate(angles):
        rad = math.radians(angle)
        x_outer = center + int(90 * math.cos(rad))
        y_outer = center + int(45 * math.sin(rad))
        x_inner = center + int(60 * math.cos(rad))
        y_inner = center + int(30 * math.sin(rad))
        
        color = [COLORS["accent"], COLORS["accent_secondary"], COLORS["accent_tertiary"], COLORS["accent"]][i]
        draw.line([(x_inner, y_inner), (x_outer, y_outer)], fill=color, width=2)
        draw.ellipse([x_outer-4, y_outer-4, x_outer+4, y_outer+4], fill=color)
    
    # Text
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        font_ver = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except:
        font_title = ImageFont.load_default()
        font_ver = ImageFont.load_default()
    
    title = "TM"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = bbox[2] - bbox[0]
    draw.text((center - title_w // 2, SIZE - 60), title, font=font_title, fill=COLORS["text_primary"])
    
    img.save(OUTPUT_SQUARE, "PNG", quality=95)
    print(f"Badge saved to: {OUTPUT_SQUARE}")


if __name__ == "__main__":
    create_banner()
    print("\nDone! Created TM-Agent branding images.")
