import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from urllib.parse import urljoin

# Kontinente jetzt auf Englisch für die App-Struktur
quellen = {
    "Europe": [
        {"name": "Indymedia DE", "url": "https://de.indymedia.org/rss.xml"},
        {"name": "Antifa Infoblatt", "url": "https://www.antifainfoblatt.de/rss.xml"},
        {"name": "Squat!net", "url": "https://de.squat.net/feed/"},
        {"name": "Tierbefreier", "url": "https://tierbefreier.org/feed/"},
        {"name": "Enough is Enough", "url": "https://enoughisenough14.org/feed/"},
        {"name": "Freedom News", "url": "https://freedomnews.org.uk/feed/"}
    ],
    "Africa": [
        {"name": "Pambazuka News", "url": "https://www.pambazuka.org/rss.xml"},
        {"name": "Zabalaza", "url": "https://zabalaza.net/feed/"},
        {"name": "ROAPE", "url": "https://roape.net/feed/"}
    ],
    "North America": [
        {"name": "It's Going Down", "url": "https://itsgoingdown.org/feed/"},
        {"name": "Rose City Antifa", "url": "https://rosecityantifa.org/feed.xml"},
        {"name": "Montreal Antifasciste", "url": "https://montreal-antifasciste.info/fr/feed/"},
        {"name": "Earth First!", "url": "https://earthfirstjournal.news/feed/"},
        {"name": "CrimethInc.", "url": "https://crimethinc.com/feed"}
    ],
    "Latin America": [
        {"name": "El Libertario", "url": "http://periodicoellibertario.blogspot.com/feeds/posts/default"},
        {"name": "Avispa Midia", "url": "https://avispa.org/feed/"},
        {"name": "Desinformémonos", "url": "https://desinformemonos.org/feed/"}
    ],
    "Asia": [
        {"name": "Lausan", "url": "https://lausan.hk/feed/"},
        {"name": "Chuang", "url": "https://chuangcn.org/feed/"},
        {"name": "New Bloom", "url": "https://newbloommag.net/feed/"}
    ],
    "Australia & NZ": [
        {"name": "MACG", "url": "https://melbacg.wordpress.com/feed/"},
        {"name": "Slackbastard", "url": "https://slackbastard.anarchobase.com/?feed=rss2"},
        {"name": "Green Left", "url": "https://www.greenleft.org.au/rss.xml"},
        {"name": "AWSM", "url": "https://awsm.nz/feed/"}
    ],
    "Libraries": [
        {"name": "Anarchistische Bibliothek (DE)", "url": "https://anarchistischebibliothek.org/feed"},
        {"name": "The Anarchist Library (EN)", "url": "https://theanarchistlibrary.org/feed"},
        {"name": "Biblioteca Anarquista (ES)", "url": "https://es.theanarchistlibrary.org/feed"},
        {"name": "Bibliothèque Anarchiste (FR)", "url": "https://fr.theanarchistlibrary.org/feed"},
        {"name": "Libreria Anarchica (IT)", "url": "https://it.theanarchistlibrary.org/feed"},
        {"name": "Biblioteca Anarquista (PT)", "url": "https://pt.theanarchistlibrary.org/feed"},
        {"name": "Zabalaza Books (Africa)", "url": "https://zabalazabooks.net/feed/"},
        {"name": "Libcom Library", "url": "https://libcom.org/library/feed"}
    ]
}

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
alle_artikel = []

for kontinent, feeds in quellen.items():
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed['url'])
            # Limit erhöht auf 10, damit der Datums-Filter mehr Sinn macht!
            for entry in parsed.entries[:10]: 
                link = entry.get('link', '')
                title = entry.get('title', 'Kein Titel')
                pubDate = entry.get('published', datetime.now().isoformat())

                full_text = ""
                image_url = ""

                if 'media_content' in entry and len(entry.media_content) > 0:
                    image_url = entry.media_content[0].get('url', '')

                if link:
                    try:
                        html = requests.get(link, headers=headers, timeout=10).text
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        if not image_url:
                            og_img = soup.find('meta', property='og:image')
                            if og_img and og_img.get('content'):
                                image_url = og_img['content']
                            else:
                                first_img = soup.find('img')
                                if first_img and first_img.get('src'):
                                    image_url = urljoin(link, first_img.get('src'))

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
                    "image": image_url
                })
        except:
            pass

with open('news.json', 'w', encoding='utf-8') as f:
    json.dump(alle_artikel, f, ensure_ascii=False, indent=2)
