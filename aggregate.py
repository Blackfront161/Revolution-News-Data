import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin
import re
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# --- KONFIGURATION & QUELLEN ---
quellen = {
    "Global": [
        {"name": "CrimethInc. (Global)", "url": "https://crimethinc.com/feed"},
        {"name": "Anarkismo (International)", "url": "http://www.anarkismo.net/backend?locale=en"},
        {"name": "ZNet (International)", "url": "https://znetwork.org/feed/"},
        {"name": "Libcom (Global News)", "url": "https://libcom.org/news/feed"},
        {"name": "IWA-AIT (Internationale)", "url": "https://iwa-ait.org/rss.xml"},
        {"name": "Agency", "url": "https://www.anarchistagency.com/feed/"},
        {"name": "Waging Nonviolence", "url": "https://wagingnonviolence.org/feed/"}
    ],
    "Europe": [
        {"name": "Indymedia DE", "url": "https://de.indymedia.org/rss.xml"},
        {"name": "Barrikade (CH)", "url": "https://barrikade.info/spip.php?page=backend"},
        {"name": "Kontrapolis (DE)", "url": "https://kontrapolis.info/feed/"},
        {"name": "Avtonom (RU)", "url": "https://avtonom.org/rss.xml"},
        {"name": "Pramen (BY)", "url": "https://pramen.io/feed/"},
        {"name": "Athens Indymedia (GR)", "url": "https://athens.indymedia.org/rss/"},
        {"name": "Apatris (GR)", "url": "https://apatris.info/feed/"},
        {"name": "Alerta (GR)", "url": "https://www.alerta.gr/feed/"},
        {"name": "Antifa Infoblatt", "url": "https://www.antifainfoblatt.de/rss.xml"},
        {"name": "Squat!net", "url": "https://de.squat.net/feed/"},
        {"name": "Freedom News", "url": "https://freedomnews.org.uk/feed/"},
        {"name": "Enough is Enough", "url": "https://enoughisenough14.org/feed/"}
    ],
    "Africa": [
        {"name": "Pambazuka News", "url": "https://www.pambazuka.org/rss.xml"},
        {"name": "Zabalaza", "url": "https://zabalaza.net/feed/"},
        {"name": "ROAPE", "url": "https://roape.net/feed/"},
        {"name": "Anarkismo (Africa)", "url": "http://www.anarkismo.net/backend?topic=africa"},
        {"name": "Amandla! Magazine", "url": "https://aidc.org.za/category/amandla-magazine/feed/"}
    ],
    "North America": [
        {"name": "It's Going Down", "url": "https://itsgoingdown.org/feed/"},
        {"name": "Rose City Antifa", "url": "https://rosecityantifa.org/feed.xml"},
        {"name": "Montreal Antifasciste", "url": "https://montreal-antifasciste.info/fr/feed/"},
        {"name": "SubMedia", "url": "https://sub.media/feed/"},
        {"name": "Black Rose / Rosa Negra", "url": "https://blackrosefed.org/feed/"},
        {"name": "C4SS", "url": "https://c4ss.org/feed"}
    ],
    "Latin America": [
        {"name": "Enlace Zapatista (EZLN)", "url": "https://enlacezapatista.ezln.org.mx/feed/"},
        {"name": "El Libertario", "url": "http://periodicoellibertario.blogspot.com/feeds/posts/default"},
        {"name": "Avispa Midia", "url": "https://avispa.org/feed/"},
        {"name": "Desinformémonos", "url": "https://desinformemonos.org/feed/"},
        {"name": "Comunizar", "url": "https://comunizar.com.ar/feed/"},
        {"name": "Indymedia Argentina", "url": "https://argentina.indymedia.org/feed/"}
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
        {"name": "CrimethInc. (Asia)", "url": "https://crimethinc.com/category/asia/feed"}
    ],
    "Australia & NZ": [
        {"name": "IndigenousX (Australia)", "url": "https://indigenousx.com.au/feed/"},
        {"name": "MACG", "url": "https://melbacg.wordpress.com/feed/"},
        {"name": "Slackbastard", "url": "https://slackbastard.anarchobase.com/?feed=rss2"},
        {"name": "Green Left", "url": "https://www.greenleft.org.au/rss.xml"},
        {"name": "AWSM", "url": "https://awsm.nz/feed/"},
        {"name": "Mutiny Blog", "url": "https://mu-tiny.blogspot.com/feeds/posts/default"}
    ],
    "Antifascism": [
        {"name": "Rose City Antifa", "url": "https://rosecityantifa.org/feed.xml"},
        {"name": "Antifa Infoblatt", "url": "https://www.antifainfoblatt.de/rss.xml"},
        {"name": "Montreal Antifasciste", "url": "https://montreal-antifasciste.info/fr/feed/"},
        {"name": "Barrikade", "url": "https://barrikade.info/spip.php?page=backend"}
    ],
    "Antisexism": [
        {"name": "Gods & Radicals", "url": "https://abeautifulresistance.org/site?format=rss"},
        {"name": "Anarkismo (Gender)", "url": "http://www.anarkismo.net/backend?topic=gender"}
    ],
    "Queer-Feminism": [
        {"name": "Queer Anarchism", "url": "https://queeranarchism.tumblr.com/rss"},
        {"name": "Black Rose (Feminism)", "url": "https://blackrosefed.org/category/anarcha-feminism/feed/"}
    ],
    "Antiracism": [
        {"name": "Institute of Race Relations", "url": "https://irr.org.uk/feed/"},
        {"name": "Black Rose (Anti-Racism)", "url": "https://blackrosefed.org/category/anti-racism/feed/"},
        {"name": "No One Is Illegal", "url": "https://noii-van.org/feed/"}
    ],
    "Anticapitalism": [
        {"name": "Enough is Enough", "url": "https://enoughisenough14.org/feed/"},
        {"name": "CrimethInc.", "url": "https://crimethinc.com/feed"},
        {"name": "Comunizar", "url": "https://comunizar.com.ar/feed/"},
        {"name": "ZNet (Global)", "url": "https://znetwork.org/feed/"}
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
    "Squatting": [
        {"name": "Squat!net", "url": "https://de.squat.net/feed/"},
        {"name": "Barrikade", "url": "https://barrikade.info/spip.php?page=backend"}
    ],
    "Demonstrations": [
        {"name": "It's Going Down", "url": "https://itsgoingdown.org/feed/"},
        {"name": "Athens Indymedia", "url": "https://athens.indymedia.org/rss/"},
        {"name": "Kontrapolis", "url": "https://kontrapolis.info/feed/"}
    ],
    "Anti-Repression": [
        {"name": "Anarchist Black Cross", "url": "https://www.abcf.net/feed/"},
        {"name": "ABC Belarus", "url": "https://abc-belarus.org/?feed=rss2&lang=en"},
        {"name": "Avtonom (Repression)", "url": "https://avtonom.org/rss.xml"},
        {"name": "Solidarity Network", "url": "https://enoughisenough14.org/feed/"}
    ],
    "Animal Liberation": [
        {"name": "Tierbefreier", "url": "https://tierbefreier.org/feed/"},
        {"name": "Unoffensive Animal", "url": "https://unoffensiveanimal.is/feed/"}
    ],
    "Eco-Anarchism": [
        {"name": "Earth First!", "url": "https://earthfirstjournal.news/feed/"},
        {"name": "Winter Oak", "url": "https://winteroak.org.uk/feed/"},
        {"name": "SubMedia", "url": "https://sub.media/feed/"}
    ],
    "Indigenous Struggles": [
        {"name": "Enlace Zapatista (EZLN)", "url": "https://enlacezapatista.ezln.org.mx/feed/"},
        {"name": "Avispa Midia", "url": "https://avispa.org/feed/"},
        {"name": "IEN Earth", "url": "https://www.ienearth.org/feed/"},
        {"name": "IndigenousX", "url": "https://indigenousx.com.au/feed/"},
        {"name": "Bulatlat (Indigenous)", "url": "https://www.bulatlat.com/feed/"}
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
        {"name": "Ill Will", "url": "https://illwill.com/feed"},
        {"name": "Sprout Distro", "url": "https://www.sproutdistro.com/feed/"},
        {"name": "Zabalaza Books (Africa)", "url": "https://zabalazabooks.net/feed/"},
        {"name": "Libcom Library", "url": "https://libcom.org/library/feed"}
    ]
}

# --- KONSTANTEN & SETUP ---
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) WorldRevolutionNews/1.0'}
AUTONOMOUS_TIMEOUT = (5.0, 15.0) # Etwas entspannter für langsame Server
# Ein neutraler, ästhetischer Platzhalter (Solarpunk-Vibe)
PLACEHOLDER_IMAGE = "https://raw.githubusercontent.com/Blackfront161/Revolution-News-Data/main/placeholder.jpg" 

# Setup für automatische Wiederholungen (Retry) bei Fehlern
retry_strategy = Retry(
    total=2, # 2 Versuche insgesamt
    backoff_factor=1, # Wartezeit zwischen Versuchen (1s, 2s)
    status_forcelist=[429, 500, 502, 503, 504], # Wiederhole bei diesen HTTP-Fehlern
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

# Bilder, die wir definitiv NICHT wollen
LAYOUT_FILES = ['logo.png', 'logo.jpg', 'logo.svg', 'banner', 'favicon', 'sidebar', 'footer', 'avatar', 'pixel', 'nav_', 'blank.gif', 'spacer.gif']
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')

alle_artikel = []

def clean_image_url(url, base_url):
    """Bereinigt und validiert eine Bild-URL."""
    if not url: return None
    full_url = urljoin(base_url, url)
    filename = full_url.split('/')[-1].lower()
    
    # Check gegen Blacklist
    if any(kw in filename for kw in LAYOUT_FILES): return None
    # Check ob Themes/Plugins Ordner (oft Layout-Assets)
    if any(kw in full_url.lower() for kw in ['/themes/', '/plugins/', '/assets/']): return None
    
    return full_url

for kontinent, feeds in quellen.items():
    print(f"\n--- Kategorie: {kontinent} ---")
    for feed in feeds:
        print(f"-> Portal: {feed['name']}...")
        try:
            # RSS Feed laden (mit Retry)
            feed_req = http.get(feed['url'], headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
            parsed = feedparser.parse(feed_req.text)
            
            for entry in parsed.entries[:4]: # Top 4 Artikel
                link = entry.get('link', '')
                title = entry.get('title', 'Kein Titel')
                pubDate = entry.get('published', datetime.now().isoformat())
                full_text = ""
                image_url = None

                # --- BILDERSUCHE STUFE 1: RSS ENCLOSED MEDIA ---
                if 'media_content' in entry and len(entry.media_content) > 0:
                    image_url = clean_image_url(entry.media_content[0].get('url', ''), link)

                # --- BILDERSUCHE STUFE 2: RSS DESCRIPTION INLINE ---
                if not image_url:
                    for content_key in ['description', 'summary']:
                        if content_key in entry and isinstance(entry[content_key], str):
                            desc_soup = BeautifulSoup(entry[content_key], 'html.parser')
                            img_tag = desc_soup.find('img')
                            if img_tag:
                                image_url = clean_image_url(img_tag.get('src') or img_tag.get('data-src'), link)
                                if image_url: break

                # --- BILDERSUCHE STUFE 3: WEBSEITE SCRAPEN (mit Retry) ---
                if not image_url and link:
                    try:
                        html_req = http.get(link, headers=HEADERS, timeout=AUTONOMOUS_TIMEOUT)
                        soup = BeautifulSoup(html_req.text, 'html.parser')
                        
                        # OpenGraph (Best Case)
                        og_img = soup.find('meta', property='og:image')
                        if og_img:
                            image_url = clean_image_url(og_img.get('content'), link)
                        
                        # Erstes echtes Img-Tag im Body
                        if not image_url:
                            for img in soup.find_all('img'):
                                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                                image_url = clean_image_url(src, link)
                                if image_url: break
                                
                        # --- BILDERSUCHE STUFE 4: REGEX NOTFALL-SCAN ---
                        if not image_url:
                            # Suche nach ALLEM was wie eine Bild-URL aussieht im rohen HTML
                            matches = re.findall(r'(https?://[^\s"<>]+\.(?:jpg|jpeg|png|webp))', html_req.text, re.IGNORECASE)
                            for match in matches:
                                image_url = clean_image_url(match, link)
                                if image_url: break

                        # Text extrahieren
                        paragraphs = soup.find_all('p')
                        text_blocks = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 30]
                        full_text = "\n\n".join(text_blocks)
                    except Exception as e:
                        print(f"   [Meldung] Einzelartikel-Scraping fehlgeschlagen: {str(e)}")
                        pass
                
                # Fallback für Text
                if not full_text or len(full_text) < 150:
                    if 'description' in entry:
                        full_text = BeautifulSoup(entry.description, 'html.parser').get_text().strip()

                # Text bereinigen und kürzen
                clean_text = full_text.strip()
                if len(clean_text) > 8000:
                    clean_text = clean_text[:8000] + "\n\n[... Text gekürzt ...]"

                # --- STUFE 5: FINALER PLATZHALTER ---
                if not image_url:
                    image_url = PLACEHOLDER_IMAGE

                alle_artikel.append({
                    "kontinent": kontinent,
                    "quelleName": feed['name'],
                    "title": title,
                    "link": link,
                    "pubDate": pubDate,
                    "content": clean_text,
                    "image": image_url
                })
        except Exception as e:
            print(f"   [Warnung] Portal komplett übersprungen: {str(e)}")
            pass

# SICHERHEITS-REISSLEINE VOR DEM SPEICHERN
if len(alle_artikel) >= 10:
    # Sortieren: Neueste zuerst
    try:
        alle_artikel.sort(key=lambda x: x['pubDate'], reverse=True)
    except:
        pass
        
    with open('news.json', 'w', encoding='utf-8') as f:
        json.dump(alle_artikel, f, ensure_ascii=False, indent=2)
    print(f"\n[ERFOLG] {len(alle_artikel)} Artikel wurden sicher gespeichert.")
else:
    print(f"\n[STOPP] Nur {len(alle_artikel)} Artikel gefunden. Speichern blockiert!")
    exit(1)
