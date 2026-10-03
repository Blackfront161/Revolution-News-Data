"""Bound current news without letting high-volume feeds erase small sources."""
from datetime import datetime, timezone
from build_web_feeds import date_value, stable_key, usable_news_item


def retain_current_sources(rows, source_names, limit=2000, now=None, days=30):
    if limit < 1:
        return []
    reference = (now or datetime.now(timezone.utc)).timestamp()
    cutoff = reference - days * 86400
    allowed = {str(name).strip().casefold() for name in source_names if name}
    ordered = sorted((r for r in rows if cutoff <= date_value(r) <= reference
                      and r.get('status') not in {'withdrawn', 'revoked', 'deleted'}
                      and r.get('deleted') is not True),
                     key=lambda r: (-date_value(r), stable_key(r)))
    representatives, seen_sources = [], set()
    for row in ordered:
        name = str(row.get('quelleName', '')).strip().casefold()
        if name in allowed and name not in seen_sources and usable_news_item(row):
            representatives.append(row)
            seen_sources.add(name)
    selected = {stable_key(r): r for r in representatives[:limit]}
    for row in ordered:
        if len(selected) >= limit:
            break
        selected.setdefault(stable_key(row), row)
    return sorted(selected.values(), key=lambda r: (-date_value(r), stable_key(r)))
