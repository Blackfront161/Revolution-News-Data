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


def repair_reviewed_article_metadata(article):
    """Repair only the reviewed publisher+URL+title, including retained rows.

    The original HTML's og:image and captioned article photos were checked on
    2026-10-27. Its English html/@lang describes the site chrome, not this
    Inuktitut article. No body, byline, date, ID or source policy is replaced.
    """
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
