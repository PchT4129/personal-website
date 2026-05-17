# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dev Server

```bash
cd ~/dev/personal-site
/home/yixiao/miniforge3/envs/personal-site/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Uses the `personal-site` conda environment. The `--reload` flag enables hot reload on file changes.

## Deploy

Push to `main` triggers automatic redeploy on Render:

```bash
git add .
git commit -m "description"
git push
```

Live at **yixiao-tao.com** (Render → Cloudflare DNS).

## Architecture

Single-page personal website with a FastAPI backend serving a Jinja2 template.

- `main.py` — one route (`GET /`) returning `templates/index.html`
- `templates/index.html` — entire site in one file: HTML structure + all JS (Leaflet map, city data, dark mode, scroll animations)
- `static/css/style.css` — all styles using CSS variables for dark/light mode theming
- `static/images/` — avatar, school logos (UCL SVG, XMUMY PNG, Xiaoshi PNG with transparent bg)
- `static/files/` — CV PDFs (cv-en.pdf, cv-zh.pdf)

## Key Patterns

**Dark mode** — toggled via `html.dark` class, persisted in `localStorage`, CSS variables handle all color switching.

**City map** — Leaflet.js with CartoCD tiles. The `cities` array in `index.html` is the single source of truth for all map markers and the country accordion list. Each city has `{ name, lat, lng, note, country, fi }` where `fi` is the flag-icons country code.

**Starlette TemplateResponse** — uses the newer API: `templates.TemplateResponse(request=request, name="index.html")` (not the old context dict form).

## Adding Cities

Add to the `cities` array in `index.html`. The accordion list is auto-generated from this array — no other changes needed.
