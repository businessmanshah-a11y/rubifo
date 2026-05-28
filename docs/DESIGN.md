# Design

## Color Palette

Warm stone with copper-amber accent. Light theme throughout.

### Strategy: Restrained
Single accent (copper-amber) at ≤10% of surface area. Everything else is warm stone neutrals.

### Tokens

| Token | Value | Use |
|---|---|---|
| `--bg` | `oklch(96.0% 0.006 72)` | Page background |
| `--surface` | `oklch(99.5% 0.003 72)` | Cards, panels |
| `--surface-2` | `oklch(96.8% 0.007 72)` | Table headers, hover states |
| `--surface-3` | `oklch(94.5% 0.008 72)` | Deep nesting |
| `--text` | `oklch(18% 0.014 52)` | Primary text |
| `--text-2` | `oklch(46% 0.010 65)` | Secondary labels |
| `--text-3` | `oklch(64% 0.008 65)` | Muted/placeholder |
| `--accent` | `oklch(52% 0.135 42)` | Primary actions, active nav |
| `--accent-dark` | `oklch(45% 0.135 42)` | Accent hover |
| `--border` | `oklch(86% 0.010 70)` | Input borders |
| `--border-soft` | `oklch(92% 0.006 70)` | Card separators |
| `--sidebar-bg` | `oklch(13.5% 0.014 52)` | Sidebar |

### Semantic States

All use **full-border treatment** — no side-stripe borders.

| State | Background | Foreground | Border |
|---|---|---|---|
| Success | `oklch(93.5% 0.040 145)` | `oklch(33% 0.120 145)` | `oklch(78% 0.100 145)` |
| Warning | `oklch(94.5% 0.050 78)` | `oklch(40% 0.125 68)` | `oklch(78% 0.110 68)` |
| Error | `oklch(93.5% 0.045 25)` | `oklch(40% 0.150 22)` | `oklch(72% 0.140 22)` |
| Info | `oklch(93.5% 0.035 248)` | `oklch(34% 0.100 248)` | `oklch(72% 0.090 248)` |

## Typography

**Font**: Inter (Google Fonts), fallback: `-apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif`

| Token | Size | Use |
|---|---|---|
| `--f-2xs` | 10px | Badge labels |
| `--f-xs` | 11px | Table headers, small labels |
| `--f-sm` | 13px | Body, table cells, buttons |
| `--f-base` | 14px | Default body |
| `--f-md` | 15px | Section headings |
| `--f-lg` | 18px | Modal headings |
| `--f-xl` | 24px | Login heading |
| `--f-2xl` | 30px | Page headings |
| `--f-3xl` | 38px | Metric values |

Weight: 400 (body), 500 (labels), 600 (section headings, buttons), 700 (page headings, metric values, nav)

## Elevation

| Level | Shadow | Use |
|---|---|---|
| `--sh-xs` | 1px lift | Metric cards, tables |
| `--sh-sm` | 2-layer subtle | Panels |
| `--sh-md` | Medium presence | Dropdowns |
| `--sh-lg` | Strong depth | Login box, modals |

## Spacing

Layout padding: `--content-pad: 36px` (collapses to 20px on mobile)  
Sidebar width: `--nav-w: 232px`  
Gap rhythm: 4 → 8 → 12 → 16 → 20 → 28 → 36px

## Components

### Metric Card
White card (`--surface`), 1px soft border, `--sh-xs` shadow, no border-top stripe.
Label: `--f-2xs`, 700 weight, uppercase, `--text-3`.
Value: `--f-3xl`, 700 weight, `--text`.

### Sidebar
Dark warm near-black (`--sidebar-bg`). Active item uses `--accent` fill, white text.
Hover: slightly lighter background. No left-stripe indicator.

### Badges
Pill shape (`border-radius: 100px`). Uses semantic color pairs. Uppercase, 700 weight, `--f-2xs`.

### Buttons
`--r-sm` (5px) radius. Primary: accent fill. Secondary: surface with border. Danger: error semantic colors.

### Data Table
Collapsed borders. Header row uses `--surface-2`, uppercase `--f-2xs` labels. Row hover: `--surface-2`.

## Rules

- No `border-left` or `border-right` colored accents
- No gradient text (`background-clip: text`)
- No `border-top` stripe on cards
- All semantic messages use full borders, not side stripes
- Emoji removed from navigation and section headings (data may still contain emoji)
