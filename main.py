from datetime import date

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware

from site_content import ROOT, STATIC, SITE_URL, SECURITY_HEADERS, gallery_photos, static_url


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
templates = Jinja2Templates(directory=ROOT / "templates")


templates.env.globals["static_url"] = static_url

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
