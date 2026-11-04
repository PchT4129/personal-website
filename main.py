import hashlib
import mimetypes
from datetime import date
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
CITY_PHOTOS = STATIC / "images" / "cities"
CITY_THUMBS = CITY_PHOTOS / "thumbs"
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
SITE_URL = "https://yixiao-tao.com"
# Some system MIME tables lack modern image types; with nosniff they must be right.
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/avif", ".avif")

# Leaflet, flags and OSM tiles are the only third-party origins. Inline styles are
# needed by Leaflet and the Matplotlib SVG; the inline script sets the theme early.
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://unpkg.com",
    "style-src 'self' 'unsafe-inline' https://unpkg.com",
    "img-src 'self' data: https://tile.openstreetmap.org https://cdn.jsdelivr.net https://unpkg.com",
    "font-src 'self'",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])
SECURITY_HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    # Keeps the referrer the OSM tile usage policy asks for, without full URLs.
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class CachedStaticFiles(StaticFiles):
    """Static files with a browser cache; templates add ?v= hashes to CSS/JS."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=86400"
        return response


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


app.mount("/static", CachedStaticFiles(directory=STATIC), name="static")
templates = Jinja2Templates(directory="templates")


@lru_cache(maxsize=64)
def _file_hash(path: str, mtime: float) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:10]


def static_url(name: str) -> str:
    """URL for a static asset with a content hash, so cached copies refresh on change."""
    path = STATIC / name
    try:
        return f"/static/{name}?v={_file_hash(str(path), path.stat().st_mtime)}"
    except FileNotFoundError:
        return f"/static/{name}"


templates.env.globals["static_url"] = static_url


def gallery_photos():
    """Discover photos on each page request, including newly added cities.

    Each entry has the original file and, when scripts/make_thumbs.py has made one,
    a smaller WebP thumbnail used by the gallery and map popups.
    """
    photos = []
    for path in CITY_PHOTOS.iterdir():
        if path.name.startswith(".") or path.suffix.lower() not in PHOTO_EXTENSIONS:
            continue
        try:
            if path.is_file() and not path.is_symlink() and path.stat().st_size:
                thumb = CITY_THUMBS / f"{path.stem}.webp"
                photos.append({"file": path.name, "thumb": f"thumbs/{thumb.name}" if thumb.is_file() else None})
        except FileNotFoundError:
            # An upload may be renamed or removed while the directory is scanned.
            continue
    return sorted(photos, key=lambda photo: photo["file"].casefold())


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"gallery_photos": gallery_photos()}
    )


@app.get("/robots.txt", include_in_schema=False)
async def robots():
    return PlainTextResponse(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")


@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    updated = date.fromtimestamp((ROOT / "templates" / "index.html").stat().st_mtime).isoformat()
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{SITE_URL}/</loc><lastmod>{updated}</lastmod></url>"
        "</urlset>\n"
    )
    return Response(xml, media_type="application/xml")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(STATIC / "images" / "icons" / "favicon.ico", headers={"Cache-Control": "public, max-age=604800"})


@app.exception_handler(StarletteHTTPException)
async def not_found(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and request.method == "GET" and not request.url.path.startswith("/static/"):
        return templates.TemplateResponse(request=request, name="404.html", status_code=404)
    return PlainTextResponse(str(exc.detail), status_code=exc.status_code, headers=getattr(exc, "headers", None))
