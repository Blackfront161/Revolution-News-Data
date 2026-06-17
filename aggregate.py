import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin

quellen = {
    "Europa": [
        {"name": "Indymedia DE", "url": "https://de.indymedia.org/rss.xml"},
        {"name": "Antifa Infoblatt", "url": "https://www.antifainfoblatt.de/rss.xml"},
        {"name": "Squat!net", "url": "https://de.squat.net/feed/"},
        {"name": "Tierbefreier", "url": "https://tierbefreier.org/feed/"},
        {"name": "Enough is Enough", "url": "https://enoughisenough14.org/feed/"},
        {"name": "Freedom News", "url": "https://freedomnews.org.uk/feed/"}
    ],
    "Afrika": [
        {"name": "Pambazuka News", "url": "https://www.pambazuka.org/rss.xml"},
        {"name": "Zabalaza", "url": "https://zabalaza.net/feed/"},
        {"name": "ROAPE", "url": "https://roape.net/feed/"}
    ],
    "Nordamerika": [
        {"name": "It's Going Down", "url": "https://itsgoingdown.org/feed/"},
        {"name": "Rose City Antifa", "url": "https://rosecityantifa.org/feed.xml"},
        {"name": "Montreal Antifasciste", "url": "https://montreal-antifasciste.info/fr/feed/"},
        {"name": "Earth First!", "url": "https://earthfirstjournal.news/feed/"},
        {"name": "CrimethInc.", "url": "https://crimethinc.com/feed"}
    ],
    "Lateinamerika": [
        {"name": "El Libertario", "url": "http://periodicoellibertario.blogspot.com/feeds/posts/default"},
        {"name": "Avispa Midia", "url": "https://avispa.org/feed/"},
        {"name": "Desinformémonos", "url": "https://desinformemonos.org/feed/"}
    ],
    "Asien": [
        {"name": "Lausan", "url": "https://lausan.hk/feed/"},
        {"name": "Chuang", "url": "https://chuangcn.org/feed/"},
        {"name": "New Bloom", "url": "https://newbloommag.net/feed/"}
    ],
    "Australien & NZ": [
        {"name": "MACG", "url": "https://melbacg.wordpress.com/feed/"},
        {"name": "Slackbastard", "url": "https://slackbastard.anarchobase.com/?feed=rss2"},
        {"name": "Green Left", "url": "https://www.greenleft.org.au/rss.xml"},
        {"name": "AWSM", "url": "https://awsm.nz/feed/"}
    ],
    "Bibliotheken": [
        {"name": "Anarchistische Bibliothek", "url": "https://anarchistischebibliothek.org/feed"},
        {"name": "The Anarchist Library", "url": "https://theanarchistlibrary.org/feed"}
    ]
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
alle_artikel = []

for kontinent, feeds in quellen.items():
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed['url'])
            for entry in parsed.entries[:4]: # Holt die 4 neuesten Artikel pro Quelle
                link = entry.get('link', '')
                title = entry.get('title', 'Kein Titel')
                pubDate = entry.get('published', datetime.now().isoformat())

                full_text = ""
                image_url = ""

                # 1. Versuche, ein Bild direkt aus dem RSS-Feed zu fischen
                if 'media_content' in entry and len(entry.media_content) > 0:
                    image_url = entry.media_content[0].get('url', '')

                if link:
                    try:
                        # Geht auf die echte Webseite und kratzt den vollen Text und das Bild
                        html = requests.get(link, headers=headers, timeout=10).text
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # BILD SUCHEN (Wenn der Feed kein Bild geliefert hat)
                        if not image_url:
                            # Methode A: Das unsichtbare Meta-Vorschaubild (oft das beste)
                            og_img = soup.find('meta', property='og:image')
                            if og_img and og_img.get('content'):
                                image_url = og_img['content']
                            else:
                                # Methode B: Das allererste Bild im Artikel nehmen
                                first_img = soup.find('img')
                                if first_img and first_img.get('src'):
                                    image_url = urljoin(link, first_img.get('src'))

                        # TEXT SUCHEN
                        paragraphs = soup.find_all('p')
                        text_blocks = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20]
                        full_text = "\n\n".join(text_blocks)
                    except:
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
                    "image": image_url  # Hier wird das gefundene Bild gespeichert!
                })
        except:
            pass

with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(alle_artikel, f, ensure_ascii=False, indent=2)
