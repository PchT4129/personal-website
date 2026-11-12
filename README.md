# Yixiao's personal site

Production target: **Cloudflare Pages**, with the domain managed through Cloudflare DNS.

## Build and preview

```sh
python -m pip install -r requirements-build.txt
python scripts/build_static.py
python -m http.server 8011 --directory dist
```

Open http://localhost:8011. Rebuild after editing templates, scripts, styles, or photos.
The build generates HTML, 640px WebP thumbnails, a gallery manifest, robots.txt,
sitemap.xml, favicon.ico and 404.html. It checks local page links and gallery assets.
Generated files stay in ignored `dist/`; source photos are never modified.
Python's preview server uses its own default error page; verify the custom 404 response on Cloudflare Pages.

For live template editing, the existing FastAPI preview remains available:
`uvicorn main:app --reload`. Its dependencies are in `requirements.txt`.

## Add photos

Put JPG/JPEG, PNG, WebP or AVIF photos in `static/images/cities/`, then commit and push.
Thumbnails are generated automatically during deployment. Use unique filename stems
(e.g. `London.jpg`, `London-02.webp`). Country and map metadata lives in
`static/js/cities.js`. Country flags remain visible.

## Cloudflare Pages setup

1. Push this checkout to GitHub. In Cloudflare **Workers & Pages**, create a
   **Pages** project using **Connect to Git**, then select `PchT4129/personal-website`.
   Choose Pages explicitly, rather than a Workers project.
2. Use these build settings (repository root):

   | Setting | Value |
   | --- | --- |
   | Production branch | `main` |
   | Framework preset | `None` |
   | Build command | `python -m pip install -r requirements-build.txt && python scripts/build_static.py` |
   | Build output directory | `dist` |
   | Python version | `.python-version` in this repository: `3.12.8` |

   Use the current v3 build image. If the dashboard asks for a Python version,
   set `PYTHON_VERSION=3.12.8` for production and preview environments.
   Pages' automatic dependency installation can be disabled with
   `SKIP_DEPENDENCY_INSTALL=1`; the explicit build command installs everything needed.
3. Deploy and test the generated `pages.dev` URL: gallery/dialog, map and country
   flags, both themes, CV downloads, robots.txt and sitemap.xml. Check an unknown
   path returns HTTP 404 with the custom error page. Check the response security
   headers too: Python's simple local preview server does not apply `_headers`.
4. Under the Pages project's **Custom domains**, add `yixiao-tao.com`.
   Follow Cloudflare's instructions to replace the old Render DNS record with the
   Pages target. Register the domain in Pages before changing DNS manually.
   Save the existing DNS record values for rollback, and retain MX/TXT mail records.
5. Verify HTTPS and the public domain, then disable automatic deployment on the old
   Render service and suspend it. The new deployment path uses Cloudflare only.
   Delete the old service later if no rollback is needed.

Future pushes to `main` build and deploy through Cloudflare's Git integration;
other enabled branches get preview URLs. GitHub Actions independently validates
builds and stores `dist` as an artifact. Pages runs its own build validation before
publishing; it does not wait for the independent GitHub Actions check.

The build generates `dist/_headers` from the shared security policy and sets a
one-day browser cache for static assets. Pages manages HTML caching and ETags.
Both production and preview `pages.dev` URLs receive `X-Robots-Tag: noindex`;
the custom domain remains indexable. A root `404.html` gives missing paths a real
404 response; do not add an SPA catch-all rewrite.

No Cloudflare credentials belong in this repository. Git integration requires a
one-time Cloudflare account sign-in and GitHub repository authorization.

Official references: [Git integration](https://developers.cloudflare.com/pages/configuration/git-integration/),
[build settings](https://developers.cloudflare.com/pages/configuration/build-configuration/),
[custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/),
[response headers](https://developers.cloudflare.com/pages/configuration/headers/).
