# Design Principles: Artistic Flair (Personal Archive)

These principles define the "Artistic Flair" aesthetic, focused on editorial contrast and hard-edged technical details. This system is designed specifically for a **FastAPI + HTMX** architecture.

## 1. Aesthetic: "Editorial Archive"
- **Color Palette**: High-contrast black on off-white (`#FDFCF8`). Subtle usage of opacity and radial grid overlays to add texture without clutter.
- **Typography**: 
  - **Display**: Large, light, italicized serif/sans with tight tracking for dramatic impact (e.g., "Off Grid").
  - **Metadata**: Strict monospace or bold condensed sans-serif for labels, usually in 10px-11px with wide tracking.
  - **Hierarchy**: Dramatic contrast between oversized headings and micro-labels.

## 2. Forms: "Hard Edges & Brutalist Shadows"
- **Borders**: Sharp 1px or 2px black borders. No rounded corners for primary cards; stay rectangular and bold.
- **Shadows**: Hard, offset shadows (e.g., `20px 20px 0px 0px rgba(0,0,0,1)`).
- **Inversion**: Use the "Invert" state (white-on-black vs black-on-white) for hover feedback.

## 3. Interaction: "HTMX-Driven Precision"
- **Server-Side Rendering**: All dynamic content must be served as HTML fragments via **FastAPI** routes.
- **Snappy Transitions**: Use `cubic-bezier(0.16, 1, 0.3, 1)` for all CSS transitions.
- **No-Scroll Stage**: The viewport remains fixed. Content is explored through localized components (spin wheel, modals).

## 4. Technical Architecture: "Zero-Node FastAPI"
- **Stack**: **Python (FastAPI)** + **Jinja2** templates.
- **Zero Build Step**: Using **HTMX** and **Tailwind CSS 4 (via Browser CDN)**. No Node.js or npm is required for production.
- **Template Inheritance**: All pages inherit from `base.html` using Jinja2 inheritance.
- **AI Agent Protocol**: 
  - To add a feature: Create a new FastAPI route in `main.py` -> Create a partial HTML in `templates/` -> Trigger via `hx-get` in the UI.

## 5. Extension Guide (For AI Agents)
- **Adding a Page**: Use `{% extends "base.html" %}`. Maintain the corner-fixed metadata pattern for consistency.
- **Adding an Interaction**: Use HTMX attributes (`hx-target`, `hx-swap`) on the trigger element. Target the `#project-modal` for detailed overlays.
- **Modifying Styles**: Directly edit the `<style>` block in `base.html` or use Tailwind classes in the templates. Avoid creating external CSS files.
