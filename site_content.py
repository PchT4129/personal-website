"""Shared content and security settings for static builds and local preview."""
import hashlib
import mimetypes
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
CITY_PHOTOS = STATIC / "images" / "cities"
CITY_THUMBS = CITY_PHOTOS / "thumbs"
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
SITE_URL = "https://yixiao-tao.com"
# Some system MIME tables lack modern image types; with nosniff they must be right.
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/avif", ".avif")

# Leaflet and OSM tiles are the only third-party origins. Inline styles are
# needed by Leaflet; the inline script sets the theme early.
CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' https://unpkg.com",
    "style-src 'self' 'unsafe-inline' https://unpkg.com",
    "img-src 'self' data: https://tile.openstreetmap.org https://unpkg.com",
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

