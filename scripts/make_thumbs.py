"""Create WebP thumbnails for the city gallery and map popups (development only).

Usage: python scripts/make_thumbs.py [--force]

Writes static/images/cities/thumbs/<photo stem>.webp at most THUMB_WIDTH px wide.
Only missing or outdated thumbnails are rebuilt. Photos without a thumbnail still
work: the site falls back to the original file. Requires Pillow.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageOps

THUMB_WIDTH = 640  # Cards render about 380 px wide; sharp on most high-DPI screens.
QUALITY = 75
SITE = Path(__file__).resolve().parents[1]
PHOTOS = SITE / 'static' / 'images' / 'cities'
THUMBS = PHOTOS / 'thumbs'
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.avif'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--force', action='store_true', help='rebuild every thumbnail')
    args = parser.parse_args()
    THUMBS.mkdir(exist_ok=True)
    sources = [p for p in PHOTOS.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS and not p.name.startswith('.')]
    expected = {source.stem + '.webp' for source in sources}
    for source in sorted(sources):
        target = THUMBS / f'{source.stem}.webp'
        if not args.force and target.exists() and target.stat().st_mtime >= source.stat().st_mtime:
            continue
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image).convert('RGB')
            if image.width > THUMB_WIDTH:
                image = image.resize((THUMB_WIDTH, round(image.height * THUMB_WIDTH / image.width)), Image.LANCZOS)
            image.save(target, 'WEBP', quality=QUALITY, method=6)
        print(f'{source.name}: {source.stat().st_size // 1024} KB → {target.stat().st_size // 1024} KB')
    for stale in THUMBS.glob('*.webp'):
        if stale.name not in expected:
            stale.unlink()
            print(f'removed stale {stale.name}')


if __name__ == '__main__':
    main()
