# E-Council Design System

## What is DESIGN.md?

`DESIGN.md` is the portable, markdown-based format for design systems, built for AI-native development. It captures colors, typography, spacing, component patterns, elevation, and usage guidance in a single human-readable file that any AI coding agent can read and follow.

## Why does this matter?

- **AI agents understand it natively** — plain markdown is what LLMs read best, with no special parsing libraries or schema validation needed.
- **Version-controllable** — a text file that can be tracked in git, reviewed in PRs, and evolved alongside the codebase.
- **Tool-agnostic** — works with Cascade, Claude Code, Cursor, Copilot, and any agent that can read project files.
- **Human-readable** — designers and developers can both read and edit it, with no proprietary formats.

## How to use this design system

1. Copy this file to the project root as `DESIGN.md`.
2. Reference `DESIGN.md` when building or updating any UI in the project.
3. Use the Tailwind v4 Play CDN and the Lucide icon CDN from `templates/base.html` to match these tokens in code.

## E-Council Design System

### Colors

#### Primary palette

- **Accent / Cyan** (`#0891b2` light, `#06b6d4` dark): primary buttons, active nav items, focus rings, key links, and positive emphasis.
- **Accent Hover** (`#0e7490` light, `#22d3ee` dark): primary button/link hover and pressed states.

#### Neutral palette

Use `slate` for surfaces, text, and borders. The scale below is semantic for both modes:

| Token | Light mode | Dark mode | Usage |
|---|---|---|---|
| Background (`surface-bg`) | `#f8fafc` | `#020617` | Page background |
| Surface (`surface`) | `#ffffff` | `#0f172a` | Cards, modals, forms, elevated panels |
| Surface Lowered (`surface-lowered`) | `#f1f5f9` | `#1e293b` | Subtle panels, table headers, hover states |
| Border (`edge`) | `#e2e8f0` | `#334155` | Dividers, input borders, card outlines |
| Text Primary (`ink`) | `#0f172a` | `#f8fafc` | Headings, body text |
| Text Secondary (`ink-2`) | `#475569` | `#cbd5e1` | Labels, descriptions, muted text |
| Text Tertiary (`ink-3`) | `#94a3b8` | `#64748b` | Placeholders, disabled text, meta |

#### Semantic colors

| Token | Light | Dark | Usage |
|---|---|---|---|
| Success (`success`) | `#059669` | `#10b981` | Success messages, income, completion |
| Danger (`danger`) | `#e11d48` | `#f43f5e` | Errors, delete actions, expenses (red) |
| Warning (`warning`) | `#f59e0b` | `#fbbf24` | Warnings, pending states |
| Info (`info`) | `#2563eb` | `#3b82f6` | Neutral notices, help text |

#### Theming note

The default theme follows `prefers-color-scheme`. A user toggle overrides it and stores the choice in `localStorage`. CSS custom properties map these colors to `--color-surface`, `--color-ink`, `--color-accent`, etc., so Chart.js and custom CSS can consume the same values.

### Typography

- **Font family**: `Inter`, `ui-sans-serif`, `system-ui`, `sans-serif`.
- **Base size**: `16px` / `1rem` with `1.5` line height.

#### Scale

| Style | Size | Weight | Line-height | Usage |
|---|---|---|---|---|
| Display / Hero | `36px` | 700 | 1.1 | Landing hero headline |
| H1 | `30px` | 700 | 1.2 | Page titles |
| H2 | `24px` | 600 | 1.25 | Section headings |
| H3 | `20px` | 600 | 1.3 | Card titles, sub-sections |
| H4 | `18px` | 600 | 1.3 | Form section headings |
| Body | `16px` | 400 | 1.5 | Paragraphs, general content |
| Small / Label | `14px` | 500 | 1.4 | Form labels, buttons, badges |
| XSmall | `12px` | 400 | 1.33 | Captions, helper text, timestamps |

### Spacing

The base unit is `4px` (`0.25rem`). All padding, margins, and gaps use this scale. Common values:

- `4px` (`0.25rem`) — icon gaps, tight inline spacing
- `8px` (`0.5rem`) — small gaps between related items
- `12px` (`0.75rem`) — input padding vertical, compact groups
- `16px` (`1rem`) — default card padding, section gaps
- `24px` (`1.5rem`) — large card padding, form section spacing
- `32px` (`2rem`) — page sections, hero spacing
- `48px` (`3rem`) — major page breaks

Container max widths:

- Auth/empty cards: `448px` (`max-w-md`)
- Single-column forms: `672px` (`max-w-2xl`)
- Dashboard content: `1280px` (`max-w-7xl`)

### Components

#### Buttons

- **Primary**: background `#0891b2` (`--color-accent`), white text, `8px` radius, padding `12px 20px`, `14px` font, weight `600`. Hover: `#0e7490` (`--color-accent-hover`).
- **Secondary**: transparent background, `1px` `#e2e8f0` border (`--color-edge`), text `#0f172a` (`--color-ink`), same radius/padding. Hover: `#f1f5f9` (`--color-surface-lowered`).
- **Danger**: background `#e11d48` (`--color-danger`), white text. Hover: `#be123c` (`--color-danger-hover`).
- **Ghost**: no border, text `#475569` (`--color-ink-2`). Hover: `#f1f5f9` (`--color-surface-lowered`).
- **Icon button**: `40×40px` square, `8px` radius, centered Lucide icon, ghost style.
- **Disabled state**: `opacity: 0.5`, `cursor: not-allowed`.

Tailwind classes: `bg-accent text-white hover:bg-accent-hover`, `border border-edge bg-surface text-ink hover:bg-surface-lowered`, etc.

#### Inputs, selects, textareas

- Height `44px` for inputs/selects; padding `10px 14px`; `8px` radius; `1px` `#e2e8f0` border (`--color-edge`); background `#ffffff` (`--color-surface`); text `#0f172a` (`--color-ink`).
- Placeholder color `#94a3b8` (`--color-ink-3`).
- Focus: `2px` solid `#0891b2` (`--color-accent`) with a subtle outer ring.
- Labels: `14px`, weight `500`, color `#475569` (`--color-ink-2`), margin-bottom `6px`.
- Error: border `#e11d48` (`--color-danger`), below-input text `#e11d48` at `14px`.
- Textarea: min-height `100px`, resize vertical.

#### Cards

- Background `#ffffff` (`--color-surface`), `1px` `#e2e8f0` border (`--color-edge`), `12px` radius, padding `24px`, subtle shadow.
- Used for forms, overviews, dashboards, and elevated panels.
- Hover on interactive cards: `background #f1f5f9` (`--color-surface-lowered`) and slightly deeper shadow.

#### Badges

- `font-size: 12px`, weight `600`, padding `4px 10px`, `9999px` radius.
- Variants:
  - Accent (`bg-accent text-white`)
  - Success (`bg-success text-white`)
  - Danger (`bg-danger text-white`)
  - Warning (`border border-warning text-warning`)
  - Info (`bg-info text-white`)
  - Default (`border border-edge text-ink-2`)
- Outline variants use a `1px` border and transparent background.

#### Modals

- Overlay: `rgba(0,0,0,0.5)` with `backdrop-filter: blur(4px)`.
- Panel: background `#ffffff` (`--color-surface`), `16px` radius, padding `24px`, max-width `512px` (`max-w-lg`), centered, large shadow.
- Close button: top-right `12px`, ghost icon button.

#### Alerts / flash messages

- `border-radius: 8px`, padding `16px`, `4px` left border in a semantic color.
- Background: `surface-lowered` (`#f1f5f9` light, `#1e293b` dark).
- Text uses the matching dark semantic color for the theme.

#### Tables

- Full width inside an `overflow-x-auto` wrapper; `8px` radius on the wrapper.
- Header: `#f1f5f9` (`--color-surface-lowered`), weight `600`.
- Rows separated by `1px` `#e2e8f0` (`--color-edge`).
- Row hover: `#f1f5f9` (`--color-surface-lowered`).

#### Empty states

- Centered icon (`48px` Lucide), heading H3, muted description, and a single primary CTA.

### Elevation

#### Border radius

- `8px` (`rounded-lg`) — buttons, inputs, alerts, table wrappers
- `12px` (`rounded-xl`) — cards
- `16px` (`rounded-2xl`) — modals
- `9999px` (`rounded-full`) — badges, avatars

#### Shadows

- **None** — flat inline content.
- **Small** (`shadow-sm`): `0 1px 2px 0 rgba(2,6,23,0.05)` — subtle cards.
- **Default** (`shadow`): `0 1px 3px 0 rgba(2,6,23,0.1), 0 1px 2px -1px rgba(2,6,23,0.1)` — hover-lift.
- **Large** (`shadow-lg`): `0 10px 15px -3px rgba(2,6,23,0.1), 0 4px 6px -4px rgba(2,6,23,0.1)` — modals, dropdowns.

### Guidelines

#### Do

- Use the semantic color tokens above rather than arbitrary hex values.
- Build mobile-first: every page starts as a single column and adapts with `sm:`, `md:`, `lg:` breakpoints.
- Keep all interactive elements at least `40×40px` (`min-h-10 min-w-10`) for touch targets.
- Maintain a minimum `4.5:1` contrast ratio for normal text and `3:1` for large text.
- Use Inter for all UI text.
- Use Lucide icons at `20px` default, `16px` inline, and `24px` for empty-state/hero illustrations.
- Use the accent color only for primary actions, active navigation, and focus states.
- Call `lucide.createIcons()` after any JavaScript that injects new icons.
- Use the form and UI Jinja macros defined in `templates/macros/` to keep pages consistent.

#### Don't

- Don't hardcode colors outside the design system.
- Don't use shadows on flat content; reserve them for cards, modals, and floating panels.
- Don't rely on color alone to convey status; pair badges/icons with text where possible.
- Don't change form `id` or `name` attributes when redesigning templates; preserve backend contract.

### Example

```html
<!-- Primary button -->
<button class="inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-accent-hover focus:outline-none focus:ring-2 focus:ring-accent">
  Create Event
</button>

<!-- Card -->
<div class="rounded-xl border border-edge bg-surface p-6 shadow-sm">
  <h3 class="text-xl font-semibold text-ink">Event Title</h3>
  <p class="mt-2 text-sm text-ink-2">Description text</p>
</div>
```

## Implementation notes

- Tailwind v4 Play CDN: `<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>`.
- Lucide icons: `<script src="https://unpkg.com/lucide@latest"></script>`; initialize with `lucide.createIcons()`.
- Theme toggle is stored in `localStorage`; default follows OS `prefers-color-scheme`.
- Chart.js uses CSS custom properties for axis/grid/dataset colors via `static/js/charts-theme.js`.
- Email templates require table-based layouts and inline styles for client compatibility.

### API and Frontend

The FastAPI backend (`api/`) exposes the full application surface at `/api/v1/` with OpenAPI/Swagger documentation at `/docs` and `/redoc`. The current Jinja2/Tailwind UI remains the production frontend while the React + TypeScript frontend is planned for Phase 4.21. When building the new frontend, reuse the existing Tailwind tokens and component patterns above, and consume the API using the same semantic color and spacing scale. Auth is JWT-based; store access tokens securely and refresh them as needed.
