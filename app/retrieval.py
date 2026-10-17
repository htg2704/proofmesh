"""Bounded retrieval. Search summaries and image matches are leads, not proof."""
import base64
import http.client
import ipaddress
import re
import socket
import ssl
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit


class PageText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []
        self.published = None

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside', 'form'}:
            self.skip += 1
        if tag == 'meta':
            a = dict(attrs)
            if a.get('property', a.get('name', '')).lower() in {'article:published_time', 'datepublished', 'date'}:
                self.published = a.get('content', '')[:100]
        if tag in {'p', 'h1', 'h2', 'h3', 'li', 'div', 'br'}:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in {'script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside', 'form'} and self.skip:
            self.skip -= 1
        if tag in {'p', 'li', 'div'}:
            self.parts.append('\n')

    def handle_data(self, text):
        if not self.skip:
            self.parts.append(text)


def public_addresses(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in {None, 443}:
        raise ValueError('Only public HTTPS sources are accepted')
    addresses = list(dict.fromkeys(info[4][0] for info in socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)))
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError('Source resolves to a non-public address')
    return parsed, addresses


class PinnedHTTPS(http.client.HTTPSConnection):
    def __init__(self, host, address):
        super().__init__(host, timeout=8, context=ssl.create_default_context())
        self.address = address

    def connect(self):
        # Resolve once, connect to that validated address, verify TLS for original host.
        sock = socket.create_connection((self.address, 443), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def fetch_page(url, claim):
    for _ in range(4):
        parsed, addresses = public_addresses(url)
        connection = PinnedHTTPS(parsed.hostname, addresses[0])
        try:
            connection.request('GET', (parsed.path or '/') + ('?' + parsed.query if parsed.query else ''),
                               headers={'User-Agent': 'ProofMesh/0.3 evidence research', 'Accept': 'text/html,text/plain', 'Accept-Encoding': 'identity'})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                url = urljoin(url, response.getheader('Location', ''))
                continue
            if response.status != 200 or not any(t in (response.getheader('Content-Type') or '') for t in ('text/html', 'text/plain')):
                raise ValueError('Source is not a readable text page')
            raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError('Source exceeds retrieval limit')
            parser = PageText()
            parser.feed(raw.decode('utf-8', errors='replace'))
            paragraphs = [' '.join(p.split()) for p in ''.join(parser.parts).split('\n') if len(p.strip()) > 15]
            terms = {w.lower() for w in re.findall(r'\w{4,}', claim)}
            ranked = sorted(enumerate(paragraphs), key=lambda pair: len(terms & set(re.findall(r'\w+', pair[1].lower()))), reverse=True)
            selected = ranked[:4]
            # Short attributed extract; never treat a page's publication date as capture date.
            text = ' '.join(p for _, p in selected)
            excerpt = ' '.join(text.split()[:120])
            if not excerpt:
                raise ValueError('No readable passage')
            return {'url': url, 'excerpt': excerpt, 'kind': 'source_page_excerpt', 'retrieved_at': datetime.now(timezone.utc).isoformat(), 'page_published_at': parser.published}
        finally:
            connection.close()
    raise ValueError('Too many source redirects')


def enrich_evidence(leads, claim, fetcher=fetch_page):
    evidence, seen = [], set()
    for lead in leads:
        if lead['url'] in seen or len(evidence) >= 6:
            continue
        seen.add(lead['url'])
        item = {**lead, 'id': f'E{len(evidence)+1}'}
        try:
            item.update(fetcher(lead['url'], claim))
            if any(e['url'] == item['url'] for e in evidence):
                continue
            item['fetch_status'] = 'retrieved'
        except Exception:
            item['fetch_status'] = 'unavailable'
            # A generated search summary is retained visibly as a lead only.
        evidence.append(item)
    return evidence


def vision_leads(image_base64):
    if not image_base64:
        return {'status': 'not_requested', 'pages': [], 'vision_calls': 0}
    from google.cloud import vision
    import io
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(base64.b64decode(image_base64))) as raw:
        image = ImageOps.exif_transpose(raw).convert('RGB'); image.thumbnail((1600, 1600))
        encoded = io.BytesIO(); image.save(encoded, format='JPEG', quality=85)
    client = vision.ImageAnnotatorClient()
    result = client.web_detection(image=vision.Image(content=encoded.getvalue()), retry=None, timeout=20)
    if result.error.message:
        raise RuntimeError('Image retrieval failed')
    pages = [{'url': p.url, 'title': p.page_title or 'Image matching page',
              'match': 'full' if p.full_matching_images else 'partial' if p.partial_matching_images else 'related',
              'kind': 'image_match_lead', 'excerpt': 'Image match returned by Cloud Vision. This does not verify the caption, capture date, place or origin.'}
             for p in result.web_detection.pages_with_matching_images if p.url.startswith('https://')][:4]
    return {'status': 'retrieved', 'pages': pages, 'vision_calls': 1, 'best_guess_labels': [v.label for v in result.web_detection.best_guess_labels][:3]}
