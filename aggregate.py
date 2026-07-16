import feedparser
import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin
import os
import re
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

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
        {"name": "Amandla! Magazine", "url": "https://aidc.org.za/category/amandla-magazine/feed/"},
        {"name": "Abahlali baseMjondolo (South Africa)", "url": "https://abahlali.org/feed/"},
        {"name": "Black Agenda Report", "url": "https://www.blackagendareport.com/feed"}
    ],
    "North America": [
        {"name": "It's Going Down", "url": "https://itsgoingdown.org/feed/"},
        {"name": "Rose City Antifa", "url": "https://rosecityantifa.org/feed.xml"},
        {"name": "Montreal Antifasciste", "url": "https://montreal-antifasciste.info/fr/feed/"},
        {"name": "SubMedia", "url": "https://sub.media/feed/"},
        {"name": "Black Rose / Rosa Negra", "url": "https://blackrosefed.org/feed/"},
        {"name": "C4SS", "url": "https://c4ss.org/feed"},
        {"name": "CrimethInc. (USA)", "url": "https://crimethinc.com/category/north-america/feed"}
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
        {"name": "Radar Squat.net (Global)", "url": "https://morss.it/https://radar.squat.net/de/events/rss"},
        {"name": "Radar Squat.net (Europa)", "url": "https://morss.it/https://radar.squat.net/de/events/region/Europe/rss"},
        {"name": "Radar Squat.net (Nordamerika)", "url": "https://morss.it/https://radar.squat.net/de/events/region/North%20America/rss"},
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
        {"name": "Worker's Spatula", "url": "https://workersspatula.wordpress.com/feed/"},
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
        {"name": "Rose City Antifa", "url": "https://rosecityantifa.org/feed.xml"},
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
        {"name": "Autostraddle", "url": "https://www.autostraddle.com/feed/"},
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
        {"name": "Worker's Spatula", "url": "https://workersspatula.wordpress.com/feed/"}
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

# HILFSFUNKTION: CHECKPOINTS SPEICHERN (Sicherheit gegen Abstürze)
def save_checkpoint():
    alle = list(archiv_dict.values())
    try:
        # Sortieren nach Datum
        alle.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
    except:
        pass
    
    events = [item for item in alle if item.get('kontinent') == 'Radar'][:1000]
    news_candidates = [item for item in alle if item.get('kontinent') != 'Radar']

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

for kontinent, feeds in quellen.items():
    print(f"\n--- Kategorie: {kontinent} ---")
    is_radar = (kontinent == "Radar")
    
    for feed in feeds:
        print(f"-> Portal: {feed['name']}...")
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
            print(f"  [FEHLER] Konnte {feed['name']} nicht abrufen.")
            continue
            
        limit = 100 if is_radar else 15
        
        # =========================================================
        # DAS NEUE SPEED-LIMIT (Macht den Code rasend schnell)
        # =========================================================
        MAX_NEUE_SCRAPES = 4 # Maximal 4 tief recherchierte Artikel pro Quelle!
        tiefe_scrapes_gemacht = 0

        for entry in parsed.entries[:limit]: 
            link = entry.get('link', '')
            title = entry.get('title', 'Kein Titel')
            title_lower = title.lower().strip()
            author = entry.get('author', 'Unknown')
            
            # Spam rausfiltern
            if any(bad in title_lower or bad in author.lower() for bad in SPAM_BLACKLIST):
                continue

            # IST DER ARTIKEL SCHON BEKANNT? (Ultraschnell überspringen!)
            if link in archiv_dict:
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
                    href = enc.get('href', '')
                    if enc.get('type', '').startswith('image/') or any(ext in href.lower() for ext in IMAGE_EXTENSIONS):
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

            clean_text = full_text.strip()
            
            if any(bad in clean_text.lower() for bad in SPAM_BLACKLIST):
                continue
            
            if is_radar:
                if clean_text == "":
                    clean_text = "Weitere Infos zum Termin auf der Originalseite."
            elif not is_radar and "anarchist news" not in feed['name'].lower() and title.lower() in clean_text.lower() and len(clean_text) < len(title) + 150:
                clean_text = "⚠️ The full text of this article is protected by the publisher's firewall. Please use the [ ORIGINAL ] button below to read it directly on their website."
            elif not is_radar and clean_text == "":
                clean_text = "⚠️ No text available. Please use the [ ORIGINAL ] button below."

            if not image_url or not image_url.startswith('http'):
                image_url = ""

            # =========================================================
            # ARTIKEL ZUM GEDÄCHTNIS HINZUFÜGEN
            # =========================================================
            archiv_dict[link] = {
                "kontinent": kontinent,
                "quelleName": feed['name'],
                "author": author,
                "title": title,
                "link": link,
                "pubDate": pubDate,
                "content": clean_text,
                "contentComplete": True if is_radar else not content_is_incomplete(clean_text),
                "image": image_url
            }
            gesehene_titel.add(title_lower)
            if is_radar: radar_count += 1
            
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

print(f"\n>>> ERFOLG: Es wurden {radar_count} Radar-Termine gefunden! <<<")
print(f"\n[ERFOLG] {len(archiv_dict)} Artikel sicher im Archiv abgelegt.")
