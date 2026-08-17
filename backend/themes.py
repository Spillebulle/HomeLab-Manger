"""User themes: the `.umbertheme` format, its derivations, and the library.

STYLE-GUIDE.md §3.2 is the specification, and it is a *family* format: a theme
somebody makes in one app opens unchanged in every other. That is the whole
point, so this file implements exactly that spec rather than a dialect of it.
If something here looks arbitrary, it is because the reference implementation
(Umber's `themelib.rs`) does it that way and a second interpretation means two
apps in one family that cannot read each other's files.

The parts worth knowing before changing anything:

* **The header decides whether a file is a theme, not the extension.** Import is
  handed whatever the file dialog returned, and a text file that is not a theme
  is refused with a sentence rather than read as a theme of entirely default
  colours.
* **A file carries 27 colours; everything else in `tokens.css` is derived.**
  That is what keeps a file portable: an app never publishes keys the rest of
  the family would report as unread, and two apps given the same file compute
  the same interface.
* **A bad line costs one colour, not the file.** The base's value stands, and
  the count of skipped lines is reported to the user. A theme that quietly took
  black for a misread line would be a theme with an invisible interface in it.
* **A theme is dark because its `base` says so**, never because its colours
  measure dark. Editing a theme towards the opposite lightness must not change
  what it says it derives from.
"""

from __future__ import annotations

import math
import os
import re
import tempfile
import unicodedata
from pathlib import Path

HEADER = "Umber theme"
EXTENSION = ".umbertheme"
MAX_NAME = 64
MAX_STEM = 48
MAX_THEMES = 128          # far past what anybody makes by hand
FALLBACK_NAME = "Untitled theme"
FALLBACK_BASE = "graphite"

# ── The twenty-seven stored keys, in file order ─────────────────────────────
# This order is also the order the editor draws them, so a file reads top to
# bottom like the pane it came from. Where the file key differs from the CSS
# name, THE FILE KEY IS THE STORED WORD and may never change.
SHARED_KEYS: list[tuple[str, str]] = [
    # (file key, tokens.css custom property)
    ("backdrop",        "--backdrop"),
    ("window",          "--window"),
    ("dock",            "--dock"),
    ("chrome",          "--chrome"),
    ("popover",         "--popover"),
    ("border",          "--line"),
    ("popover_border",  "--line-popover"),
    ("control",         "--control"),
    ("control_hover",   "--control-hover"),
    ("control_active",  "--control-active"),
    ("rail",            "--rail"),
    ("knob",            "--knob"),
    ("text_strong",     "--text-strong"),
    ("text",            "--text"),
    ("text_muted",      "--text-muted"),
    ("text_dim",        "--text-dim"),
    ("accent",          "--accent"),
    ("accent_dim",      "--accent-dim"),
    ("warning",         "--caution"),
    ("warning_bg",      "--caution-bg"),
    ("warning_border",  "--caution-line"),
    ("link_1",          "--series-1"),
    ("link_2",          "--series-2"),
    ("link_3",          "--series-3"),
    ("link_4",          "--series-4"),
    ("link_5",          "--series-5"),
    ("link_6",          "--series-6"),
]
KEY_ORDER = [k for k, _ in SHARED_KEYS]
KEY_TO_CSS = dict(SHARED_KEYS)
assert len(KEY_ORDER) == 27, "the format stores exactly twenty-seven colours"

GROUP_LABELS = [        # for the editor, grouped exactly as §2.1
    ("Surfaces", ["backdrop", "window", "dock", "chrome", "popover"]),
    ("Lines", ["border", "popover_border"]),
    ("Controls", ["control", "control_hover", "control_active", "rail", "knob"]),
    ("Type", ["text_strong", "text", "text_muted", "text_dim"]),
    ("Accent", ["accent", "accent_dim"]),
    ("Warnings", ["warning", "warning_bg", "warning_border"]),
    ("Link colours", ["link_1", "link_2", "link_3", "link_4", "link_5", "link_6"]),
]


# ── colour ─────────────────────────────────────────────────────────────────
_HEX6 = re.compile(r"^#?([0-9a-fA-F]{6})$")
_HEX3 = re.compile(r"^#?([0-9a-fA-F]{3})$")


def parse_colour(text: str) -> str | None:
    """`#RRGGBB`, `RRGGBB` and `#RGB` in; `#RRGGBB` out. Anything else is
    refused rather than guessed, and NEVER an alpha channel."""
    t = (text or "").strip()
    m = _HEX6.match(t)
    if m:
        return "#" + m.group(1).upper()
    m = _HEX3.match(t)
    if m:
        r, g, b = m.group(1)
        return ("#" + r + r + g + g + b + b).upper()
    return None


def _rgb(hexs: str) -> tuple[int, int, int]:
    h = hexs.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(rgb) -> str:
    return "#" + "".join("%02X" % max(0, min(255, round(c))) for c in rgb)


def mix(a: str, b: str, t: float) -> str:
    """`a` t-of-the-way to `b`. Straight sRGB, which is what "40 % of the way
    to" reads as and what the reference implementation does."""
    ar, ag, ab = _rgb(a)
    br, bg, bb = _rgb(b)
    return _hex((ar + (br - ar) * t, ag + (bg - ag) * t, ab + (bb - ab) * t))


def rgba(hexs: str, alpha: float) -> str:
    r, g, b = _rgb(hexs)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _srgb(c: float) -> float:
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055


def oklch_hex(L: float, C: float, h: float) -> str:
    """The built-ins are written as OKLCH so they stay checkable line by line
    against `tokens.css`; the file format is hex, so they convert here."""
    hr = math.radians(h)
    a, b = C * math.cos(hr), C * math.sin(hr)
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return _hex((
        _srgb(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s) * 255,
        _srgb(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s) * 255,
        _srgb(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s) * 255,
    ))


# ── the built-in themes ────────────────────────────────────────────────────
# Graphite and Paper are the family's, and every app ships both under exactly
# these ids. They are compiled in, never files: nothing shipped lives in the
# library, or an update would replace a user's edits wholesale.
#
# The neutrals are §2.2's recipes. The accent entries are the app's own and are
# filled in at load time from tokens.css, so `set-accent.py` stays the one place
# the accent is chosen.
_GRAPHITE_NEUTRALS = {
    "backdrop":       oklch_hex(0.164, 0.005, 264),
    "window":         oklch_hex(0.182, 0.004, 264),
    "dock":           oklch_hex(0.195, 0.004, 264),
    "chrome":         oklch_hex(0.209, 0.004, 264),
    "popover":        oklch_hex(0.227, 0.006, 271),
    "border":         oklch_hex(0.276, 0.006, 258),
    "popover_border": oklch_hex(0.301, 0.008, 264),
    "control":        oklch_hex(0.244, 0.006, 271),
    "control_hover":  oklch_hex(0.276, 0.006, 258),
    "rail":           oklch_hex(0.276, 0.006, 258),
    "knob":           oklch_hex(0.928, 0.003, 265),
    "text_strong":    oklch_hex(0.928, 0.003, 265),
    "text":           oklch_hex(0.841, 0.005, 258),
    "text_muted":     oklch_hex(0.695, 0.008, 261),
    "text_dim":       oklch_hex(0.622, 0.008, 261),
    "warning":        oklch_hex(0.693, 0.096, 38),
    "warning_bg":     oklch_hex(0.245, 0.023, 42),
    "warning_border": oklch_hex(0.424, 0.068, 35),
    "link_1": "#3F7BE8", "link_2": "#46B04A", "link_3": "#A96BE8",
    "link_4": "#1FB5B5", "link_5": "#EE5AA8", "link_6": "#F0D53C",
}
_PAPER_NEUTRALS = {
    "backdrop":       oklch_hex(0.908, 0.010, 82),
    "window":         oklch_hex(0.944, 0.007, 81),
    "dock":           oklch_hex(0.953, 0.007, 81),
    "chrome":         oklch_hex(0.971, 0.006, 85),
    "popover":        "#FFFFFF",
    "border":         oklch_hex(0.890, 0.010, 82),
    "popover_border": oklch_hex(0.890, 0.010, 82),
    "control":        oklch_hex(0.929, 0.009, 85),
    "control_hover":  oklch_hex(0.896, 0.010, 82),
    "rail":           oklch_hex(0.890, 0.010, 82),
    "knob":           "#FFFFFF",
    "text_strong":    oklch_hex(0.342, 0.004, 68),
    "text":           oklch_hex(0.342, 0.004, 68),
    "text_muted":     oklch_hex(0.526, 0.007, 75),
    "text_dim":       oklch_hex(0.634, 0.008, 81),
    "warning":        oklch_hex(0.518, 0.114, 39),
    "warning_bg":     oklch_hex(0.943, 0.018, 49),
    "warning_border": oklch_hex(0.832, 0.042, 51),
    "link_1": "#2A5AB4", "link_2": "#2E7C33", "link_3": "#7742AE",
    "link_4": "#137F7F", "link_5": "#B0326E", "link_6": "#7E760A",
}

# --good and --critical are NOT themeable: the fixed hues of §2.5, at the
# lightness the base's theme uses.
_SEMANTIC = {
    "dark": {
        "--good": oklch_hex(0.70, 0.10, 145), "--good-bg": oklch_hex(0.245, 0.025, 145),
        "--good-line": oklch_hex(0.424, 0.070, 145),
        "--critical": oklch_hex(0.66, 0.13, 22), "--critical-bg": oklch_hex(0.245, 0.03, 22),
        "--critical-line": oklch_hex(0.424, 0.090, 22),
    },
    "light": {
        "--good": oklch_hex(0.50, 0.11, 145), "--good-bg": oklch_hex(0.94, 0.03, 145),
        "--good-line": oklch_hex(0.83, 0.05, 145),
        "--critical": oklch_hex(0.50, 0.14, 22), "--critical-bg": oklch_hex(0.94, 0.03, 22),
        "--critical-line": oklch_hex(0.83, 0.06, 22),
    },
}

_TOKENS_CSS = Path(__file__).resolve().parent.parent / "frontend/static/tokens.css"


def _app_accent() -> dict[str, dict[str, str]]:
    """The app's own accent, read from tokens.css so `set-accent.py` stays the
    single place it is chosen. Falls back to the guide's stock recipe."""
    try:
        s = _TOKENS_CSS.read_text(encoding="utf-8")
        h = float(re.search(r"--accent-h:\s*([\d.]+)", s).group(1))
        L = float(re.search(r"--accent-l:\s*([\d.]+)", s).group(1))
        C = float(re.search(r"--accent-c:\s*([\d.]+)", s).group(1))
        m = re.search(r"--accent:\s*oklch\(([\d.]+) ([\d.]+) var\(--accent-h\)\)", s)
        lL, lC = (float(m.group(1)), float(m.group(2))) if m else (0.55, 0.10)
    except Exception:                                    # pragma: no cover
        h, L, C, lL, lC = 68.0, 0.674, 0.101, 0.55, 0.10
    return {
        "dark": {"accent": oklch_hex(L, C, h),
                 "accent_dim": oklch_hex(0.447, C * 0.604, h),
                 "control_active": oklch_hex(0.29, 0.012, h)},
        "light": {"accent": oklch_hex(lL, lC, h),
                  "accent_dim": oklch_hex(0.79, lC * 0.36, h),
                  "control_active": oklch_hex(0.909, 0.020, h)},
    }


def builtin(base_id: str) -> dict[str, str]:
    """The twenty-seven values of a shipped theme. An id this build does not
    know falls back to graphite."""
    accent = _app_accent()
    if base_id == "paper":
        return {**_PAPER_NEUTRALS, **accent["light"]}
    return {**_GRAPHITE_NEUTRALS, **accent["dark"]}


BUILTINS = {
    "graphite": {"id": "graphite", "name": "Graphite", "scheme": "dark"},
    "paper":    {"id": "paper",    "name": "Paper",    "scheme": "light"},
}


def base_scheme(base_id: str) -> str:
    """A theme is dark because its base is, stated rather than measured off its
    colours."""
    return BUILTINS.get(base_id, BUILTINS[FALLBACK_BASE])["scheme"]


# ── derivation ─────────────────────────────────────────────────────────────
def derive(colours: dict[str, str], base_id: str) -> dict[str, str]:
    """The full `tokens.css` colour table from the twenty-seven stored keys.

    Everything not stored is computed here, which is what lets two apps given
    the same file compute the same interface.
    """
    scheme = base_scheme(base_id)
    out: dict[str, str] = {KEY_TO_CSS[k]: colours[k] for k in KEY_ORDER}

    out["--line-soft"]   = mix(colours["border"], colours["window"], 0.40)
    out["--line-dashed"] = mix(colours["border"], colours["text_dim"], 0.30)
    out["--placeholder"] = mix(colours["text_dim"], colours["window"], 0.30)
    out["--field"]       = colours["dock"] if scheme == "dark" else colours["popover"]
    out["--accent-ink"]  = colours["window"] if scheme == "dark" else colours["popover"]
    out["--accent-tint"] = rgba(colours["accent"], 0.07)
    out["--accent-ring"] = rgba(colours["accent"], 0.35)
    out["--grid"]        = out["--line-soft"]
    out["--area-alpha"]  = "0.14"
    out.update(_SEMANTIC[scheme])
    return out


# ── the file ───────────────────────────────────────────────────────────────
class ThemeFileError(ValueError):
    """The file is not a theme. Refused with a sentence, never read as a theme
    of entirely default colours."""


def _clean_name(text: str) -> str:
    """Control characters become spaces, then trim and cut to 64. The bound is
    not decoration: a name ends up on a card laid out every frame."""
    cleaned = "".join(" " if unicodedata.category(c)[0] == "C" else c for c in text or "")
    return cleaned.strip()[:MAX_NAME].strip()


def parse(text: str, *, stem: str = "") -> tuple[dict, int]:
    """Decode a `.umbertheme`. Returns (theme, skipped).

    `theme` is `{name, base, scheme, colours}` where `colours` is the complete
    twenty-seven, the base filling anything the file did not carry. `skipped`
    counts lines that named a colour but could not be read, so the caller can
    say so.
    """
    if text.startswith("\ufeff"):
        text = text[1:]                      # a byte-order mark is ignored
    lines = text.splitlines()
    if not lines or lines[0].strip().lower() != HEADER.lower():
        raise ThemeFileError(
            f"That file is not a theme. A theme's first line is "
            f"\u201c{HEADER}\u201d."
        )

    body = []
    for raw in lines[1:]:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue                          # blank, comment, or not a pair
        key, _, value = line.partition("=")
        body.append((key.strip(), value.strip()))

    # Read `base` first, then the colours: two passes, so the order somebody's
    # editor left the lines in cannot decide what the absent tokens fall back to.
    base = FALLBACK_BASE
    name = ""
    for key, value in body:
        if key == "base":
            base = value if value in BUILTINS else FALLBACK_BASE
        elif key == "name":
            name = _clean_name(value)

    colours = dict(builtin(base))
    skipped = 0
    for key, value in body:
        if key in ("base", "name"):
            continue
        parsed = parse_colour(value)
        if key not in KEY_TO_CSS or parsed is None:
            # A line that will not parse, and a key this build does not have,
            # cost that one colour and nothing else.
            skipped += 1
            continue
        colours[key] = parsed

    if not name:
        name = _clean_name(stem) or FALLBACK_NAME
    return {"name": name, "base": base, "scheme": base_scheme(base),
            "colours": colours}, skipped


def encode(name: str, base: str, colours: dict[str, str]) -> str:
    """Write every key, in file order, even where it equals the base's value,
    so what leaves the app is complete and legible."""
    base = base if base in BUILTINS else FALLBACK_BASE
    filled = {**builtin(base), **{k: v for k, v in colours.items() if k in KEY_TO_CSS}}
    out = [HEADER, "", f"name = {_clean_name(name) or FALLBACK_NAME}", f"base = {base}", ""]
    for label, keys in GROUP_LABELS:
        out.append(f"# {label}")
        for k in keys:
            out.append(f"{k} = {parse_colour(filled[k]) or '#000000'}")
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def skipped_sentence(n: int) -> str:
    return (f"{n} line{'' if n == 1 else 's'} could not be read, so those colours "
            f"came from the theme it names as its base.")


# ── the library on disk ────────────────────────────────────────────────────
def slugify(name: str) -> str:
    """The id is the filename stem: lower-cased, runs of non-alphanumerics
    collapsed to `-`, trimmed, cut to 48, `theme` if nothing survives."""
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")[:MAX_STEM].strip("-")
    return s or "theme"


class ThemeLibrary:
    """A directory of files, one theme per file. A write touches one small file
    rather than an index holding every theme, and the files are ordinary files
    somebody can hand to somebody else."""

    def __init__(self, directory: Path):
        self.dir = Path(directory)

    def _ensure(self) -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        return self.dir

    def path_for(self, theme_id: str) -> Path:
        # Defend the directory: an id is a stem, never a path.
        return self.dir / (slugify(theme_id) + EXTENSION)

    def unique_id(self, name: str) -> str:
        """A name already in the library gets a number rather than replacing a
        theme somebody built."""
        stem = slugify(name)
        candidate, n = stem, 2
        while (self.dir / (candidate + EXTENSION)).exists():
            suffix = f"-{n}"
            candidate = stem[:MAX_STEM - len(suffix)] + suffix
            n += 1
        return candidate

    def list(self) -> list[dict]:
        if not self.dir.is_dir():
            return []
        out = []
        for p in sorted(self.dir.glob("*" + EXTENSION))[:MAX_THEMES]:
            try:
                theme, skipped = parse(p.read_text(encoding="utf-8", errors="replace"),
                                       stem=p.stem)
            except ThemeFileError:
                continue                      # not a theme; leave it alone
            out.append({"id": p.stem, "name": theme["name"], "base": theme["base"],
                        "scheme": theme["scheme"], "skipped": skipped,
                        "builtin": False})
        return out

    def read(self, theme_id: str) -> tuple[dict, int]:
        p = self.path_for(theme_id)
        if not p.is_file():
            raise FileNotFoundError(theme_id)
        return parse(p.read_text(encoding="utf-8", errors="replace"), stem=p.stem)

    def write(self, theme_id: str, text: str) -> None:
        """Atomic: temp file, then rename."""
        self._ensure()
        target = self.path_for(theme_id)
        fd, tmp = tempfile.mkstemp(dir=str(self.dir), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            os.replace(tmp, target)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def delete(self, theme_id: str) -> bool:
        p = self.path_for(theme_id)
        if p.is_file():
            p.unlink()
            return True
        return False

    def raw(self, theme_id: str) -> str:
        return self.path_for(theme_id).read_text(encoding="utf-8", errors="replace")
