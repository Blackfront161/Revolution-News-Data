"""Seven evidenced HTTPS identities only; not a source-wide URL policy.

The publisher's exact 301 targets and HTTPS canonical metadata were verified on
2026-11-14. Bodies and titles are never fetched, inferred or replaced here.
"""
import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

REVIEWED_HTTP_IDENTITIES = {'http://www.democracynow.org/2026/11/10/pete_hegseth_impeachment_risk': {'to': 'https://www.democracynow.org/2026/11/10/pete_hegseth_impeachment_risk', 'source': 'Democracy Now! (Global)', 'titleSha256': 'ca1bf492e1838261459f425db656aac5790fcfe2d5a9a84955184a7089af8c4e', 'pubDate': 'Tue, 10 Nov 2026 08:15:35 -0500'}, 'http://www.democracynow.org/2026/11/9/stephen_miller_chief_of_staff': {'to': 'https://www.democracynow.org/2026/11/9/stephen_miller_chief_of_staff', 'source': 'Democracy Now! (Global)', 'titleSha256': 'b570beeca44b836391d312869c8258babaad7597592b81d99faaa6f8f2c65758', 'pubDate': 'Mon, 09 Nov 2026 08:16:34 -0500'}, 'http://www.democracynow.org/2026/11/6/mississippi_senate_election_southern_us_shift': {'to': 'https://www.democracynow.org/2026/11/6/mississippi_senate_election_southern_us_shift', 'source': 'Democracy Now! (Global)', 'titleSha256': '469ad50ee6e39598b044f4f04bd4846b13e3683b6843885483f1aab0b4293cbf', 'pubDate': 'Fri, 06 Nov 2026 08:15:23 -0500'}, 'http://www.democracynow.org/2026/11/5/2026_midterm_election_overview': {'to': 'https://www.democracynow.org/2026/11/5/2026_midterm_election_overview', 'source': 'Democracy Now! (Global)', 'titleSha256': '016cf466d4df1aa51cebf3ca4a8a81907b7d7ebd30ad9ecd562235d912227623', 'pubDate': 'Thu, 05 Nov 2026 08:16:22 -0500'}, 'http://www.democracynow.org/2026/11/4/keisha_lance_bottoms_becomes_first_black': {'to': 'https://www.democracynow.org/2026/11/4/keisha_lance_bottoms_becomes_first_black', 'source': 'Democracy Now! (Global)', 'titleSha256': 'e0b57686f8c26282139c025fea6537f9dd3e999411e6421667fb33f768c068b4', 'pubDate': 'Wed, 04 Nov 2026 08:47:37 -0500'}, 'http://www.democracynow.org/2026/11/3/midterm_ballot_measures': {'to': 'https://www.democracynow.org/2026/11/3/midterm_ballot_measures', 'source': 'Democracy Now! (Global)', 'titleSha256': 'f7f02ecb65085eda23a0a43fd834f8f23a1a6402f7d13e366497fa66c0abac7b', 'pubDate': 'Tue, 03 Nov 2026 08:15:01 -0500'}, 'http://www.democracynow.org/2026/11/2/matthew_cole_jared_kushner_book': {'to': 'https://www.democracynow.org/2026/11/2/matthew_cole_jared_kushner_book', 'source': 'Democracy Now! (Global)', 'titleSha256': '7805eb30f6b3a14fa4d057041d9e87f675def8562ff27e2ea634a572b6bbd951', 'pubDate': 'Mon, 02 Nov 2026 08:18:24 -0500'}}
REVIEWED_TARGETS = frozenset(rule["to"] for rule in REVIEWED_HTTP_IDENTITIES.values())


class ReviewedArticleIdentityError(ValueError):
    """A reviewed identity conflict must abort publication, not skip an entry."""



def _timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            stamp = parsedate_to_datetime(value)
        except (ValueError, TypeError, OverflowError):
            return None
    # A missing timezone is not evidence of the reviewed publication instant.
    if stamp.tzinfo is None:
        return None
    return stamp.astimezone(timezone.utc)


def canonicalize_reviewed_link(link, source, title, published):
    """Convert only an exact reviewed HTTP identity; unknown URLs stay unchanged."""
    if not isinstance(link, str) or link not in REVIEWED_HTTP_IDENTITIES:
        return link
    rule = REVIEWED_HTTP_IDENTITIES[link]
    if (source != rule["source"] or not isinstance(title, str)
            or hashlib.sha256(title.encode("utf-8")).hexdigest() != rule["titleSha256"]
            or _timestamp(published) != _timestamp(rule["pubDate"])):
        raise ReviewedArticleIdentityError("Reviewed HTTP article identity changed; refusing unverified canonicalization")
    return rule["to"]


def canonicalize_reviewed_articles(rows):
    """No input mutation; identical aliases coalesce, conflicting revisions fail."""
    output, seen = [], {}
    for row in rows:
        if not isinstance(row, dict):
            output.append(row)
            continue
        link = canonicalize_reviewed_link(row.get("link"), row.get("quelleName"),
                                          row.get("title"), row.get("pubDate"))
        current = dict(row, link=link) if link != row.get("link") else row
        if link in REVIEWED_TARGETS:
            if link in seen:
                if seen[link] != current:
                    raise ReviewedArticleIdentityError("Conflicting reviewed HTTP/HTTPS article revisions; refusing silent replacement")
                continue
            seen[link] = current
        output.append(current)
    return output


def canonicalize_reviewed_withdrawals(keys):
    """A restrictive tombstone applies to either already-proven URL spelling."""
    return {REVIEWED_HTTP_IDENTITIES[key]["to"] if key in REVIEWED_HTTP_IDENTITIES else key
            for key in keys}
