import feedparser
import requests
import cloudscraper
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

try:
    from trafilatura import extract as trafilatura_extract
except ImportError:
    trafilatura_extract = None

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


# -----------------------------------------------------------------
# NEUE QUELLEN MIT MEHREREN PASSENDEN KATEGORIEN
# -----------------------------------------------------------------
# Jede Quelle wird hier nur einmal gepflegt. Der Code trägt sie automatisch
# in alle genannten Kategorien ein. Dank des Feed-Caches weiter unten wird
# derselbe RSS-Feed trotzdem nur einmal aus dem Internet geladen.
NEUE_MEHRFACH_QUELLEN = [
    {
        "name": "Direkte Aktion (DE)",
        "url": "https://direkteaktion.org/rss/",
        "categories": ["Europe", "Labor Struggles", "Theory & Strategy", "Anticapitalism"]
    },
    {
        "name": "Organise Magazine",
        "url": "https://organisemagazine.org.uk/feed/",
        "categories": ["Global", "Europe", "Theory & Strategy", "Antifascism", "Anticapitalism"]
    },
    {
        "name": "Corporate Watch",
        "url": "https://corporatewatch.org/feed/",
        "categories": ["Europe", "Anticapitalism", "No Borders", "Squatting & Housing", "Anti-Rep & Prisons", "Cyberactivism"]
    },
    {
        "name": "The Final Straw Radio",
        "url": "https://thefinalstrawradio.libsyn.com/rss",
        "categories": ["Global", "Theory & Strategy", "Anti-Rep & Prisons", "Antifascism"]
    },
    {
        "name": "Alarm Phone",
        "url": "https://alarmphone.org/en/feed/",
        "categories": ["Europe", "Africa", "No Borders", "Anti-Rep & Prisons"]
    },
    {
        "name": "Disability Debrief",
        "url": "https://www.disabilitydebrief.org/rss/",
        "categories": ["Global", "Radical Health & Disability"]
    }
]

for source in NEUE_MEHRFACH_QUELLEN:
    clean_name = str(source.get("name", "")).strip()
    clean_url = str(source.get("url", "")).strip()

    if not clean_name or not clean_url:
        continue

    for category in source.get("categories", []):
        clean_category = str(category or "").strip()
        if not clean_category:
            continue

        category_feeds = quellen.setdefault(clean_category, [])
        already_exists = any(
            str(existing.get("url", "")).strip() == clean_url
            for existing in category_feeds
        )

        if not already_exists:
            category_feeds.append({"name": clean_name, "url": clean_url})

SPAM_BLACKLIST = [
    "sicherheitslage verschlimmert",
    "mordeaffen",
    "kurt gustav wilckens"
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
AUTONOMOUS_TIMEOUT = (8.0, 15.0) 

retry_strategy = Retry(total=2, backoff_factor=1.0, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
adapter = HTTPAdapter(max_retries=retry_strategy)

http = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
http.mount("https://", adapter)
http.mount("http://", adapter)

session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)

LAYOUT_FILES = ['logo.png', 'logo.jpg', 'logo.svg', 'banner', 'favicon', 'sidebar', 'footer', 'avatar', 'pixel', 'nav_', 'blank.gif', 'spacer.gif']
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')

def clean_image_url(url, base_url):
    if not url: return None
    full_url = urljoin(base_url, url)
    filename = full_url.split('/')[-1].lower()
    if any(kw in filename for kw in LAYOUT_FILES): return None
    if any(kw in full_url.lower() for kw in ['/themes/', '/plugins/', '/assets/']): return None
    return full_url


WAF_PHRASES = [
    "please wait a moment while we ensure the security",
    "protected by anubis",
    "enable javascript and cookies",
    "access denied",
    "checking your browser"
]

TRUNCATION_HINTS = [
    "read more", "continue reading", "weiterlesen", "lire la suite",
    "leer más", "continua a leggere", "read the full article",
    "zum vollständigen artikel", "[...]"
]


def normalize_article_text(value):
    text = str(value or '').replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.strip() for line in text.split('\n')]
    cleaned = []
    previous = None
    for line in lines:
        if not line:
            if cleaned and cleaned[-1] != '':
                cleaned.append('')
            continue
        if line == previous:
            continue
        cleaned.append(line)
        previous = line
    return '\n'.join(cleaned).strip()


def page_is_blocked(text):
    lowered = str(text or '').lower()
    return any(phrase in lowered for phrase in WAF_PHRASES)


def text_looks_truncated(text):
    clean = normalize_article_text(text)
    lowered = clean.lower()
    if len(clean) < 900:
        return True
    if clean.endswith('...') or clean.endswith('…'):
        return True
    tail = lowered[-350:]
    return any(hint in tail for hint in TRUNCATION_HINTS)


def extract_feed_text(entry):
    candidates = []
    try:
        for content_item in entry.get('content', []) or []:
            value = getattr(content_item, 'value', None)
            if value is None and isinstance(content_item, dict):
                value = content_item.get('value', '')
            if value:
                candidates.append(BeautifulSoup(str(value), 'html.parser').get_text(separator='\n\n'))
    except Exception:
        pass

    for key in ('description', 'summary'):
        try:
            value = entry.get(key, '')
            if value:
                candidates.append(BeautifulSoup(str(value), 'html.parser').get_text(separator='\n\n'))
        except Exception:
            pass

    candidates = [normalize_article_text(candidate) for candidate in candidates]
    candidates = [candidate for candidate in candidates if candidate and not page_is_blocked(candidate)]
    return max(candidates, key=len, default='')


def extract_main_text_from_html(html, url):
    if not html or page_is_blocked(html):
        return ''

    extracted = ''
    if trafilatura_extract is not None:
        try:
            extracted = trafilatura_extract(
                html,
                url=url,
                output_format='txt',
                include_comments=False,
                include_tables=False,
                favor_recall=True,
                deduplicate=True
            ) or ''
        except Exception as error:
            print(f"  [TRAFILATURA-FEHLER] {url}: {type(error).__name__}: {error}")

    extracted = normalize_article_text(extracted)
    if len(extracted) >= 300 and not page_is_blocked(extracted):
        return extracted

    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(['script', 'style', 'noscript', 'nav', 'footer', 'header', 'aside', 'form', 'svg']):
        tag.decompose()

    selectors = [
        'article', 'main', '.entry-content', '.post-content', '.article-content',
        '.article-body', '.field--name-body', '.node__content', '.story-body',
        '[itemprop="articleBody"]'
    ]
    candidates = []
    for selector in selectors:
        for container in soup.select(selector):
            paragraphs = [
                node.get_text(' ', strip=True)
                for node in container.find_all(['p', 'h2', 'h3', 'blockquote', 'li'])
                if len(node.get_text(' ', strip=True)) > 25
            ]
            candidate = normalize_article_text('\n\n'.join(paragraphs))
            if candidate:
                candidates.append(candidate)

    if not candidates:
        paragraphs = [
            node.get_text(' ', strip=True)
            for node in soup.find_all(['p', 'h2', 'h3', 'blockquote'])
            if len(node.get_text(' ', strip=True)) > 30
        ]
        candidates.append(normalize_article_text('\n\n'.join(paragraphs)))

    candidates = [candidate for candidate in candidates if candidate and not page_is_blocked(candidate)]
    return max(candidates, key=len, default='')


def should_refresh_existing_article(article):
    if not isinstance(article, dict):
        return False
    content = normalize_article_text(article.get('content', ''))
    if content and len(content) >= 2000 and not text_looks_truncated(content):
        return False

    last_attempt = article.get('contentRefreshAttemptedAt')
    if last_attempt:
        try:
            last_dt = datetime.fromisoformat(str(last_attempt).replace('Z', '+00:00'))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - last_dt < timedelta(days=7):
                return False
        except Exception:
            pass
    return True


def choose_best_article_text(feed_text, page_text):
    feed_text = normalize_article_text(feed_text)
    page_text = normalize_article_text(page_text)
    if not page_text:
        return feed_text
    if not feed_text:
        return page_text
    if text_looks_truncated(feed_text) and len(page_text) > len(feed_text):
        return page_text
    if len(page_text) >= len(feed_text) * 1.15:
        return page_text
    return feed_text


# =================================================================
# RADAR.SQUAT API
# =================================================================
# Die API wird in Zeitabschnitten abgefragt. Dadurch greifen wir nicht nur
# auf einen RSS-Ausschnitt zu, sondern erhalten strukturierte Eventdaten.
RADAR_API_URL = "https://radar.squat.net/api/1.2/search/events.json"
RADAR_BASE_URL = "https://radar.squat.net"
RADAR_DAYS_AHEAD = 120
RADAR_CHUNK_DAYS = 30
RADAR_LIMIT_PER_CHUNK = 500
RADAR_FIELDS = ",".join([
    "title", "title_field", "body", "date_time", "offline", "category",
    "topic", "og_group_ref", "price", "price_category", "event_status",
    "uuid", "nid", "url", "language", "link", "image", "flyer"
])


def as_list(value):
    """Macht aus API-Werten zuverlässig eine Liste."""
    if value is None or value is False:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        # Suchresultate können als Objekt mit numerischen Schlüsseln kommen.
        return list(value.values())
    return [value]


def first_text(value, *keys):
    """Liest aus wechselnden Radar-Feldformen den ersten brauchbaren Text."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
        for key in ("name", "label", "title", "value", "summary", "url", "uri"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
    return ""


def radar_term_names(value):
    names = []
    for item in as_list(value):
        name = first_text(item, "name", "label", "title")
        if name and name not in names:
            names.append(name)
    return names


def radar_parse_timestamp(value):
    """Versteht Unix-Zeit, ISO-Zeit und Radar-Zeitstrings."""
    if value is None or value == "":
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if not text:
        return 0
    try:
        return int(float(text))
    except (TypeError, ValueError):
        pass
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())
    except (TypeError, ValueError):
        return 0


def radar_datetime_data(event):
    entries = [item for item in as_list(event.get("date_time")) if isinstance(item, dict)]
    if not entries:
        return 0, 0

    candidates = []
    for item in entries:
        start = radar_parse_timestamp(item.get("value") or item.get("time_start"))
        end = radar_parse_timestamp(item.get("value2") or item.get("time_end"))
        if start:
            candidates.append((start, end or start))

    if not candidates:
        return 0, 0
    candidates.sort(key=lambda pair: pair[0])
    return candidates[0]


def timestamp_iso(timestamp):
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def radar_clean_html(value):
    if isinstance(value, dict):
        value = value.get("value") or value.get("summary") or ""
    return BeautifulSoup(str(value or ""), "html.parser").get_text(separator="\n\n").strip()


def radar_absolute_url(value):
    text = first_text(value, "url", "display_url", "uri")
    if not text:
        return ""
    return urljoin(RADAR_BASE_URL + "/", text)


def radar_image_url(event):
    """Sucht vorsichtig nach einem Bild oder Flyer in verschachtelten Feldern."""
    def walk(value):
        if isinstance(value, str):
            if value.startswith("http") and any(ext in value.lower() for ext in IMAGE_EXTENSIONS):
                return value
            return ""
        if isinstance(value, list):
            for item in value:
                found = walk(item)
                if found:
                    return found
        if isinstance(value, dict):
            for key in ("url", "uri", "file_url", "source", "src"):
                candidate = value.get(key)
                if isinstance(candidate, str) and candidate:
                    absolute = urljoin(RADAR_BASE_URL + "/", candidate)
                    if absolute.startswith("http"):
                        return absolute
            for item in value.values():
                found = walk(item)
                if found:
                    return found
        return ""

    return walk(event.get("image")) or walk(event.get("flyer"))


def radar_location_data(event):
    locations = [item for item in as_list(event.get("offline")) if isinstance(item, dict)]
    if not locations:
        return {
            "venue": "", "address": "", "city": "", "country": "",
            "postal_code": "", "timezone": "", "lat": "", "lon": ""
        }

    location = locations[0]
    address = location.get("address") if isinstance(location.get("address"), dict) else {}
    map_data = location.get("map") if isinstance(location.get("map"), dict) else {}

    venue = first_text(location, "title", "name", "label")
    city = first_text(address, "locality", "dependent_locality")
    country = first_text(address, "country")
    postal_code = first_text(address, "postal_code")
    street = first_text(address, "thoroughfare")
    premise = first_text(address, "premise")

    address_parts = []
    for part in (street, premise, postal_code, city, country):
        if part and part not in address_parts:
            address_parts.append(part)

    return {
        "venue": venue,
        "address": ", ".join(address_parts),
        "city": city,
        "country": country.upper() if len(country) == 2 else country,
        "postal_code": postal_code,
        "timezone": first_text(location, "timezone"),
        "lat": first_text(map_data, "lat"),
        "lon": first_text(map_data, "lon")
    }


def radar_event_link(event, uuid):
    direct = radar_absolute_url(event.get("url"))
    if direct:
        return direct

    for link_item in as_list(event.get("link")):
        candidate = radar_absolute_url(link_item)
        if candidate:
            return candidate

    if uuid:
        return f"{RADAR_BASE_URL}/api/1.2/node/{uuid}.json"
    return RADAR_BASE_URL


def convert_radar_event(event):
    if not isinstance(event, dict):
        return None

    uuid = first_text(event, "uuid")
    title = first_text(event, "title", "title_field") or "Event ohne Titel"
    start_ts, end_ts = radar_datetime_data(event)
    if not start_ts:
        return None

    body = radar_clean_html(event.get("body"))
    if not body:
        body = "Weitere Informationen findest du beim Originalevent auf Radar.squat."

    location = radar_location_data(event)
    groups = radar_term_names(event.get("og_group_ref"))
    categories = radar_term_names(event.get("category"))
    tags = radar_term_names(event.get("topic"))
    price_categories = radar_term_names(event.get("price_category"))
    price = first_text(event, "price")
    status = first_text(event, "event_status")
    link = radar_event_link(event, uuid)
    image = radar_image_url(event)

    text_for_online = f"{title} {body}".lower()
    if location["venue"] or location["city"] or location["address"]:
        event_mode = "offline"
    elif "online" in text_for_online or "stream" in text_for_online:
        event_mode = "online"
    else:
        event_mode = "unknown"

    return {
        "type": "event",
        "sourceType": "radar-api",
        "eventSource": "Radar.squat",
        "eventApiId": uuid,
        "kontinent": "Radar",
        "categories": ["Radar"],
        "quelleName": "Radar.squat API",
        "author": ", ".join(groups) if groups else "Radar.squat",
        "title": title,
        "link": link,
        # pubDate bleibt für ältere App-Versionen erhalten.
        "pubDate": timestamp_iso(start_ts),
        "eventStart": timestamp_iso(start_ts),
        "eventEnd": timestamp_iso(end_ts),
        "eventVenue": location["venue"],
        "eventAddress": location["address"],
        "eventCity": location["city"],
        "eventCountry": location["country"],
        "eventPostalCode": location["postal_code"],
        "eventTimezone": location["timezone"],
        "eventLatitude": location["lat"],
        "eventLongitude": location["lon"],
        "eventCategories": categories,
        "eventTags": tags,
        "eventGroups": groups,
        "eventPrice": price,
        "eventPriceCategories": price_categories,
        "eventStatus": status,
        "eventLanguage": first_text(event, "language"),
        "eventMode": event_mode,
        "content": body,
        "image": image if image.startswith("http") else ""
    }


def fetch_radar_api_events():
    """Lädt kommende Radar-Events. Bei einem Fehler wird None zurückgegeben."""
    now = datetime.now(timezone.utc)
    overall_end = now + timedelta(days=RADAR_DAYS_AHEAD)
    cursor = now
    events_by_id = {}

    print(f"\n--- Radar API: kommende {RADAR_DAYS_AHEAD} Tage ---")

    while cursor < overall_end:
        chunk_end = min(cursor + timedelta(days=RADAR_CHUNK_DAYS), overall_end)
        params = {
            "limit": str(RADAR_LIMIT_PER_CHUNK),
            "language": "de",
            "fields": RADAR_FIELDS,
            "filter[~and][search_api_aggregation_1][~gte]": str(int(cursor.timestamp())),
            "filter[~or][search_api_aggregation_1][~lte]": str(int(chunk_end.timestamp()))
        }

        try:
            response = session.get(
                RADAR_API_URL,
                params=params,
                headers={**HEADERS, "Accept": "application/json"},
                timeout=(10, 45)
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            print(f"  [RADAR-API-FEHLER] {cursor.date()} bis {chunk_end.date()}: {error}")
            return None

        raw_results = payload.get("result", {}) if isinstance(payload, dict) else {}
        chunk_events = as_list(raw_results)
        print(f"  [RADAR API] {cursor.date()} bis {chunk_end.date()}: {len(chunk_events)} Rohdatensätze")

        for raw_event in chunk_events:
            converted = convert_radar_event(raw_event)
            if not converted:
                continue
            unique_id = converted.get("eventApiId") or converted.get("link")
            events_by_id[unique_id] = converted

        cursor = chunk_end

    return list(events_by_id.values())


def replace_radar_api_events(archive, new_events):
    """Ersetzt nur alte API-Events. Andere Eventquellen bleiben erhalten."""
    old_api_keys = [
        key for key, article in archive.items()
        if isinstance(article, dict) and article.get("sourceType") == "radar-api"
    ]
    for key in old_api_keys:
        archive.pop(key, None)

    # Eine frühere Systemmeldung entfernen, sobald echte Daten vorhanden sind.
    system_key = "https://radar.squat.net"
    if new_events and archive.get(system_key, {}).get("quelleName") == "System Info":
        archive.pop(system_key, None)

    for event in new_events:
        archive[event["link"]] = event


# =================================================================
# 1. ARCHIV LADEN (Das clevere Gedächtnis, das nie vergisst)
# =================================================================
archiv_dict = {}

# Merkt sich, unter welchem Link ein bereits bekannter Titel gespeichert ist.
# So können wir bei exakt gleichem Titel eine zusätzliche Kategorie ergänzen,
# statt denselben Artikel ein zweites Mal anzulegen.
titel_zu_link = {}


def normalize_title(value):
    """Vereinheitlicht einen Titel für einen vorsichtigen Dublettenvergleich."""
    return " ".join(str(value or "").lower().split())


def get_article_categories(article):
    """Liest neue categories-Listen und alte kontinent-Felder gemeinsam."""
    categories = []
    raw_categories = article.get('categories', [])

    if isinstance(raw_categories, list):
        for category in raw_categories:
            clean_category = str(category or '').strip()
            if clean_category and clean_category not in categories:
                categories.append(clean_category)
    elif isinstance(raw_categories, str):
        clean_category = raw_categories.strip()
        if clean_category:
            categories.append(clean_category)

    old_category = str(article.get('kontinent', '') or '').strip()
    if old_category and old_category not in categories:
        categories.append(old_category)

    return categories


def add_category(article, category):
    """Ergänzt eine Kategorie und erhält das alte kontinent-Feld als Kompatibilität."""
    clean_category = str(category or '').strip()
    categories = get_article_categories(article)
    category_was_added = False

    if clean_category and clean_category not in categories:
        categories.append(clean_category)
        category_was_added = True

    article['categories'] = categories

    # Alte App-Versionen kennen nur kontinent. Deshalb bleibt das erste Element erhalten.
    if not str(article.get('kontinent', '') or '').strip() and categories:
        article['kontinent'] = categories[0]

    return category_was_added


def register_title(article):
    """Registriert nur ausreichend aussagekräftige Titel für die Dublettenerkennung."""
    normalized = normalize_title(article.get('title', ''))
    link = str(article.get('link', '') or '').strip()

    # Sehr kurze Titel wie "News" werden nicht zusammengeführt.
    if len(normalized) >= 12 and link:
        titel_zu_link.setdefault(normalized, link)


try:
    if os.path.exists('news.json'):
        with open('news.json', 'r', encoding='utf-8') as f:
            alter_stand = json.load(f)

            if not isinstance(alter_stand, list):
                raise ValueError('news.json muss eine Liste von Artikeln enthalten.')

            for art in alter_stand:
                if not isinstance(art, dict):
                    continue

                link = str(art.get('link', '') or '').strip()
                if not link:
                    continue

                # Migriert alte Artikel automatisch auf das neue Kategorienformat.
                art['categories'] = get_article_categories(art)
                if not art.get('kontinent') and art['categories']:
                    art['kontinent'] = art['categories'][0]

                # Falls eine alte Datei denselben Link mehrfach enthält, werden Kategorien
                # zusammengeführt, statt dass der letzte Eintrag alles überschreibt.
                if link in archiv_dict:
                    existing = archiv_dict[link]
                    for category in art['categories']:
                        add_category(existing, category)

                    # Behalte nach Möglichkeit den längeren Artikeltext.
                    if len(str(art.get('content', ''))) > len(str(existing.get('content', ''))):
                        existing['content'] = art.get('content', '')
                else:
                    archiv_dict[link] = art

                register_title(archiv_dict[link])
except Exception as error:
    print(f"Starte mit leerem Archiv oder konnte das Archiv nicht laden: {error}")

radar_count = 0 

# Wandelt unterschiedliche RSS-Datumsformate in eine Zahl um, die korrekt sortiert werden kann.
def date_to_timestamp(value):
    if not value:
        return 0

    text = str(value).strip()

    try:
        parsed = parsedate_to_datetime(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (TypeError, ValueError, OverflowError):
        pass

    try:
        parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except (TypeError, ValueError, OverflowError):
        return 0


# Speichert zuerst eine temporäre Datei und ersetzt news.json erst nach erfolgreichem Schreiben.
# Dadurch bleibt die alte news.json erhalten, wenn der Prozess während des Speicherns abstürzt.
def save_checkpoint():
    all_items = list(archiv_dict.values())

    event_items = [
        item for item in all_items
        if isinstance(item, dict) and "Radar" in get_article_categories(item)
    ]
    article_items = [
        item for item in all_items
        if not (isinstance(item, dict) and "Radar" in get_article_categories(item))
    ]

    # Nachrichten: neueste zuerst. Events: nächster Termin zuerst.
    article_items.sort(
        key=lambda article: date_to_timestamp(article.get('pubDate')),
        reverse=True
    )
    event_items.sort(
        key=lambda event: date_to_timestamp(event.get('eventStart') or event.get('pubDate'))
    )

    # Reserviert bis zu 500 Plätze für Events und den Rest für Nachrichten.
    event_items = event_items[:500]
    remaining_slots = max(0, 2000 - len(event_items))
    article_items = article_items[:remaining_slots]
    all_items = article_items + event_items

    target = Path('news.json')
    temporary = Path('news.json.tmp')

    temporary.write_text(
        json.dumps(all_items, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    os.replace(temporary, target)

# Speichert bereits geladene Feeds im Arbeitsspeicher.
# Das ist wichtig, weil einige Quellen zu mehreren Kategorien gehören.
feed_cache = {}

for kontinent, feeds in quellen.items():
    print(f"\n--- Kategorie: {kontinent} ---")
    is_radar = (kontinent == "Radar")
    
    for feed in feeds:
        print(f"-> Portal: {feed['name']}...")
        feed_url = str(feed.get('url', '') or '').strip()
        parsed = feed_cache.get(feed_url)

        if parsed is not None:
            print("  [CACHE] Feed wurde bereits geladen; vorhandene Daten werden wiederverwendet.")
        else:
            try:
                feed_req = http.get(feed_url, headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
                feed_req.raise_for_status()
                parsed = feedparser.parse(feed_req.content)

                if not parsed.entries:
                    feed_req = session.get(feed_url, headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
                    feed_req.raise_for_status()
                    parsed = feedparser.parse(feed_req.content)

            except requests.RequestException as error:
                print(f"  [HTTP-FEHLER] Erster Abruf von {feed['name']}: {error}")
                try:
                    feed_req = session.get(feed_url, headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
                    feed_req.raise_for_status()
                    parsed = feedparser.parse(feed_req.content)
                except requests.RequestException as fallback_error:
                    print(f"  [HTTP-FEHLER] Ersatzabruf von {feed['name']}: {fallback_error}")
                    parsed = None
                except Exception as parser_error:
                    print(f"  [PARSER-FEHLER] {feed['name']}: {type(parser_error).__name__}: {parser_error}")
                    parsed = None
            except Exception as error:
                print(f"  [UNERWARTETER FEHLER] {feed['name']}: {type(error).__name__}: {error}")
                parsed = None

            # Auch ein fehlgeschlagener Feed wird für diesen Programmlauf gemerkt,
            # damit dieselbe kaputte URL nicht in jeder Kategorie erneut geladen wird.
            feed_cache[feed_url] = parsed
                
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
            link = entry.get('link', '').strip()
            if not link:
                print(f"  [ÜBERSPRUNGEN] Eintrag ohne Link bei {feed['name']}")
                continue

            title = entry.get('title', 'Kein Titel')
            title_lower = normalize_title(title)
            author = entry.get('author', 'Unknown')
            
            # Spam rausfiltern
            if any(bad in title_lower or bad in author.lower() for bad in SPAM_BLACKLIST):
                continue

            # IST DER ARTIKEL SCHON BEKANNT?
            # Normalerweise wird nur die neue Kategorie ergänzt. Kurze oder offensichtlich
            # gekürzte Alttexte werden höchstens einmal pro Woche erneut geprüft.
            existing_article = archiv_dict.get(link)
            refresh_existing = False
            if existing_article is not None:
                category_added = add_category(existing_article, kontinent)
                if category_added:
                    print(f"  [KATEGORIE ERGÄNZT] {title} -> {kontinent}")
                if is_radar:
                    radar_count += 1
                    continue
                refresh_existing = should_refresh_existing_article(existing_article)
                if not refresh_existing:
                    continue
                print(f"  [VOLLTEXT-PRÜFUNG] Bereits bekannter, kurzer Artikel: {title}")

            # Manche Portale verwenden unterschiedliche Links für denselben Artikel.
            # Bei einem ausreichend langen, exakt gleichen Titel wird ebenfalls nur
            # die neue Kategorie ergänzt.
            known_title_link = titel_zu_link.get(title_lower)
            if not refresh_existing and known_title_link and not is_radar and known_title_link in archiv_dict:
                category_added = add_category(archiv_dict[known_title_link], kontinent)
                if category_added:
                    print(f"  [TITEL-DUBLETTE, KATEGORIE ERGÄNZT] {title} -> {kontinent}")
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

            # Alle Textvarianten des Feeds werden verglichen. Manche Portale
            # liefern den Volltext in content:encoded, andere in summary.
            if not is_radar:
                full_text = extract_feed_text(entry)

            # Bei wahrscheinlich gekürzten Feeds wird zusätzlich die Artikelseite
            # geladen. Trafilatura entfernt Navigation, Werbung und Seitenleisten.
            # Schutzsysteme wie Anubis werden nicht umgangen.
            should_fetch_page = (
                link and not is_radar and
                (text_looks_truncated(full_text) or len(full_text) < 2000)
            )
            if should_fetch_page:
                try:
                    time.sleep(1.0)
                    html_req = http.get(link, headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
                    html_req.raise_for_status()
                    soup = BeautifulSoup(html_req.text, 'html.parser')

                    if not image_url:
                        og_img = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'})
                        if og_img:
                            image_url = clean_image_url(og_img.get('content'), link)

                    if not image_url:
                        for img in soup.find_all('img'):
                            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                            image_url = clean_image_url(src, link)
                            if image_url:
                                break

                    page_text = extract_main_text_from_html(html_req.text, link)
                    full_text = choose_best_article_text(full_text, page_text)
                except requests.RequestException as error:
                    print(f"  [ARTIKEL-FEHLER] {link}: {error}")
                except Exception as error:
                    print(f"  [EXTRAKTIONS-FEHLER] {link}: {type(error).__name__}: {error}")

            clean_text = normalize_article_text(full_text)
            
            if any(bad in clean_text.lower() for bad in SPAM_BLACKLIST):
                continue
            
            if is_radar:
                if clean_text == "":
                    clean_text = "Weitere Infos zum Termin auf der Originalseite."
            elif not is_radar and clean_text == "":
                clean_text = "⚠️ Der vollständige Text konnte von dieser Quelle nicht automatisch geladen werden. Bitte öffne den Originalartikel."

            if not image_url or not image_url.startswith('http'):
                image_url = ""

            # =========================================================
            # ARTIKEL ZUM GEDÄCHTNIS HINZUFÜGEN ODER VOLLTEXT VERBESSERN
            # =========================================================
            if refresh_existing and existing_article is not None:
                existing_article['contentRefreshAttemptedAt'] = datetime.now(timezone.utc).isoformat()
                old_text = normalize_article_text(existing_article.get('content', ''))
                if clean_text and not clean_text.startswith('⚠️') and len(clean_text) > len(old_text) + 100:
                    existing_article['content'] = clean_text
                    print(f"  [VOLLTEXT AKTUALISIERT] {title}: {len(old_text)} -> {len(clean_text)} Zeichen")
                if image_url and not existing_article.get('image'):
                    existing_article['image'] = image_url
                if author and str(existing_article.get('author', '')).lower() in ('', 'unknown'):
                    existing_article['author'] = author
                register_title(existing_article)
                continue

            archiv_dict[link] = {
                "type": "event" if is_radar else "article",
                "sourceType": "event-feed" if is_radar else "rss",
                "kontinent": kontinent,
                "categories": [kontinent],
                "quelleName": feed['name'],
                "author": author,
                "title": title,
                "link": link,
                "pubDate": pubDate,
                "eventStart": pubDate if is_radar else "",
                "eventEnd": "",
                "eventVenue": "",
                "eventAddress": "",
                "eventCity": "",
                "eventCountry": "",
                "eventPostalCode": "",
                "eventCategories": [],
                "eventTags": [],
                "eventGroups": [],
                "eventPrice": "",
                "eventPriceCategories": [],
                "eventStatus": "",
                "eventMode": "unknown" if is_radar else "",
                "content": clean_text,
                "image": image_url
            }
            register_title(archiv_dict[link])
            if is_radar: radar_count += 1
            
        # =========================================================
        # CHECKPOINT NACH JEDER QUELLE SPEICHERN (Sichert die Daten)
        # =========================================================
        save_checkpoint()

# RADAR.SQUAT DIREKT ÜBER DIE ÖFFENTLICHE API LADEN
radar_api_events = fetch_radar_api_events()
if radar_api_events is not None:
    replace_radar_api_events(archiv_dict, radar_api_events)
    radar_count += len(radar_api_events)
    print(f"[RADAR API] {len(radar_api_events)} strukturierte Events übernommen.")
    save_checkpoint()
else:
    print("[RADAR API] Abruf fehlgeschlagen. Bereits gespeicherte API-Events bleiben erhalten.")

# SYSTEM-MELDUNG FALLS RADAR GESTÖRT IST
if radar_count == 0:
    archiv_dict["https://radar.squat.net"] = {
        "kontinent": "Radar",
        "categories": ["Radar"],
        "quelleName": "System Info",
        "author": "News-Bot",
        "title": "🛡️ Eventquellen vorübergehend nicht erreichbar",
        "link": "https://radar.squat.net",
        "pubDate": datetime.now().isoformat(),
        "content": "Die Eventquellen konnten in diesem Update-Lauf nicht geladen werden. Beim nächsten automatischen Lauf wird es erneut versucht.",
        "image": ""
    }
    save_checkpoint()

print(f"\n>>> ERFOLG: Es wurden {radar_count} Radar-Termine gefunden! <<<")
print(f"\n[ERFOLG] {len(archiv_dict)} Artikel sicher im Archiv abgelegt.")