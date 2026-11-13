"""Small, evidence-bound article corrections; never publisher-wide permissions."""

from urllib.parse import urlsplit


NUNATSIAQ_SCHOOL_PATH = (
    "/stories/article/new-taloyoak-high-school-unveiled-with-public-ceremony_inuk/"
)
NUNATSIAQ_SCHOOL_TITLE = (
    "ᓄᑖᖅ ᑕᓗᕐᔪᐊᕐᒥ ᐃᓕᓐᓂᐊᕐᕕᐊᓗᒃ ᑭᒃᑯᓕᒫᓄᑦ ᐅᐸᒃᑕᐅᓯᒪᓪᓗᓂ ᒪᑐᐃᖅᑕᐅᔪᖅ"
)
NUNATSIAQ_SCHOOL_IMAGE = (
    "https://cdn.nunatsiaq.com/wp-content/uploads/2026/10/"
    "Pangniq-school-1_inuk-1200x630.jpeg"
)
NUNATSIAQ_SCHOOL_SECOND_IMAGE = (
    "https://cdn.nunatsiaq.com/wp-content/uploads/2026/10/"
    "Pangniq-school-2_inuk-400x300.jpeg"
)

# Five news URLs verified in the public source archives on 2026-10-27.
# This is not a publisher-wide event-to-news conversion. The agenda source
# and all genuine Radar records remain outside this reviewed correction.
CRIMETHINC_NEWS_PATHS = frozenset({
    "/2026/10/21/the-student-revolt-in-france-spreads-moving-forward-with-rage-and-solidarity",
    "/2026/10/06/french-youth-fight-against-a-bleak-future",
    "/2026/10/22/introducing-the-nspm-7-defendants-union",
    "/2026/10/15/fighting-evictions-and-gentrification-in-madrid-and-barcelona-a-report-from-the-encampment-movement",
    "/2026/09/29/if-bolsonaro-wins-they-kill-us-if-lula-wins-they-let-us-die-on-the-2026-elections-in-brazil",
})


def repair_reviewed_rss_news_type(article):
    """Undo the known RSS agenda overwrite, preserving all other metadata."""
    try:
        url = urlsplit(str(article.get("link") or ""))
    except ValueError:
        return article
    categories = article.get("categories", [])
    categories = categories if isinstance(categories, list) else [categories]
    if (
        url.scheme != "https" or url.hostname != "crimethinc.com"
        or url.username or url.password or url.netloc != "crimethinc.com"
        or url.query or url.fragment or url.path not in CRIMETHINC_NEWS_PATHS
        or article.get("quelleName") not in {"CrimethInc.", "CrimethInc. (Global)"}
        or article.get("kontinent") == "Radar" or "Radar" in categories
    ):
        return article
    # Full archives retain the artificial event dates; public source chunks
    # omit them. Preserve any record with independently different event dates.
    if any(article.get(key) and article[key] != article.get("pubDate")
           for key in ("eventStart", "eventEnd")):
        return article
    if article.get("type") == "event":
        if article.get("sourceType") != "rss-event":
            return article
        article["type"] = "article"
        article.pop("sourceType", None)
        article.pop("eventStart", None)
        article.pop("eventEnd", None)
    # These five exact canonical publisher pages were read in English. This
    # does not infer article language from a location or a publisher homepage.
    article["language"] = "en"
    article["languages"] = ["en"]
    return article


def repair_reviewed_article_metadata(article):
    """Apply reviewed identity-bound corrections, including retained rows.

    The original HTML's og:image and captioned article photos were checked on
    2026-10-27. Its English html/@lang describes the site chrome, not this
    Inuktitut article. No body, byline, date, ID or source policy is replaced.
    """
    article = repair_reviewed_rss_news_type(article)
    try:
        url = urlsplit(str(article.get("link") or ""))
    except ValueError:
        return article
    if (
        url.scheme != "https"
        or url.hostname != "nunatsiaq.com"
        or url.path != NUNATSIAQ_SCHOOL_PATH
        or article.get("quelleName") != "Nunatsiaq News"
        or article.get("title") != NUNATSIAQ_SCHOOL_TITLE
    ):
        return article
    article["language"] = "iu"
    article["languages"] = ["iu"]
    # Correct an existing media admission, without enabling media for a row
    # which has none or is explicitly restricted/withdrawn.
    if (
        (article.get("image") or article.get("images"))
        and article.get("importMode") != "metadata-only"
        and article.get("status") not in {"withdrawn", "revoked", "deleted"}
        and not article.get("deleted")
    ):
        article["image"] = NUNATSIAQ_SCHOOL_IMAGE
        article["images"] = [NUNATSIAQ_SCHOOL_IMAGE, NUNATSIAQ_SCHOOL_SECOND_IMAGE]
    return article
