---
name: py-web-design
description: Design system and UI extension guide for apps/py-web — "Artistic Flair" editorial aesthetic, HTMX-driven FastAPI, Zero-Node stack
---

## Aesthetic: "Editorial Archive"

- **Color palette**: High-contrast black on off-white (`#FDFCF8`). Subtle opacity and radial grid overlays for texture.
- **Typography**:
  - Display: Large, light, italicized serif/sans with tight tracking (e.g., `font-weight: 300; font-style: italic; letter-spacing: -0.02em`)
  - Metadata: Strict monospace or bold condensed sans-serif, 10–11px, wide tracking
  - Hierarchy: Dramatic contrast between oversized headings and micro-labels
- **No rounded corners** on primary cards — rectangular and bold only

## Forms: "Hard Edges & Brutalist Shadows"

- Borders: Sharp `1px` or `2px solid black`. No border-radius on primary cards.
- Shadows: Hard offset — `box-shadow: 20px 20px 0px 0px rgba(0,0,0,1)`
- Hover state: Invert (white-on-black ↔ black-on-white), no soft transitions

## Interaction: "HTMX-Driven Precision"

- All dynamic content: HTML fragments returned from **FastAPI** routes, swapped via HTMX
- CSS transitions: always use `cubic-bezier(0.16, 1, 0.3, 1)`
- Viewport stays fixed — no full-page scrolling; use localized components (modals, spin wheels, drawers)
- Modal target: `#project-modal` is the canonical overlay anchor

## Technical Architecture: "Zero-Node FastAPI"

| Concern | Solution |
|---------|----------|
| Server | Python (FastAPI) + Uvicorn |
| Templates | Jinja2 — all pages `{% extends "base.html" %}` |
| Reactivity | HTMX (via CDN) |
| Styling | Tailwind CSS 4 (via Browser CDN) — no Node/npm build step |
| Auth | OAuth2-Proxy at ingress — no auth code in app |

- Corner-fixed metadata pattern must be preserved across all pages
- Never create external CSS files — edit `<style>` block in `base.html` or use Tailwind classes

## AI Agent Protocol

### Adding a page
1. Add a new `async def` route in `src/web/main.py` returning `TemplateResponse`
2. Create `templates/<page>.html` starting with `{% extends "base.html" %}`
3. Preserve the corner-fixed metadata block

### Adding an interaction
1. Add a FastAPI route returning a partial HTML fragment
2. Put `hx-get`, `hx-target`, `hx-swap` on the trigger element in the template
3. Target `#project-modal` for overlay content

### Modifying styles
- Edit the `<style>` block in `base.html` **or** add Tailwind utility classes inline
- Do **not** create new `.css` files
