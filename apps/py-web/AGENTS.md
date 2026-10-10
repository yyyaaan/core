# apps/py-web (personal site)

FastAPI + Jinja2 + HTMX, styled with Tailwind CSS 4 via the browser CDN. **Zero-Node**: no npm, no build step, no bundler. Don't introduce one.

## Structure

- Routes in `src/web/main.py`. Pages return `TemplateResponse`; interactions return HTML fragments from `templates/partials/`.
- Every page `{% extends "base.html" %}`. All custom CSS lives in the `<style>` block of `base.html` or as Tailwind classes. Never add `.css` files.
- `#project-modal` in `base.html` is the overlay target for HTMX swaps; reuse it rather than adding new overlays.
- Keep the corner-fixed metadata elements in `base.html` on every page.

## Design system ("editorial archive")

- Black on off-white `#FDFCF8`; texture from subtle opacity and grid overlays.
- Type: oversized light italic display headings with tight tracking, against tiny (10–11px) wide-tracked mono or condensed labels. The contrast is the point.
- Hard edges: 1–2px solid black borders, no border-radius on primary cards, hard offset shadows (`20px 20px 0 0 #000`). Hover inverts colors.
- Motion: `cubic-bezier(0.16, 1, 0.3, 1)` for transitions.
- The viewport stays fixed (no full-page scroll); content lives in modals, drawers and other local components.

## Adding things

- Page: `async def` route + `templates/<page>.html` extending `base.html`.
- Interaction: route returning a partial, trigger with `hx-get` / `hx-target` / `hx-swap`.
- Run `uv run web` (port 8001, reload) and `uv run pytest apps/py-web/tests/`.
