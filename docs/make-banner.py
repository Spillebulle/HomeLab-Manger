#!/usr/bin/env python3
"""Compose the repository banner: the app mark beside the wordmark.

Writes `docs/images/banner.png` (dark ground) and `docs/images/banner-paper.png`
(light ground), both 1354 x 461. Re-runnable: it overwrites both files.

    python docs/make-banner.py

The mark artwork and the typeface are read out of the app itself, so the banner
cannot drift from what the interface uses. Override either with `--mark` and
`--font` when running from somewhere the defaults do not resolve.

Requires Pillow.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent

WIDTH = 1354
HEIGHT = 461
MARGIN = 120           # smallest gap between the group and the left/right edge
TRACKING = -2.0        # px, per the house wordmark
WORDMARK = "HOMELAB MANGER"

# Mark side and the gap to the wordmark, both as multiples of the cap height,
# so the two halves stay in proportion whatever the wordmark is.
MARK_PER_CAP = 1.9
GAP_PER_CAP = 0.55

GROUNDS = {
    "banner.png": ("#0D0E10", "#E6E7E9"),
    "banner-paper.png": ("#E4E0D9", "#3A3836"),
}


def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(path), size)
    try:
        font.set_variation_by_axes([900, 100])   # Weight 900, Width 100
    except OSError:
        pass                                     # static face, already Black
    return font


def text_width(font: ImageFont.FreeTypeFont, text: str) -> float:
    """Advance width with the house tracking applied."""
    return sum(font.getlength(c) for c in text) + TRACKING * (len(text) - 1)


def cap_height(font: ImageFont.FreeTypeFont) -> float:
    top, bottom = font.getbbox("H")[1], font.getbbox("H")[3]
    return bottom - top


def fit_size(font_path: Path, group_width: int, mark_aspect: float) -> int:
    """Largest font size whose mark + gap + wordmark fits `group_width`."""
    lo, hi = 8, 400
    while lo < hi:
        mid = (lo + hi + 1) // 2
        font = load_font(font_path, mid)
        cap = cap_height(font)
        total = (cap * MARK_PER_CAP * mark_aspect
                 + cap * GAP_PER_CAP
                 + text_width(font, WORDMARK))
        if total <= group_width:
            lo = mid
        else:
            hi = mid - 1
    return lo


def draw_tracked(draw: ImageDraw.ImageDraw, xy, text, font, fill) -> None:
    x, y = xy
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += font.getlength(char) + TRACKING


def compose(mark_src: Image.Image, font_path: Path, ground: str, ink: str) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), ground)
    draw = ImageDraw.Draw(canvas)

    size = fit_size(font_path, WIDTH - 2 * MARGIN, mark_src.width / mark_src.height)
    font = load_font(font_path, size)
    cap = cap_height(font)

    mark_h = int(round(cap * MARK_PER_CAP))
    mark_w = int(round(mark_src.width * mark_h / mark_src.height))
    gap = cap * GAP_PER_CAP
    word_w = text_width(font, WORDMARK)

    group_w = mark_w + gap + word_w
    left = (WIDTH - group_w) / 2
    middle = HEIGHT / 2

    mark = mark_src.resize((mark_w, mark_h), Image.LANCZOS)
    canvas.paste(mark, (int(round(left)), int(round(middle - mark_h / 2))), mark)

    # Sit the wordmark on the mark's optical centre: the cap-height band centred
    # on the same line, not the font's own ascender-to-descender box.
    top, bottom = font.getbbox("H")[1], font.getbbox("H")[3]
    baseline_y = middle + cap / 2
    draw_tracked(draw, (left + mark_w + gap, baseline_y - bottom), WORDMARK, font, ink)

    return canvas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mark", type=Path, default=REPO / "frontend/static/mark-256.png")
    ap.add_argument("--font", type=Path, default=REPO / "frontend/static/fonts/Archivo.ttf")
    ap.add_argument("--out", type=Path, default=REPO / "docs/images")
    args = ap.parse_args()

    for path in (args.mark, args.font):
        if not path.exists():
            print(f"Missing: {path}", file=sys.stderr)
            return 1

    args.out.mkdir(parents=True, exist_ok=True)
    mark_src = Image.open(args.mark).convert("RGBA")
    # Trim the artwork's own transparent border so the mark's drawn size is the
    # size this script sets, not whatever padding the source file carries.
    box = mark_src.getchannel("A").getbbox()
    if box:
        mark_src = mark_src.crop(box)

    for name, (ground, ink) in GROUNDS.items():
        target = args.out / name
        compose(mark_src, args.font, ground, ink).save(target, "PNG")
        print(f"Wrote {target} ({WIDTH} x {HEIGHT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
