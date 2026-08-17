# UI conventions

Dated 2026-08-17. What the interface is made of, so that a change made in one
part of the SPA looks like it came from the same hand as every other part.

The rules themselves live in `../../Design-Principles/STYLE-GUIDE.md`. This page
settles only what that guide leaves to the project: which tokens this app sets,
what the class vocabulary is, and how the old markup maps onto the new.

## What this app sets

The accent is **`#E13A9D`**, `oklch(0.628 0.221 349.1)`. It is the one colour
this project chooses; every other accent token derives from it.

**Changing it is one command**, because it touches the token file, the mark, all
the favicons and the banner together:

```sh
python docs/set-accent.py "#E13A9D"          # apply
python docs/set-accent.py "#3987E5" --check  # measure only, change nothing
python docs/set-accent.py "#3987E5" --keep-logo
```

The script refuses to write a colour that fails a contrast floor, and warns when
the hue sits close to a semantic colour or to a sibling app's accent. It also
picks the light-theme value for you: a colour bright enough to read on graphite
is usually too pale on paper, so light is the same hue re-stepped darker until it
clears the floors. Run it with `--check` for the current measurements rather than
trusting numbers written down here, which go stale the moment the accent moves.

Two things it warns about for the present colour, both accepted:

- It is 33 degrees from `--critical`. Distinguishable in practice, since one is
  magenta and the other a muted red, but they are the same warm family.
- It is 2 degrees from `--series-5`, the fifth categorical chart colour. That
  matters only in a chart with five or more series, which nothing in this app
  draws today. The rule that actually protects the accent is that it is never
  used as one of several series, and that still holds.

## Files

| File | What it holds |
|---|---|
| `frontend/static/tokens.css` | The tokens. Vendored from Design-Principles; only the accent block is ours. |
| `frontend/static/app.css` | Every component in §7 drawn once, in plain CSS against the tokens. |
| `frontend/static/fonts/Archivo.ttf` | The house typeface, bundled. Never a CDN. |
| `frontend/index.html` | The SPA. The icon sprite is inline at the top of `<body>`. |

Tailwind is still loaded from the Play CDN and is still the layout plumbing:
`flex`, `grid`, `gap-*`, `w-*`, `truncate`, `overflow-*`. It is no longer allowed
to carry colour, type size, radius or border. Those come from `app.css` classes
or, where a one-off is genuinely needed, from an inline `style` naming a token.

## The class vocabulary

Use these rather than reaching for utilities. The full list is the section
headings of `app.css`; the ones that come up constantly:

| Need | Class |
|---|---|
| Page/panel/dialog title | `.t-page` `.t-heading` |
| Body, control, small, tiny text | `.t-body` `.t-control` `.t-small` `.t-tiny` |
| Ink rank | `.t-strong` `.t-muted` `.t-dim` |
| A number read as a value | `.figure` (mono, tabular) |
| Section label inside a list | `.eyebrow` |
| Navigation row | `.nav-row` + `.is-selected` |
| Titled region | `.panel` `.panel-head` `.panel-body` |
| Buttons | `.btn` `.btn-primary` `.btn-outline` `.btn-ghost` `.btn-danger` `.btn-icon` |
| Inputs | `.input` `.field-label` `.field-hint` `.field-error` `.search` |
| Checkbox / toggle | `.check` `.toggle` |
| Tabs (<= 5 options) | `.segmented` + `.is-selected` |
| Rows and tables | `.row` `.tbl` `.kv` |
| Stat | `.tile` in a `.tile-grid` |
| Pickable thing | `.card` in a `.card-grid` |
| State | `.badge-good` `.badge-caution` `.badge-critical`, `.dot-good` … |
| Read-only figure | `.chip` |
| Dialog | `.scrim` + `.modal` + `.modal-sm/md/lg` |
| Menu / dropdown list | `.popover` `.popover-item` |
| Sentence in a box | `.notice` `.notice-critical` `.notice-good` |
| Nothing here yet | `.empty` |

## Icons

Font Awesome is gone. Icons are Lucide 0.544 (ISC) as an inline `<symbol>`
sprite, 24-unit viewBox, 1.5 stroke, round caps, referenced as:

```html
<svg class="icon"><use href="#i-server"/></svg>
```

`.icon` is 16 px (rows, buttons), `.icon-20` for panel headers, `.icon-24` for
empty states. Never larger, never a Unicode glyph, never an emoji. Colour comes
from `currentColor`, so set it on the parent: `text-muted` at rest,
`text-strong` on hover or selected, `accent` only for an active item.

Adding an icon means adding its Lucide symbol to the sprite. It does not mean
reaching for a different set. The two brand marks (`#i-github`, `#i-docker`) are
Simple Icons and are fill rather than stroke, because Lucide has no brands.

The mapping used when Font Awesome was removed:

| Was | Now | Was | Now |
|---|---|---|---|
| `fa-xmark` | `i-x` | `fa-triangle-exclamation` | `i-triangle-alert` |
| `fa-trash` | `i-trash-2` | `fa-plus` | `i-plus` |
| `fa-circle-notch fa-spin` | `i-loader-circle` + `.spinner` | `fa-plug-circle-check` | `i-plug-zap` |
| `fa-gauge`, `fa-gauge-high` | `i-gauge` | `fa-bolt` | `i-zap` |
| `fa-power-off` | `i-power` | `fa-pen` | `i-pencil` |
| `fa-globe` | `i-globe` | `fa-gear` | `i-settings` |
| `fa-display` | `i-monitor` | `fa-arrows-rotate` | `i-refresh-cw` |
| `fa-server` | `i-server` | `fa-rotate-right` | `i-rotate-cw` |
| `fa-rotate-left` | `i-rotate-ccw` | `fa-plug` | `i-plug` |
| `fa-lock` | `i-lock` | `fa-lock-open` | `i-lock-open` |
| `fa-floppy-disk` | `i-save` | `fa-download` | `i-download` |
| `fa-code` | `i-code` | `fa-clock-rotate-left` | `i-history` |
| `fa-bell` | `i-bell` | `fa-thermometer-half` | `i-thermometer` |
| `fa-stop` | `i-square` | `fa-sliders` | `i-sliders-horizontal` |
| `fa-sitemap`, `fa-network-wired` | `i-network` | `fa-right-left` | `i-arrow-right-left` |
| `fa-right-from-bracket` | `i-log-out` | `fa-rectangle-list` | `i-list` |
| `fa-question` | `i-circle-help` | `fa-plug-circle-xmark` | `i-unplug` |
| `fa-paper-plane` | `i-send` | `fa-microchip` | `i-cpu` |
| `fa-link` | `i-link` | `fa-link-slash` | `i-unlink` |
| `fa-key` | `i-key` | `fa-info-circle` | `i-info` |
| `fa-heart-pulse` | `i-activity` | `fa-hard-drive` | `i-hard-drive` |
| `fa-flask` | `i-flask-conical` | `fa-file-import` | `i-file-input` |
| `fa-ethernet` | `i-ethernet-port` | `fa-copy` | `i-copy` |
| `fa-circle-xmark` | `i-circle-x` | `fa-circle-exclamation` | `i-circle-alert` |
| `fa-circle-check`, `fa-check-circle` | `i-circle-check` | `fa-chart-line` | `i-chart-line` |
| `fa-chevron-right` / `-down` | `i-chevron-right` / `i-chevron-down` | `fa-github` / `fa-docker` | `i-github` / `i-docker` |

## Colour, before and after

The four ad-hoc colours and the Tailwind palette are both gone:

| Was | Now |
|---|---|
| `bg-surface` `#0f1117` | `var(--window)` for a page, `var(--backdrop)` for the ground |
| `bg-panel` `#161b27` | `var(--dock)` |
| `bg-card` `#1e2433` | `var(--chrome)` |
| `border-border` `#2a3144` | `var(--line)` |
| `bg-blue-600/20` + `text-blue-300` (selected) | `.is-selected`: `--control` fill, strong text, 3 px accent bar |
| `bg-blue-600` (primary button) | `.btn-primary` |
| `text-gray-200 / -400 / -500` | `--text` / `--text-muted` / `--text-dim` |
| `text-green-400` / `text-red-400` / `text-yellow-400` | `--good` / `--critical` / `--caution`, and usually a `.dot` rather than coloured text |
| `.tab-active` 2 px blue underline | `.segmented` |

## Things that are not negotiable

- **Selection is neutral.** `--control` fill, `text-strong`, plus a small accent
  mark. An accent background on a selected row, tab, nav item or card is the one
  defect this whole language exists to avoid.
- **The accent means selected, in hand, or primary**, and nothing else. The
  closed list is §2.4. Status is semantic colour, not the accent.
- **No raw hex in markup.** If a colour is missing, add a token.
- **Shadows only under things that float**: menus, dialogs, toasts. Not cards,
  not panels, not rows.
- **Figures are monospaced.** Every reading, count, percentage, size and time.
- **British spelling, sentence case, no em dashes** in anything a user reads.
- **A control that lies is worse than none.** Disable it with a `title` saying
  why, or do not draw it. A progress bar never animates over an unknown total.
- **No data is an en dash**, never a zero.

## Themes

Three states. `<html>` carries `class="dark"` or `class="light"` when the user
has chosen, and **nothing** when they follow the system. The choice is stored in
`localStorage` under `hlm-theme` as `dark` / `light` / `system`. Components never
read the class; they read tokens.

Chart.js is fed the tokens at render time by reading them off
`getComputedStyle(document.documentElement)`, and the charts are rebuilt on a
theme change. A chart never hard-codes a colour either.
