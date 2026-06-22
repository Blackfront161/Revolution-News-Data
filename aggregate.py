import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin

quellen = {
    # --- STARTSEITE: GLOBAL ---
    "Global": [
        {"name": "CrimethInc. (Global)", "url": "https://crimethinc.com/feed"},
        {"name": "Anarkismo (International)", "url": "http://www.anarkismo.net/backend?locale=en"},
        {"name": "ZNet (International)", "url": "https://znetwork.org/feed/"},
        {"name": "Libcom (Global News)", "url": "https://libcom.org/news/feed"},
        {"name": "IWA-AIT (Internationale)", "url": "https://iwa-ait.org/rss.xml"},
        {"name": "Agency", "url": "https://www.anarchistagency.com/feed/"},
        {"name": "Waging Nonviolence", "url": "https://wagingnonviolence.org/feed/"}
    ],

    # --- KONTINENTE ---
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
    
    # --- THEMEN & KÄMPFE ---
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

    # --- BIBLIOTHEKEN ---
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

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
alle_artikel = []

# Faires Zeitlimit für alternative Server: 4s Verbindungsaufbau, 10s Datenübertragung
AUTONOMOUS_TIMEOUT = (4.0, 10.0)

for kontinent, feeds in quellen.items():
    print(f"\n--- Starte Kategorie: {kontinent} ---")
    for feed in feeds:
        print(f"-> Verarbeite Portal: {feed['name']}...")
        try:
            feed_req = requests.get(feed['url'], headers=headers, timeout=AUTONOMOUS_TIMEOUT)
            parsed = feedparser.parse(feed_req.text)
            
            for entry in parsed.entries[:4]: 
                link = entry.get('link', '')
                title = entry.get('title', 'Kein Titel')
                pubDate = entry.get('published', datetime.now().isoformat())

                full_text = ""
                image_url = ""

                # SCHRITT 1: Direktes Feed-Bild (media_content) prüfen
                if 'media_content' in entry and len(entry.media_content) > 0:
                    image_url = entry.media_content[0].get('url', '')

                # SCHRITT 2: NEU & REVOLUTIONÄR - RSS-Beschreibung nach eingebetteten Beitragsbildern abscannen
                if not image_url:
                    for content_key in ['description', 'summary']:
                        if content_key in entry and isinstance(entry[content_key], str):
                            desc_soup = BeautifulSoup(entry[content_key], 'html.parser')
                            img_tag = desc_soup.find('img')
                            if img_tag and img_tag.get('src'):
                                image_url = img_tag['src']
                                break

                # SCHRITT 3: Falls kein Bild im Feed war, die Webseite direkt laden (mit intelligentem Filter)
                if link:
                    try:
                        html = requests.get(link, headers=headers, timeout=AUTONOMOUS_TIMEOUT).text
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        if not image_url:
                            og_img = soup.find('meta', property='og:image')
                            if og_img and og_img.get('content'):
                                image_url = og_img['content']
                        
                        if not image_url:
                            for img in soup.find_all('img'):
                                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                                if src:
                                    full_src = urljoin(link, src)
                                    filename = full_src.split('/')[-1].lower()
                                    
                                    # Smarter Filter: Blockiert nur reine Design-Assets (wie logo.png), erlaubt aber Artikel-Bilder (wie logo_article.jpg)
                                    layout_files = ['logo.png', 'logo.jpg', 'logo.svg', 'banner', 'favicon', 'sidebar', 'footer', 'avatar', 'pixel', 'nav_']
                                    if not any(kw in filename for kw in layout_files) and not any(kw in full_src.lower() for kw in ['/themes/', '/plugins/']):
                                        image_url = full_src
                                        break

                        paragraphs = soup.find_all('p')
                        text_blocks = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20]
                        full_text = "\n\n".join(text_blocks)
                    except Exception as e:
                        print(f"   [Meldung] Einzelartikel-Scraping übersprungen: {str(e)}")
                        pass
                
                if not full_text or len(full_text) < 100:
                    full_text = entry.get('description', '')

                clean_soup = BeautifulSoup(full_text, 'html.parser')
                clean_text = clean_soup.get_text(separator="\n\n").strip()

                if len(clean_text) > 8000:
                    clean_text = clean_text[:8000] + "\n\n[... Text gekürzt ...]"

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
            print(f"   [Warnung] Portal übersprungen: {str(e)}")
            pass

# REISSLEINE
if len(alle_artikel) >= 10:
    with open('news.json', 'w', encoding='utf-8') as f:
        json.dump(alle_artikel, f, ensure_ascii=False, indent=2)
    print(f"\n[ERFOLG] {len(alle_artikel)} Artikel wurden gespeichert.")
else:
    print(f"\n[STOPP] Speichern blockiert!")
    exit(1)
