# UI conventions

Dated 2026-08-17. What the interface is made of, so that a change made in one
part of the SPA looks like it came from the same hand as every other part.

The rules themselves live in `../../Design-Principles/STYLE-GUIDE.md`. This page
settles only what that guide leaves to the project: which tokens this app sets,
what the class vocabulary is, and how the old markup maps onto the new.

## What this app sets

The accent hue is 255. `--accent` is raised off the guide's stock recipe so it
lands on exactly `#3987E5`, the blue the logo is drawn in:

| Token | Dark | Light |
|---|---|---|
| `--accent-h` | 255 | 255 |
| `--accent` | `oklch(0.622 0.161 255)` = `#3987E5` | `oklch(0.55 0.160 255)` |
| `--accent-dim` | `oklch(0.447 0.097 255)` | `oklch(0.79 0.058 255)` |

Everything else derives, so the system holds: two constants changed in
`frontend/static/tokens.css`, no colour hard-coded into a component. Measured
contrast, against the floors in §2.6 (accent on chrome 3:1, accent-ink on accent
4.5:1):

| | backdrop | window | dock | chrome | control |
|---|---|---|---|---|---|
| dark accent | 5.30 | 5.15 | 5.03 | 4.88 | 4.47 |
| light accent | | 4.16 | 4.28 | 4.51 | 3.98 |

`accent-ink` on `accent` is 5.15 dark, 4.90 light.

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
