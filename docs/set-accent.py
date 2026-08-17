"""Set the application's accent colour from a single hex.

The accent is the one colour this project chooses; everything else derives from
it. This script does the whole job so trying a colour is one command rather than
an afternoon:

    python docs/set-accent.py "#E13A9D"
    python docs/set-accent.py "#E13A9D" --check     # report only, change nothing

It rewrites the accent block in `frontend/static/tokens.css`, recolours the mark
and every favicon from the logo artwork, and rebuilds the banner.

What it checks before writing, and refuses on:

  * sRGB gamut, for both the dark and the light value
  * accent on every surface it is drawn on, floor 3:1  (STYLE-GUIDE 2.6)
  * accent-ink on accent, floor 4.5:1

What it warns about but allows, because they are judgement calls:

  * hue proximity to a semantic colour, which is how an accent stops reading as
    "selected" and starts reading as "a status"
  * hue proximity to a sibling app's accent

The light theme is not the same lightness and chroma as the dark one. A colour
bright enough to read on graphite is usually too pale on paper, so the light
value is the same hue re-stepped darker until it clears the floor.
"""

from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOKENS = REPO / "frontend/static/tokens.css"
LOGO = REPO / "frontend/static/logo.png"

# The surfaces the accent is drawn on, as OKLCH, straight from tokens.css.
DARK_SURFACES = {
    "backdrop": (0.164, 0.005, 264), "window": (0.182, 0.004, 264),
    "dock": (0.195, 0.004, 264), "chrome": (0.209, 0.004, 264),
    "control": (0.244, 0.006, 271),
}
LIGHT_SURFACES = {
    "window": (0.944, 0.007, 81), "dock": (0.953, 0.007, 81),
    "chrome": (0.971, 0.006, 85), "control": (0.929, 0.009, 85),
}
DARK_INK = (0.182, 0.004, 264)          # --accent-ink is --window in the dark theme
ACCENT_FLOOR, INK_FLOOR = 3.0, 4.5

# Hues the accent has to stay legible against. Semantic colours mean state, and
# an accent that looks like one of them is the defect the language exists to
# avoid (STYLE-GUIDE 2.4).
NEIGHBOURS = [
    ("--good (up / ok)", 145.0), ("--caution (warning)", 38.0),
    ("--critical (down / failed)", 22.0), ("Umber's ochre (sibling app)", 67.5),
]


# ── colour maths ────────────────────────────────────────────────────────────
def _srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def oklch_to_rgb(L: float, C: float, h: float) -> list[float]:
    hr = math.radians(h)
    a, b = C * math.cos(hr), C * math.sin(hr)
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return [_srgb(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
            _srgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
            _srgb(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)]


def rgb_to_oklch(hexs: str) -> tuple[float, float, float]:
    hexs = hexs.lstrip("#")
    def lin(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(hexs[i:i + 2], 16) / 255) for i in (0, 2, 4))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def hexify(rgb) -> str:
    return "#" + "".join("%02X" % max(0, min(255, round(c * 255))) for c in rgb)


def in_gamut(rgb, tol: float = 0.002) -> bool:
    return all(-tol <= c <= 1 + tol for c in rgb)


def luminance(rgb) -> float:
    def f(c: float) -> float:
        c = max(0.0, min(1.0, c))
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def max_chroma(L: float, h: float) -> float:
    lo, hi = 0.0, 0.4
    while hi - lo > 1e-4:
        mid = (lo + hi) / 2
        if in_gamut(oklch_to_rgb(L, mid, h)):
            lo = mid
        else:
            hi = mid
    return lo


def pick_light(h: float, chroma: float) -> tuple[float, float]:
    """Darkest-but-not-murky light value that clears both floors."""
    worst = min(LIGHT_SURFACES.values(), key=lambda t: t[0])
    for L in [x / 100 for x in range(62, 38, -1)]:
        C = min(chroma, max_chroma(L, h))
        rgb = oklch_to_rgb(L, C, h)
        on_surface = min(contrast(rgb, oklch_to_rgb(*s)) for s in LIGHT_SURFACES.values())
        if on_surface >= ACCENT_FLOOR and contrast([1, 1, 1], rgb) >= INK_FLOOR:
            return L, C
    raise SystemExit("No light value of this hue clears the contrast floors.")


# ── report ──────────────────────────────────────────────────────────────────
def report(hexv: str):
    L, C, h = rgb_to_oklch(hexv)
    dark = oklch_to_rgb(L, C, h)
    if not in_gamut(dark):
        raise SystemExit(f"{hexv} is outside sRGB.")
    lL, lC = pick_light(h, C)
    light = oklch_to_rgb(lL, lC, h)

    print(f"{hexv.upper()}  ->  oklch({L:.3f} {C:.3f} {h:.1f})")
    print(f"  light theme: oklch({lL:.2f} {lC:.3f} {h:.1f}) = {hexify(light)}\n")

    fails = []
    print("  contrast (floor 3:1 on a surface, 4.5:1 for ink on the accent)")
    for name, s in DARK_SURFACES.items():
        v = contrast(dark, oklch_to_rgb(*s))
        ok = v >= ACCENT_FLOOR
        fails += [] if ok else [f"dark accent on {name} {v:.2f}:1"]
        print(f"    dark  on {name:9s} {v:5.2f}:1  {'ok' if ok else 'FAILS'}")
    v = contrast(oklch_to_rgb(*DARK_INK), dark)
    fails += [] if v >= INK_FLOOR else [f"dark ink on accent {v:.2f}:1"]
    print(f"    dark  ink on accent {v:5.2f}:1  {'ok' if v >= INK_FLOOR else 'FAILS'}")
    for name, s in LIGHT_SURFACES.items():
        v = contrast(light, oklch_to_rgb(*s))
        fails += [] if v >= ACCENT_FLOOR else [f"light accent on {name} {v:.2f}:1"]
        print(f"    light on {name:9s} {v:5.2f}:1  {'ok' if v >= ACCENT_FLOOR else 'FAILS'}")
    v = contrast([1, 1, 1], light)
    fails += [] if v >= INK_FLOOR else [f"light ink on accent {v:.2f}:1"]
    print(f"    light ink on accent {v:5.2f}:1  {'ok' if v >= INK_FLOOR else 'FAILS'}")

    print("\n  hue distance to the colours it must not be confused with")
    warns = []
    for name, nh in NEIGHBOURS:
        d = abs(((h - nh + 180) % 360) - 180)
        note = "COLLIDES" if d < 30 else ("close" if d < 45 else "clear")
        if d < 30:
            warns.append(f"{name} is {d:.0f} degrees away")
        print(f"    {name:30s} {d:6.1f} deg  {note}")
    return L, C, h, lL, lC, fails, warns


# ── writing ─────────────────────────────────────────────────────────────────
def write_tokens(L, C, h, lL, lC):
    s = TOKENS.read_text(encoding="utf-8")
    s = re.sub(r"--accent-h: [\d.]+;", f"--accent-h: {h:.1f};", s)
    s = re.sub(r"--accent-l: [\d.]+;", f"--accent-l: {L:.3f};", s)
    s = re.sub(r"--accent-c: [\d.]+;", f"--accent-c: {C:.3f};", s)
    s = re.sub(r"--accent:(\s+)oklch\([\d.]+ [\d.]+ var\(--accent-h\)\);",
               rf"--accent:\1oklch({lL:.2f} {lC:.3f} var(--accent-h));", s)
    # accent-dim keeps the guide's ratio to the accent in each theme
    s = re.sub(r"--accent-dim:(\s+)oklch\(0\.447 [\d.]+ var\(--accent-h\)\);",
               rf"--accent-dim:\1oklch(0.447 {C * 0.604:.3f} var(--accent-h));", s)
    s = re.sub(r"--accent-dim:(\s+)oklch\(0\.79 [\d.]+ var\(--accent-h\)\);",
               rf"--accent-dim:\1oklch(0.79 {lC * 0.36:.3f} var(--accent-h));", s)
    TOKENS.write_text(s, encoding="utf-8")
    print(f"  tokens.css   accent-h {h:.1f}, dark oklch({L:.3f} {C:.3f}), light oklch({lL:.2f} {lC:.3f})")


def write_marks(accent_hex: str):
    from PIL import Image
    accent = tuple(int(accent_hex.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    src = Image.open(LOGO).convert("RGBA")
    px = src.load()
    w, hgt = src.size

    # The artwork is a glyph over an OPAQUE WHITE interior on a transparent
    # surround. Solve for glyph coverage on whichever channel separates the two
    # most: hard-coding one channel works for a blue glyph and fails for orange.
    k = max(range(3), key=lambda i: abs(255 - accent[i]))
    denom = 255 - accent[k] or 1

    mark = Image.new("RGBA", (w, hgt))
    mp = mark.load()
    for y in range(hgt):
        for x in range(w):
            c = px[x, y]
            if c[3] == 0:
                continue
            t = max(0.0, min(1.0, (255 - c[k]) / denom))
            mp[x, y] = (*accent, int(c[3] * t))

    mark = mark.crop(mark.getbbox())
    side = max(mark.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2))
    for size, name in [(256, "mark-256.png"), (64, "mark-64.png"),
                       (64, "logo-64.png"), (32, "favicon.png")]:
        canvas.resize((size, size), Image.LANCZOS).save(
            REPO / "frontend/static" / name, optimize=True)
    canvas.resize((256, 256), Image.LANCZOS).save(
        REPO / "frontend/static/favicon.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    # The source artwork itself, so the banner and the app agree.
    recol = Image.new("RGBA", (w, hgt))
    rp = recol.load()
    for y in range(hgt):
        for x in range(w):
            c = px[x, y]
            if c[3] == 0:
                continue
            t = max(0.0, min(1.0, (255 - c[k]) / denom))
            rp[x, y] = (round(255 + (accent[0] - 255) * t),
                        round(255 + (accent[1] - 255) * t),
                        round(255 + (accent[2] - 255) * t), c[3])
    recol.save(LOGO, optimize=True)
    print(f"  mark + favicons + logo.png recoloured to {accent_hex.upper()} "
          f"(separated on channel {'RGB'[k]})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hex", help='the accent, e.g. "#E13A9D"')
    ap.add_argument("--check", action="store_true", help="report only, change nothing")
    ap.add_argument("--force", action="store_true", help="write even if a floor fails")
    ap.add_argument("--keep-logo", action="store_true",
                    help="leave the logo alone; only the accent changes")
    a = ap.parse_args()

    if not re.fullmatch(r"#?[0-9a-fA-F]{6}", a.hex):
        raise SystemExit("Give a six-digit hex, e.g. #E13A9D")
    hexv = "#" + a.hex.lstrip("#").upper()

    L, C, h, lL, lC, fails, warns = report(hexv)
    if fails:
        print("\n  FAILS:", "; ".join(fails))
        if not a.force and not a.check:
            raise SystemExit("  Refusing to write. Pass --force to override.")
    if warns:
        print("\n  worth knowing:", "; ".join(warns))
    if a.check:
        print("\n  --check, nothing written.")
        return 0

    print()
    write_tokens(L, C, h, lL, lC)
    if not a.keep_logo:
        write_marks(hexv)
    banner = REPO / "docs/make-banner.py"
    if banner.exists():
        subprocess.run([sys.executable, str(banner)], check=False,
                       capture_output=True)
        print("  banner rebuilt")
    print("\n  Done. Regenerate the screenshots with:")
    print("    python docs/seed-demo.py && python docs/shots.py docs/images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
