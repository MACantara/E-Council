# E-Council Redesign — HAND-OVER

**Date:** 2026-07-09  
**Current branch/state:** Work-in-Progress redesign  
**Last completed work:** Dashboard, event-management, account settings, and document overview pages redesigned with Tailwind v4 and the shared macro system.

## ✅ What is done

### Design system foundation
- `DESIGN.md` and `templates/base.html` define a Tailwind v4 CDN theme (`@theme`) with semantic tokens:
  `surface-bg`, `surface`, `surface-lowered`, `edge`, `ink`, `ink-2`, `ink-3`, `accent`, `danger`, `success`, `warning`, `info`, etc.
- Shared macros in `templates/macros/`
  - `forms.html` — `input`, `textarea`, `select`, `file_input`
  - `ui.html` — `button`, `button_link`, `card`, `badge`, `alert`, `modal`, `empty_state`
  - `icons.html` — `lucide`
  - `email.html` — `email_button` for table-based email layouts
- `static/js/theme.js` handles light/dark toggle and fires `themeChanged` so Chart.js colors update.
- Legacy chart CSS aliases live in `templates/base.html` until custom CSS is purged.

### Pages/templates that have been redesigned

- **Landing page** — `templates/index.html`
  - Fixed module count to "Three modules" and added Lucide icons to module headings.
- **Authentication pages** — `templates/auth/login.html`, `signup.html`, `forgot-password.html`, `reset-password.html`
- **Email templates** — all `.html` and `.txt` templates under `templates/email/`
- **Dashboard & overview pages**
  - `templates/dashboard/council-overview.html`
  - `templates/dashboard/council-overview-sidebar.html`
  - `templates/events/events-overview.html`
  - `templates/events/event-dashboard.html`
- **Event management pages**
  - `templates/events/add-event.html`
  - `templates/events/update-event.html`
  - `templates/events/add-transaction.html`
  - `templates/events/update-transaction.html`
  - `templates/events/invite-user.html`
  - `templates/events/delete-event.html`
- **Document module overview pages**
  - `templates/concept-papers/concept-papers-overview.html`
  - `templates/documentation/documentation-overview.html`
  - `templates/financial-reports/financial-reports-overview.html`
  - `templates/board-resolutions/board-resolutions-overview.html`
  - `templates/minutes-of-meeting/minutes-of-the-meeting-overview.html`
- **Account pages**
  - `templates/account/account.html`
  - `templates/account/account-settings.html`
  - `templates/account/account-settings-sidebar.html`
  - `templates/account/email-settings.html`
  - `templates/account/password-security-settings.html`
  - `static/js/account/password-security-settings.js` updated for Lucide icons and Tailwind classes.

### Tests
- `pytest -q` passes **62 tests** after the latest edits.

---

## ⏳ What is NOT done

### 1. Document add/update/delete forms
These files still use legacy custom CSS classes (`council-overview-container`, `input-pair`, `primary-button`, `secondary-button`, etc.):

- **Concept papers**
  - `templates/concept-papers/add-concept-paper.html`
  - `templates/concept-papers/update-concept-paper.html`
  - `templates/concept-papers/delete-concept-paper.html`
  - `templates/concept-papers/concept-paper-generation.html`
- **Documentation**
  - `templates/documentation/add-documentation.html`
  - `templates/documentation/update-documentation.html`
  - `templates/documentation/delete-documentation.html`
- **Financial reports**
  - `templates/financial-reports/add-financial-report.html`
  - `templates/financial-reports/update-financial-report.html`
  - `templates/financial-reports/delete-financial-report.html`
- **Board resolutions**
  - `templates/board-resolutions/add-board-resolution.html`
  - `templates/board-resolutions/update-board-resolution.html`
  - `templates/board-resolutions/delete-board-resolution.html`
- **Minutes of the meeting**
  - `templates/minutes-of-meeting/add-minutes-of-the-meeting.html`
  - `templates/minutes-of-meeting/update-minutes-of-the-meeting.html`
  - `templates/minutes-of-meeting/delete-minutes-of-the-meeting.html`

### 2. Custom CSS to purge
The `static/css/` directory still contains legacy selectors that should be replaced by Tailwind utilities. Files to review and largely delete:

- `static/css/base.css` (5.5 KB)
- `static/css/components/`
  - `buttons.css`
  - `cards.css`
  - `forms.css`
  - `modals.css`
  - `tables.css`
- `static/css/layouts/`
  - `grid.css`
  - `header.css`
  - `sidebar.css`
- `static/css/pages/`
  - `auth.css`
  - `dashboard.css`
  - `documentation.css`

Some of these may still be loaded by `static/css/styles.css`.

### 3. JS hook classes that may still need a CSS home
A few class names are still used only as JavaScript hooks and no longer need styled rules:

- `show-password-button` — used in auth and `password-security-settings.js` to find toggle buttons.
- `input-pair` — used in `add-event.js` to hide/show fields via `closest('.input-pair')`.

When custom CSS is purged, these classes can remain as unstyled JS hooks.

---

## 🎯 Tailwind / CSS reduction plan

Goal: reduce custom CSS to near zero. Use Tailwind utility classes and arbitrary values (`[...]`) for any one-off sizes or colors.

### Recommended approach

1. **Finish the document forms first.**
   - Use the `input`, `select`, `textarea`, `file_input`, `button`, `button_link`, and `card` macros.
   - Wrap forms with the sidebar layout pattern already established:
     ```html
     <div class="flex min-h-[calc(100vh-4rem)] flex-col lg:flex-row">
       {% include "dashboard/council-overview-sidebar.html" %}
       <main class="flex-1 overflow-auto p-4 lg:p-8">
         <div class="mx-auto max-w-2xl space-y-6">
           ...
         </div>
       </main>
     </div>
     ```
2. **Audit and purge `static/css/`**
   - Once no template references old classes, remove the legacy component/page CSS.
   - Keep a minimal `styles.css` if still needed for a few global resets, or merge it into `base.css`.
   - Use Tailwind `@theme`/`@layer` directives in `base.html` for any remaining design tokens.
3. **Replace arbitrary hex values with design tokens**
   - Avoid inline styles or `style` attributes. Use `bg-surface`, `text-ink-2`, `border-edge`, etc.
   - For chart colors and special one-offs, use arbitrary values such as `text-[#0891b2]` or `bg-[#0f172a]` only when a token does not already exist.
4. **Keep JS hooks minimal**
   - Retain `show-password-button`, `input-pair`, and any modal JS hooks as plain class names with no CSS rules.
5. **Final verification**
   - Run `pytest -q` after each batch of template edits.
   - Spot-check rendered pages in both light and dark mode.
   - Confirm Chart.js charts update correctly on `themeChanged`.

### Macro cheat sheet

```jinja
{% from 'macros.forms.html' import input, textarea, select, file_input %}
{% from 'macros.ui.html' import button, button_link, card, badge, alert, empty_state %}
{% from 'macros.icons.html' import lucide %}
```

Example button:
```html
{{ button_link('Create New', url_for('...'), variant='primary', icon='plus') }}
```

Example card:
```html
{% call card(title='Section Title') %}
  ...
{% endcall %}
```

---

## ⚠️ Important constraints

- **Do not change form field `id` or `name` attributes.** Backend routes rely on them.
- **Do not remove or move `csrf_token` hidden inputs** in forms.
- **Preserve status-select names and `data-*` attributes** on overview pages so the existing `*-overview.js` files continue to work.
- Email templates still require table layouts and inline styles for client compatibility; do not convert them to Tailwind.
- Some JS files (`utils.js`) rely on `.modal`/`data-modal-*` classes. Review those when converting modal markup.

---

## 🔧 Notes from the latest session

- `templates/account/account-settings.html` was corrected so the delete-account cancel button id matches `account-settings.js` (`cancel-delete-user-account-button`).
- `static/js/account/password-security-settings.js` was converted from Bootstrap `bi-*` icons to Lucide `x-circle`/`check-circle` icon spans toggled with `.hidden`.
- `templates/account/password-security-settings.html` still references `show-password-button` as a JS hook; no custom CSS is required for it.
- `pytest -q` currently reports **62 passed** and a few third-party deprecation warnings.
