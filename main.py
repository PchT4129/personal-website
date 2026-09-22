from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
CITY_PHOTOS = Path(__file__).resolve().parent / "static" / "images" / "cities"
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}


def gallery_photos():
    """Discover photos on each page request, including newly added cities."""
    photos = []
    for path in CITY_PHOTOS.iterdir():
        if path.name.startswith(".") or path.suffix.lower() not in PHOTO_EXTENSIONS:
            continue
        try:
            if path.is_file() and not path.is_symlink() and path.stat().st_size:
                photos.append(path.name)
        except FileNotFoundError:
            # An upload may be renamed or removed while the directory is scanned.
            continue
    return sorted(photos, key=str.casefold)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request=request, name="index.html", context={"gallery_photos": gallery_photos()}
    )
