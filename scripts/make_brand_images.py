"""Generate favicon.ico, apple-touch-icon.png and the 1200x630 social share card.

Usage: python scripts/make_brand_images.py [--font-dir /usr/share/fonts/truetype]

Development only (Pillow). Outputs go to static/images/icons/ and
static/images/og-card.png. Colors match the light theme in static/css/style.css.
"""
import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SITE = Path(__file__).resolve().parents[1]
ICONS = SITE / 'static' / 'images' / 'icons'
BG, TEXT, MUTED, ACCENT, BORDER = '#ffffff', '#171717', '#606060', '#171717', '#dddddd'


def font(font_dir, name, size):
    return ImageFont.truetype(str(font_dir / name), size)


def icon(size, font_dir):
    scale = 4  # Draw large, then downsample for smooth edges.
    image = Image.new('RGBA', (size * scale, size * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, size * scale - 1, size * scale - 1), radius=round(size * scale * .22), fill=ACCENT)
    draw.text((size * scale / 2, size * scale * .52), 'yt.', font=font(font_dir, 'lato/Lato-Black.ttf', round(size * scale * .46)), fill='white', anchor='mm')
    return image.resize((size, size), Image.LANCZOS)


def share_card(font_dir):
    width, height, margin = 1200, 630, 84
    card = Image.new('RGB', (width, height), BG)
    draw = ImageDraw.Draw(card)
    portrait = 380
    with Image.open(SITE / 'static' / 'images' / 'avatar.jpg') as avatar:
        avatar = avatar.convert('RGB').resize((portrait, portrait), Image.LANCZOS)
    left = width - margin - portrait
    top = (height - portrait) // 2
    card.paste(avatar, (left, top))
    x = margin
    draw.text((x, 150), 'ROBOTICS & AI  ·  UCL', font=font(font_dir, 'dejavu/DejaVuSansMono.ttf', 22), fill=ACCENT)
    draw.text((x, 196), 'Yixiao Tao', font=font(font_dir, 'lato/Lato-Bold.ttf', 96), fill=TEXT)
    body = font(font_dir, 'lato/Lato-Regular.ttf', 32)
    for index, line in enumerate(['How robots see, hear, and understand', 'their surroundings: SLAM, vision and', 'multimodal perception.']):
        draw.text((x, 330 + index * 46), line, font=body, fill=MUTED)
    draw.line((x, height - 112, left - 60, height - 112), fill=BORDER, width=2)
    draw.text((x, height - 92), 'yixiao-tao.com', font=font(font_dir, 'dejavu/DejaVuSansMono.ttf', 24), fill=ACCENT)
    return card


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--font-dir', type=Path, default=Path('/usr/share/fonts/truetype'))
    args = parser.parse_args()
    ICONS.mkdir(parents=True, exist_ok=True)
    icon(256, args.font_dir).save(ICONS / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    touch = Image.new('RGB', (180, 180), ACCENT)  # iOS ignores transparency; fill the corners.
    touch.paste(icon(180, args.font_dir), (0, 0), icon(180, args.font_dir))
    touch.save(ICONS / 'apple-touch-icon.png', optimize=True)
    share_card(args.font_dir).save(SITE / 'static' / 'images' / 'og-card.png', optimize=True)
    for path in [ICONS / 'favicon.ico', ICONS / 'apple-touch-icon.png', SITE / 'static' / 'images' / 'og-card.png']:
        print(f'{path.relative_to(SITE)}: {path.stat().st_size // 1024} KB')


if __name__ == '__main__':
    main()
