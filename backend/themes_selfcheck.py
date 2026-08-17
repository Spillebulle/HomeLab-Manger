"""Check `backend/themes.py` against STYLE-GUIDE.md §3.2, point by point.

    python -m backend.themes_selfcheck

The `.umbertheme` format is a *family* format: a file written here has to open
unchanged in the other apps, and one written there has to open here. That makes
the format the one part of this project where "it looks right on screen" is not
evidence of anything, so each rule in §3.2 gets an assertion.

There is no test suite in this repository and this is deliberately not the start
of one. It exists because an interchange format cannot be checked by looking at
it, and a silent drift here breaks somebody else's app, not ours.
"""

from __future__ import annotations

import sys

from . import themes as T


def main() -> int:
    ok = fail = 0

    def check(label: str, cond: bool, detail: object = "") -> None:
        nonlocal ok, fail
        if cond:
            ok += 1
            print(f"  ok    {label}")
        else:
            fail += 1
            print(f"  FAIL  {label}  {detail}")

    print("the file")
    check("stores exactly twenty-seven colours", len(T.KEY_ORDER) == 27, len(T.KEY_ORDER))
    try:
        T.parse("not a theme\nbackdrop = #000000\n")
        check("a file that is not a theme is refused", False)
    except T.ThemeFileError as exc:
        check("a non-theme is refused with a sentence", str(exc).endswith("."), exc)
    check("the header is case-insensitive and a BOM is ignored",
          T.parse("﻿UMBER THEME\nname = x\n")[0]["name"] == "x")
    check("blank, comment and no-'=' lines are skipped",
          T.parse("Umber theme\n\n# c\nnope\nname = Kept\n")[0]["name"] == "Kept")

    print("\nthe two lines that are not colours")
    check("a name is cut to 64", len(T.parse("Umber theme\nname = " + "z" * 200)[0]["name"]) == 64)
    check("control characters become spaces",
          T.parse("Umber theme\nname = ab\n")[0]["name"] == "a b")
    check("a blank name falls back to the file's stem",
          T.parse("Umber theme\n", stem="my-file")[0]["name"] == "my-file")
    check("and then to 'Untitled theme'",
          T.parse("Umber theme\n", stem="")[0]["name"] == T.FALLBACK_NAME)
    check("an id the reader does not know falls back to graphite",
          T.parse("Umber theme\nbase = nonsense\n")[0]["base"] == "graphite")
    check("a theme is dark because its base is, not because its colours are",
          T.parse("Umber theme\nbase = paper\n")[0]["scheme"] == "light")

    print("\ncolours")
    check("#RRGGBB in", T.parse_colour("#a1cb35") == "#A1CB35")
    check("RRGGBB in", T.parse_colour("a1cb35") == "#A1CB35")
    check("#RGB in, because that is what people type", T.parse_colour("#abc") == "#AABBCC")
    check("no alpha, ever", T.parse_colour("#A1CB3580") is None)
    check("anything else is refused rather than guessed",
          T.parse_colour("rebeccapurple") is None)

    theme, skipped = T.parse("Umber theme\nbase = graphite\nbackdrop = #101010\n"
                             "window = not-a-colour\nnope_key = #ffffff\n")
    check("a good line still lands", theme["colours"]["backdrop"] == "#101010")
    check("a line that will not parse costs that one colour",
          theme["colours"]["window"] == T.builtin("graphite")["window"])
    check("a key this build does not have costs one colour too", skipped == 2, skipped)
    check("what was skipped is counted and said", "base" in T.skipped_sentence(2))

    print("\ntwo passes")
    check("the order the lines are in cannot decide the fallbacks",
          T.parse("Umber theme\nbackdrop = #123456\nbase = paper\n")[0]["colours"]["window"]
          == T.builtin("paper")["window"])

    print("\nwriting")
    text = T.encode("Round trip", "graphite", {"backdrop": "#101010"})
    check("the first line is the header", text.splitlines()[0] == T.HEADER)
    written = [l.split("=")[0].strip() for l in text.splitlines()
               if "=" in l and not l.startswith("#")]
    check("every key is written, in file order",
          [k for k in written if k not in ("name", "base")] == T.KEY_ORDER)
    again, sk = T.parse(text)
    check("a round trip is lossless", sk == 0 and again["colours"]
          == T.parse(T.encode(again["name"], again["base"], again["colours"]))[0]["colours"])
    check("nothing with an alpha channel ever leaves",
          all(len(l.split("=")[1].strip()) == 7 for l in text.splitlines()
              if "=" in l and l.split("=")[0].strip() in T.KEY_TO_CSS))

    print("\nderivation")
    g, p = T.builtin("graphite"), T.builtin("paper")
    d, dl = T.derive(g, "graphite"), T.derive(p, "paper")
    check("--line-soft is border 40% of the way to window",
          d["--line-soft"] == T.mix(g["border"], g["window"], 0.40))
    check("--line-dashed is border 30% of the way to text-dim",
          d["--line-dashed"] == T.mix(g["border"], g["text_dim"], 0.30))
    check("--placeholder is text-dim 30% of the way to window",
          d["--placeholder"] == T.mix(g["text_dim"], g["window"], 0.30))
    check("--field is dock in a dark theme", d["--field"] == g["dock"])
    check("--field is popover in a light theme", dl["--field"] == p["popover"])
    check("--accent-ink is window in a dark theme", d["--accent-ink"] == g["window"])
    check("--accent-ink is popover in a light theme", dl["--accent-ink"] == p["popover"])
    check("--accent-tint is the accent at 7%", d["--accent-tint"] == T.rgba(g["accent"], 0.07))
    check("--accent-ring is the accent at 35%", d["--accent-ring"] == T.rgba(g["accent"], 0.35))
    check("--grid is --line-soft", d["--grid"] == d["--line-soft"])
    check("--good and --critical are not themeable",
          d["--good"] != dl["--good"] and "--critical" in d)
    check("--area-alpha is the constant", d["--area-alpha"] == "0.14")

    print("\nthe library")
    check("a slug collapses runs of non-alphanumerics", T.slugify("My  Nice Theme!!") == "my-nice-theme")
    check("a slug that survives nothing becomes 'theme'", T.slugify("!!!") == "theme")
    check("a slug is cut to 48", len(T.slugify("x" * 100)) == 48)

    print(f"\n{ok} passed, {fail} failed")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
