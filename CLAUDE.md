# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dev Server

```bash
cd ~/dev/personal-site
/home/yixiao/miniforge3/envs/personal-site/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Uses the `personal-site` conda environment. The `--reload` flag enables hot reload on file changes.

## Deploy

Target: Cloudflare Pages with Git integration. See `README.md` for initial setup
and domain cutover. Build command:
`python -m pip install -r requirements-build.txt && python scripts/build_static.py`.
Publish `dist/`; `.python-version` pins the build interpreter. The build generates
Pages `_headers` from `site_content.SECURITY_HEADERS`, including static caching
and noindex on pages.dev hosts. Do not add an SPA catch-all rewrite.
GitHub Actions validates builds on pushes and PRs; Pages independently builds and
publishes through its Git integration. Photos and thumbnails are generated at build
time. FastAPI is retained for local development. Production needs no Python server.

## Architecture

Single-page personal website with a FastAPI backend serving a Jinja2 template.

- `main.py` — `GET /` renders `templates/index.html`; scans `static/images/cities/` on every request to discover gallery photos (and their thumbnails). Also serves `/robots.txt`, `/sitemap.xml`, `/favicon.ico`, a `404.html` page, gzip, security headers (CSP), and `Cache-Control` on `/static`
- `templates/index.html` — semantic page structure, project summaries, system diagram, and early theme initialization
- `static/js/site.js` — navigation, theme, lazy-loaded Leaflet map, city search, photo dialog, and contact links
- `static/js/cities.js` — shared travel data for markers, searchable country lists, and photo journal
- `static/css/style.css` — all styles using CSS variables for dark/light mode theming
- `templates/illustrations/` — inline SVGs: SAV-SLAM architecture and a data-derived LoopLens plot; use site theme variables
- `scripts/draw_looplens.py` — regenerates the LoopLens chart from saved KITTI trajectories and ground truth (NumPy/Matplotlib, development only); also exports `static/images/projects/looplens-kitti00.svg`. The inline include is compacted (RDP-simplified paths); `--compact-only` re-compacts it without the data
- `scripts/make_thumbs.py` — builds 640px WebP gallery thumbnails in `static/images/cities/thumbs/` (Pillow, also used during static builds)
- `scripts/make_brand_images.py` — builds `static/images/icons/` (favicon, apple-touch-icon) and the 1200×630 `static/images/og-card.png` share image
- `static/images/` — avatar, share card, icons, school logos (UCL JPG, XMUMY SVG, Xiaoshi PNG with transparent bg)
- `static/files/` — CV PDFs (cv-en.pdf, cv-zh.pdf)

## Key Patterns

**Dark mode** — toggled via `html.dark` class, persisted in `localStorage`, CSS variables handle all color switching.

**City map** — Leaflet.js with OpenStreetMap standard tiles (URL configured on `#map`); CSS adapts the tile layer to dark mode. Keep visible attribution and default browser caching/referrer behavior per https://operations.osmfoundation.org/policies/tiles/. The `cities` array in `static/js/cities.js` supplies map markers, the searchable country accordion, travel counts, and country metadata for gallery photos. Each city has `{ name, lat, lng, note, country, fi, photo? }`; `fi` is a retained country code, and optional `photo` is a filename under `static/images/cities/`. Leaflet loads when the map enters the viewport; other interactions still work if the CDN is unavailable.

**Asset URLs** — reference CSS/JS with `{{ static_url('css/style.css') }}`; it appends a content hash so the one-day static cache refreshes after each change. New third-party origins must be added to `CSP` in `site_content.py`.

**Starlette TemplateResponse** — uses the newer API: `templates.TemplateResponse(request=request, name="index.html")` (not the old context dict form).

## Adding Cities

Add to the `cities` array in `static/js/cities.js`. The accordion list is auto-generated from this array — no other changes needed.

## City Gallery

Add JPG/JPEG, PNG, WebP, or AVIF files to `static/images/cities/`, run `python scripts/make_thumbs.py`, and refresh the page. Without a thumbnail the original file is used, so the photo still appears, only heavier. The server scans this folder on each page request; filenames need no manual registration. Name photos after cities, e.g. `London.jpg` or `London-02.webp` for additional shots. Existing aliases such as `Tromso.jpg` and `New York.jpg` retain their city metadata. Unknown names still appear in the gallery without invented country or map coordinates; add a city to `cities.js` when those details are available. Adding a gallery photo does not automatically change the map popup photo.

The gallery shows three photos per desktop view, with arrows and native touch scrolling. It never advances automatically. The first three featured cities are followed by the remaining photos alphabetically. Server code changes require restarting uvicorn unless it runs with `--reload`; new photo files only need a page refresh.
