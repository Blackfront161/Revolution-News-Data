"""Restricted metadata admission; never copy a feed body or publisher media."""
from urllib.parse import urlsplit


REGION_ALIASES = {"Global": "Global", "Europe": "Europe", "Europa": "Europe", "Africa": "Africa", "Afrika": "Africa", "North America": "North America", "Latin America": "Latin America", "Asia": "Asia", "Asien": "Asia", "Australia & NZ": "Australia & NZ"}
TOPICS = {"Labor Struggles", "Antifascism", "Antisexism", "Queer-Feminism", "Antiracism", "No Borders", "Anticapitalism", "Theory & Strategy", "Anticolonialism", "Anti-Imperialism", "Squatting & Housing", "Demonstrations", "Anti-Rep & Prisons", "Cyberactivism", "No War", "Animal Liberation", "Eco-Anarchism", "Indigenous Struggles", "Radical Health & Disability", "Libraries", "Movement News"}


def metadata_categories(categories, continent):
    values = categories if isinstance(categories, list) else []
    result = list(dict.fromkeys(REGION_ALIASES.get(str(value), str(value)) for value in values if value))
    if not set(REGION_ALIASES.values()).intersection(result):
        result.insert(0, REGION_ALIASES.get(str(continent), "Global"))
    if not TOPICS.intersection(result):
        result.append("Movement News")
    return result


def metadata_article(feed, entry, continent):
    """Return a link record for an explicitly restricted source, or reject it."""
    if feed.get("importMode") != "metadata-only":
        raise ValueError("metadata-only admission required")
    link = str(entry.get("link") or "").strip()
    parsed = urlsplit(link)
    home = urlsplit(str(feed.get("homepage") or ""))
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or not home.hostname or parsed.hostname != home.hostname):
        return None
    title = str(entry.get("title") or "").strip()
    if not title:
        return None
    categories = metadata_categories(feed.get("categories"), continent)
    reviewed_topic = (feed.get("metadataTopicOverrides") or {}).get(link)
    if isinstance(reviewed_topic, dict) and reviewed_topic.get("title") == title:
        categories = metadata_categories(
            [value for value in categories if value in REGION_ALIASES.values()]
            + [value for value in reviewed_topic.get("topics", []) if value in TOPICS], continent
        )
    region = next(value for value in categories if value in REGION_ALIASES.values())
    topic = next(value for value in categories if value in TOPICS)
    # This sentence is WRN-authored. Even an RSS summary may contain a full text.
    return {
        "kontinent": continent,
        "categories": categories,
        "primaryRegion": region,
        "primaryTopic": topic,
        "secondaryTopics": [value for value in categories if value in TOPICS and value != topic],
        "classificationConfidence": 0.4,
        "classificationMethod": "source-metadata-only",
        "editorialReview": True,
        "editorialReviewReasons": ["headline-only metadata record"],
        "quelleName": feed["name"],
        "author": str(entry.get("author") or "Unknown").strip(),
        "title": title,
        "link": link,
        "pubDate": entry.get("published") or entry.get("updated") or "",
        "content": "Überschrift und Originalverweis. Den Beitrag auf der Originalseite lesen.",
        "contentComplete": False,
        "image": "",
        "images": [],
        "language": (feed.get("languages") or ["und"])[0],
        "languages": list(feed.get("languages") or ["und"]),
        "originCountry": feed.get("originCountry", ""),
        "originCountryCode": feed.get("originCountryCode", ""),
        "originRegion": feed.get("originRegion", ""),
        "sourceHomepage": feed.get("homepage", ""),
        "importMode": "metadata-only",
        "rightsReview": feed.get("rightsReview", "unknown"),
    }


def article_is_withdrawn(article):
    """Explicit withdrawal signals, never a technical fetch failure."""
    return article.get("status") in {"withdrawn", "revoked", "deleted"} or article.get("deleted") is True


def restrict_existing_article(article, source_policies):
    """Apply a newly reviewed restricted source policy to old archive rows too."""
    name = str(article.get("quelleName") or article.get("source") or article.get("sourceName") or "").strip().casefold()
    matching = [feed for feed in source_policies or []
                if name and str(feed.get("name") or "").strip().casefold() == name]
    if article_is_withdrawn(article) or any(article_is_withdrawn(feed) for feed in matching):
        return None
    # Directory/disabled import policies do not admit an article body or card.
    # A disabled fetch status alone remains a technical pause, not a withdrawal.
    if any(policy.get("importMode") not in (None, "", "fulltext", "metadata-only", "directory-only", "disabled")
           for policy in [article] + matching):
        raise ValueError("Unknown article import policy; refusing archive changes")
    if any(policy.get("status") == "directory-only"
           or policy.get("importMode") in ("directory-only", "disabled")
           for policy in [article] + matching):
        return None
    feeds = [dict(feed, importMode="metadata-only") for feed in matching
             if feed.get("importMode") == "metadata-only"
             or feed.get("contentPolicy") == "metadata_and_links_only"]
    if not feeds:
        if (article.get("importMode") == "metadata-only"
                or article.get("contentPolicy") == "metadata_and_links_only"):
            # A row-level restriction also wins without a matching registry row.
            try:
                parsed = urlsplit(str(article.get("link") or ""))
            except ValueError:
                return None
            feed = {key: article[key] for key in (
                "categories", "languages", "originCountry", "originCountryCode",
                "originRegion", "rightsReview") if key in article}
            feed.update(name=article.get("quelleName") or article.get("source") or "Unknown source",
                        homepage=article.get("sourceHomepage") or f"{parsed.scheme}://{parsed.netloc}/",
                        importMode="metadata-only")
            entry = {"title": article.get("title"), "link": article.get("link"),
                     "published": article.get("pubDate"), "author": article.get("author")}
            restricted = metadata_article(feed, entry, article.get("kontinent") or "Global")
            if restricted is not None and article.get("id"):
                restricted["id"] = article["id"]
            return restricted
        return article
    entry = {"title": article.get("title"), "link": article.get("link"),
             "published": article.get("pubDate"), "author": article.get("author")}
    for feed in feeds:
        admitted = metadata_article(feed, entry, article.get("kontinent") or (feed.get("categories") or ["Global"])[0])
        if admitted is not None:
            if article.get("id"):
                admitted["id"] = article["id"]
            return admitted
    # An old external/non-HTTPS link cannot bypass a restricted publisher's host guard.
    return None
