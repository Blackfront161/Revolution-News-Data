import feedparser
import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import os
import re
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


# WRN 1.7.23 ENTRY SAFETY
AGGREGATE_ENTRY_ERRORS = []


def safe_text(value, fallback=""):
    if value is None:
        return fallback

    try:
        text = value if isinstance(value, str) else str(value)
    except Exception:
        return fallback

    text = text.strip()
    return text if text else fallback


def safe_lower(value, fallback=""):
    return safe_text(value, fallback).casefold()


def log_feed_entry_error(feed_name, entry, error):
    try:
        title_value = (
            entry.get("title")
            if hasattr(entry, "get")
            else ""
        )
    except Exception:
        title_value = ""

    record = {
        "feed": safe_text(feed_name, "Unbekannte Quelle"),
        "title": safe_text(title_value, "Unbekannter Eintrag"),
        "errorType": type(error).__name__,
        "error": safe_text(error, "Unbekannter Fehler"),
        "recordedAt": datetime.now().isoformat(),
    }

    AGGREGATE_ENTRY_ERRORS.append(record)

    print(
        "  [EINTRAG ÜBERSPRUNGEN] "
        f"{record['feed']} – {record['title']}: "
        f"{record['errorType']}: {record['error']}"
    )


def save_aggregate_error_report():
    payload = {
        "schemaVersion": 1,
        "generatedAt": datetime.now().isoformat(),
        "errorCount": len(AGGREGATE_ENTRY_ERRORS),
        "errors": AGGREGATE_ENTRY_ERRORS[-500:],
    }

    with open(
        "aggregate-errors.json",
        "w",
        encoding="utf-8",
    ) as report_file:
        json.dump(
            payload,
            report_file,
            ensure_ascii=False,
            indent=2,
        )



# --- KONFIGURATION & QUELLEN ---
quellen = {
    "Global": [
        {"name": "Anarchist Federation", "url": "https://www.anarchistfederation.net/feed/"},
        {"name": "CrimethInc. (Global)", "url": "https://crimethinc.com/feed"},
        {"name": "Anarkismo (International)", "url": "http://www.anarkismo.net/backend?locale=en"},
        {"name": "ZNet (International)", "url": "https://znetwork.org/feed/"},
        {"name": "Libcom (Global News)", "url": "https://libcom.org/news/feed"},
        {"name": "IWA-AIT (Internationale)", "url": "https://iwa-ait.org/rss.xml"},
        {"name": "Agency", "url": "https://www.anarchistagency.com/feed/"},
        {"name": "Waging Nonviolence", "url": "https://wagingnonviolence.org/feed/"},
        {"name": "Anarchist News", "url": "https://morss.it/https://anarchistnews.org/rss.xml"},
        {"name": "A-Infos (Global)", "url": "http://www.ainfos.ca/ainfos.xml"},
        {"name": "Autonomies", "url": "https://autonomies.org/feed/"},
        {"name": "Unicorn Riot", "url": "https://unicornriot.ninja/feed/"},
        {"name": "Abolition Media", "url": "https://www.abolitionmedia.noblogs.org/feed/"},
        {"name": "Slingshot Collective", "url": "https://slingshotcollective.org/feed/"}
    ],
    "Europe": [
        {"name": "Paris-Luttes (FR)", "url": "https://paris-luttes.info/spip.php?page=backend"},
        {"name": "Lundi Matin (FR)", "url": "https://lundi.am/spip.php?page=backend"},
        {"name": "Rebellyon (FR)", "url": "https://rebellyon.info/spip.php?page=backend"},
        {"name": "MIA Marseille (FR)", "url": "https://mars-infos.org/spip.php?page=backend"},
        {"name": "Barrikade (CH)", "url": "https://barrikade.info/spip.php?page=backend"},
        {"name": "Kontrapolis (DE)", "url": "https://kontrapolis.info/feed/"},
        {"name": "Perspektive Online (DE)", "url": "https://www.perspektive-online.de/feed/"},
        {"name": "Avtonom (RU)", "url": "https://avtonom.org/rss.xml"},
        {"name": "Pramen (BY)", "url": "https://pramen.io/feed/"},
        {"name": "Athens Indymedia (GR)", "url": "https://athens.indymedia.org/rss/"},
        {"name": "Apatris (GR)", "url": "https://apatris.org/feed/"},
        {"name": "Alerta (GR)", "url": "https://www.alerta.gr/feed/"},
        {"name": "Infolibre (GR)", "url": "https://infolibre.gr/feed/"},
        {"name": "OmniaTV (GR)", "url": "https://omniatv.com/feed/"},
        {"name": "Antifa Infoblatt", "url": "https://www.antifainfoblatt.de/rss.xml"},
        {"name": "Freedom News", "url": "https://freedomnews.org.uk/feed/"},
        {"name": "A-Radio Berlin", "url": "https://www.aradio-berlin.org/feed/"},
        {"name": "A Las Barricadas (ES)", "url": "https://www.alasbarricadas.org/noticias/rss.xml"},
        {"name": "Umanita Nova (IT)", "url": "http://www.umanitanova.org/feed/"},
        {"name": "Federacja Anarchistyczna (PL)", "url": "https://federacja-anarchistyczna.pl/feed/"},
        {"name": "Antifa.cz", "url": "https://www.antifa.cz/rss.xml"},
        {"name": "Lower Class Magazine", "url": "https://lowerclassmag.com/feed/"},
        {"name": "Anarchist Communist Group", "url": "https://www.anarchistcommunism.org/feed/"}
    ],
    "Africa": [
        {"name": "Pambazuka News", "url": "https://www.pambazuka.org/rss.xml"},
        {
            "name": "The Elephant (Kenya)",
            "url": "https://www.theelephant.info/feed/",
            "homepage": "https://www.theelephant.info/",
            "language": "en",
            "categories": ["Africa", "Anticolonialism", "Anti-Imperialism"],
            "originCountry": "Kenya",
            "originCountryCode": "KE",
            "originRegion": "East Africa",
        },
        {"name": "Mada Masr (Egypt)", "url": "https://madamasr.com/en/feed"},
        {"name": "Attac / CADTM Maroc", "url": "https://www.cadtm.org/spip.php?page=backend"},
        {"name": "Zabalaza", "url": "https://zabalaza.net/feed/"},
        {"name": "ROAPE", "url": "https://roape.net/feed/"},
        {"name": "Anarkismo (Africa)", "url": "http://www.anarkismo.net/backend?topic=africa"},
        {"name": "Abahlali baseMjondolo (South Africa)", "url": "https://abahlali.org/feed/"},
        {"name": "Black Agenda Report", "url": "https://www.blackagendareport.com/feed"}
    ],
    "North America": [
        {"name": "It's Going Down", "url": "https://itsgoingdown.org/feed/"},
        {"name": "Montreal Antifasciste", "url": "https://montreal-antifasciste.info/fr/feed/"},
        {"name": "SubMedia", "url": "https://sub.media/feed/"},
        {"name": "Black Rose / Rosa Negra", "url": "https://blackrosefed.org/feed/"},
        {"name": "C4SS", "url": "https://c4ss.org/feed"},
        {"name": "CrimethInc.", "url": "https://crimethinc.com/feed"},
        {"name": "Unicorn Riot", "url": "https://unicornriot.ninja/feed/"},
        {"name": "Indigenous Action", "url": "https://www.indigenousaction.org/feed/"},
        {"name": "The Appeal", "url": "https://theappeal.org/feed/"},
        {"name": "Truthout", "url": "https://truthout.org/feed/"},
        {"name": "Waging Nonviolence", "url": "https://wagingnonviolence.org/feed/"},
        {"name": "Slingshot Collective", "url": "https://slingshotcollective.org/feed/"}
    ],
    "Latin America": [
        {"name": "Enlace Zapatista (EZLN)", "url": "https://enlacezapatista.ezln.org.mx/feed/"},
        {"name": "El Libertario", "url": "http://periodicoellibertario.blogspot.com/feeds/posts/default"},
        {"name": "Avispa Midia", "url": "https://avispa.org/feed/"},
        {"name": "Desinformémonos", "url": "https://desinformemonos.org/feed/"},
        {"name": "Comunizar", "url": "https://comunizar.com.ar/feed/"},
        {"name": "Indymedia Argentina", "url": "https://argentina.indymedia.org/feed/"},
        {"name": "ANRed (Argentina)", "url": "https://www.anred.org/feed/"},
        {"name": "Pueblos en Camino", "url": "https://pueblosencamino.org/feed/"},
        {"name": "Subversiones (Mexico)", "url": "https://subversiones.org/feed/"}
    ],
    "Radar": [
        {"name": "Kontrapolis (Berlin)", "url": "https://kontrapolis.info/feed/"},
        # Stressfaktor-Termine werden bereits über die öffentliche
        # Radar.squat-API geladen. Der frühere Direkt-Feed liefert inzwischen
        # nur noch eine Bot-Schutzseite und würde dieselben Termine doppeln.
        {"name": "Paris-Luttes (Agenda FR)", "url": "https://paris-luttes.info/spip.php?page=backend-agenda"},
        {"name": "Barrikade (CH)", "url": "https://barrikade.info/spip.php?page=backend"},
        {"name": "CrimethInc. (Events)", "url": "https://morss.it/https://crimethinc.com/categories/events/feed"},
        {"name": "Gancio Cisti", "url": "https://gancio.cisti.org/feed/rss"},
        {"name": "Nantes Révoltée Agenda", "url": "https://nantes.indymedia.org/events/feed/"},
        {"name": "LaPunta Firenze", "url": "https://lapunta.org/feed/rss", "homepage": "https://lapunta.org/"},
        {"name": "Convoca-la Barcelona", "url": "https://bcn.convoca.la/feed/rss", "homepage": "https://bcn.convoca.la/"},
        {"name": "Convócala Madrid", "url": "https://mad.convoca.la/feed/rss", "homepage": "https://mad.convoca.la/"},
        {"name": "Rhein-Main Events", "url": "https://events.rheinmain.social/feed/rss", "homepage": "https://events.rheinmain.social/"},
        {"name": "Akce Nolog Praha", "url": "https://akce.nolog.cz/feed/rss", "homepage": "https://akce.nolog.cz/"},
        {"name": "Vagancio Buenos Aires", "url": "https://vagancio.partidopirata.com.ar/feed/rss", "homepage": "https://vagancio.partidopirata.com.ar/"},
        {"name": "Enredad.es", "url": "https://enredad.es/feed/rss", "homepage": "https://enredad.es/"},
        {"name": "ALÉ Montpellier", "url": "https://www.aleale.org/feed/rss", "homepage": "https://www.aleale.org/"},
        {"name": "Agenda des Luttes Rouen", "url": "https://agenda.rouen-luttes.org/feed/rss", "homepage": "https://agenda.rouen-luttes.org/"}
    ],
    "Asia": [
        {"name": "Bulatlat (Philippines)", "url": "https://www.bulatlat.com/feed/"},
        {
            "name": "The Polis Project (India)",
            "url": "https://www.thepolisproject.com/feed/",
            "homepage": "https://www.thepolisproject.com/",
            "language": "en",
            "categories": ["Asia", "Antifascism", "Anticolonialism", "Anti-Rep & Prisons"],
            "originCountry": "India",
            "originCountryCode": "IN",
            "originRegion": "South Asia",
        },
        {"name": "Rojava Info Center", "url": "https://rojavainformationcenter.org/feed/"},
        {
            "name": "ANF English (Kurdistan)",
            "url": "https://english.anf-news.com/feed.rss",
            "homepage": "https://english.anf-news.com/",
        },
        {"name": "Lausan (HK)", "url": "https://lausan.hk/feed/"},
        {"name": "Chuang (CN)", "url": "https://chuangcn.org/feed/"},
        {"name": "New Bloom (TW)", "url": "https://newbloommag.net/feed/"},
        {"name": "Mekong Review", "url": "https://mekongreview.com/feed/"},
        {"name": "Thozhilalar Koodam (India)", "url": "https://tnlabor.in/feed/"},
        {"name": "Radical Socialist (India)", "url": "http://www.radicalsocialist.in/index.php?format=feed&type=rss"},
        {"name": "Palang Hitam (Indonesia)", "url": "https://palanghitam.noblogs.org/feed/"},
        {"name": "Federation of Anarchism Era", "url": "https://asranarshism.com/feed/"},
        {"name": "Fauda", "url": "https://fauda.noblogs.org/feed/"},
        {"name": "Manila Today", "url": "https://manilatoday.net/feed/"},
        {"name": "Kodao Productions", "url": "https://kodao.org/feed/"},
        {"name": "Karapatan (Human Rights)", "url": "https://www.karapatan.org/feed/"},
        {"name": "Asian Labour Review", "url": "https://labourreview.org/feed/"}
    ],
    "Australia & NZ": [
        {"name": "IndigenousX (Australia)", "url": "https://indigenousx.com.au/feed/"},
        {"name": "MACG", "url": "https://melbacg.wordpress.com/feed/"},
        {"name": "Slackbastard", "url": "https://slackbastard.anarchobase.com/?feed=rss2"},
        {"name": "Green Left", "url": "https://www.greenleft.org.au/rss.xml"},
        {"name": "AWSM", "url": "https://awsm.nz/feed/"},
        {"name": "Red Flag (Aus)", "url": "https://redflag.org.au/feed"},
        {"name": "Overland", "url": "https://overland.org.au/feed/"}
    ],
    "Labor Struggles": [
        {"name": "IWW (Global)", "url": "https://www.iww.org/feed/"},
        {"name": "FAU (Deutschland)", "url": "https://www.fau.org/rss.xml"},
        {"name": "CNT (Spanien)", "url": "https://www.cnt.es/feed/"},
        {"name": "Labor Notes", "url": "https://labornotes.org/feed"},
        {"name": "AngryWorkers", "url": "https://angryworkers.org/feed/"},
        {"name": "LabourNet DE", "url": "https://www.labournet.de/feed/"},
        {"name": "Libcom (Workplace)", "url": "https://libcom.org/news/feed"},
        {"name": "Thozhilalar Koodam", "url": "https://tnlabor.in/feed/"}
    ],
    "Antifascism": [
        {"name": "Unicorn Riot", "url": "https://unicornriot.ninja/feed/"},
        {"name": "Antifa Infoblatt", "url": "https://www.antifainfoblatt.de/rss.xml"},
        {"name": "Montreal Antifasciste", "url": "https://montreal-antifasciste.info/fr/feed/"},
        {"name": "Barrikade", "url": "https://barrikade.info/spip.php?page=backend"},
        {"name": "Act for Freedom Now!", "url": "https://actforfree.noblogs.org/feed/"},
        {"name": "Fajfa (Antifa)", "url": "https://fajfa.noblogs.org/feed/"},
        {"name": "Antifa.cz", "url": "https://www.antifa.cz/rss.xml"},
        {"name": "Antifa Bern", "url": "https://antifa-bern.ch/feed/"}
    ],
    "Antisexism": [
        {"name": "Anarkismo (Gender)", "url": "http://www.anarkismo.net/backend?topic=gender"},
        {"name": "Jineolojî Academy", "url": "https://jineoloji.eu/en/feed/"},
        {"name": "Ni Una Menos", "url": "https://niunamenos.org.ar/feed/"},
        {"name": "Feministische Antifa", "url": "https://fantifa.noblogs.org/feed/"},
        {"name": "Missy Magazine (DE)", "url": "https://missy-magazine.de/feed/"}
    ],
    "Queer-Feminism": [
        {"name": "Queer Anarchism", "url": "https://queeranarchism.tumblr.com/rss"},
        {"name": "Black Rose (Feminism)", "url": "https://blackrosefed.org/category/anarcha-feminism/feed/"},
        {"name": "GenderIT (Technofeminism)", "url": "https://www.genderit.org/rss.xml"},
        {"name": "Transgender Europe (TGEU)", "url": "https://tgeu.org/feed/"},
        {
            "name": "Autostraddle News",
            "url": "https://www.autostraddle.com/category/news/feed/",
            "homepage": "https://www.autostraddle.com/category/news/",
            "categories": ["Queer-Feminism", "North America"],
            "language": "en",
            "originCountry": "United States",
            "originCountryCode": "US",
            "originRegion": "North America",
            "imageHosts": ["autostraddle.com", "www.autostraddle.com"]
        },
        {"name": "Make Rojava Green Again", "url": "https://makerojavagreenagain.org/feed/"},
        {"name": "Pinko Magazine", "url": "https://pinko.online/feed/"},
        {"name": "Feminist Anti-War Resistance", "url": "https://femagainstwar.org/feed/"}
    ],
    "Antiracism": [
        {"name": "Institute of Race Relations", "url": "https://irr.org.uk/feed/"},
        {"name": "Black Rose (Anti-Racism)", "url": "https://blackrosefed.org/category/anti-racism/feed/"},
        {"name": "Colorlines", "url": "https://colorlines.com/feed/"},
        {"name": "Abolition Journal", "url": "https://abolitionjournal.org/feed/"}
    ],
    "No Borders": [
        {"name": "Abolish Frontex", "url": "https://abolishfrontex.org/feed/"},
        {"name": "Sea-Watch", "url": "https://sea-watch.org/feed/"},
        {"name": "Are You Syrious?", "url": "https://medium.com/feed/are-you-syrious"},
        {"name": "No One Is Illegal", "url": "https://noii-van.org/feed/"},
        {"name": "Migrant Solidarity Network (CH)", "url": "https://migrant-solidarity-network.ch/feed/"}
    ],
    "Anticapitalism": [
        {"name": "CrimethInc.", "url": "https://crimethinc.com/feed"},
        {"name": "Comunizar", "url": "https://comunizar.com.ar/feed/"},
        {"name": "ZNet (Global)", "url": "https://znetwork.org/feed/"},
        {"name": "Tricontinental: Institute for Social Research", "url": "https://thetricontinental.org/feed/"},
        {"name": "Monthly Review", "url": "https://monthlyreview.org/feed/"},
        {"name": "Novara Media (UK)", "url": "https://novaramedia.com/feed/"},
        {"name": "The New Inquiry", "url": "https://thenewinquiry.com/feed/"}
    ],
    "Theory & Strategy": [
        {"name": "Ill Will", "url": "https://illwill.com/feed"},
        {"name": "Endnotes", "url": "https://endnotes.org.uk/feed.xml"},
        {"name": "Wildcat", "url": "https://www.wildcat-www.de/wildcat.rss"},
        {"name": "CrimethInc. (Texts)", "url": "https://crimethinc.com/categories/texts/feed"}
    ],
    "Anticolonialism": [
        {"name": "Avispa Midia", "url": "https://avispa.org/feed/"},
        {"name": "Lausan", "url": "https://lausan.hk/feed/"},
        {"name": "Black Rose (Anti-Colonial)", "url": "https://blackrosefed.org/category/anti-colonialism/feed/"}
    ],
    "Anti-Imperialism": [
        {"name": "Pambazuka News", "url": "https://www.pambazuka.org/rss.xml"},
        {"name": "ROAPE", "url": "https://roape.net/feed/"},
        {"name": "Asian Labour Review", "url": "https://labourreview.org/feed/"}
    ],
    "Squatting & Housing": [
        {"name": "Squat!net", "url": "https://de.squat.net/feed/"},
        {"name": "Barrikade", "url": "https://barrikade.info/spip.php?page=backend"},
        {"name": "Mietergewerkschaft Berlin", "url": "https://mietergewerkschaft.berlin/feed/"},
        {"name": "Housing Action", "url": "https://housingaction.noblogs.org/feed/"},
        {"name": "Recht auf Stadt (Hamburg)", "url": "https://www.rechtaufstadt.net/feed/"},
        {"name": "Zwangsräumung Verhindern (Berlin)", "url": "https://zwangsraeumungverhindern.org/feed/"},
        {"name": "Defend Council Housing (UK)", "url": "https://www.defendcouncilhousing.org.uk/feed/"}
    ],
    "Demonstrations": [
        {"name": "It's Going Down", "url": "https://itsgoingdown.org/feed/"},
        {"name": "Athens Indymedia", "url": "https://athens.indymedia.org/rss/"},
        {"name": "Kontrapolis", "url": "https://kontrapolis.info/feed/"}
    ],
    "Anti-Rep & Prisons": [
        {"name": "IWOC (Incarcerated Workers)", "url": "https://incarceratedworkers.org/feed"},
        {"name": "Kite Line Radio", "url": "https://kitelineradio.noblogs.org/feed/"},
        {"name": "Critical Resistance", "url": "https://criticalresistance.org/feed/"},
        {"name": "Rote Hilfe", "url": "https://www.rote-hilfe.de/rss.xml"},
        {"name": "Anarchist Black Cross", "url": "https://www.abcf.net/feed/"},
        {"name": "ABC Belarus", "url": "https://abc-belarus.org/?feed=rss2&lang=en"},
        {"name": "BOAK (RU)", "url": "https://boak.noblogs.org/feed/"},
    ],
    "Cyberactivism": [
        {"name": "Systemli", "url": "https://www.systemli.org/feed.xml"},
        {"name": "DDoSecrets", "url": "https://ddosecrets.com/api.php?action=featuredfeed&feed=rss"},
        {"name": "Kolektiva Media (Video)", "url": "https://kolektiva.media/feeds/videos.xml?videoFilter=local"},
        {"name": "Electronic Frontier Foundation", "url": "https://www.eff.org/rss/updates.xml"}
    ],
    "No War": [
        {"name": "War Resisters' International", "url": "https://wri-irg.org/en/feed"},
        {"name": "Rheinmetall Entwaffnen", "url": "https://rheinmetallentwaffnen.noblogs.org/feed/"},
        {"name": "Antimilitarismus", "url": "https://antimilitarismus.noblogs.org/feed/"},
        {"name": "Democracy Now! (Global)", "url": "https://www.democracynow.org/democracynow.rss"},
        {"name": "Stop the War Coalition", "url": "https://www.stopwar.org.uk/feed/"},
        {"name": "Labor for Palestine", "url": "https://laborforpalestine.net/feed/"},
        {"name": "World BEYOND War", "url": "https://worldbeyondwar.org/feed/"}
    ],
    "Animal Liberation": [
        {"name": "Tierbefreier", "url": "https://tierbefreier.org/feed/"},
        {"name": "Unoffensive Animal", "url": "https://unoffensiveanimal.is/feed/"},
        {"name": "ALF Press Office (North America)", "url": "https://animalliberationpressoffice.org/NAALPO/feed/"},
        {"name": "Hunt Saboteurs Association (UK)", "url": "https://www.huntsabs.org.uk/feed/"},
    ],
    "Eco-Anarchism": [
        {"name": "Earth First!", "url": "https://earthfirstjournal.news/feed/"},
        {"name": "Winter Oak", "url": "https://winteroak.org.uk/feed/"},
        {"name": "SubMedia", "url": "https://sub.media/feed/"},
        {"name": "Solarpunk Magazine", "url": "https://solarpunkmagazine.com/feed/"},
        {"name": "Defend the Atlanta Forest", "url": "https://defendtheatlantaforest.org/feed/"},
        {"name": "Desmog", "url": "https://www.desmog.com/feed/"},
        {"name": "Ende Gelände", "url": "https://www.ende-gelaende.org/feed/"}
    ],
    "Indigenous Struggles": [
        {"name": "Enlace Zapatista (EZLN)", "url": "https://enlacezapatista.ezln.org.mx/feed/"},
        {"name": "Avispa Midia", "url": "https://avispa.org/feed/"},
        {"name": "IEN Earth", "url": "https://www.ienearth.org/feed/"},
        {"name": "IndigenousX", "url": "https://indigenousx.com.au/feed/"},
        {"name": "Bulatlat (Indigenous)", "url": "https://www.bulatlat.com/feed/"},
        {"name": "Cultural Survival", "url": "https://www.culturalsurvival.org/news/rss.xml"},
        {"name": "Native News Online", "url": "https://nativenewsonline.net/?format=feed&type=rss"},
        {"name": "Grist (Indigenous Affairs)", "url": "https://grist.org/indigenous/feed/"},
        {"name": "Indigenous Action", "url": "https://www.indigenousaction.org/feed/"},
        {"name": "Mapuexpress (Mapuche)", "url": "https://www.mapuexpress.org/feed/"},
        {"name": "Warrior Publications", "url": "https://warriorpublications.wordpress.com/feed/"}
    ],
    "Radical Health & Disability": [
        {"name": "Asylum Magazine", "url": "https://asylummagazine.org/feed/"},
        {"name": "Mad in America", "url": "https://www.madinamerica.com/feed/"},
        {"name": "Disability Visibility", "url": "https://disabilityvisibilityproject.com/feed/"}
    ],
    "Libraries": [
        {"name": "Anarchistische Bibliothek (DE)", "url": "https://de.anarchistlibraries.net/feed/"},
        {"name": "The Anarchist Library (EN)", "url": "https://theanarchistlibrary.org/feed"},
        {"name": "Biblioteca Anarquista (ES)", "url": "https://es.anarchistlibraries.net/feed/"},
        {"name": "Bibliothèque Anarchiste (FR)", "url": "https://fr.anarchistlibraries.net/feed/"},
        {"name": "Libreria Anarchica (IT)", "url": "https://it.theanarchistlibrary.org/feed"},
        {"name": "Biblioteca Anarquista (PT)", "url": "https://pt.theanarchistlibrary.org/feed"},
        {"name": "Anarchist Library (RU)", "url": "https://ru.anarchistlibraries.net/feed/"},
        {"name": "Anarchist Library (TR)", "url": "https://tr.theanarchistlibrary.org/feed"},
        {"name": "Anarchist Library (PL)", "url": "https://pl.theanarchistlibrary.org/feed"},
        {"name": "Anarchist Library (SV)", "url": "https://www.anarkistiskabiblioteket.se/feed/"},
        {"name": "RevoltLib", "url": "https://revoltlib.com/feed"},
        {"name": "Sprout Distro", "url": "https://www.sproutdistro.com/feed/"},
        {"name": "Zabalaza Books (Africa)", "url": "https://zabalazabooks.net/feed/"},
        {"name": "Libcom Library", "url": "https://libcom.org/news/feed"}
    ]
}
# WRN MULTILINGUAL SOURCES 1.8.2 START
# Additive and idempotent: the existing source dictionary is never replaced.
_wrn_extra_sources_182 = [{'name': 'Graswurzelrevolution', 'kind': 'news', 'adapter': 'rss', 'languages': ['de'], 'homepage': 'https://www.graswurzel.net/gwr/', 'feedUrl': 'https://www.graswurzel.net/gwr/feed/', 'categories': ['Europe', 'No War', 'Anarchism'], 'status': 'approved'}, {'name': 'Agência Pública', 'kind': 'news', 'adapter': 'rss', 'languages': ['pt'], 'homepage': 'https://apublica.org/', 'feedUrl': 'https://apublica.org/feed/', 'categories': ['Latin America', 'Environment', 'Investigative'], 'status': 'approved'}, {'name': 'Bianet Türkçe', 'kind': 'news', 'adapter': 'rss', 'languages': ['tr'], 'homepage': 'https://bianet.org/', 'feedUrl': 'https://bianet.org/rss/bianet', 'categories': ['Europe', 'Labor Struggles', 'Antiracism', 'Queer-Feminism'], 'originCountry': 'Türkiye', 'originCountryCode': 'TR', 'originRegion': 'Türkiye', 'status': 'approved', 'addedIn': '1.8.2'}, {'name': 'Evrensel', 'kind': 'news', 'adapter': 'rss', 'languages': ['tr'], 'homepage': 'https://www.evrensel.net/', 'feedUrl': 'https://www.evrensel.net/rss/haber.xml', 'categories': ['Europe', 'Labor Struggles', 'Anticapitalism', 'No War'], 'originCountry': 'Türkiye', 'originCountryCode': 'TR', 'originRegion': 'Türkiye', 'status': 'approved', 'addedIn': '1.8.2'}, {'name': 'Bianet Kurdî', 'kind': 'news', 'adapter': 'rss', 'languages': ['ku'], 'homepage': 'https://bianet.org/kurdi', 'feedUrl': 'https://bianet.org/rss/kurdi', 'categories': ['Europe', 'Anticolonialism', 'Antiracism', 'No Borders'], 'originCountry': 'Türkiye', 'originCountryCode': 'TR', 'originRegion': 'Türkiye', 'status': 'approved', 'addedIn': '1.8.2'}, {'name': 'Pressin Kurdî', 'kind': 'news', 'adapter': 'rss', 'languages': ['ku'], 'homepage': 'https://pressin.info/kurdi', 'feedUrl': 'https://pressin.info/kurdi/rss/latest-posts', 'categories': ['Asia', 'Anticolonialism', 'Anti-Imperialism'], 'originCountry': 'Iraq', 'originCountryCode': 'IQ', 'originRegion': 'Kurdistan Region', 'status': 'approved', 'addedIn': '1.8.2'}]
for _wrn_source in _wrn_extra_sources_182:
    _wrn_name = str(_wrn_source.get('name', '')).casefold()
    _wrn_url = str(_wrn_source.get('feedUrl', '')).rstrip('/').casefold()
    _wrn_existing = None
    for _wrn_existing_bucket in quellen.values():
        if not isinstance(_wrn_existing_bucket, list):
            continue
        for _wrn_item in _wrn_existing_bucket:
            if not isinstance(_wrn_item, dict):
                continue
            _wrn_item_name = str(_wrn_item.get('name', '')).casefold()
            _wrn_item_url = str(
                _wrn_item.get('url')
                or _wrn_item.get('feedUrl')
                or _wrn_item.get('feed')
                or ''
            ).rstrip('/').casefold()
            if _wrn_item_name == _wrn_name or _wrn_item_url == _wrn_url:
                _wrn_existing = _wrn_item
                break
        if _wrn_existing is not None:
            break
    if _wrn_existing is None:
        _wrn_primary_category = _wrn_source.get('categories', ['Global'])[0]
        _wrn_existing = {
            'name': _wrn_source['name'],
            'url': _wrn_source['feedUrl'],
        }
        quellen.setdefault(_wrn_primary_category, []).append(_wrn_existing)
    _wrn_existing.setdefault('homepage', _wrn_source.get('homepage', ''))
    _wrn_existing.setdefault('language', _wrn_source.get('languages', ['und'])[0])
    _wrn_existing.setdefault('languages', list(_wrn_source.get('languages', ['und'])))
    _wrn_existing.setdefault('categories', list(_wrn_source.get('categories', ['Global'])))
    _wrn_existing.setdefault('originCountry', _wrn_source.get('originCountry', ''))
    _wrn_existing.setdefault('originCountryCode', _wrn_source.get('originCountryCode', ''))
    _wrn_existing.setdefault('originRegion', _wrn_source.get('originRegion', ''))
# WRN MULTILINGUAL SOURCES 1.8.2 END

# WRN SOURCE EXPANSION 1.8.5 START
_wrn_extra_sources_185 = [
    {
        "name": "Africa Is a Country",
        "url": "https://africasacountry.com/feed",
        "homepage": "https://africasacountry.com/",
        "language": "en",
        "categories": ["Africa", "Anticolonialism", "Anti-Imperialism", "Theory & Strategy"],
        "originRegion": "Africa",
    },
    {
        "name": "African Feminism",
        "url": "https://africanfeminism.com/feed/",
        "homepage": "https://africanfeminism.com/",
        "language": "en",
        "categories": ["Africa", "Antisexism", "Queer-Feminism", "Anticolonialism"],
        "originRegion": "Africa",
    },
    {
        "name": "Minority Africa",
        "url": "https://minorityafrica.org/feed/",
        "homepage": "https://minorityafrica.org/",
        "language": "en",
        "categories": ["Africa", "Antisexism", "Queer-Feminism", "Antiracism", "Indigenous Struggles", "Radical Health & Disability", "No Borders"],
        "originRegion": "Africa",
    },
    {
        "name": "Elitsha",
        "url": "https://elitshanews.org.za/en/feed/",
        "homepage": "https://elitshanews.org.za/",
        "language": "en",
        "categories": ["Africa", "Labor Struggles", "Squatting & Housing", "Antiracism"],
        "originCountry": "South Africa",
        "originCountryCode": "ZA",
        "originRegion": "Southern Africa",
    },
    {
        "name": "African Arguments",
        "url": "https://africanarguments.org/feed/",
        "homepage": "https://africanarguments.org/",
        "language": "en",
        "categories": ["Africa", "Anticolonialism", "Anti-Imperialism"],
        "originRegion": "Africa",
    },
    {
        "name": "WoMin African Alliance",
        "url": "https://womin.africa/feed/",
        "homepage": "https://womin.africa/",
        "language": "en",
        "categories": ["Africa", "Antisexism", "Eco-Anarchism", "Indigenous Struggles", "Anticapitalism"],
        "originRegion": "Africa",
    },
    {
        "name": "APTN News",
        "url": "https://www.aptnnews.ca/feed/",
        "homepage": "https://www.aptnnews.ca/",
        "language": "en",
        "categories": ["Indigenous Struggles", "North America", "Anticolonialism"],
        "originCountry": "Canada",
        "originCountryCode": "CA",
        "originRegion": "North America",
    },
    {
        "name": "IndigiNews",
        "url": "https://indiginews.com/feed/",
        "homepage": "https://indiginews.com/",
        "language": "en",
        "categories": ["Indigenous Struggles", "North America", "Anticolonialism"],
        "originCountry": "Canada",
        "originCountryCode": "CA",
        "originRegion": "North America",
    },
    {
        "name": "Nunatsiaq News",
        "url": "https://nunatsiaq.com/feed/",
        "homepage": "https://nunatsiaq.com/",
        "language": "en",
        "categories": ["Indigenous Struggles", "North America", "Anticolonialism"],
        "originCountry": "Canada",
        "originCountryCode": "CA",
        "originRegion": "Inuit Nunangat",
    },
    {
        "name": "The Feminist Wire",
        "url": "https://thefeministwire.com/feed/",
        "homepage": "https://thefeministwire.com/",
        "language": "en",
        "categories": ["Antisexism", "Queer-Feminism", "Antiracism", "North America"],
        "originRegion": "North America",
    },
    {
        "name": "Feminist Newswire",
        "url": "https://feminist.org/news/feed/",
        "homepage": "https://feminist.org/news/",
        "language": "en",
        "categories": ["Antisexism", "Queer-Feminism", "North America"],
        "originRegion": "North America",
    },
    {
        "name": "AWID",
        "url": "https://www.awid.org/rss.xml",
        "homepage": "https://www.awid.org/",
        "language": "en",
        "categories": ["Antisexism", "Queer-Feminism", "Anticapitalism", "Global"],
        "originRegion": "Global",
    },
    {
        "name": "Equality Now",
        "url": "https://equalitynow.org/feed/",
        "homepage": "https://equalitynow.org/",
        "language": "en",
        "categories": ["Antisexism", "Global"],
        "originRegion": "Global",
    },
    {
        "name": "Women Enabled International",
        "url": "https://womenenabled.org/feed/",
        "homepage": "https://womenenabled.org/",
        "language": "en",
        "categories": ["Antisexism", "Radical Health & Disability", "Global"],
        "originRegion": "Global",
    },
    {
        "name": "Anarşist Haberler",
        "url": "https://www.anarsisthaberler.net/feed/",
        "homepage": "https://www.anarsisthaberler.net/",
        "language": "tr",
        "categories": ["Europe", "Theory & Strategy", "Anticapitalism", "Antifascism"],
        "originCountry": "Türkiye",
        "originCountryCode": "TR",
        "originRegion": "Türkiye",
        "minArticleTextLength": 700,
        "articleSelectors": ["article", ".entry-content", "main"],
    },
    {
        "name": "Radikal Perspektif",
        "url": "https://rpkolektif.wordpress.com/feed/",
        "homepage": "https://rpkolektif.wordpress.com/",
        "language": "tr",
        "categories": ["Europe", "Theory & Strategy", "Anticapitalism"],
        "originCountry": "Türkiye",
        "originCountryCode": "TR",
        "originRegion": "Türkiye",
        "minArticleTextLength": 700,
        "articleSelectors": ["article", ".entry-content", "main"],
    },
    {
        "name": "Yeryüzü Postası",
        "url": "https://www.yeryuzupostasi.org/feed/",
        "homepage": "https://www.yeryuzupostasi.org/",
        "language": "tr",
        "categories": ["Europe", "Anticapitalism", "Labor Struggles", "Theory & Strategy", "No War"],
        "originCountry": "Türkiye",
        "originCountryCode": "TR",
        "originRegion": "Türkiye",
        "minArticleTextLength": 700,
        "articleSelectors": ["article", ".entry-content", "main"],
    },
]

_wrn_known_source_names_185 = {
    safe_lower(item.get("name"))
    for bucket in quellen.values()
    for item in bucket
    if isinstance(item, dict)
}
for _wrn_source in _wrn_extra_sources_185:
    if safe_lower(_wrn_source.get("name")) in _wrn_known_source_names_185:
        continue
    _wrn_primary_category = _wrn_source.get("categories", ["Global"])[0]
    quellen.setdefault(_wrn_primary_category, []).append(_wrn_source)
    _wrn_known_source_names_185.add(safe_lower(_wrn_source.get("name")))

for _wrn_bucket in quellen.values():
    for _wrn_source in _wrn_bucket:
        if safe_lower(_wrn_source.get("name")).startswith("bianet "):
            _wrn_source["maxNewItems"] = 1
        if safe_lower(_wrn_source.get("name")) == "truthout":
            # Truthouts Feed enthält nur Anreißer. Der erste Reparaturlauf
            # darf deshalb alle im Feed sichtbaren Auszüge nachladen; danach
            # werden vollständige Artikel weiterhin sofort übersprungen.
            _wrn_source["maxNewItems"] = 15
            _wrn_source["minArticleTextLength"] = 1200
            _wrn_source["articleSelectors"] = [
                "[itemprop='articleBody']",
                ".article-content",
                ".entry-content",
                "article",
                "main",
            ]
ARTICLE_MIN_LENGTHS = {
    safe_lower(source.get("name")): max(
        350,
        int(source.get("minArticleTextLength", 700)),
    )
    for bucket in quellen.values()
    for source in bucket
    if isinstance(source, dict) and safe_text(source.get("name"))
}
# WRN SOURCE EXPANSION 1.8.5 END

SPAM_BLACKLIST = [
    "sicherheitslage verschlimmert",
    "mordeaffen",
    "kurt gustav wilckens"
]

# Quellen mit abgeschnittenen RSS-Texten sollen die App nicht dominieren.
# Vollständige Artikel bleiben von dieser Grenze unberührt.
MAX_INCOMPLETE_PER_SOURCE = 6
INCOMPLETE_SOURCE_LIMITS = {
    "anarchist news": 4,
}
INCOMPLETE_MARKERS = (
    "read more",
    "continue reading",
    "continue to read",
    "read the full article",
    "full story at",
    "weiterlesen",
    "mehr lesen",
    " appeared first on ",
    "no text available",
    "full text of this article is protected",
)

REGION_CATEGORIES = {
    "Global", "Europe", "Africa", "North America",
    "Latin America", "Asia", "Australia & NZ",
}
COUNTRY_PRIMARY_REGIONS = {
    "DZ": "Africa", "AO": "Africa", "BJ": "Africa", "BW": "Africa",
    "BF": "Africa", "BI": "Africa", "CM": "Africa", "CD": "Africa",
    "CG": "Africa", "CI": "Africa", "EG": "Africa", "ET": "Africa",
    "GH": "Africa", "KE": "Africa", "MA": "Africa", "MZ": "Africa",
    "NG": "Africa", "RW": "Africa", "SN": "Africa", "SO": "Africa",
    "ZA": "Africa", "SD": "Africa", "TZ": "Africa", "TN": "Africa",
    "UG": "Africa", "ZM": "Africa", "ZW": "Africa",
    "US": "North America", "CA": "North America", "GL": "North America",
    "MX": "Latin America", "AR": "Latin America", "BO": "Latin America",
    "BR": "Latin America", "CL": "Latin America", "CO": "Latin America",
    "CR": "Latin America", "CU": "Latin America", "EC": "Latin America",
    "GT": "Latin America", "HT": "Latin America", "HN": "Latin America",
    "NI": "Latin America", "PA": "Latin America", "PE": "Latin America",
    "PY": "Latin America", "SV": "Latin America", "UY": "Latin America",
    "VE": "Latin America",
    "CN": "Asia", "HK": "Asia", "IN": "Asia", "ID": "Asia",
    "JP": "Asia", "KR": "Asia", "KP": "Asia", "MY": "Asia",
    "MM": "Asia", "NP": "Asia", "PK": "Asia", "PH": "Asia",
    "SG": "Asia", "LK": "Asia", "TH": "Asia", "TW": "Asia",
    "VN": "Asia", "BD": "Asia", "KH": "Asia", "AF": "Asia",
    "IQ": "Asia", "IR": "Asia", "IL": "Asia", "PS": "Asia",
    "LB": "Asia", "SY": "Asia", "JO": "Asia", "YE": "Asia",
    "AU": "Australia & NZ", "NZ": "Australia & NZ", "FJ": "Australia & NZ",
    "PG": "Australia & NZ", "WS": "Australia & NZ", "VU": "Australia & NZ",
    "AL": "Europe", "AT": "Europe", "BE": "Europe", "BG": "Europe",
    "CH": "Europe", "CZ": "Europe", "DE": "Europe", "DK": "Europe",
    "ES": "Europe", "FI": "Europe", "FR": "Europe", "GB": "Europe",
    "GR": "Europe", "HR": "Europe", "HU": "Europe", "IE": "Europe",
    "IT": "Europe", "NL": "Europe", "NO": "Europe", "PL": "Europe",
    "PT": "Europe", "RO": "Europe", "RS": "Europe", "SE": "Europe",
    "TR": "Europe", "UA": "Europe",
}
TOPIC_CATEGORY_PATTERNS = {
    "Labor Struggles": (
        r"\bstrike\b", r"\bstrikers?\b", r"\bworkers?\b", r"\btrade union\b",
        r"\blabou?r\b", r"\bunionis", r"\bstreik", r"\barbeiter", r"\bgewerkschaft",
        r"\bgr[eè]ve", r"\bsyndicat", r"\bhuelga", r"\bsindicat", r"\bgrev",
        r"\bişçi", r"\bemekçi", r"\bsendika", r"\bdireniş",
        r"\btrabajador", r"\btrabalhador", r"\bεργαζ", r"\bαπεργ",
        r"\bрабоч", r"\bзабастов", r"\bعامل", r"\bإضراب", r"\bkarker",
    ),
    "Antifascism": (
        r"\banti[- ]?fasc", r"\bfascis", r"\bneo[- ]?nazi", r"\bfar[- ]right\b",
        r"\bextreme droite\b", r"\bextrema derecha\b", r"\bultradestra\b",
        r"\brechtsextrem", r"\bafd\b", r"\bfaşis", r"\başırı sağ",
        r"\bantifascis", r"\bantifascist", r"\bαντιφασ", r"\bфашис",
        r"\bfaşîst",
    ),
    "Antisexism": (
        r"\bsexism", r"\bmisogyn", r"\bpatriarch", r"\bsexual violence\b",
        r"\bsexual assault\b", r"\bharassment\b", r"\bsexismus", r"\bviolaci[oó]n",
        r"\bviolence sexuelle\b", r"\bviolenza sessuale\b", r"\bcinsiyetçi",
        r"\bcinsel şiddet", r"\bkadına yönelik şiddet", r"\btaciz",
        r"\bviolencia machista", r"\bfeminicid", r"\bfemicid",
        r"\bέμφυλη βία", r"\bпатриарх", r"\bнасилие над женщ",
        r"\bعنف ضد المرأة", r"\bkadın cinayet",
    ),
    "Queer-Feminism": (
        r"\bqueer\b", r"\blgbt", r"\btrans(?:gender|phob| rights?)?\b",
        r"\blesbian", r"\bhomophob", r"\bfeminis", r"\bnon[- ]?binary\b",
        r"\blgbti", r"\bkuir", r"\btransfobi",
        r"\bmujeres?\b", r"\bderechos reproductiv", r"\bγυναικ",
        r"\bфемини", r"\bженщин", r"\bنسوي", r"\bjin\b",
    ),
    "Antiracism": (
        r"\banti[- ]?rac", r"\bracis", r"\bwhite supremacy\b",
        r"\bxenophob", r"\bapartheid\b", r"\brassismus\b",
        r"\bırkçı", r"\bırkçılık", r"\bnefret suçu",
        r"\bdiscriminaci[oó]n racial", r"\bρατσισ", r"\bрасизм",
        r"\bعنصري", r"\birqperest",
    ),
    "No Borders": (
        r"\bmigran", r"\brefugee", r"\basylum\b", r"\bborder", r"\bdeport",
        r"\bimmigration\b", r"\bfl[uü]cht", r"\babschieb", r"\br[eé]fugi",
        r"\bgöçmen", r"\bmülteci", r"\bsığınmacı", r"\bsınır dışı",
        r"\bfrontera", r"\brefugiado", r"\bμετανάστ", r"\bπρόσφυγ",
        r"\bмигран", r"\bбежен", r"\bلاجئ", r"\bمهاجر", r"\bpenaber",
    ),
    "Anticapitalism": (
        r"\banti[- ]?capital", r"\bcapitalis", r"\bclass struggle\b",
        r"\bworking class\b", r"\bneoliberal", r"\bkapitalis", r"\bcapitalismo\b",
        r"\bsermaye", r"\bözelleştir",
        r"\blucha de clases", r"\banticapitalis", r"\bκαπιταλισ",
        r"\bкапитализм", r"\bرأسمالي", r"\bkapîtalîzm",
    ),
    "Theory & Strategy": (
        r"\banarchis", r"\blibertarian communis", r"\bmutual aid\b",
        r"\bdirect action\b", r"\bsyndicalis", r"\bpolitical theory\b",
        r"\brevolutionary strateg", r"\bbook review\b", r"\banarş",
        r"\bdayanışma", r"\bdoğrudan eylem",
        r"\bautogesti[oó]n", r"\bcomunismo libertario", r"\bαναρχ",
        r"\bанарх", r"\bанархи", r"\bلاسلطوي", r"\bئەنارشی",
    ),
    "Anticolonialism": (
        r"\banti[- ]?coloni", r"\bdecoloni", r"\bcolonialis",
        r"\bsettler colon", r"\bcolonial rule\b", r"\bsömürge", r"\bkolonyal",
        r"\bcolonialismo", r"\bdescolon", r"\bαποικιοκρα", r"\bколониал",
        r"\bاستعمار", r"\bkolonyalîzm",
    ),
    "Anti-Imperialism": (
        r"\banti[- ]?imperial", r"\bimperialis", r"\bimperial power\b", r"\bemperyal",
        r"\bαντιιμπεριαλ", r"\bимпериал", r"\bإمبريال", r"\bîmperyal",
    ),
    "Squatting & Housing": (
        r"\bsquat", r"\bhousing\b", r"\btenant", r"\brent strike\b",
        r"\beviction", r"\bhausbesetz", r"\bmiet", r"\blogement\b",
        r"\bbarınma", r"\bkonut", r"\bkira", r"\btahliye",
        r"\bdesalojo", r"\bocupaci[oó]n", r"\bστέγα", r"\bκατάληψη",
        r"\bвыселен", r"\bсквот", r"\bإسكان",
    ),
    "Demonstrations": (
        r"\bprotest", r"\bdemonstrat", r"\brally\b", r"\bmarch\b",
        r"\bmobilis", r"\bkundgebung", r"\bmanifestaci[oó]n\b",
        r"\bprotesto", r"\beylem", r"\byürüyüş", r"\bmiting",
        r"\bmarcha\b", r"\bδιαδήλω", r"\bпротест", r"\bмитинг",
        r"\bاحتجاج", r"\bخۆپیشاندان",
    ),
    "Anti-Rep & Prisons": (
        r"\bprison", r"\barrest", r"\brepress",
        r"\bdetention\b", r"\bincarcer", r"\bpolitical prisoner",
        r"\bprisoner support\b", r"\babolition(?:ist|ism)?\b",
        r"\bpolice (?:violence|brutality|killing|raid|repression)\b",
        r"\bstate repression\b", r"\bknast\b", r"\bgef[aä]ng",
        r"\bcezaevi", r"\bhapishane", r"\bgözaltı", r"\btutuk", r"\bmahkeme",
        r"\bc[aá]rcel", r"\bprisi[oó]n", r"\bdetenid", r"\brepresi[oó]n",
        r"\bφυλακ", r"\bαστυνομ", r"\bтюрьм", r"\bарест", r"\bполици",
        r"\bسجن", r"\bاعتقال", r"\bشرطة", r"\bzindan", r"\bgirtî",
    ),
    "Cyberactivism": (
        r"\bcyber", r"\bdigital rights?\b", r"\bsurveillance\b", r"\bencryption\b",
        r"\bhack(?:er|ing)?\b", r"\bprivacy\b", r"\bopen[- ]source\b",
        r"\bdijital hak", r"\bgözetim", r"\bsansür", r"\bsiber",
        r"\bvigilancia digital", r"\bλογοκρισ", r"\bнаблюден", r"\bцензур",
        r"\bمراقبة", r"\bسانسور",
    ),
    "No War": (
        r"\banti[- ]?war\b", r"\bwar\b", r"\bmilitar", r"\barmy\b",
        r"\bweapons?\b", r"\bconscription\b", r"\bceasefire\b", r"\bkrieg",
        r"\baufr[uü]st", r"\barmement\b", r"\bsavaş", r"\bsilah", r"\basker",
        r"\bguerra\b", r"\bαντιπολεμ", r"\bвойн", r"\bвоенн",
        r"\bحرب", r"\bسلاح", r"\bşer\b",
    ),
    "Animal Liberation": (
        r"\banimal liberation\b", r"\banimal rights?\b", r"\bvegan",
        r"\bslaughterhouse\b", r"\bhunt sab", r"\btierbefrei", r"\bvivisection\b",
        r"\bhayvan hak", r"\bmezbaha",
        r"\bliberaci[oó]n animal", r"\bαπελευθέρωση ζώων", r"\bживотн",
        r"\bحقوق الحيوان",
    ),
    "Eco-Anarchism": (
        r"\bclimate\b", r"\becolog", r"\benvironment", r"\bforest\b",
        r"\bpipeline\b", r"\bfossil fuel", r"\bmining\b", r"\bklima",
        r"\biklim", r"\bekoloji", r"\bçevre", r"\bmaden",
        r"\bcambio clim[aá]tico", r"\bmedio ambiente", r"\bκλίμα",
        r"\bокружающей сред", r"\bклимат", r"\bمناخ", r"\bژینگە",
    ),
    "Indigenous Struggles": (
        r"\bindigenous\b", r"\bfirst nations?\b", r"\bnative peoples?\b",
        r"\bmapuche\b", r"\bzapatist", r"\baboriginal\b", r"\bindigen", r"\byerli halk",
        r"\bpueblos? originarios?", r"\bιθαγεν", r"\bкоренн", r"\bالسكان الأصلي",
    ),
    "Radical Health & Disability": (
        r"\bdisabil", r"\bmental health\b", r"\bpsychiatr", r"\bhealth care\b",
        r"\bhealthcare\b", r"\bclinic\b", r"\bableis", r"\bbehinder",
        r"\bengelli", r"\bruh sağlığı", r"\bsağlık",
    ),
    "Libraries": (
        r"\banarchist librar", r"\bbiblioth[eè]que anarch", r"\bbiblioteca anarqu",
        r"\banarchistische bibliothek\b",
    ),
    "Movement News": (),
}

TOPIC_CATEGORY_STRONG_PATTERNS = {
    "Labor Struggles": (
        r"\bgeneral strike\b", r"\bwildcat strike\b", r"\bstrike action\b",
        r"\bpicket line\b", r"\bcollective bargaining\b", r"\bworkers'? control\b",
        r"\bgenel grev\b", r"\biş bırakma\b", r"\bgreve générale\b",
    ),
    "Antifascism": (
        r"\banti[- ]?fascist action\b", r"\bfascist attack\b",
        r"\bneo[- ]?nazi attack\b", r"\bwhite nationalist\b",
        r"\bantifaschistische aktion\b", r"\bfaşist saldır",
    ),
    "Antisexism": (
        r"\bgender[- ]based violence\b", r"\bdomestic violence\b",
        r"\bsexual abuse\b", r"\bviolence against women\b",
        r"\bpatriarchal violence\b", r"\bfeminist strike\b",
        r"\berkek şiddeti\b", r"\bkadın cinayet",
    ),
    "Queer-Feminism": (
        r"\btrans liberation\b", r"\bqueer liberation\b",
        r"\breproductive justice\b", r"\babortion rights?\b",
        r"\blgbtqia?\+? rights?\b", r"\bpride march\b", r"\bkürtaj hakkı\b",
    ),
    "Antiracism": (
        r"\bracial justice\b", r"\bpolice racism\b", r"\bracist attack\b",
        r"\bwhite supremacist\b", r"\banti[- ]?racist action\b",
        r"\bırkçı saldır",
    ),
    "No Borders": (
        r"\bno borders?\b", r"\brefugee solidarity\b",
        r"\bmigrant solidarity\b", r"\bdeportation flight\b",
        r"\bdetention cent(?:er|re)\b", r"\bsınır dışı edil",
    ),
    "Anticapitalism": (
        r"\bclass war\b", r"\babolish capitalism\b",
        r"\bcapitalist crisis\b", r"\bsocial revolution\b",
        r"\bkapitalist sistem\b",
    ),
    "Theory & Strategy": (
        r"\bpolitical strategy\b", r"\bmovement strategy\b",
        r"\bprefigurative politics\b", r"\bdual power\b",
        r"\bcounter[- ]power\b", r"\banarchist theory\b",
        r"\blibertarian communism\b", r"\bdevrimci strateji\b",
    ),
    "Anticolonialism": (
        r"\bsettler colonialism\b", r"\bcolonial occupation\b",
        r"\bdecolonial struggle\b", r"\bcolonial violence\b",
        r"\bsömürgecilik karşıtı\b",
    ),
    "Anti-Imperialism": (
        r"\banti[- ]?imperialist struggle\b", r"\bimperialist war\b",
        r"\bforeign occupation\b", r"\beconomic imperialism\b",
        r"\bemperyalist savaş\b",
    ),
    "Squatting & Housing": (
        r"\bhousing crisis\b", r"\btenant union\b", r"\brent resistance\b",
        r"\beviction resistance\b", r"\bsquat eviction\b",
        r"\bzwangsräum", r"\bkira grevi\b",
    ),
    "Demonstrations": (
        r"\bmass protest\b", r"\bstreet protest\b", r"\bprotest march\b",
        r"\bsolidarity demonstration\b", r"\bbasın açıklaması\b",
        r"\bkitlesel eylem\b",
    ),
    "Anti-Rep & Prisons": (
        r"\bpolitical prisoner", r"\bprisoner support\b",
        r"\bprison abolition\b", r"\bpolice raid\b",
        r"\bpolice violence\b", r"\bstate repression\b",
        r"\bsolitary confinement\b", r"\banti[- ]?repression\b",
        r"\bcezaevi direnişi\b", r"\bpolis şiddeti\b",
    ),
    "Cyberactivism": (
        r"\bdigital surveillance\b", r"\bstate surveillance\b",
        r"\bdigital repression\b", r"\binternet shutdown\b",
        r"\bdata protection\b", r"\bfree software\b",
    ),
    "No War": (
        r"\banti[- ]?war movement\b", r"\bwar resistance\b",
        r"\bconscientious object", r"\bmilitary occupation\b",
        r"\barms shipment\b", r"\bweapons export\b",
        r"\bceasefire now\b", r"\bsavaş karşıtı\b", r"\bvicdani ret\b",
    ),
    "Animal Liberation": (
        r"\banimal liberation front\b", r"\bfactory farming\b",
        r"\banimal exploitation\b", r"\bslaughterhouse blockade\b",
        r"\bhayvan özgürleş",
    ),
    "Eco-Anarchism": (
        r"\bclimate justice\b", r"\becological crisis\b",
        r"\benvironmental justice\b", r"\bforest occupation\b",
        r"\banti[- ]?mining\b", r"\bfossil infrastructure\b",
        r"\biklim adaleti\b", r"\bekolojik yıkım\b",
    ),
    "Indigenous Struggles": (
        r"\bindigenous sovereignty\b", r"\bindigenous resistance\b",
        r"\bland back\b", r"\btribal sovereignty\b",
        r"\bnative land\b", r"\byerli halkların\b",
    ),
    "Radical Health & Disability": (
        r"\bdisability justice\b", r"\bmad pride\b",
        r"\bpsychiatric abolition\b", r"\bcollective access\b",
        r"\bhealth workers? strike\b", r"\bsağlık emekçi",
    ),
    "Libraries": (
        r"\banarchist archive\b", r"\binfoshop\b",
        r"\bradical librar", r"\bmovement archive\b",
    ),
    "Movement News": (),
}

TOPIC_CATEGORY_MIN_SCORES = {
    "Labor Struggles": 4.2,
    "Queer-Feminism": 4.3,
    "Theory & Strategy": 4.7,
    "Demonstrations": 4.4,
    "Anti-Rep & Prisons": 4.5,
    "No War": 4.5,
    "Radical Health & Disability": 4.5,
}
TOPIC_DEFAULT_MIN_SCORE = 4.0
TOPIC_MAX_ASSIGNMENTS = 3
# Some outlets are explicitly scoped to a movement field (for example
# Anarchist Black Cross prison-support groups). Their source profile remains a
# valid fallback, while broad magazines still require evidence in the article.
TOPIC_SOURCE_FALLBACKS = {
    "Anti-Rep & Prisons",
    "Indigenous Struggles",
    "Animal Liberation",
    "Libraries",
}


def score_article_topics(title, content, configured, primary, source_tags=None):
    configured_list = [
        safe_text(category)
        for category in (configured if isinstance(configured, list) else [configured])
        if safe_text(category)
    ]
    title_text = safe_text(title).casefold()
    content_text = safe_text(content)[:16000].casefold()
    tags_text = " ".join(
        safe_text(tag.get("term") if isinstance(tag, dict) else tag)
        for tag in (source_tags or [])
    ).casefold()
    regex_cache = globals().setdefault("_WRN_TOPIC_REGEX_CACHE", {})

    def compiled(pattern):
        return regex_cache.setdefault(
            pattern,
            re.compile(pattern, flags=re.IGNORECASE),
        )

    def combined(patterns):
        if not patterns:
            return None
        return compiled("(?:" + ")|(?:".join(patterns) + ")")

    def occurrences(regex, value, limit=3):
        if regex is None or not value:
            return 0
        count = 0
        for _ in regex.finditer(value):
            count += 1
            if count >= limit:
                break
        return count

    scores = {}
    for category, patterns in TOPIC_CATEGORY_PATTERNS.items():
        if category == "Movement News":
            continue
        score = 0.0
        if category in configured_list:
            score += 0.75
        if category == primary:
            score += 0.75
        general_regex = combined(patterns)
        if general_regex and general_regex.search(title_text):
            score += 3.25
        if general_regex and tags_text and general_regex.search(tags_text):
            score += 2.5
        content_hits = occurrences(general_regex, content_text, limit=5)
        if content_hits:
            score += 1.55 + (content_hits - 1) * 0.65

        strong_regex = combined(
            TOPIC_CATEGORY_STRONG_PATTERNS.get(category, ())
        )
        if strong_regex and strong_regex.search(title_text):
            score += 5.5
        if strong_regex and tags_text and strong_regex.search(tags_text):
            score += 4.0
        content_hits = occurrences(strong_regex, content_text)
        if content_hits:
            score += 3.0 + (content_hits - 1) * 0.9
        if score:
            scores[category] = round(score, 2)
    return scores


def classify_article(
    title,
    content,
    configured,
    primary,
    source_tags=None,
    origin_country_code="",
):
    configured_list = [
        safe_text(category)
        for category in (configured if isinstance(configured, list) else [configured])
        if safe_text(category)
    ]
    configured_regions = [
        category for category in configured_list
        if category in REGION_CATEGORIES
    ]
    country_region = COUNTRY_PRIMARY_REGIONS.get(
        safe_text(origin_country_code).upper()
    )
    non_global_regions = [
        category for category in configured_regions
        if category != "Global"
    ]
    primary_region = (
        country_region
        or (primary if primary in REGION_CATEGORIES and primary != "Global" else "")
        or (non_global_regions[0] if non_global_regions else "")
        or (primary if primary in REGION_CATEGORIES else "")
        or (configured_regions[0] if configured_regions else "")
        or "Global"
    )
    categories = [primary_region]

    scores = score_article_topics(
        title,
        content,
        configured_list,
        primary,
        source_tags,
    )
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best_score = ranked[0][1] if ranked else 0.0
    matched_topics = [
        category
        for category, score in ranked
        if (
            score >= TOPIC_CATEGORY_MIN_SCORES.get(
                category,
                TOPIC_DEFAULT_MIN_SCORE,
            )
            and score >= best_score - 1.6
        )
    ][:TOPIC_MAX_ASSIGNMENTS]

    for category in matched_topics:
        if category not in categories:
            categories.append(category)

    assignment_method = "content"
    if not matched_topics:
        # A source profile is only a weak prior. If title, tags and body do not
        # substantiate a topic, assigning every item from a specialised outlet
        # to that topic produces misleading sections (for example culture
        # reviews from a feminist magazine). Keep such items discoverable in
        # Movement News instead of inventing topical certainty.
        configured_topics = [
            category for category in configured_list
            if category in TOPIC_SOURCE_FALLBACKS
        ]
        fallback = (
            primary
            if primary in TOPIC_SOURCE_FALLBACKS
            else configured_topics[0] if len(configured_topics) == 1 else ""
        )
        if fallback:
            categories.append(fallback)
            matched_topics = [fallback]
            assignment_method = "specialised-source"
        else:
            categories.append("Movement News")
            matched_topics = ["Movement News"]
            assignment_method = "editorial-review"

    primary_topic = matched_topics[0]
    secondary_topics = matched_topics[1:]
    best_topic_score = float(scores.get(primary_topic, 0.0))
    if assignment_method == "content":
        confidence = max(0.58, min(0.98, best_topic_score / 8.0))
    elif assignment_method == "specialised-source":
        confidence = 0.58
    else:
        confidence = 0.35

    review_reasons = []
    if confidence < 0.6:
        review_reasons.append("low-topic-confidence")
    if primary_region == "Global" and safe_text(origin_country_code):
        review_reasons.append("country-without-region-map")
    if primary_topic == "Movement News":
        review_reasons.append("no-specific-topic-evidence")

    return {
        "categories": categories,
        "primaryRegion": primary_region,
        "primaryTopic": primary_topic,
        "secondaryTopics": secondary_topics,
        "classificationConfidence": round(confidence, 3),
        "classificationMethod": assignment_method,
        "topicScores": {
            key: value for key, value in ranked[:6]
        },
        "editorialReview": bool(review_reasons),
        "editorialReviewReasons": review_reasons,
    }


def infer_article_categories(
    title,
    content,
    configured,
    primary,
    source_tags=None,
    origin_country_code="",
):
    return classify_article(
        title,
        content,
        configured,
        primary,
        source_tags,
        origin_country_code,
    )["categories"]


GANCIO_EVENT_DATE_RE = re.compile(
    r"^\[(?P<date>\d{4}-\d{2}-\d{2})(?:[ T][^\]]+)?\]\s*"
)


def normalize_feed_event(title, published):
    clean_title = safe_text(title, "Termin ohne Titel")
    match = GANCIO_EVENT_DATE_RE.match(clean_title)
    if not match:
        return clean_title, safe_text(
            published,
            datetime.now().isoformat(),
        )
    return (
        GANCIO_EVENT_DATE_RE.sub("", clean_title).strip() or clean_title,
        f"{match.group('date')}T12:00:00Z",
    )


def repair_overbroad_archive_categories(article):
    if article.get("kontinent") == "Radar":
        return article
    current = article.get("categories", [article.get("kontinent", "Global")])
    current = current if isinstance(current, list) else [current]
    topic_count = sum(
        1 for category in current if category in TOPIC_CATEGORY_PATTERNS
    )
    if topic_count >= 3:
        article["categories"] = infer_article_categories(
            article.get("title"),
            article.get("content"),
            current,
            article.get("kontinent", "Global"),
        )
    return article


def content_is_incomplete(text, min_length=350):
    clean = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    try:
        required_length = max(350, int(min_length or 350))
    except (TypeError, ValueError):
        required_length = 350
    if len(clean) < required_length:
        return True
    return any(marker in clean for marker in INCOMPLETE_MARKERS)


def incomplete_limit_for_source(source_name):
    normalized = str(source_name or "").strip().lower()
    for source_fragment, limit in INCOMPLETE_SOURCE_LIMITS.items():
        if source_fragment in normalized:
            return limit
    return MAX_INCOMPLETE_PER_SOURCE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
AUTONOMOUS_TIMEOUT = (8.0, 15.0) 

retry_strategy = Retry(total=2, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
adapter = HTTPAdapter(max_retries=retry_strategy)

http = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
http.mount("https://", adapter)
http.mount("http://", adapter)

session = requests.Session()
session.mount("https://", adapter)

RADAR_API_URL = "https://radar.squat.net/api/1.2/search/events.json"
RADAR_API_FIELDS = ",".join((
    "body",
    "category",
    "date_time",
    "image",
    "price",
    "link",
    "offline",
    "offline:address",
    "offline:map",
    "offline:timezone",
    "topic",
    "title",
    "language",
    "url",
    "created",
    "uuid",
))

LAYOUT_FILES = ['logo.png', 'logo.jpg', 'logo.svg', 'banner', 'favicon', 'sidebar', 'footer', 'avatar', 'pixel', 'nav_', 'blank.gif', 'spacer.gif']
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')

def clean_image_url(url, base_url):
    if not url: return None
    full_url = urljoin(base_url, url)
    filename = full_url.split('/')[-1].lower()
    if any(kw in filename for kw in LAYOUT_FILES): return None
    if any(kw in full_url.lower() for kw in ['/themes/', '/plugins/', '/assets/']): return None
    return full_url


def collect_image_urls(soup, base_url, limit=24):
    images = []
    if not soup:
        return images
    for image in soup.find_all('img'):
        width = safe_text(image.get('width'))
        height = safe_text(image.get('height'))
        if width.isdigit() and int(width) < 180:
            continue
        if height.isdigit() and int(height) < 100:
            continue
        src = (
            image.get('data-src')
            or image.get('data-lazy-src')
            or image.get('data-original')
            or image.get('data-lazy')
            or image.get('src')
        )
        srcset = safe_text(image.get('data-srcset') or image.get('srcset'))
        if srcset:
            srcset_candidates = [
                part.strip().split(' ')[0]
                for part in srcset.split(',')
                if part.strip()
            ]
            if srcset_candidates:
                src = srcset_candidates[-1]
        candidate = clean_image_url(src, base_url)
        if candidate and candidate.startswith(('http://', 'https://')) and candidate not in images:
            images.append(candidate)
        if len(images) >= limit:
            break
    return images


DEFAULT_ARTICLE_SELECTORS = (
    "[itemprop='articleBody']",
    ".article-content",
    ".entry-content",
    ".post-content",
    ".story-content",
    ".article-body",
    "article",
    "main",
)


def select_article_root(soup, configured_selectors=None):
    selectors = [
        safe_text(selector)
        for selector in (configured_selectors or [])
        if safe_text(selector)
    ]
    for selector in (*selectors, *DEFAULT_ARTICLE_SELECTORS):
        try:
            candidate = soup.select_one(selector)
        except Exception:
            candidate = None
        if candidate and len(candidate.get_text(" ", strip=True)) >= 250:
            return candidate
    return soup


def extract_article_text(root):
    if not root:
        return ""
    for unwanted in root.select(
        "script, style, nav, footer, aside, form, noscript, "
        ".newsletter, .related, .recommended, .social-share, .advertisement"
    ):
        unwanted.decompose()
    paragraphs = [
        paragraph.get_text(" ", strip=True)
        for paragraph in root.find_all(("p", "li"))
    ]
    text_blocks = [
        paragraph
        for paragraph in paragraphs
        if len(paragraph) > 30
    ]
    return "\n\n".join(text_blocks)


def scrape_article_page(
    link,
    feed,
    existing_text="",
    existing_image="",
    existing_images=None,
):
    """Load a publisher page once and preserve its full text and media."""

    full_text = safe_text(existing_text)
    image_url = clean_image_url(existing_image, link)
    image_urls = list(existing_images or [])

    try:
        time.sleep(1.5)
        html_req = http.get(
            link,
            headers=HEADERS,
            timeout=AUTONOMOUS_TIMEOUT,
        )
        html_req.raise_for_status()
        soup = BeautifulSoup(html_req.text, "html.parser")
        article_root = select_article_root(
            soup,
            feed.get("articleSelectors"),
        )

        for candidate in collect_image_urls(article_root, link):
            if candidate not in image_urls:
                image_urls.append(candidate)

        if not image_url:
            og_img = (
                soup.find("meta", property="og:image")
                or soup.find("meta", attrs={"name": "twitter:image"})
            )
            if og_img:
                image_url = clean_image_url(
                    og_img.get("content"),
                    link,
                )
                if image_url and image_url not in image_urls:
                    image_urls.insert(0, image_url)

        if not image_url:
            for img in soup.find_all("img"):
                src = (
                    img.get("src")
                    or img.get("data-src")
                    or img.get("data-lazy-src")
                    or img.get("data-original")
                    or img.get("data-lazy")
                )
                image_url = clean_image_url(src, link)
                if image_url:
                    if image_url not in image_urls:
                        image_urls.append(image_url)
                    break

        page_text = extract_article_text(article_root)
        if len(page_text) > len(full_text):
            full_text = page_text

        waf_phrases = (
            "Please wait a moment while we ensure the security",
            "Protected by Anubis",
            "Enable JavaScript and cookies",
            "Verifying your browser before connecting",
            "Making sure you're not a bot",
        )
        if any(
            phrase.casefold() in full_text.casefold()
            for phrase in waf_phrases
        ):
            full_text = safe_text(existing_text)
    except Exception:
        return full_text, image_url, image_urls

    return full_text, image_url, image_urls


# =================================================================
# 1. ARCHIV LADEN (Das clevere Gedächtnis, das nie vergisst)
# =================================================================
archiv_dict = {}
gesehene_titel = set()

try:
    for archive_file in ('news.json', 'events.json'):
        if not os.path.exists(archive_file):
            continue
        with open(archive_file, 'r', encoding='utf-8') as f:
            alter_stand = json.load(f)
            for art in alter_stand:
                # Nachrichten und Termine werden getrennt veröffentlicht, aber
                # für Deduplizierung gemeinsam in den Arbeitsspeicher geladen.
                if "link" in art:
                    archiv_dict[art['link']] = art
                    titel_clean = art.get('title', '').lower().strip()
                    gesehene_titel.add(titel_clean)
except Exception as e:
    print("Starte mit leerem Archiv (Erster Durchlauf).")

radar_count = 0 
TARGET_SOURCE_NAMES = {
    name.strip().casefold()
    for name in os.environ.get("WRN_NEWS_SOURCE_NAMES", "").split(",")
    if name.strip()
}
if "autostraddle news" in TARGET_SOURCE_NAMES:
    for archive_key, archive_item in list(archiv_dict.items()):
        if safe_lower(archive_item.get("quelleName")) == "autostraddle":
            archiv_dict.pop(archive_key, None)


def radar_terms(value):
    if not isinstance(value, list):
        return []
    return [
        safe_text(item.get("name"))
        for item in value
        if isinstance(item, dict) and safe_text(item.get("name"))
    ]


def radar_iso_date(raw_value):
    try:
        return datetime.fromtimestamp(
            int(str(raw_value)),
            tz=timezone.utc,
        ).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, OSError):
        return ""


def radar_image_url(event):
    image = event.get("image")
    if not isinstance(image, dict):
        return ""
    file_ref = image.get("file")
    if not isinstance(file_ref, dict):
        return ""
    uri = safe_text(file_ref.get("uri"))
    if not uri:
        return ""
    file_id = safe_text(file_ref.get("id"))
    filename = safe_text(file_ref.get("filename"))
    if file_id and filename:
        return (
            "https://radar.squat.net/sites/default/files/"
            f"styles/large/public/{filename}"
        )
    return ""


def radar_price_text(value):
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return safe_text(value)
    if isinstance(value, dict):
        parts = [
            safe_text(value.get(key))
            for key in ("value", "amount", "description", "summary")
        ]
        return " · ".join(part for part in parts if part)
    if isinstance(value, list):
        return " · ".join(
            part for part in (radar_price_text(item) for item in value) if part
        )
    return ""


def fetch_radar_events():
    """Fetch the current structured Radar.squat event search.

    Radar's public search already limits results to events whose end time is
    current or in the future. The global query provides the worldwide
    near-term window. Switzerland is additionally fetched as a complete
    country facet because its events otherwise disappear behind Radar's
    500-result global API limit. Results are merged by Radar's stable API id.
    """
    payloads = {}
    raw_results = {}
    queries = (
        ("global", {}),
        ("switzerland", {"facets[country][]": "CH"}),
    )
    for query_name, extra_params in queries:
        response = session.get(
            RADAR_API_URL,
            params={
                "limit": 500,
                "fields": RADAR_API_FIELDS,
                **extra_params,
            },
            headers={
                **HEADERS,
                "Accept": "application/json",
            },
            timeout=(10, 65),
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("result")
        if not isinstance(result, dict):
            raise ValueError(
                f"Radar API returned no result object for {query_name}."
            )
        payloads[query_name] = payload
        raw_results.update(result)

    global_payload = payloads["global"]
    swiss_payload = payloads["switzerland"]

    fetched = []
    for api_id, event in raw_results.items():
        if not isinstance(event, dict):
            continue

        dates = event.get("date_time")
        if not isinstance(dates, list) or not dates:
            continue
        date_info = dates[0] if isinstance(dates[0], dict) else {}
        event_start = radar_iso_date(date_info.get("value"))
        event_end = radar_iso_date(date_info.get("value2"))
        if not event_start:
            continue

        locations = event.get("offline")
        location = (
            locations[0]
            if isinstance(locations, list)
            and locations
            and isinstance(locations[0], dict)
            else {}
        )
        address = location.get("address")
        if not isinstance(address, dict):
            address = {}
        map_data = location.get("map")
        if not isinstance(map_data, dict):
            map_data = {}

        body = event.get("body")
        body_html = (
            safe_text(body.get("value"))
            if isinstance(body, dict)
            else safe_text(body)
        )
        content = BeautifulSoup(
            body_html,
            "html.parser",
        ).get_text(separator="\n\n").strip()
        if not content:
            content = "Weitere Informationen auf der Radar.squat-Originalseite."

        title = safe_text(event.get("title"), "Termin ohne Titel")
        canonical_url = safe_text(
            event.get("url"),
            f"https://radar.squat.net/en/node/{api_id}",
        )
        categories = radar_terms(event.get("category"))
        topics = radar_terms(event.get("topic"))
        language = safe_lower(event.get("language"), "und")
        venue = safe_text(address.get("name_line"), safe_text(location.get("title")))
        city = safe_text(address.get("locality"))
        country = safe_text(address.get("country")).upper()
        street = safe_text(address.get("thoroughfare"))
        postal = safe_text(address.get("postal_code"))
        external_links = [
            safe_text(item.get("url"))
            for item in event.get("link", [])
            if isinstance(item, dict) and safe_text(item.get("url"))
        ]

        fetched.append({
            "kontinent": "Radar",
            "categories": ["Radar"],
            "quelleName": "Radar.squat",
            "author": "Radar.squat",
            "title": title,
            "link": canonical_url,
            "pubDate": event_start,
            "content": content,
            "contentComplete": True,
            "image": radar_image_url(event),
            "language": language,
            "languages": [language],
            "sourceType": "radar-api",
            "eventApiId": safe_text(api_id),
            "eventUuid": safe_text(event.get("uuid")),
            "eventStart": event_start,
            "eventEnd": event_end or event_start,
            "eventTimezone": safe_text(location.get("timezone")),
            "eventCountry": country,
            "eventCity": city,
            "eventVenue": venue,
            "eventAddress": street,
            "eventPostal": postal,
            "eventLatitude": safe_text(map_data.get("lat")),
            "eventLongitude": safe_text(map_data.get("lon")),
            "eventCategories": categories,
            "eventTags": topics,
            "eventGroups": [],
            "eventPrice": radar_price_text(event.get("price")),
            "eventExternalLinks": external_links,
            "eventRecurrence": safe_text(date_info.get("rrule")),
            "sourceHomepage": "https://radar.squat.net",
        })

    fetched.sort(key=lambda item: item.get("eventStart", ""))
    return fetched, {
        "reportedCount": int(global_payload.get("count") or len(fetched)),
        "switzerlandReportedCount": int(
            swiss_payload.get("count") or 0
        ),
        "loadedCount": len(fetched),
        "facets": (
            global_payload.get("facets")
            if isinstance(global_payload.get("facets"), dict)
            else {}
        ),
    }


try:
    if TARGET_SOURCE_NAMES:
        raise LookupError("targeted-news-refresh")
    radar_events, radar_metadata = fetch_radar_events()
    # Replace stale Radar/API rows on every successful run. Non-Radar event
    # feeds remain intact and are refreshed by the normal loop below.
    for archive_key, archive_item in list(archiv_dict.items()):
        old_source = safe_lower(archive_item.get("quelleName"))
        old_link = safe_lower(archive_item.get("link"))
        if (
            archive_item.get("sourceType") in {"radar-api", "radar-api-meta"}
            or old_source.startswith("radar squat.net")
            or (
                archive_item.get("kontinent") == "Radar"
                and "radar.squat.net" in old_link
            )
        ):
            archiv_dict.pop(archive_key, None)
    for radar_event in radar_events:
        archiv_dict[radar_event["link"]] = radar_event
    radar_count = len(radar_events)
    print(
        "\n--- Radar.squat API ---\n"
        f"  [OK] {radar_count} aktuelle Termine geladen "
        f"(global bis zu 500 von {radar_metadata['reportedCount']}; "
        f"Schweiz vollständig {radar_metadata['switzerlandReportedCount']})."
    )
except Exception as radar_error:
    if TARGET_SOURCE_NAMES:
        radar_count = sum(
            1
            for archive_item in archiv_dict.values()
            if (
                archive_item.get("sourceType") == "radar-api"
                or safe_lower(archive_item.get("quelleName")).startswith(
                    "radar squat.net"
                )
            )
        )
        print(
            "\n--- Radar.squat API ---\n"
            "  [ÜBERSPRUNGEN] Gezielte Nachrichten-Aktualisierung; "
            f"{radar_count} vorhandene Termine bleiben erhalten."
        )
    else:
        print(
            "\n--- Radar.squat API ---\n"
            "  [FEHLER] Strukturierter Abruf fehlgeschlagen; "
            f"bestehende Radar-Termine bleiben erhalten: {radar_error}"
        )

# HILFSFUNKTION: CHECKPOINTS SPEICHERN (Sicherheit gegen Abstürze)
def save_checkpoint():
    alle = list(archiv_dict.values())
    try:
        # Sortieren nach Datum
        alle.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
    except:
        pass
    
    events = [item for item in alle if item.get('kontinent') == 'Radar']
    try:
        events.sort(
            key=lambda item: (
                item.get("eventStart")
                or item.get("pubDate")
                or ""
            )
        )
    except Exception:
        pass
    events = events[:1000]
    news_candidates = [
        repair_overbroad_archive_categories(item)
        for item in alle
        if item.get('kontinent') != 'Radar'
    ]

    # Von abgeschnittenen Vorschautexten bleiben pro Quelle nur die aktuellsten
    # Einträge. So verdrängen Feeds mit ständigem „Read more“ keine Volltexte.
    incomplete_counts = {}
    news = []
    for article in news_candidates:
        source = str(article.get('quelleName') or 'Unbekannte Quelle')
        minimum_length = ARTICLE_MIN_LENGTHS.get(
            safe_lower(source),
            700,
        )
        incomplete = (
            article.get('contentComplete') is False
            or content_is_incomplete(
                article.get('content'),
                minimum_length,
            )
        )
        article['contentComplete'] = not incomplete
        if incomplete:
            count = incomplete_counts.get(source, 0)
            if count >= incomplete_limit_for_source(source):
                continue
            incomplete_counts[source] = count + 1
        news.append(article)
        if len(news) >= 2000:
            break

    with open('news.json', 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    with open('events.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


if os.environ.get("WRN_RADAR_ONLY", "").strip().lower() in {
    "1", "true", "yes", "on"
}:
    save_checkpoint()
    save_aggregate_error_report()
    print(
        "\n[ERFOLG] Radar.squat wurde separat aktualisiert: "
        f"{radar_count} strukturierte Termine."
    )
    raise SystemExit(0)

for kontinent, feeds in quellen.items():
    print(f"\n--- Kategorie: {kontinent} ---")
    is_radar = (kontinent == "Radar")
    
    for feed in feeds:
        if not isinstance(feed, dict):
            print(
                "  [FEHLER] Ungültiger Quellen-Eintrag "
                "übersprungen."
            )
            continue
        if (
            TARGET_SOURCE_NAMES
            and safe_lower(feed.get("name")) not in TARGET_SOURCE_NAMES
        ):
            continue

        feed_name = safe_text(
            feed.get("name"),
            "Unbekannte Quelle",
        )

        print(f"-> Portal: {feed_name}...")
        parsed = None
        try:
            feed_req = http.get(feed['url'], headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
            parsed = feedparser.parse(feed_req.text)
            if not parsed.entries:
                feed_req = session.get(feed['url'], headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
                parsed = feedparser.parse(feed_req.content)
        except:
            try:
                feed_req = session.get(feed['url'], headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
                parsed = feedparser.parse(feed_req.content)
            except:
                pass
                
        if not parsed or not parsed.entries:
            print(f"  [FEHLER] Konnte {feed_name} nicht abrufen.")
            continue
            
        limit = 100 if is_radar else 15
        
        # =========================================================
        # DAS NEUE SPEED-LIMIT (Macht den Code rasend schnell)
        # =========================================================
        MAX_NEUE_SCRAPES = max(
            1,
            int(feed.get("maxNewItems", 4)),
        )
        tiefe_scrapes_gemacht = 0
        attempted_links = set()

        for entry in parsed.entries[:limit]: 
            try:
                if not hasattr(entry, "get"):
                    raise TypeError(
                        "Feed-Eintrag unterstützt keine "
                        "get()-Abfragen."
                    )
                link = entry.get('link', '')
                title = safe_text(entry.get("title"), "Kein Titel")
                entry_published = entry.get(
                    'published',
                    entry.get('updated', datetime.now().isoformat()),
                )
                event_start = ""
                if is_radar:
                    title, event_start = normalize_feed_event(
                        title,
                        entry_published,
                    )
                title_lower = safe_lower(title).strip()
                author = safe_text(entry.get("author"), "Unknown")
                source_tags = entry.get("tags", [])
                minimum_article_length = int(
                    feed.get("minArticleTextLength", 700)
                )
            
                # Spam rausfiltern
                if any(bad in title_lower or bad in safe_lower(author) for bad in SPAM_BLACKLIST):
                    continue

                # IST DER ARTIKEL SCHON BEKANNT? (Ultraschnell überspringen!)
                existing_article = archiv_dict.get(link)
                if existing_article:
                    configured_categories = feed.get("categories", [kontinent])
                    if not isinstance(configured_categories, list):
                        configured_categories = [configured_categories]
                    existing_article["categories"] = infer_article_categories(
                        existing_article.get("title", ""),
                        existing_article.get("content", ""),
                        configured_categories,
                        kontinent,
                        source_tags,
                    )
                    for existing_key, configured_key in (
                        ("sourceHomepage", "homepage"),
                        ("originCountry", "originCountry"),
                        ("originCountryCode", "originCountryCode"),
                        ("originRegion", "originRegion"),
                    ):
                        configured_value = safe_text(
                            feed.get(configured_key)
                        )
                        if configured_value:
                            existing_article[existing_key] = (
                                configured_value
                            )
                    existing_article["sourceTags"] = [
                        safe_text(
                            tag.get("term")
                            if isinstance(tag, dict)
                            else tag
                        )
                        for tag in source_tags
                        if safe_text(
                            tag.get("term")
                            if isinstance(tag, dict)
                            else tag
                        )
                    ]
                    if is_radar:
                        existing_article["title"] = title
                        existing_article["pubDate"] = event_start
                        existing_article["eventStart"] = event_start
                        existing_article["eventEnd"] = event_start
                        existing_article["type"] = "event"
                        existing_article["sourceType"] = "rss-event"
                        radar_count += 1
                        continue
                    if not content_is_incomplete(
                        existing_article.get("content", ""),
                        minimum_article_length,
                    ):
                        existing_article["contentComplete"] = True
                        continue
                
                if (
                    not existing_article
                    and title_lower in gesehene_titel
                    and not is_radar
                ):
                    continue

                # Pro Quelle werden neue und unvollständige bestehende
                # Artikel gemeinsam begrenzt. So werden ältere Feed-Auszüge
                # schrittweise repariert, ohne die Quellseite zu überlasten.
                if not is_radar:
                    if tiefe_scrapes_gemacht >= MAX_NEUE_SCRAPES:
                        continue 
                    tiefe_scrapes_gemacht += 1
                    attempted_links.add(link)
            
                pubDate = event_start if is_radar else entry_published
                full_text = safe_text(
                    existing_article.get("content")
                    if existing_article
                    else ""
                )
                image_url = (
                    existing_article.get("image")
                    if existing_article
                    else None
                )
                image_urls = list(
                    existing_article.get("images", [])
                    if existing_article
                    and isinstance(existing_article.get("images"), list)
                    else []
                )

                if is_radar:
                    radar_desc = entry.get('summary', entry.get('description', ''))
                    full_text = BeautifulSoup(str(radar_desc), 'html.parser').get_text(separator="\n\n").strip()

                # Bilder abgreifen
                if 'media_content' in entry and len(entry.media_content) > 0:
                    image_url = clean_image_url(entry.media_content[0].get('url', ''), link)
                    if image_url:
                        image_urls.append(image_url)

                if not image_url and 'enclosures' in entry and len(entry.enclosures) > 0:
                    for enc in entry.enclosures:
                        href = safe_text(enc.get("href"))
                        if safe_text(enc.get("type")).startswith('image/') or any(ext in href.lower() for ext in IMAGE_EXTENSIONS):
                            image_url = clean_image_url(href, link)
                            if image_url:
                                image_urls.append(image_url)
                                break

                for content_key in ['description', 'summary']:
                    if content_key in entry and isinstance(entry[content_key], str):
                        desc_soup = BeautifulSoup(entry[content_key], 'html.parser')
                        for candidate in collect_image_urls(desc_soup, link):
                            if candidate not in image_urls:
                                image_urls.append(candidate)
                        if not image_url and image_urls:
                            image_url = image_urls[0]

                # Text extrahieren (Der langsame Teil - aber auf 4 Limitiert!)
                if not is_radar:
                    try:
                        if 'content' in entry and len(entry.content) > 0:
                            c_obj = entry.content[0]
                            val = c_obj.value if hasattr(c_obj, 'value') else (c_obj.get('value', '') if isinstance(c_obj, dict) else '')
                            content_soup = BeautifulSoup(str(val), 'html.parser')
                            for candidate in collect_image_urls(content_soup, link):
                                if candidate not in image_urls:
                                    image_urls.append(candidate)
                            if not image_url and image_urls:
                                image_url = image_urls[0]
                            feed_text = content_soup.get_text(separator="\n\n").strip()
                            if len(feed_text) > len(full_text):
                                full_text = feed_text
                    except:
                        pass

                if (
                    link
                    and not is_radar
                    and content_is_incomplete(
                        full_text,
                        minimum_article_length,
                    )
                ):
                    full_text, image_url, image_urls = (
                        scrape_article_page(
                            link,
                            feed,
                            full_text,
                            image_url,
                            image_urls,
                        )
                    )
            
                if not is_radar and (not full_text or len(full_text) < 150) and 'description' in entry:
                    try:
                        full_text = BeautifulSoup(str(entry.description), 'html.parser').get_text(separator="\n\n").strip()
                    except:
                        pass

                clean_text = safe_text(full_text)
            
                if any(bad in clean_text.casefold() for bad in SPAM_BLACKLIST):
                    continue
            
                if is_radar:
                    if clean_text == "":
                        clean_text = "Weitere Infos zum Termin auf der Originalseite."
                elif not is_radar and "anarchist news" not in safe_lower(feed_name) and safe_lower(title) in clean_text.casefold() and len(clean_text) < len(title) + 150:
                    clean_text = "⚠️ The full text of this article is protected by the publisher's firewall. Please use the [ ORIGINAL ] button below to read it directly on their website."
                elif not is_radar and clean_text == "":
                    clean_text = "⚠️ No text available. Please use the [ ORIGINAL ] button below."

                if not image_url or not image_url.startswith('http'):
                    image_url = ""
                image_urls = [
                    candidate
                    for candidate in image_urls
                    if candidate and candidate.startswith(('http://', 'https://'))
                ]
                if image_url and image_url not in image_urls:
                    image_urls.insert(0, image_url)

                allowed_image_hosts = {
                    safe_lower(host)
                    for host in feed.get("imageHosts", [])
                    if safe_text(host)
                }
                if allowed_image_hosts:
                    if image_url:
                        image_host = safe_lower(urlparse(image_url).hostname)
                        if image_host not in allowed_image_hosts:
                            image_url = ""
                    image_urls = [
                        candidate
                        for candidate in image_urls
                        if safe_lower(urlparse(candidate).hostname) in allowed_image_hosts
                    ]

                # =========================================================
                # ARTIKEL ZUM GEDÄCHTNIS HINZUFÜGEN
                # =========================================================
                classification = classify_article(
                    title,
                    clean_text,
                    feed.get("categories", [kontinent]),
                    kontinent,
                    source_tags,
                    feed.get("originCountryCode"),
                )
                feed_categories = classification["categories"]

                feed_languages = feed.get(
                    "languages",
                    [feed.get("language", "und")],
                )
                if not isinstance(feed_languages, list):
                    feed_languages = [feed_languages]
                feed_languages = [
                    safe_lower(language, "und")
                    for language in feed_languages
                    if safe_text(language)
                ] or ["und"]

                archiv_dict[link] = {
                    "kontinent": kontinent,
                    "categories": feed_categories,
                    "primaryRegion": classification["primaryRegion"],
                    "primaryTopic": classification["primaryTopic"],
                    "secondaryTopics": classification["secondaryTopics"],
                    "classificationConfidence": classification["classificationConfidence"],
                    "classificationMethod": classification["classificationMethod"],
                    "editorialReview": classification["editorialReview"],
                    "editorialReviewReasons": classification["editorialReviewReasons"],
                    "quelleName": feed_name,
                    "author": author,
                    "title": title,
                    "link": link,
                    "pubDate": pubDate,
                    "content": clean_text,
                    "contentComplete": True if is_radar else not content_is_incomplete(
                        clean_text,
                        minimum_article_length,
                    ),
                    "image": image_url,
                    "images": image_urls[:24],
                    "language": feed_languages[0],
                    "languages": feed_languages,
                    "originCountry": safe_text(feed.get("originCountry")),
                    "originCountryCode": safe_text(feed.get("originCountryCode")),
                    "originRegion": safe_text(feed.get("originRegion")),
                    "sourceHomepage": safe_text(feed.get("homepage")),
                    "sourceTags": [
                        safe_text(
                            tag.get("term")
                            if isinstance(tag, dict)
                            else tag
                        )
                        for tag in source_tags
                        if safe_text(
                            tag.get("term")
                            if isinstance(tag, dict)
                            else tag
                        )
                    ],
                }
                if is_radar:
                    archiv_dict[link].update({
                        "type": "event",
                        "sourceType": "rss-event",
                        "eventStart": event_start,
                        "eventEnd": event_start,
                    })
                gesehene_titel.add(title_lower)
                if is_radar: radar_count += 1
            except Exception as entry_error:
                log_feed_entry_error(
                    feed_name,
                    entry,
                    entry_error,
                )
                continue

        # Unvollständige ältere Artikel können aus dem aktuellen RSS-Fenster
        # herausfallen. Nutze freie Abrufplätze, um auch diese Archiv-Einträge
        # schrittweise zu reparieren, statt sie dauerhaft als Anreißer zu
        # belassen.
        if not is_radar and tiefe_scrapes_gemacht < MAX_NEUE_SCRAPES:
            minimum_article_length = int(
                feed.get("minArticleTextLength", 700)
            )
            repair_candidates = [
                (archive_link, article)
                for archive_link, article in archiv_dict.items()
                if (
                    safe_lower(article.get("quelleName"))
                    == safe_lower(feed_name)
                    and archive_link not in attempted_links
                    and content_is_incomplete(
                        article.get("content", ""),
                        minimum_article_length,
                    )
                )
            ]
            repair_candidates.sort(
                key=lambda pair: safe_text(
                    pair[1].get("pubDate")
                ),
                reverse=True,
            )
            for archive_link, article in repair_candidates:
                if tiefe_scrapes_gemacht >= MAX_NEUE_SCRAPES:
                    break
                tiefe_scrapes_gemacht += 1
                repaired_text, repaired_image, repaired_images = (
                    scrape_article_page(
                        archive_link,
                        feed,
                        article.get("content", ""),
                        article.get("image", ""),
                        article.get("images", []),
                    )
                )
                if len(repaired_text) > len(
                    safe_text(article.get("content"))
                ):
                    article["content"] = safe_text(repaired_text)
                if repaired_image:
                    article["image"] = repaired_image
                article["images"] = list(dict.fromkeys(
                    candidate
                    for candidate in repaired_images
                    if candidate
                ))[:24]
                article["contentComplete"] = not content_is_incomplete(
                    article.get("content", ""),
                    minimum_article_length,
                )
            
        # =========================================================
        # CHECKPOINT NACH JEDER QUELLE SPEICHERN (Sichert die Daten)
        # =========================================================
        save_checkpoint()

# SYSTEM-MELDUNG FALLS RADAR GESTÖRT IST
if radar_count == 0:
    archiv_dict["system_info_radar"] = {
        "kontinent": "Radar",
        "quelleName": "System Info",
        "author": "News-Bot",
        "title": "🛡️ Radar temporär blockiert",
        "link": "https://radar.squat.net",
        "pubDate": datetime.now().isoformat(),
        "content": "Die Terminkalender haben aktuell ihre Firewalls verschärft und blockieren den automatischen Abruf. Wir versuchen es beim nächsten Update-Durchlauf erneut. Bitte besuche die Seiten in der Zwischenzeit direkt über den Button unten.",
        "image": ""
    }
    save_checkpoint()

save_aggregate_error_report()

print(f"\n>>> ERFOLG: Es wurden {radar_count} Radar-Termine gefunden! <<<")
print(f"\n[ERFOLG] {len(archiv_dict)} Artikel sicher im Archiv abgelegt.")
