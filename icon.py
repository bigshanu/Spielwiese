"""Generates icon.png (1024x1024) for the YouTube Downloader app."""

from PIL import Image, ImageDraw
import math

SIZE = 1024
BG      = (26,  26,  46)   # #1a1a2e  — App-Dunkelblau
RED     = (233, 69,  96)   # #e94560  — App-Rot
WHITE   = (255, 255, 255)
SHADOW  = (15,  15,  30, 120)


def draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)


def draw_arrow(draw, cx, cy, color):
    """Draw a clean downward arrow: shaft + arrowhead + underline bar."""
    # Shaft
    sw, sh = 72, 210
    draw.rectangle(
        [cx - sw // 2, cy - 200, cx + sw // 2, cy - 200 + sh],
        fill=color,
    )
    # Arrowhead (triangle)
    aw, ah = 220, 150
    apex_y = cy - 200 + sh + ah
    draw.polygon(
        [(cx, apex_y), (cx - aw // 2, apex_y - ah), (cx + aw // 2, apex_y - ah)],
        fill=color,
    )
    # Underline bar
    bw, bh = 340, 52
    bar_y = cy + 220
    draw.rounded_rectangle(
        [cx - bw // 2, bar_y, cx + bw // 2, bar_y + bh],
        radius=26,
        fill=color,
    )


def make_icon(path: str = "icon.png"):
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # ── Background rounded square ──────────────────────────────────────────
    draw_rounded_rect(draw, [0, 0, SIZE - 1, SIZE - 1], radius=200, fill=BG)

    # ── Subtle inner glow ring (dark red, slightly larger than circle) ─────
    cx, cy = SIZE // 2, SIZE // 2
    glow_r = 345
    glow_color = (90, 20, 38, 180)
    glow_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.ellipse(
        [cx - glow_r, cy - glow_r - 10, cx + glow_r, cy + glow_r - 10],
        fill=glow_color,
    )
    img = Image.alpha_composite(img, glow_img)
    draw = ImageDraw.Draw(img)

    # ── Red circle ────────────────────────────────────────────────────────
    r = 320
    draw.ellipse([cx - r, cy - r - 10, cx + r, cy + r - 10], fill=RED)

    # ── Highlight (top-left lens effect) ──────────────────────────────────
    highlight = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hl_draw = ImageDraw.Draw(highlight)
    hl_draw.ellipse([cx - r, cy - r - 10, cx + r, cy + r - 10],
                    fill=(255, 255, 255, 0))
    hl_draw.ellipse(
        [cx - r + 20, cy - r + 20, cx + 20, cy + 20],
        fill=(255, 255, 255, 22),
    )
    img = Image.alpha_composite(img, highlight)
    draw = ImageDraw.Draw(img)

    # ── White download arrow ───────────────────────────────────────────────
    draw_arrow(draw, cx, cy - 10, WHITE)

    img.save(path, "PNG")
    print(f"Icon gespeichert: {path}")


if __name__ == "__main__":
    make_icon()
