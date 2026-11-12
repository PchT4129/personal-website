"""Build the deployable site in dist without starting an application server."""
import json
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from site_content import SITE_URL, SECURITY_HEADERS, gallery_photos, static_url
from scripts.make_thumbs import build_thumbs

OUTPUT = ROOT / 'dist'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        self.urls.extend(attrs[key] for key in ('href', 'src', 'poster') if attrs.get(key))


def validate(output):
    """Fail deployment when a page links to a missing local file or anchor."""
    for page in output.glob('*.html'):
        parser = Links()
        parser.feed(page.read_text())
        for url in parser.urls:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc:
                continue
            if not parsed.path:
                if parsed.fragment and parsed.fragment not in parser.ids:
                    raise ValueError(f'{page.name}: missing anchor {url}')
                continue
            target = output / unquote(parsed.path).lstrip('/')
            if target.is_dir():
                target /= 'index.html'
            if not target.is_file():
                raise ValueError(f'{page.name}: missing asset {url}')
    for photo in json.loads((output / 'gallery-manifest.json').read_text()):
        for filename in (photo['file'], photo['thumb']):
            if not filename or not (output / 'static/images/cities' / filename).is_file():
                raise ValueError(f'Missing gallery asset: {filename}')


def build():
    # Clean only the fixed, generated output directory; source assets stay untouched.
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(ROOT / 'static', OUTPUT / 'static')
    photos_dir = OUTPUT / 'static/images/cities'
    build_thumbs(photos=photos_dir, thumbs=photos_dir / 'thumbs', force=True)
    photos = gallery_photos()
    for photo in photos:
        photo['thumb'] = f"thumbs/{Path(photo['file']).stem}.webp"
    env = Environment(loader=FileSystemLoader(ROOT / 'templates'),
                      autoescape=select_autoescape(['html', 'xml']), undefined=StrictUndefined)
    env.globals['static_url'] = static_url
    for template, name in [('index.html', 'index.html'), ('404.html', '404.html')]:
        (OUTPUT / name).write_text(env.get_template(template).render(gallery_photos=photos))
    (OUTPUT / 'gallery-manifest.json').write_text(json.dumps(photos, ensure_ascii=False, indent=2))
    (OUTPUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n')
    # Omit lastmod rather than claiming a checkout timestamp is a content update.
    (OUTPUT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'<url><loc>{SITE_URL}/</loc></url></urlset>\n')
    shutil.copy2(OUTPUT / 'static/images/icons/favicon.ico', OUTPUT / 'favicon.ico')
    # Pages reads this file as response-header configuration, not as a public asset.
    headers = ['/*']
    headers.extend(f'  {name}: {value}' for name, value in SECURITY_HEADERS.items())
    headers.extend([
        '', '/static/*', '  Cache-Control: public, max-age=86400',
        '', 'https://:project.pages.dev/*', '  X-Robots-Tag: noindex',
        '', 'https://:version.:project.pages.dev/*', '  X-Robots-Tag: noindex',
    ])
    (OUTPUT / '_headers').write_text('\n'.join(headers) + '\n')
    validate(OUTPUT)
    print(f'Built and validated {OUTPUT}: {len(photos)} gallery photos')


if __name__ == '__main__':
    build()
