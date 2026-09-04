"""Render the Legend battle-log card as a PNG with Pillow.

A header (name, rank, total trophies, attack/defense sums) over a grid of tiles,
one per recorded attack/defense. Since the API gives no stars, each tile carries
a small crossed-swords (attack) or shield (defense) marker instead.
"""

from __future__ import annotations

import io
import math

# Colours (Discord-dark friendly).
BG = (18, 19, 24)
HEADER = (120, 35, 40)
HEADER_SUB = (90, 26, 30)
TEXT = (240, 240, 245)
MUTED = (200, 200, 210)
ATTACK = (196, 158, 54)      # gold
ATTACK_TEXT = (30, 26, 12)
DEFENSE = (150, 58, 58)      # red
DEFENSE_TEXT = (245, 235, 235)
MARKER = (255, 255, 255)

WIDTH = 900
PAD = 30
COLS = 8
TILE_H = 66
GAP = 10
HEADER_H = 132


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
    except TypeError:  # older Pillow: no size arg
        return ImageFont.load_default()


def _center_text(draw, box, text, font, fill):
    left, top, right, bottom = box
    tb = draw.textbbox((0, 0), text, font=font)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    x = left + (right - left - tw) / 2 - tb[0]
    y = top + (bottom - top - th) / 2 - tb[1]
    draw.text((x, y), text, font=font, fill=fill)


def _swords(draw, cx, cy, s, color):
    draw.line((cx - s, cy - s, cx + s, cy + s), fill=color, width=3)
    draw.line((cx - s, cy + s, cx + s, cy - s), fill=color, width=3)


def _shield(draw, cx, cy, s, color):
    draw.polygon(
        [(cx - s, cy - s), (cx + s, cy - s), (cx + s, cy - s // 3), (cx, cy + s), (cx - s, cy - s // 3)],
        fill=color,
    )


def render_card(*, name: str, tag: str, rank, trophies: int, events: list) -> bytes:
    """events: list of {'direction': 'attack'|'defense', 'delta': int}."""
    from PIL import Image, ImageDraw

    attacks = [e for e in events if e["direction"] == "attack"]
    defenses = [e for e in events if e["direction"] == "defense"]
    att_sum = sum(e["delta"] for e in attacks)
    def_sum = sum(-e["delta"] for e in defenses)

    tile_w = (WIDTH - 2 * PAD - (COLS - 1) * GAP) / COLS
    rows = max(1, math.ceil(len(events) / COLS)) if events else 0
    grid_h = rows * (TILE_H + GAP)
    height = HEADER_H + PAD + grid_h + PAD

    img = Image.new("RGB", (WIDTH, int(height)), BG)
    draw = ImageDraw.Draw(img)

    f_name = _font(34, bold=True)
    f_big = _font(30, bold=True)
    f_mid = _font(20, bold=True)
    f_small = _font(18)
    f_tile = _font(22, bold=True)

    # Header bar.
    draw.rounded_rectangle((PAD, PAD, WIDTH - PAD, PAD + HEADER_H - 20), radius=14, fill=HEADER)
    rank_txt = f"#{rank}  " if rank else ""
    draw.text((PAD + 22, PAD + 16), f"{rank_txt}{name}", font=f_name, fill=TEXT)
    total_txt = f"Total: {trophies}"
    tb = draw.textbbox((0, 0), total_txt, font=f_big)
    draw.text((WIDTH - PAD - 22 - (tb[2] - tb[0]), PAD + 18), total_txt, font=f_big, fill=TEXT)

    draw.text((PAD + 22, PAD + 66), f"Attacks  +{att_sum} / {len(attacks)}", font=f_mid, fill=(235, 220, 170))
    dtxt = f"Defenses  -{def_sum} / {len(defenses)}"
    tb = draw.textbbox((0, 0), dtxt, font=f_mid)
    draw.text((WIDTH - PAD - 22 - (tb[2] - tb[0]), PAD + 66), dtxt, font=f_mid, fill=(235, 190, 190))
    draw.text((PAD + 22, PAD + 96), f"{tag}", font=f_small, fill=MUTED)

    # Tiles.
    y0 = PAD + HEADER_H + PAD
    for i, ev in enumerate(events):
        r, c = divmod(i, COLS)
        x = PAD + c * (tile_w + GAP)
        y = y0 + r * (TILE_H + GAP)
        is_attack = ev["direction"] == "attack"
        bg = ATTACK if is_attack else DEFENSE
        fg = ATTACK_TEXT if is_attack else DEFENSE_TEXT
        draw.rounded_rectangle((x, y, x + tile_w, y + TILE_H), radius=10, fill=bg)
        delta = ev["delta"]
        label = f"+{delta}" if delta >= 0 else str(delta)
        _center_text(draw, (x, y + 4, x + tile_w, y + TILE_H - 20), label, f_tile, fg)
        mcx, mcy = x + tile_w / 2, y + TILE_H - 16
        if is_attack:
            _swords(draw, mcx, mcy, 7, fg)
        else:
            _shield(draw, mcx, mcy, 7, fg)

    if not events:
        _center_text(draw, (PAD, y0, WIDTH - PAD, y0 + 40), "No tracked attacks yet this season.", f_mid, MUTED)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
