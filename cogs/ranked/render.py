"""Render the ranked battle-log card as a PNG with Pillow.

Styled after the in-game Legend battle log: a dark-red header (name, rank, total,
attack/defense sums) over a cream grid of tiles, one per recorded attack/defense
this week. Gold = a max attack, tan = a partial attack, pink = a defense. Since
the API gives no stars, each tile carries a small swords/shield marker.
"""

from __future__ import annotations

import io
import math

# Palette.
BG = (20, 21, 24)
HEADER = (122, 34, 38)
HEADER_SUB = (96, 26, 30)
PANEL = (238, 230, 210)         # cream grid background
PANEL_EDGE = (210, 200, 176)
TEXT_LIGHT = (245, 240, 235)
GOLD_TROPHY = (240, 196, 70)

TILE_GOLD = (233, 201, 95)      # max attack (>= threshold)
TILE_GOLD_EDGE = (198, 165, 58)
TILE_TAN = (214, 206, 186)      # partial attack
TILE_TAN_EDGE = (188, 178, 156)
TILE_PINK = (231, 176, 176)     # defense
TILE_PINK_EDGE = (198, 118, 118)
TILE_TEXT = (44, 38, 28)
MARKER = (70, 58, 40)

MAX_ATTACK = 35                 # attacks >= this render as "max" (gold)

WIDTH = 924
PAD = 26
COLS = 12
GAP = 6
TILE_H = 72
HEADER_H = 120
MAX_TILES = 120


def _font(size: int, bold: bool = False):
    from PIL import ImageFont

    names = (
        ["DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
        if bold
        else ["DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def _text_size(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1], b


def _center(draw, box, text, font, fill):
    left, top, right, bottom = box
    tw, th, b = _text_size(draw, text, font)
    draw.text((left + (right - left - tw) / 2 - b[0], top + (bottom - top - th) / 2 - b[1]), text, font=font, fill=fill)


def _trophy(draw, x, y, s, color):
    draw.ellipse((x, y, x + s, y + s * 0.72), fill=color)
    draw.rectangle((x + s * 0.38, y + s * 0.58, x + s * 0.62, y + s * 0.86), fill=color)
    draw.rectangle((x + s * 0.24, y + s * 0.84, x + s * 0.76, y + s), fill=color)


def _swords(draw, cx, cy, s, color):
    draw.line((cx - s, cy - s, cx + s, cy + s), fill=color, width=3)
    draw.line((cx - s, cy + s, cx + s, cy - s), fill=color, width=3)


def _shield(draw, cx, cy, s, color):
    draw.polygon(
        [(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy - s // 3), (cx, cy + s), (cx - s, cy - s // 3)], fill=color
    )


def render_card(*, name: str, tag: str, rank, trophies: int, events: list) -> bytes:
    """events: list of {'direction': 'attack'|'defense', 'delta': int}."""
    from PIL import Image, ImageDraw

    events = events[:MAX_TILES]
    attacks = [e for e in events if e["direction"] == "attack"]
    defenses = [e for e in events if e["direction"] == "defense"]
    att_sum = sum(e["delta"] for e in attacks)
    def_sum = sum(-e["delta"] for e in defenses)

    tile_w = (WIDTH - 2 * PAD - (COLS - 1) * GAP) / COLS
    rows = max(1, math.ceil(len(events) / COLS)) if events else 1
    panel_top = HEADER_H + PAD
    grid_h = rows * (TILE_H + GAP) - GAP
    panel_h = grid_h + 2 * PAD
    height = int(panel_top + panel_h + PAD)

    img = Image.new("RGB", (WIDTH, height), BG)
    draw = ImageDraw.Draw(img)

    f_name = _font(34, bold=True)
    f_total = _font(30, bold=True)
    f_sub = _font(21, bold=True)
    f_tag = _font(17)
    f_tile = _font(22, bold=True)

    # ── Header ────────────────────────────────────────────────────────────────
    draw.rounded_rectangle((PAD, PAD, WIDTH - PAD, PAD + HEADER_H), radius=16, fill=HEADER)
    draw.rounded_rectangle((PAD, PAD + 52, WIDTH - PAD, PAD + HEADER_H), radius=16, fill=HEADER_SUB)

    rank_txt = f"#{rank}  " if rank else ""
    draw.text((PAD + 24, PAD + 12), f"{rank_txt}{name}", font=f_name, fill=TEXT_LIGHT)

    total_txt = f"Total: {trophies}"
    tw, _, _ = _text_size(draw, total_txt, f_total)
    draw.text((WIDTH - PAD - 24 - tw - 34, PAD + 14), total_txt, font=f_total, fill=TEXT_LIGHT)
    _trophy(draw, WIDTH - PAD - 24 - 26, PAD + 16, 26, GOLD_TROPHY)

    draw.text((PAD + 24, PAD + 66), f"Attacks  +{att_sum}", font=f_sub, fill=(238, 220, 170))
    dtxt = f"Defenses  -{def_sum}"
    tw, _, _ = _text_size(draw, dtxt, f_sub)
    draw.text((WIDTH - PAD - 24 - tw, PAD + 66), dtxt, font=f_sub, fill=(238, 195, 195))

    # ── Cream tile panel ────────────────────────────────────────────────────
    draw.rounded_rectangle(
        (PAD, panel_top, WIDTH - PAD, panel_top + panel_h), radius=14, fill=PANEL, outline=PANEL_EDGE, width=2
    )

    x0 = PAD + PAD
    y0 = panel_top + PAD
    for i, ev in enumerate(events):
        r, c = divmod(i, COLS)
        x = x0 + c * (tile_w + GAP)
        y = y0 + r * (TILE_H + GAP)
        delta = ev["delta"]
        is_attack = ev["direction"] == "attack"
        if not is_attack:
            fill, edge = TILE_PINK, TILE_PINK_EDGE
        elif delta >= MAX_ATTACK:
            fill, edge = TILE_GOLD, TILE_GOLD_EDGE
        else:
            fill, edge = TILE_TAN, TILE_TAN_EDGE
        draw.rounded_rectangle((x, y, x + tile_w, y + TILE_H), radius=9, fill=fill, outline=edge, width=2)
        label = f"+{delta}" if delta >= 0 else str(delta)
        _center(draw, (x, y + 6, x + tile_w, y + TILE_H - 22), label, f_tile, TILE_TEXT)
        mcx, mcy = x + tile_w / 2, y + TILE_H - 16
        if is_attack:
            _swords(draw, mcx, mcy, 7, MARKER)
        else:
            _shield(draw, mcx, mcy, 7, MARKER)

    # Player tag centered under the panel.
    _center(draw, (PAD, height - PAD - 2, WIDTH - PAD, height - 2), tag, f_tag, (150, 150, 158))

    if not events:
        _center(draw, (PAD, panel_top, WIDTH - PAD, panel_top + panel_h), "No tracked attacks this week.", f_sub, (150, 140, 120))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
