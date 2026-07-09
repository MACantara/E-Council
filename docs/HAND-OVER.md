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

No outstanding redesign work remains. The document add/update/delete forms have been converted to Tailwind CSS and the shared macro system, the legacy `static/css/` directory has been removed, and JS-only classes (`show-password-button`, `input-pair`) remain as unstyled hooks. Ongoing improvements are now tracked in `docs/ROADMAP.md`.

---

## 🎯 Tailwind / CSS reduction plan

Goal: reduce custom CSS to near zero. Use Tailwind utility classes and arbitrary values (`[...]`) for any one-off sizes or colors.

### Recommended approach

The Tailwind CSS 4 migration and macro rollout are complete. The legacy `static/css/` directory has been removed and all listed forms use Tailwind utilities and the shared macros. Future template work should follow `DESIGN.md` tokens and the existing macro patterns.

1. **Use the shared macros for new forms**
   - `input`, `select`, `textarea`, `file_input`, `button`, `button_link`, and `card` from `templates/macros/`.
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
2. **Use Tailwind design tokens**
   - Avoid inline styles or `style` attributes. Use `bg-surface`, `text-ink-2`, `border-edge`, etc.
   - For chart colors and special one-offs, use arbitrary values such as `text-[#0891b2]` or `bg-[#0f172a]` only when a token does not already exist.
3. **Keep JS hooks minimal**
   - Retain `show-password-button`, `input-pair`, and any modal JS hooks as plain class names with no CSS rules.
4. **Final verification**
   - Run `pytest -q` after each batch of template edits.
   - Spot-check rendered pages in both light and dark mode.
   - Confirm Chart.js charts update correctly on `themeChanged`.

### Macro cheat sheet

```jinja
{% from 'macros/forms.html' import input, textarea, select, file_input %}
{% from 'macros/ui.html' import button, button_link, card, badge, alert, empty_state %}
{% from 'macros/icons.html' import lucide %}
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

## � Environment variables

All runtime configuration is loaded from environment variables. A complete, commented example is provided in `.env.example`.

### Required for any environment
- `SECRET_KEY` — Flask secret key for sessions and tokens.
- `SQLALCHEMY_DATABASE_URI` — Database connection URI (SQLite or MySQL).
- `MAIL_DEFAULT_SENDER` — Email address used as the sender for system emails.

### Required for features
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USE_SSL`, `MAIL_USERNAME`, `MAIL_PASSWORD` — SMTP settings for sending emails.
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` — Cloudinary for image uploads.
- `GOOGLE_GEMINI_AI_API_KEY` — Google Gemini for AI-assisted document generation.

### Optional
- `SENTRY_DSN` — Sentry DSN for error tracking.
- `FLASK_ENV` — `development`, `testing`, or `production` (defaults to `development`).

Copy `.env.example` to `.env`, fill in the values, and restart the application. The `.env` file is gitignored and must never be committed.

---

## �🔧 Notes from the latest session

- `templates/account/account-settings.html` was corrected so the delete-account cancel button id matches `account-settings.js` (`cancel-delete-user-account-button`).
- `static/js/account/password-security-settings.js` was converted from Bootstrap `bi-*` icons to Lucide `x-circle`/`check-circle` icon spans toggled with `.hidden`.
- `templates/account/password-security-settings.html` still references `show-password-button` as a JS hook; no custom CSS is required for it.
- `pytest -q` currently reports **62 passed** and a few third-party deprecation warnings.
