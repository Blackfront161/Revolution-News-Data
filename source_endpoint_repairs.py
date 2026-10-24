"""Reviewed transport aliases; stable source identity URLs remain unchanged.

Changing a request address never grants republication rights. These repairs admit
new records as metadata only, preserving the original source name and key.
"""
from urllib.parse import urlsplit

REPAIRS = {
    'antifa-bern.ch/feed': ('https://www.antifa.ch/feed/', 'https://www.antifa.ch/', 'de'),
    'umanitanova.org/feed': ('https://umanitanova.org/feed/', 'https://umanitanova.org/', 'it'),
    'perspektive-online.de/feed': ('https://perspektive-online.net/feed/', 'https://perspektive-online.net/', 'de'),
    'lausan.hk/feed': ('https://lausancollective.com/feed/', 'https://lausancollective.com/', 'en'),
    'mietergewerkschaft.berlin/feed': ('https://mg-berlin.org/feed/', 'https://mg-berlin.org/', 'de'),
    'niunamenos.org.ar/feed': ('https://niunamenos.ar/feed/', 'https://niunamenos.ar/', 'es'),
    'pt.theanarchistlibrary.org/feed': ('https://pt.anarchistlibraries.net/feed', 'https://pt.anarchistlibraries.net/', 'pt'),
    'femagainstwar.org/feed': ('https://femantiwar.org/ru/feed/', 'https://femantiwar.org/ru/', 'ru'),
    'colorlines.com/feed': ('https://colorlines.com/rss.xml', 'https://colorlines.com/', 'en'),
    'culturalsurvival.org/news/rss.xml': ('https://www.culturalsurvival.org/rss.xml', 'https://www.culturalsurvival.org/', 'en'),
}


def reviewed_source(source):
    """Return a copy; match only reviewed old feed addresses, never other paths."""
    result = dict(source)
    raw = str(source.get('url') or source.get('feedUrl') or '')
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError:
        return result
    if parsed.scheme not in {'http', 'https'} or parsed.username or parsed.password:
        return result
    host = (parsed.hostname or '').lower().removeprefix('www.')
    if port not in (None, 80, 443) or parsed.query or parsed.fragment:
        return result
    repair = REPAIRS.get(host + parsed.path.rstrip('/'))
    if not repair:
        return result
    request_url, homepage, language = repair
    result.update(requestUrl=request_url, homepage=homepage, languages=[language],
                  language=language, importMode='metadata-only',
                  rightsReview='Transportadresse geprüft; nur Überschrift, Datum, Autor und Originalverweis. Keine neue Volltext- oder Medienfreigabe.',
                  endpointReviewedAt='2026-10-24')
    return result


def request_url(source):
    current = reviewed_source(source)
    return current.get('requestUrl') or current.get('url') or current.get('feedUrl') or ''
