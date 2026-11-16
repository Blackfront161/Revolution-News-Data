"""Reject a duplicate feed delivery without changing established article ownership."""
from urllib.parse import urlsplit


def duplicate_ownership_skip(existing, incoming_source, configured_sources, link):
    """True only for distinct, unambiguous owners of an exactly identical feed URL.

    No row, body, policy or identity is mutated or transferred. Transport aliases
    and same-host feeds are not evidence of identical configured feeds.
    """
    if not isinstance(existing, dict) or existing.get('link') != link:
        return False
    owner = existing.get('quelleName')
    if not isinstance(owner, str) or not owner or owner == incoming_source:
        return False
    urls = []
    for name in (owner, incoming_source):
        rows = [r for r in configured_sources if isinstance(r, dict) and r.get('name') == name]
        if not rows:
            return False
        values = set()
        for row in rows:
            candidates = [row[k] for k in ('url', 'feedUrl') if row.get(k)]
            if not candidates or any(not isinstance(v, str) for v in candidates):
                return False
            values.update(candidates)
        if len(values) != 1:
            return False
        value = next(iter(values))
        try:
            parsed = urlsplit(value)
            if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
                return False
        except ValueError:
            return False
        urls.append(value)
    return urls[0] == urls[1]
