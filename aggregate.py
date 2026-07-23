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
        {"name": "Apatris (GR)", "url": "https://apatris.info/feed/"},
        {"name": "Alerta (GR)", "url": "https://www.alerta.gr/feed/"},
        {"name": "Infolibre (GR)", "url": "https://infolibre.gr/feed/"},
        {"name": "OmniaTV (GR)", "url": "https://omniatv.com/feed/"},
        {"name": "Antifa Infoblatt", "url": "https://www.antifainfoblatt.de/rss.xml"},
        {"name": "Freedom News", "url": "https://freedomnews.org.uk/feed/"},
        {"name": "Enough is Enough", "url": "https://enoughisenough14.org/feed/"},
        {"name": "A-Radio Berlin", "url": "https://www.aradio-berlin.org/feed/"},
        {"name": "A Las Barricadas (ES)", "url": "https://www.alasbarricadas.org/noticias/rss.xml"},
        {"name": "Umanita Nova (IT)", "url": "http://www.umanitanova.org/feed/"},
        {"name": "Federacja Anarchistyczna (PL)", "url": "https://federacja-anarchistyczna.pl/feed/"},
        {"name": "Antifa.cz", "url": "https://www.antifa.cz/rss.xml"},
        {"name": "Lower Class Magazine", "url": "https://lowerclassmag.com/feed/"},
        {"name": "Megafon Bern", "url": "https://megafon.ch/feed/"},
        {"name": "Anarchist Communist Group", "url": "https://www.anarchistcommunism.org/feed/"}
    ],
    "Africa": [
        {"name": "Pambazuka News", "url": "https://www.pambazuka.org/rss.xml"},
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
        {"name": "Kontrapolis (Berlin)", "url": "https://morss.it/https://kontrapolis.info/category/termine/feed/"},
        {"name": "Stressfaktor (Berlin)", "url": "https://morss.it/https://stressfaktor.squat.net/termine.rss"},
        {"name": "Paris-Luttes (Agenda FR)", "url": "https://morss.it/https://paris-luttes.info/spip.php?page=backend-agenda"},
        {"name": "Barrikade (CH)", "url": "https://morss.it/https://barrikade.info/spip.php?page=backend-breves"},
        {"name": "CrimethInc. (Events)", "url": "https://morss.it/https://crimethinc.com/categories/events/feed"}
    ],
    "Asia": [
        {"name": "Bulatlat (Philippines)", "url": "https://www.bulatlat.com/feed/"},
        {"name": "Rojava Info Center", "url": "https://rojavainformationcenter.org/feed/"},
        {"name": "ANF English (Kurdistan)", "url": "https://anfenglish.com/rss"},
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
        {"name": "Mutiny Blog", "url": "https://mu-tiny.blogspot.com/feeds/posts/default"},
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
        {"name": "Libcom (Workplace)", "url": "https://libcom.org/workplace/feed"},
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
        {"name": "Gods & Radicals", "url": "https://abeautifulresistance.org/site?format=rss"},
        {"name": "Anarkismo (Gender)", "url": "http://www.anarkismo.net/backend?topic=gender"},
        {"name": "Jineolojî Academy", "url": "https://jineoloji.org/en/feed/"},
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
        {"name": "Enough is Enough", "url": "https://enoughisenough14.org/feed/"},
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
        {"name": "Solidarity Network", "url": "https://enoughisenough14.org/feed/"},
        {"name": "BOAK (RU)", "url": "https://boak.noblogs.org/feed/"},
        {"name": "SoliNetz", "url": "https://solinetz.ch/feed/"}
    ],
    "Cyberactivism": [
        {"name": "Riseup Networks", "url": "https://riseup.net/en/feed"},
        {"name": "Systemli", "url": "https://www.systemli.org/feed.xml"},
        {"name": "Autistici/Inventati", "url": "https://www.autistici.org/feed/"},
        {"name": "Nadir.org", "url": "https://www.nadir.org/nadir/aktuell/rss/nadir.xml"},
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
        {"name": "VGT Schweiz", "url": "https://vgt.ch/news/rss.xml"},
        {"name": "Direct Action Everywhere (DxE)", "url": "https://www.directactioneverywhere.com/rss.xml"}
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
        {"name": "Anarchistische Bibliothek (DE)", "url": "https://anarchistischebibliothek.org/feed"},
        {"name": "The Anarchist Library (EN)", "url": "https://theanarchistlibrary.org/feed"},
        {"name": "Biblioteca Anarquista (ES)", "url": "https://es.theanarchistlibrary.org/feed"},
        {"name": "Bibliothèque Anarchiste (FR)", "url": "https://fr.theanarchistlibrary.org/feed"},
        {"name": "Libreria Anarchica (IT)", "url": "https://it.theanarchistlibrary.org/feed"},
        {"name": "Biblioteca Anarquista (PT)", "url": "https://pt.theanarchistlibrary.org/feed"},
        {"name": "Anarchist Library (RU)", "url": "https://ru.theanarchistlibrary.org/feed"},
        {"name": "Anarchist Library (TR)", "url": "https://tr.theanarchistlibrary.org/feed"},
        {"name": "Anarchist Library (PL)", "url": "https://pl.theanarchistlibrary.org/feed"},
        {"name": "Anarchist Library (SV)", "url": "https://sv.theanarchistlibrary.org/feed"},
        {"name": "RevoltLib", "url": "https://revoltlib.com/feed"},
        {"name": "Sprout Distro", "url": "https://www.sproutdistro.com/feed/"},
        {"name": "Zabalaza Books (Africa)", "url": "https://zabalazabooks.net/feed/"},
        {"name": "Libcom Library", "url": "https://libcom.org/library/feed"}
    ]
}
# WRN MULTILINGUAL SOURCES 1.8.2 START
# Additive and idempotent: the existing source dictionary is never replaced.
_wrn_extra_sources_182 = [{'name': 'Graswurzelrevolution', 'kind': 'news', 'adapter': 'rss', 'languages': ['de'], 'homepage': 'https://www.graswurzel.net/gwr/', 'feedUrl': 'https://www.graswurzel.net/gwr/feed/', 'categories': ['Europe', 'No War', 'Anarchism'], 'status': 'approved'}, {'name': 'Agência Pública', 'kind': 'news', 'adapter': 'rss', 'languages': ['pt'], 'homepage': 'https://apublica.org/', 'feedUrl': 'https://apublica.org/feed/', 'categories': ['Latin America', 'Environment', 'Investigative'], 'status': 'approved'}, {'name': 'Bianet Türkçe', 'kind': 'news', 'adapter': 'rss', 'languages': ['tr'], 'homepage': 'https://bianet.org/', 'feedUrl': 'https://bianet.org/rss/bianet', 'categories': ['Europe', 'Labor Struggles', 'Antiracism', 'Queer-Feminism'], 'originCountry': 'Türkiye', 'originCountryCode': 'TR', 'originRegion': 'Türkiye', 'status': 'approved', 'addedIn': '1.8.2'}, {'name': 'Evrensel', 'kind': 'news', 'adapter': 'rss', 'languages': ['tr'], 'homepage': 'https://www.evrensel.net/', 'feedUrl': 'https://www.evrensel.net/rss/?do=rss', 'categories': ['Europe', 'Labor Struggles', 'Anticapitalism', 'No War'], 'originCountry': 'Türkiye', 'originCountryCode': 'TR', 'originRegion': 'Türkiye', 'status': 'approved', 'addedIn': '1.8.2'}, {'name': 'Bianet Kurdî', 'kind': 'news', 'adapter': 'rss', 'languages': ['ku'], 'homepage': 'https://bianet.org/kurdi', 'feedUrl': 'https://bianet.org/rss/kurdi', 'categories': ['Europe', 'Anticolonialism', 'Antiracism', 'No Borders'], 'originCountry': 'Türkiye', 'originCountryCode': 'TR', 'originRegion': 'Türkiye', 'status': 'approved', 'addedIn': '1.8.2'}, {'name': 'Pressin Kurdî', 'kind': 'news', 'adapter': 'rss', 'languages': ['ku'], 'homepage': 'https://pressin.info/kurdi', 'feedUrl': 'https://pressin.info/kurdi/rss/latest-posts', 'categories': ['Asia', 'Anticolonialism', 'Anti-Imperialism'], 'originCountry': 'Iraq', 'originCountryCode': 'IQ', 'originRegion': 'Kurdistan Region', 'status': 'approved', 'addedIn': '1.8.2'}]
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
TOPIC_CATEGORY_PATTERNS = {
    "Labor Struggles": (
        r"\bstrike\b", r"\bstrikers?\b", r"\bworkers?\b", r"\btrade union\b",
        r"\blabou?r\b", r"\bunionis", r"\bstreik", r"\barbeiter", r"\bgewerkschaft",
        r"\bgr[eè]ve", r"\bsyndicat", r"\bhuelga", r"\bsindicat", r"\bgrev",
    ),
    "Antifascism": (
        r"\banti[- ]?fasc", r"\bfascis", r"\bneo[- ]?nazi", r"\bfar[- ]right\b",
        r"\bextreme droite\b", r"\bextrema derecha\b", r"\bultradestra\b",
        r"\brechtsextrem", r"\bafd\b",
    ),
    "Antisexism": (
        r"\bsexism", r"\bmisogyn", r"\bpatriarch", r"\bsexual violence\b",
        r"\bsexual assault\b", r"\bharassment\b", r"\bsexismus", r"\bviolaci[oó]n",
        r"\bviolence sexuelle\b", r"\bviolenza sessuale\b",
    ),
    "Queer-Feminism": (
        r"\bqueer\b", r"\blgbt", r"\btrans(?:gender|phob| rights?)?\b",
        r"\blesbian", r"\bhomophob", r"\bfeminis", r"\bnon[- ]?binary\b",
    ),
    "Antiracism": (
        r"\banti[- ]?rac", r"\bracis", r"\bwhite supremacy\b",
        r"\bxenophob", r"\bapartheid\b", r"\brassismus\b",
    ),
    "No Borders": (
        r"\bmigran", r"\brefugee", r"\basylum\b", r"\bborder", r"\bdeport",
        r"\bimmigration\b", r"\bfl[uü]cht", r"\babschieb", r"\br[eé]fugi",
    ),
    "Anticapitalism": (
        r"\banti[- ]?capital", r"\bcapitalis", r"\bclass struggle\b",
        r"\bworking class\b", r"\bneoliberal", r"\bkapitalis", r"\bcapitalismo\b",
    ),
    "Theory & Strategy": (
        r"\banarchis", r"\blibertarian communis", r"\bmutual aid\b",
        r"\bdirect action\b", r"\bsyndicalis", r"\bpolitical theory\b",
        r"\brevolutionary strateg", r"\bbook review\b",
    ),
    "Anticolonialism": (
        r"\banti[- ]?coloni", r"\bdecoloni", r"\bcolonialis",
        r"\bsettler colon", r"\bcolonial rule\b",
    ),
    "Anti-Imperialism": (
        r"\banti[- ]?imperial", r"\bimperialis", r"\bimperial power\b",
    ),
    "Squatting & Housing": (
        r"\bsquat", r"\bhousing\b", r"\btenant", r"\brent strike\b",
        r"\beviction", r"\bhausbesetz", r"\bmiet", r"\blogement\b",
    ),
    "Demonstrations": (
        r"\bprotest", r"\bdemonstrat", r"\brally\b", r"\bmarch\b",
        r"\bmobilis", r"\bkundgebung", r"\bmanifestaci[oó]n\b",
    ),
    "Anti-Rep & Prisons": (
        r"\bprison", r"\bpolice\b", r"\barrest", r"\brepress",
        r"\bdetention\b", r"\bincarcer", r"\bpolitical prisoner",
        r"\bcourt\b", r"\btrial\b", r"\bknast\b", r"\bgef[aä]ng",
    ),
    "Cyberactivism": (
        r"\bcyber", r"\bdigital rights?\b", r"\bsurveillance\b", r"\bencryption\b",
        r"\bhack(?:er|ing)?\b", r"\bprivacy\b", r"\bopen[- ]source\b",
    ),
    "No War": (
        r"\banti[- ]?war\b", r"\bwar\b", r"\bmilitar", r"\barmy\b",
        r"\bweapons?\b", r"\bconscription\b", r"\bceasefire\b", r"\bkrieg",
        r"\baufr[uü]st", r"\barmement\b",
    ),
    "Animal Liberation": (
        r"\banimal liberation\b", r"\banimal rights?\b", r"\bvegan",
        r"\bslaughterhouse\b", r"\bhunt sab", r"\btierbefrei", r"\bvivisection\b",
    ),
    "Eco-Anarchism": (
        r"\bclimate\b", r"\becolog", r"\benvironment", r"\bforest\b",
        r"\bpipeline\b", r"\bfossil fuel", r"\bmining\b", r"\bklima",
    ),
    "Indigenous Struggles": (
        r"\bindigenous\b", r"\bfirst nations?\b", r"\bnative peoples?\b",
        r"\bmapuche\b", r"\bzapatist", r"\baboriginal\b", r"\bindigen",
    ),
    "Radical Health & Disability": (
        r"\bdisabil", r"\bmental health\b", r"\bpsychiatr", r"\bhealth care\b",
        r"\bhealthcare\b", r"\bclinic\b", r"\bableis", r"\bbehinder",
    ),
    "Libraries": (
        r"\banarchist librar", r"\bbiblioth[eè]que anarch", r"\bbiblioteca anarqu",
        r"\banarchistische bibliothek\b",
    ),
}


def infer_article_categories(title, content, configured, primary):
    configured_list = [
        safe_text(category)
        for category in (configured if isinstance(configured, list) else [configured])
        if safe_text(category)
    ]
    text = f"{safe_text(title)} {safe_text(content)}".casefold()
    categories = []
    for category in configured_list:
        if category in REGION_CATEGORIES and category not in categories:
            categories.append(category)
    if primary in REGION_CATEGORIES and primary not in categories:
        categories.append(primary)

    matched_topics = []
    for category, patterns in TOPIC_CATEGORY_PATTERNS.items():
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            matched_topics.append(category)

    for category in matched_topics:
        if category not in categories:
            categories.append(category)

    configured_topics = [
        category for category in configured_list
        if category in TOPIC_CATEGORY_PATTERNS
    ]
    if not matched_topics:
        fallback = primary if primary in TOPIC_CATEGORY_PATTERNS else (
            configured_topics[0] if len(configured_topics) == 1 else ""
        )
        if fallback and fallback not in categories:
            categories.append(fallback)
    return categories or [safe_text(primary, "Global")]


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


def content_is_incomplete(text):
    clean = re.sub(r"\s+", " ", str(text or "")).strip().lower()
    if len(clean) < 350:
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
        incomplete = article.get('contentComplete') is False or content_is_incomplete(article.get('content'))
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
        MAX_NEUE_SCRAPES = 4 # Maximal 4 tief recherchierte Artikel pro Quelle!
        tiefe_scrapes_gemacht = 0

        for entry in parsed.entries[:limit]: 
            try:
                if not hasattr(entry, "get"):
                    raise TypeError(
                        "Feed-Eintrag unterstützt keine "
                        "get()-Abfragen."
                    )
                link = entry.get('link', '')
                title = safe_text(entry.get("title"), "Kein Titel")
                title_lower = safe_lower(title).strip()
                author = safe_text(entry.get("author"), "Unknown")
            
                # Spam rausfiltern
                if any(bad in title_lower or bad in safe_lower(author) for bad in SPAM_BLACKLIST):
                    continue

                # IST DER ARTIKEL SCHON BEKANNT? (Ultraschnell überspringen!)
                if link in archiv_dict:
                    existing_article = archiv_dict[link]
                    configured_categories = feed.get("categories", [kontinent])
                    if not isinstance(configured_categories, list):
                        configured_categories = [configured_categories]
                    existing_categories = existing_article.get("categories", [])
                    if not isinstance(existing_categories, list):
                        existing_categories = [existing_categories]
                    existing_article["categories"] = list(dict.fromkeys(
                        [
                            safe_text(category)
                            for category in (
                                existing_categories
                                + configured_categories
                            )
                            if safe_text(category)
                        ]
                    ))
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
                    if is_radar: radar_count += 1
                    continue
                
                if title_lower in gesehene_titel and not is_radar:
                    continue

                # SPEED-LIMIT CHECK FÜR KOMPLETT NEUE ARTIKEL
                if not is_radar:
                    if tiefe_scrapes_gemacht >= MAX_NEUE_SCRAPES:
                        # Wir haben die 4 neuesten Artikel dieser Quelle gezogen. 
                        # Den Rest holen wir bequem beim nächsten GitHub-Lauf in 2 Stunden!
                        continue 
                    tiefe_scrapes_gemacht += 1
            
                pubDate = entry.get('published', entry.get('updated', datetime.now().isoformat()))
                full_text = ""
                image_url = None

                if is_radar:
                    radar_desc = entry.get('summary', entry.get('description', ''))
                    full_text = BeautifulSoup(str(radar_desc), 'html.parser').get_text(separator="\n\n").strip()

                # Bilder abgreifen
                if 'media_content' in entry and len(entry.media_content) > 0:
                    image_url = clean_image_url(entry.media_content[0].get('url', ''), link)

                if not image_url and 'enclosures' in entry and len(entry.enclosures) > 0:
                    for enc in entry.enclosures:
                        href = safe_text(enc.get("href"))
                        if safe_text(enc.get("type")).startswith('image/') or any(ext in href.lower() for ext in IMAGE_EXTENSIONS):
                            image_url = clean_image_url(href, link)
                            if image_url: break

                if not image_url:
                    for content_key in ['description', 'summary']:
                        if content_key in entry and isinstance(entry[content_key], str):
                            desc_soup = BeautifulSoup(entry[content_key], 'html.parser')
                            img_tag = desc_soup.find('img')
                            if img_tag:
                                image_url = clean_image_url(img_tag.get('src') or img_tag.get('data-src'), link)
                                if image_url: break

                # Text extrahieren (Der langsame Teil - aber auf 4 Limitiert!)
                if not is_radar:
                    try:
                        if 'content' in entry and len(entry.content) > 0:
                            c_obj = entry.content[0]
                            val = c_obj.value if hasattr(c_obj, 'value') else (c_obj.get('value', '') if isinstance(c_obj, dict) else '')
                            full_text = BeautifulSoup(str(val), 'html.parser').get_text(separator="\n\n").strip()
                    except:
                        pass

                if link and not is_radar and len(full_text) < 300:
                    try:
                        time.sleep(1.5) # Pflichtpause, damit wir nicht blockiert werden
                        html_req = http.get(link, headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
                        soup = BeautifulSoup(html_req.text, 'html.parser')
                    
                        if not image_url:
                            og_img = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'})
                            if og_img:
                                image_url = clean_image_url(og_img.get('content'), link)
                    
                        if not image_url:
                            for img in soup.find_all('img'):
                                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                                image_url = clean_image_url(src, link)
                                if image_url: break

                        paragraphs = soup.find_all('p')
                        text_blocks = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30]
                        full_text = "\n\n".join(text_blocks)
                    
                        waf_phrases = ["Please wait a moment while we ensure the security", "Protected by Anubis", "Enable JavaScript and cookies"]
                        if any(phrase.lower() in full_text.lower() for phrase in waf_phrases):
                            full_text = "" 
                    except:
                        pass
            
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

                allowed_image_hosts = {
                    safe_lower(host)
                    for host in feed.get("imageHosts", [])
                    if safe_text(host)
                }
                if image_url and allowed_image_hosts:
                    image_host = safe_lower(urlparse(image_url).hostname)
                    if image_host not in allowed_image_hosts:
                        image_url = ""

                # =========================================================
                # ARTIKEL ZUM GEDÄCHTNIS HINZUFÜGEN
                # =========================================================
                feed_categories = infer_article_categories(
                    title,
                    clean_text,
                    feed.get("categories", [kontinent]),
                    kontinent,
                )

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
                    "quelleName": feed_name,
                    "author": author,
                    "title": title,
                    "link": link,
                    "pubDate": pubDate,
                    "content": clean_text,
                    "contentComplete": True if is_radar else not content_is_incomplete(clean_text),
                    "image": image_url,
                    "language": feed_languages[0],
                    "languages": feed_languages,
                    "originCountry": safe_text(feed.get("originCountry")),
                    "originCountryCode": safe_text(feed.get("originCountryCode")),
                    "originRegion": safe_text(feed.get("originRegion")),
                    "sourceHomepage": safe_text(feed.get("homepage")),
                }
                gesehene_titel.add(title_lower)
                if is_radar: radar_count += 1
            except Exception as entry_error:
                log_feed_entry_error(
                    feed_name,
                    entry,
                    entry_error,
                )
                continue
            
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
