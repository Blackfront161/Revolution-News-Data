window.onerror = function(msg, url, line, col, error) {
    const stat = document.getElementById('status-container');
    if (stat) { stat.style.color = '#FF0033'; stat.innerText = `CRASH GEFUNDEN: ${msg} (Zeile ${line})`; }
    return false;
};

// DER CACHE-BYPASS LINK FÜR SOFORTIGE UPDATES
const GITHUB_JSON_URL = "https://blackfront161.github.io/Revolution-News-Data/news.json";
const PROXY_URL = "https://revolution-proxy.paghklo.workers.dev";
let capVal1 = 0; let capVal2 = 0;

// Wandelt beliebigen Text so um, dass er gefahrlos in einen HTML-String eingesetzt werden kann.
function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Erlaubt bei externen Links und Bildern ausschließlich http:// und https://.
function getSafeHttpUrl(value) {
    try {
        const url = new URL(String(value ?? ""));
        if (url.protocol === "http:" || url.protocol === "https:") return url.href;
    } catch (error) {}
    return "";
}

// Kodiert Text für Inline-Button-Aufrufe, damit Anführungszeichen keinen Code beschädigen.
function encodeText(value) {
    return btoa(unescape(encodeURIComponent(String(value ?? ""))));
}

function decodeText(value) {
    return decodeURIComponent(escape(atob(value)));
}

// Fügt übersetzten Klartext mit sichtbaren Zeilenumbrüchen ein, ohne HTML auszuführen.
function appendMultilineText(element, text, addEmptyLine = false) {
    if (!element) return;
    if (addEmptyLine && element.childNodes.length > 0) {
        element.append(document.createElement("br"), document.createElement("br"));
    }
    const lines = String(text ?? "").split("\n");
    lines.forEach((line, index) => {
        if (index > 0) element.append(document.createElement("br"));
        element.append(document.createTextNode(line));
    });
}

function changeFontSize(sizeValue) {
    document.documentElement.style.fontSize = sizeValue + "%";
    localStorage.setItem('wrn_font_zoom', sizeValue);
}

async function fetchFromGemini(promptText) {
    try {
        const response = await fetch(PROXY_URL, {
            method: "POST",
            // ACHTUNG: Dieser Header ist im Browser sichtbar und deshalb kein echtes Geheimnis.
            // Er bleibt vorerst erhalten, damit dein vorhandener Worker weiter funktioniert.
            headers: { "Content-Type": "application/json", "X-App-Secret": "revolution161" },
            body: JSON.stringify({ contents: [{ parts: [{ text: promptText }] }] })
        });

        if (!response.ok) {
            console.error("Übersetzungsserver antwortet mit Status", response.status);
            return { error: true };
        }

        const data = await response.json();
        if (data.error || !data.candidates) return { error: true };
        return data;
    } catch (error) {
        console.error("Übersetzungsfehler:", error);
        return { error: true };
    }
}

const starSpinner = `<svg class="spinner" viewBox="0 0 24 24" width="1.4em" height="1.4em"><path fill="url(#rbGrad)" stroke="var(--color-accent)" stroke-width="0.5" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>`;
const rbStar = `<svg viewBox="0 0 24 24" width="1.2em" height="1.2em" style="vertical-align: sub; margin-left: 4px;"><path fill="url(#rbGrad)" stroke="#FF0000" stroke-width="0.5" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>`;

const uiTexte = {
    en: {
        init: "Loading data...", error: "Offline Mode.", btnTranslate: "Translate", btnLoading: "Translating...", btnDone: "Translated",
        btnReadMore: "Original", btnExpand: "Read More ⬇️", btnCollapse: "Collapse ⬆️", filterAll: "All Portals", sortNew: "Newest", sortOld: "Oldest",
        searchRegion: "🌍 Region", searchTopic: "🏷️ Topic", latestNews: "Latest Updates:", translatingRest: "Translating remaining text...",
        topBookmarks: "Bookmarks", btnDonateTop: "Donate", donateTitle: "Support the Project", 
        donateBody: "This project runs independently. Donations are voluntary.", donateWarning: "⚠️ WARNING: By proceeding, you are leaving the anonymous app environment and will be redirected to PayPal.",
        btnPaypal: "Continue to PayPal", btnDonateCancel: "Close", dateLabel: "DATE:", langLabel: "Translate to:",
        searchPlace: "Search articles...", bookmarkCat: "Saved Bookmarks", btnBookmark: "Bookmark" + rbStar, btnUnbookmark: "Saved" + rbStar,
        themeLabel: "Design:", themeDark: "Dark", themeLight: "Light", clearBtn: "Clear Cache 🗑️",
        catGlobal: "Global", catEurope: "Europe", catAfrica: "Africa", catNorthAmerica: "North Am.", catLatinAmerica: "Latin Am.", catAsia: "Asia", catAustralia: "Australia",
        catLabor: "Labor", catAntifascism: "Antifa", catAntisexism: "Antisexism", catQueer: "Queer", catAntiracism: "Antiracism", catNoBorders: "No Borders", catAnticapitalism: "Anti-Cap", catTheory: "Theory", catAnticolonialism: "Anti-Col", catAntiimperialism: "Anti-Imp", catSquatting: "Housing/Squats", catDemos: "Demos", catAntirepression: "Anti-Rep/Prisons", catCyber: "Cyber", catNoWar: "No War", catAnimal: "Animal Lib", catEco: "Eco-Anarchy", catIndigenous: "Indigenous", catHealth: "Health/Disability", catLibraries: "Libraries",
        fbBtn: "💬 Contact", fbTitle: "Contact", fbPlace: "Write your ideas or bug reports here...", fbCaptcha: "Captcha: What is", fbCancel: "Cancel", fbSend: "Send via Mail", fbErrCap: "Captcha is wrong!", fbErrEmpty: "Please write something first.",
        infoBtn: "ℹ️ Info", infoTitle: "App Info & Security (OPSEC)", archiveTitle: "🗄️ Archive (> 3 Months)", publisherLabel: "SOURCE:", authorLabel: "AUTHOR:", contactLabel: "Contact:",
        radarSummary: "Events & Demos", radarCat: "Events & Demos",
        infoBody: `<p><strong>Passion Project:</strong> This is an independent, non-commercial passion project. It may contain errors. Please report bugs or broken sources via the "Contact" section.</p><p><strong>Local app data:</strong> This app does not require user accounts and does not intentionally set advertising or analytics cookies. Bookmarks, reading history, settings, and the offline news cache are stored locally in your browser.</p><p><strong>External connections:</strong> Loading news data, article images, translations, original articles, and PayPal may connect your browser to external providers. Those providers can receive normal technical connection data such as an IP address.</p><p><strong>Content & AI translations:</strong> This app aggregates external RSS content. AI-generated translations may contain errors. Please check the original source when accuracy is important.</p>`
    },
    de: {
        init: "Lade Daten...", error: "Offline Modus.", btnTranslate: "Übersetzen", btnLoading: "Übersetze...", btnDone: "Übersetzt",
        btnReadMore: "Zum Original", btnExpand: "Weiterlesen ⬇️", btnCollapse: "Zuklappen ⬆️", filterAll: "Alle Quellen", sortNew: "Neueste", sortOld: "Älteste",
        searchRegion: "🌍 Region", searchTopic: "🏷️ Thema", latestNews: "Aktuelle Updates:", translatingRest: "Übersetze Rest...",
        topBookmarks: "Lesezeichen", btnDonateTop: "Spenden", donateTitle: "Projekt unterstützen", 
        donateBody: "Dieses Projekt läuft unabhängig. Spenden von Unterstützer*innen sind freiwillig.", donateWarning: "⚠️ HINWEIS: Wenn du fortfährst, verlässt du die anonyme App-Umgebung und wirst zu PayPal weitergeleitet.",
        btnPaypal: "Weiter zu PayPal", btnDonateCancel: "Schließen", dateLabel: "DATUM:", langLabel: "Übersetzen in:",
        searchPlace: "Artikel suchen...", bookmarkCat: "Lesezeichen", btnBookmark: "Merken" + rbStar, btnUnbookmark: "Gemerkt" + rbStar,
        themeLabel: "Design:", themeDark: "Dunkel", themeLight: "Hell", clearBtn: "Cache löschen 🗑️",
        catGlobal: "Global", catEurope: "Europa", catAfrica: "Afrika", catNorthAmerica: "Nordam.", catLatinAmerica: "Lateinam.", catAsia: "Asien", catAustralia: "Australien",
        catLabor: "Arbeitskämpfe", catAntifascism: "Antifaschismus", catAntisexism: "Antisexismus", catQueer: "Queer-Feminismus", catAntiracism: "Antirassismus", catNoBorders: "No Borders", catAnticapitalism: "Antikapitalismus", catTheory: "Theorie & Strategie", catAnticolonialism: "Antikolonialismus", catAntiimperialism: "Anti-Imperialismus", catSquatting: "Hausbesetzungen", catDemos: "Demonstrationen", catAntirepression: "Anti-Rep & Knast", catCyber: "Cyber-Aktivismus", catNoWar: "Kriegsdienstverweigerung", catAnimal: "Tierbefreiung", catEco: "Ökologie & Klima", catIndigenous: "Indigene Kämpfe", catHealth: "Radical Health", catLibraries: "Bibliotheken",
        fbBtn: "💬 Kontakt", fbTitle: "Kontakt", fbPlace: "Schreibe hier Ideen, Fehler oder neue Quellen...", fbCaptcha: "Captcha: Was ist", fbCancel: "Abbrechen", fbSend: "Senden (Mail)", fbErrCap: "Captcha ist falsch!", fbErrEmpty: "Bitte schreibe zuerst einen Text.",
        infoBtn: "ℹ️ Info", infoTitle: "App Info & Sicherheit", archiveTitle: "🗄️ Archiv (> 3 Monate)", publisherLabel: "QUELLE:", authorLabel: "AUTOR*IN:", contactLabel: "Kontakt:",
        radarSummary: "Termine & Demos", radarCat: "Termine & Demos",
        infoBody: `<p><strong>Aus Leidenschaft:</strong> Dieses Projekt ist ein unabhängiges Leidenschaftsprojekt von und für Aktivist*innen. Bitte melde Bugs oder fehlerhafte Quellen über den Kontakt-Bereich.</p><p><strong>Lokale App-Daten:</strong> Die App benötigt keine Benutzer*innenkonten und setzt selbst keine beabsichtigten Werbe- oder Analyse-Cookies. Lesezeichen, Lesestatus, Einstellungen und der Offline-Nachrichtencache werden lokal in deinem Browser gespeichert.</p><p><strong>Externe Verbindungen:</strong> Beim Laden der Nachrichtendaten, externer Artikelbilder, Übersetzungen, Originalartikel oder von PayPal kann dein Browser Verbindungen zu anderen Anbietern herstellen. Diese Anbieter können dabei übliche technische Verbindungsdaten wie eine IP-Adresse erhalten.</p><p><strong>Inhalte und KI-Übersetzungen:</strong> Die App bündelt fremde RSS-Inhalte. KI-generierte Übersetzungen können Fehler enthalten. Prüfe bei wichtigen Angaben bitte die Originalquelle.</p>`
    },
    es: { btnTranslate: "Traducir", catGlobal: "Global", catEurope: "Europa", searchRegion: "🌍 Región", searchTopic: "🏷️ Tema", radarSummary: "Eventos & Demos", radarCat: "Eventos & Demos" },
    fr: { btnTranslate: "Traduire", catGlobal: "Global", catEurope: "Europe", searchRegion: "🌍 Région", searchTopic: "🏷️ Thème", radarSummary: "Événements & Démos", radarCat: "Événements & Démos" },
    it: { btnTranslate: "Traduci", catGlobal: "Globale", catEurope: "Europa", searchRegion: "🌍 Regione", searchTopic: "🏷️ Tema", radarSummary: "Eventi & Demos", radarCat: "Eventi & Demos" },
    pt: { btnTranslate: "Traduzir", catGlobal: "Global", catEurope: "Europa", searchRegion: "🌍 Região", searchTopic: "🏷️ Tema", radarSummary: "Eventos & Demos", radarCat: "Eventos & Demos" },
    ru: { btnTranslate: "Перевести", catGlobal: "Мир", catEurope: "Европа", searchRegion: "🌍 Регион", searchTopic: "🏷️ Тема", radarSummary: "События и Акции", radarCat: "События и Акции" },
    el: { btnTranslate: "Μετάφραση", catGlobal: "Παγκόσμια", catEurope: "Ευρώπη", searchRegion: "🌍 Περιοχή", searchTopic: "🏷️ Θέμα", radarSummary: "Εκδηλώσεις", radarCat: "Εκδηλώσεις" },
    tr: { btnTranslate: "Çevir", catGlobal: "Küresel", catEurope: "Avrupa", searchRegion: "🌍 Bölge", searchTopic: "🏷️ Konu", radarSummary: "Etkinlikler", radarCat: "Etkinlikler" }
};

const fallbackLang = uiTexte['en'];
Object.keys(uiTexte).forEach(lang => {
    Object.keys(fallbackLang).forEach(key => {
        if (uiTexte[lang][key] === undefined) { uiTexte[lang][key] = fallbackLang[key]; }
    });
});

let currentLang = "en";
let activeKontinent = "Global"; 
let allNewsData = []; 

let currentFilteredItems = []; 
let currentlyDisplayedCount = 0;
const ITEMS_PER_PAGE = 15;
let isRendering = false;

let currentSourceFilter = "ALL"; 
let zineArticles = []; 

function setTxt(id, text) { const e = document.getElementById(id); if (e && text) e.innerText = text; }
function setHtml(id, html) { const e = document.getElementById(id); if (e && html) e.innerHTML = html; }
function setPh(id, text) { const e = document.getElementById(id); if (e && text) e.placeholder = text; }

function changeTheme(themeName) {
    const body = document.getElementById('app-body');
    if(body) {
        body.classList.remove('theme-dark', 'theme-light'); body.classList.add(themeName);
        localStorage.setItem('wrn_theme_style', themeName);
    }
}

function clearAllData() {
    const confirmTxt = currentLang === "de" ? "Möchtest du wirklich alle Daten und Einstellungen restlos löschen?" : "Completely clear all bookmarks, history, and settings?";
    if (confirm(confirmTxt)) { localStorage.clear(); window.location.reload(); }
}

function changeLanguage() {
    const langSelect = document.getElementById('ui-language');
    if(langSelect) { currentLang = langSelect.value; }
    localStorage.setItem('wrn_system_lang', currentLang); 
    
    const t = uiTexte[currentLang] || uiTexte['en'];
    document.documentElement.lang = currentLang;
    
    setTxt('txt-lang-label', t.langLabel); setTxt('txt-theme-label', t.themeLabel); setTxt('opt-theme-dark', t.themeDark); setTxt('opt-theme-light', t.themeLight); setTxt('btn-clear-cache', t.clearBtn); setTxt('txt-region-summary', t.searchRegion); setTxt('txt-topic-summary', t.searchTopic); setTxt('txt-archive-title', t.archiveTitle); setTxt('txt-contact-label', t.contactLabel); setTxt('opt-sort-new', t.sortNew); setTxt('opt-sort-old', t.sortOld); setTxt('txt-top-bookmarks', t.topBookmarks); setTxt('txt-donate-btn', t.btnDonateTop); setTxt('txt-donate-title', t.donateTitle); setTxt('txt-donate-body', t.donateBody); setTxt('txt-donate-warning', t.donateWarning); setTxt('btn-paypal', t.btnPaypal); setTxt('btn-donate-cancel', t.btnDonateCancel); setPh('search-input', t.searchPlace);
    
    setTxt('btn-glob', t.catGlobal); setTxt('btn-eur', t.catEurope); setTxt('btn-afr', t.catAfrica); setTxt('btn-nam', t.catNorthAmerica); setTxt('btn-lam', t.catLatinAmerica); setTxt('btn-asi', t.catAsia); setTxt('btn-aus', t.catAustralia);
    setTxt('cat-labor', t.catLabor); setTxt('cat-antifascism', t.catAntifascism); setTxt('cat-antisexism', t.catAntisexism); setTxt('cat-queer', t.catQueer); setTxt('cat-antiracism', t.catAntiracism); setTxt('cat-noborders', t.catNoBorders); setTxt('cat-anticapitalism', t.catAnticapitalism); setTxt('cat-theory', t.catTheory); setTxt('cat-anticolonialism', t.catAnticolonialism); setTxt('cat-antiimperialism', t.catAntiimperialism); setTxt('cat-squatting', t.catSquatting); setTxt('cat-demos', t.catDemos); setTxt('cat-antirepression', t.catAntirepression); setTxt('cat-cyber', t.catCyber); setTxt('cat-nowar', t.catNoWar); setTxt('cat-animal', t.catAnimal); setTxt('cat-eco', t.catEco); setTxt('cat-indigenous', t.catIndigenous); setTxt('cat-health', t.catHealth); setTxt('btn-lib', t.catLibraries); 
    setTxt('txt-radar-summary', t.radarSummary);

    setTxt('btn-open-info', "ℹ️ " + t.infoBtn); setTxt('txt-info-title', t.infoTitle); setHtml('txt-info-body', t.infoBody); setTxt('btn-open-feedback', t.fbBtn); setTxt('txt-fb-title', t.fbTitle); setPh('fb-text', t.fbPlace); setTxt('txt-captcha-q', t.fbCaptcha); setTxt('btn-fb-cancel', t.fbCancel); setTxt('btn-fb-send', t.fbSend);
    
    if(activeKontinent === "Bookmarks") { showBookmarks(); } else if (allNewsData.length > 0) { setTxt('status-container', t.latestNews); applyFilters(); }
}

function getSavedBookmarks() { return JSON.parse(localStorage.getItem('wrn_bookmarks') || '[]'); }
function getReadArticles() { return JSON.parse(localStorage.getItem('wrn_read_list') || '[]'); }

function markAsRead(link, idNum) {
    let readList = getReadArticles();
    if (!readList.includes(link)) { readList.push(link); localStorage.setItem('wrn_read_list', JSON.stringify(readList)); }
    const card = document.getElementById(`card-${idNum}`); if(card) card.classList.add('read');
}

function toggleBookmark(idNum) {
    let bookmarks = getSavedBookmarks(); let article = currentFilteredItems[idNum];
    let existingIdx = bookmarks.findIndex(b => b.link === article.link);
    const t = uiTexte[currentLang] || uiTexte['en'];

    if (existingIdx > -1) { bookmarks.splice(existingIdx, 1); setHtml(`bmark-${idNum}`, t.btnBookmark); } 
    else { bookmarks.push(article); setHtml(`bmark-${idNum}`, t.btnUnbookmark); }
    
    localStorage.setItem('wrn_bookmarks', JSON.stringify(bookmarks));
    if(activeKontinent === "Bookmarks") showBookmarks();
}

// Wird nur beim Klick auf den Lesezeichen-Button benutzt und schaltet die Ansicht um.
function ladeBookmarks() {
    if (activeKontinent === "Bookmarks") {
        ladeKontinentNews("Global");
        return;
    }
    showBookmarks();
}

// Zeigt oder aktualisiert die Lesezeichen, ohne unbeabsichtigt zu Global zurückzuspringen.
function showBookmarks() {
    activeKontinent = "Bookmarks";
    const rawBookmarks = getSavedBookmarks();

    document.querySelectorAll('.btn-nav').forEach(btn => btn.classList.remove('active'));
    const bBtn = document.getElementById('btn-bookmarks');
    if (bBtn) bBtn.classList.add('active');

    const t = uiTexte[currentLang] || uiTexte['en'];
    setTxt('status-container', t.bookmarkCat + ` (${rawBookmarks.length})`);

    currentSourceFilter = "ALL";
    currentFilteredItems = rawBookmarks;
    applyFilters(true);
}

function addToZine(globalIndex) {
    let article = currentFilteredItems[globalIndex];
    if(!zineArticles.includes(article)) {
        zineArticles.push(article);
        document.getElementById('txt-zine-count').innerText = `📄 Zine (${zineArticles.length})`;
        alert(currentLang === "de" ? "Artikel zum Zine hinzugefügt!" : "Article added to Zine!");
    } else {
        alert(currentLang === "de" ? "Dieser Artikel ist schon in deinem Zine." : "Article is already in your Zine.");
    }
}

function printZine() {
    if(zineArticles.length === 0) {
        alert(currentLang === "de" ? "Dein Zine ist noch leer! Füge zuerst Artikel hinzu." : "Your Zine is empty! Add articles first.");
        return;
    }
    
    let printWindow = window.open('', '_blank');
    let html = `<html><head><title>Zine Export</title>
    <style>
        body { font-family: serif; color: black; background: white; margin: 20px; line-height: 1.4; }
        .zine-article { column-count: 2; column-gap: 30px; margin-bottom: 40px; border-bottom: 2px solid black; padding-bottom: 20px; }
        h1 { font-family: sans-serif; text-transform: uppercase; font-size: 1.5em; column-span: all; text-align: center; border-bottom: 1px solid black; padding-bottom: 10px;}
        .meta { font-style: italic; font-size: 0.8em; margin-bottom: 15px; column-span: all; text-align: center; }
        p { text-indent: 15px; margin-top: 0; }
        @media print { body { margin: 0; } }
    </style>
    </head><body>`;

    zineArticles.forEach(a => {
        html += `<div class="zine-article">`;
        html += `<h1>${escapeHtml(a.title || 'Kein Titel')}</h1>`;
        html += `<div class="meta">Quelle: ${escapeHtml(a.quelleName || 'Unknown')} | Datum: ${escapeHtml(a.pubDate ? a.pubDate.substring(0,10) : '')}</div>`;
        html += `<p>${escapeHtml(a.content || '').replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')}</p>`;
        html += `</div>`;
    });

    html += `</body></html>`;
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    
    setTimeout(() => { printWindow.print(); }, 500);
}

function openDonate() { const ov = document.getElementById('fb-overlay'); if(ov) ov.style.display = 'block'; const md = document.getElementById('donate-modal'); if(md) md.style.display = 'block'; }
function openFeedback() {
    const ov = document.getElementById('fb-overlay'); if(ov) ov.style.display = 'block'; const md = document.getElementById('fb-modal'); if(md) md.style.display = 'block';
    capVal1 = Math.floor(Math.random() * 10) + 1; capVal2 = Math.floor(Math.random() * 10) + 1;
    setTxt('captcha-num1', capVal1); setTxt('captcha-num2', capVal2);
    const ca = document.getElementById('captcha-answer'); if(ca) ca.value = ''; const ft = document.getElementById('fb-text'); if(ft) ft.value = '';
}
function openInfo() { const ov = document.getElementById('fb-overlay'); if(ov) ov.style.display = 'block'; const md = document.getElementById('info-modal'); if(md) md.style.display = 'block'; }
function closeAllModals() { 
    const ov = document.getElementById('fb-overlay'); if(ov) ov.style.display = 'none'; 
    const m1 = document.getElementById('fb-modal'); if(m1) m1.style.display = 'none'; 
    const m2 = document.getElementById('info-modal'); if(m2) m2.style.display = 'none'; 
    const m3 = document.getElementById('donate-modal'); if(m3) m3.style.display = 'none'; 
    const m4 = document.getElementById('sources-modal'); if(m4) m4.style.display = 'none'; 
}
function submitFeedback() {
    const ca = document.getElementById('captcha-answer'); const ft = document.getElementById('fb-text'); if(!ca || !ft) return;
    const userAnswer = parseInt(ca.value); const text = ft.value.trim(); const t = uiTexte[currentLang] || uiTexte['en'];
    if (text === "") { alert(t.fbErrEmpty); return; }
    if (userAnswer !== (capVal1 + capVal2)) { alert(t.fbErrCap); return; }
    window.location.href = `mailto:worldrevnews@brief.li?subject=Contact&body=${encodeURIComponent(text)}`; closeAllModals();
}

function openSourcesModal() {
    const ov = document.getElementById('fb-overlay');
    if (ov) ov.style.display = 'block';

    const md = document.getElementById('sources-modal');
    if (md) md.style.display = 'block';

    const listContainer = document.getElementById('sources-list-container');
    if (!listContainer) return;
    listContainer.textContent = '';

    const t = uiTexte[currentLang] || uiTexte['en'];

    const createSourceButton = (label, sourceName, isActive, isAll = false) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn-micro';
        button.style.width = '100%';
        button.style.textAlign = 'left';
        button.style.padding = '10px';
        button.style.fontSize = '0.8rem';
        button.style.justifyContent = 'flex-start';

        if (isAll) {
            button.style.borderColor = 'var(--color-green)';
            button.style.color = 'var(--color-green)';
        } else if (isActive) {
            button.style.background = 'rgba(0, 240, 255, 0.2)';
            button.style.borderColor = 'var(--color-cyan)';
            button.style.color = 'var(--text-main)';
        }

        button.textContent = label;
        button.addEventListener('click', () => filterBySource(sourceName));
        return button;
    };

    listContainer.append(createSourceButton(`🌍 ${t.filterAll}`, 'ALL', currentSourceFilter === 'ALL', true));

    const baseList = (activeKontinent === 'Bookmarks')
        ? getSavedBookmarks()
        : allNewsData.filter(item => item.kontinent === activeKontinent);

    const portals = [...new Set(baseList.map(item => item.quelleName).filter(Boolean))].sort();
    portals.forEach(portal => {
        listContainer.append(createSourceButton(portal, portal, currentSourceFilter === portal));
    });
}

function filterBySource(sourceName) { currentSourceFilter = sourceName; closeAllModals(); applyFilters(); }

async function initialisiereApp() {
    setTxt('status-container', "Lade Daten...");
    let hasCache = false;
    
    try {
        const res = await fetch(GITHUB_JSON_URL + "?v=" + new Date().getTime());
        const fetchedData = await res.json();
        
        allNewsData = fetchedData;
        try { localStorage.setItem('cached_news_data', JSON.stringify(allNewsData)); } catch(e) {}
        hasCache = true;
        ladeKontinentNews("Global");
    } catch (err) {
        try {
            const offlineData = localStorage.getItem('cached_news_data');
            if (offlineData && offlineData.length > 10) {
                allNewsData = JSON.parse(offlineData);
                ladeKontinentNews("Global");
            } else {
                setTxt('status-container', "[ FEHLER ] Keine Daten und kein Internet.");
            }
        } catch(e) {
            setTxt('status-container', "[ FEHLER ] Keine Daten und kein Internet.");
        }
    }
}

function ladeKontinentNews(kontinent) {
    if(kontinent === "Bookmarks") return ladeBookmarks();
    activeKontinent = kontinent; currentSourceFilter = "ALL"; 
    
    document.querySelectorAll('.btn-nav').forEach(btn => btn.classList.remove('active'));
    const btnMap = { 'Global': 'btn-glob', 'Europe': 'btn-eur', 'Africa': 'btn-afr', 'North America': 'btn-nam', 'Latin America': 'btn-lam', 'Asia': 'btn-asi', 'Australia & NZ': 'btn-aus', 'Labor Struggles': 'cat-labor', 'Antifascism': 'cat-antifascism', 'Antisexism': 'cat-antisexism', 'Queer-Feminism': 'cat-queer', 'Antiracism': 'cat-antiracism', 'No Borders': 'cat-noborders', 'Anticapitalism': 'cat-anticapitalism', 'Theory & Strategy': 'cat-theory', 'Anticolonialism': 'cat-anticolonialism', 'Anti-Imperialism': 'cat-antiimperialism', 'Squatting & Housing': 'cat-squatting', 'Demonstrations': 'cat-demos', 'Anti-Rep & Prisons': 'cat-antirepression', 'Cyberactivism': 'cat-cyber', 'No War': 'cat-nowar', 'Animal Liberation': 'cat-animal', 'Eco-Anarchism': 'cat-eco', 'Indigenous Struggles': 'cat-indigenous', 'Radical Health & Disability': 'cat-health', 'Libraries': 'btn-lib', 'Radar': 'cat-radar' };
    if(btnMap[kontinent]) { const b = document.getElementById(btnMap[kontinent]); if(b) b.classList.add('active'); }

    const t = uiTexte[currentLang] || uiTexte['en']; setTxt('status-container', t.latestNews);
    applyFilters();
}

function applyFilters(isBookmark = false) {
    const iSel = document.getElementById('search-input');
    const selPortal = currentSourceFilter || "ALL"; 
    const searchQuery = iSel ? iSel.value.toLowerCase().trim() : "";
    const sortOrder = document.getElementById('sort-select') ? document.getElementById('sort-select').value : "new";
    
    let baseList = (activeKontinent === "Bookmarks" || isBookmark) ? getSavedBookmarks() : allNewsData.filter(item => item.kontinent === activeKontinent);
    let filtered = (selPortal === "ALL") ? baseList : baseList.filter(a => a.quelleName === selPortal);
    
    if (searchQuery !== "") { filtered = filtered.filter(a => (a.title && a.title.toLowerCase().includes(searchQuery)) || (a.content && a.content.toLowerCase().includes(searchQuery))); }

    filtered.sort((a, b) => {
        let da = 0; let db = 0;
        if(a.pubDate) da = new Date(a.pubDate).getTime(); if(b.pubDate) db = new Date(b.pubDate).getTime();
        if (sortOrder === "old") return (isNaN(da) ? 0 : da) - (isNaN(db) ? 0 : db); 
        else return (isNaN(db) ? 0 : db) - (isNaN(da) ? 0 : da); 
    });
    
    currentFilteredItems = filtered;
    currentlyDisplayedCount = 0;
    
    const container = document.getElementById('feed-container'); const archiveContainer = document.getElementById('archive-container');
    if(container) container.innerHTML = "";
    if(archiveContainer) archiveContainer.innerHTML = "";
    
    renderNextBatch();
}

// === DER REPARIERTE RENDER-BLOCK FÜR ABSÄTZE UND HTML-SCHUTZ ===
function renderNextBatch() {
    if (isRendering) return;
    isRendering = true;

    const container = document.getElementById('feed-container'); 
    const archiveContainer = document.getElementById('archive-container'); 
    const archiveTitle = document.getElementById('txt-archive-title');
    if(!container || !archiveContainer) { isRendering = false; return; }
    
    const batch = currentFilteredItems.slice(currentlyDisplayedCount, currentlyDisplayedCount + ITEMS_PER_PAGE);
    
    if (batch.length === 0 && currentlyDisplayedCount === 0) { 
        container.innerHTML = `<div style="padding:20px; text-align:center; color:var(--text-muted); font-family:monospace;">[ NO DATA FOUND ]</div>`;
        isRendering = false; return; 
    } 

    const t = uiTexte[currentLang] || uiTexte['en'];
    let bookmarks = getSavedBookmarks(); let readList = getReadArticles();
    const today = new Date(); const ninetyDaysMs = 90 * 24 * 60 * 60 * 1000;
    let archiveCount = archiveContainer.children.length; 
    
    batch.forEach((item, batchIndex) => {
        const globalIndex = currentlyDisplayedCount + batchIndex; 
        let formatDatum = "LIVE"; let isOld = false;
        try {
            if (item.pubDate) {
                const articleDate = new Date(item.pubDate);
                if (!isNaN(articleDate.getTime())) {
                    formatDatum = articleDate.toISOString().substring(0, 10);
                    if ((today - articleDate) > ninetyDaysMs) { isOld = true; }
                }
            }
        } catch(e) {}

        const fullText = item.content || "Text not available.";
        
        // NEU: Wandelt die Python-Zeilenumbrüche sicher in echte HTML-Absätze (<br>) um!
        const safeFullText = fullText.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\n/g, "<br>");
        
        let teaserText = fullText.substring(0, 100) + "...";
        try { const sentenceMatch = fullText.match(/[^.!?]+[.!?]+/); if(sentenceMatch) teaserText = sentenceMatch[0]; } catch(e) {}
        const safeTeaserText = teaserText.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        
        const safeImageUrl = getSafeHttpUrl(item.image);
        const safeArticleUrl = getSafeHttpUrl(item.link);
        const encodedArticleLink = encodeText(item.link || '');
        const encodedArticleTitle = encodeText(item.title || '');
        const imgHtml = safeImageUrl
            ? `<img src="${escapeHtml(safeImageUrl)}" class="article-img" style="display:block;" loading="lazy" referrerpolicy="no-referrer" alt="${escapeHtml(item.title || '')}">`
            : '';

        let isSaved = bookmarks.some(b => b.link === item.link); let bookmarkTxt = isSaved ? t.btnUnbookmark : t.btnBookmark;
        let isReadClass = readList.includes(item.link) ? "read" : "";

        let publisherName = item.quelleName ? item.quelleName.trim() : "Unbekannte Quelle";
        let authorName = item.author ? item.author.trim() : "";
        
        let isRadar = (item.kontinent === "Radar");
        // Der grüne Look für die Termine
        let cardStyle = isRadar ? `style="border: 1px solid var(--color-green); box-shadow: 0 0 15px rgba(0, 255, 0, 0.15);"` : "";
        let titleColor = isRadar ? `color: var(--color-green);` : "";
        
        let metaHtml = `<span class="meta-label">${escapeHtml(t.publisherLabel)}</span> <span style="color:var(--text-main);">${escapeHtml(publisherName)}</span> <br>`;
        if (authorName !== "" && authorName.toLowerCase() !== "unknown" && authorName.toLowerCase() !== publisherName.toLowerCase()) {
            metaHtml += `<span class="meta-label">${escapeHtml(t.authorLabel)}</span> <span style="color:var(--text-main);">${escapeHtml(authorName)}</span> <br>`;
        }
        metaHtml += `<span class="meta-label">${escapeHtml(t.dateLabel)}</span> <span style="color:var(--text-main);">${escapeHtml(formatDatum)}</span>`;

        let articleHTML = `
            <div class="card ${isReadClass}" id="card-${globalIndex}" data-translated="none" ${cardStyle}>
                <div class="meta">${metaHtml}</div>
                <div class="title" id="title-${globalIndex}" style="${titleColor}">${escapeHtml(item.title || 'No Title')}</div>
                ${imgHtml}
                <div class="teaser" id="teaser-${globalIndex}">${safeTeaserText}</div>
                <div class="full-content" id="content-${globalIndex}">${safeFullText}</div>
                <div class="button-row">
                    <button class="btn-expand" id="expand-${globalIndex}" onclick="toggleArticle(${globalIndex}, event)">${t.btnExpand}</button>
                    <button class="btn-translate" id="btn-${globalIndex}" onclick="translateArticle(${globalIndex})"><span>[ ${t.btnTranslate} ]</span></button>
                    <button class="btn-translate" style="border-color: #B026FF; color: #B026FF;" id="bmark-${globalIndex}" onclick="toggleBookmark(${globalIndex})">${bookmarkTxt}</button>
                    <button class="btn-translate" style="border-color: #00FFCC; color: #00FFCC;" onclick="addToZine(${globalIndex})">[ 📄 ZINE ]</button>
                    <button class="btn-translate" style="border-color: var(--color-cyan); color: var(--color-cyan);" onclick="shareArticle('${encodedArticleTitle}', '${encodedArticleLink}')">[ SHARE 🔗 ]</button>
                    ${safeArticleUrl ? `<a href="${escapeHtml(safeArticleUrl)}" target="_blank" rel="noopener noreferrer" referrerpolicy="no-referrer" class="btn-translate" style="border-color: var(--color-accent); color: var(--color-accent); text-decoration:none;" onclick="markAsRead(decodeText('${encodedArticleLink}'), ${globalIndex})">[ ${escapeHtml(t.btnReadMore)} ]</a>` : ''}
                </div>
            </div>
        `;

        if (isOld) { archiveContainer.insertAdjacentHTML('beforeend', articleHTML); archiveCount++; } 
        else { container.insertAdjacentHTML('beforeend', articleHTML); }
    });

    if (archiveTitle) { if (archiveCount > 0) { archiveTitle.style.display = "block"; } else { archiveTitle.style.display = "none"; } }
    
    currentlyDisplayedCount += batch.length;
    isRendering = false;
}

function shareArticle(encodedTitle, encodedLink) {
    try {
        const title = decodeText(encodedTitle); const link = decodeText(encodedLink);
        if (navigator.share) { navigator.share({ title: title, url: link }).catch(console.error); } 
        else { navigator.clipboard.writeText(title + " - " + link); alert("Link copied to clipboard!"); }
    } catch(e) {}
}

// === DER REPARIERTE KLICK-BLOCK ===
async function toggleArticle(idNum, event) {
    if (event) event.stopPropagation(); // <-- Verhindert das automatische Schließen
    
    const teaser = document.getElementById(`teaser-${idNum}`); 
    const fullContent = document.getElementById(`content-${idNum}`);
    const btn = document.getElementById(`expand-${idNum}`); 
    const card = document.getElementById(`card-${idNum}`);
    if(!teaser || !fullContent || !btn || !card) return;
    const t = uiTexte[currentLang] || uiTexte['en'];

    try { markAsRead(currentFilteredItems[idNum].link, idNum); } catch(e){}

    if (card.dataset.expanded === "true") {
        teaser.style.display = "block"; fullContent.style.display = "none";
        btn.innerText = t.btnExpand; card.dataset.expanded = "false";
    } else {
        teaser.style.display = "none"; fullContent.style.display = "block";
        btn.innerText = t.btnCollapse; card.dataset.expanded = "true";
    }
}


function translateArticle(idNum) {
    const titleEl = document.getElementById('title-' + idNum); const teaserEl = document.getElementById('teaser-' + idNum);
    const contentEl = document.getElementById('content-' + idNum); const btnEl = document.getElementById('btn-' + idNum); const card = document.getElementById('card-' + idNum);
    if(!titleEl || !teaserEl || !contentEl || !btnEl || !card) return;
    
    const t = uiTexte[currentLang] || uiTexte['en'];

    if(card.dataset.translated === "full" || card.dataset.translated === "translating") return;
    try { markAsRead(currentFilteredItems[idNum].link, idNum); } catch(e){}

    card.dataset.translated = "translating"; 
    const isExpanded = (contentEl.style.display === "block");
    
    let zielSprache = "English"; const sel = document.getElementById('ui-language');
    if(sel && sel.options[sel.selectedIndex]) zielSprache = sel.options[sel.selectedIndex].text;
    let genderInstruction = (zielSprache === "Deutsch") ? " Achte bei der deutschen Übersetzung unbedingt auf geschlechtergerechte Sprache (Gendern mit Sternchen, z.B. Aktivist*innen)." : "";

    if (!isExpanded) {
        btnEl.innerHTML = `${starSpinner} <span style="margin-left: 8px;">[ ${t.btnLoading} ]</span>`;
        let promptText = `Translate title and text fluently into ${zielSprache}.${genderInstruction} Separate with "---". \n\nTitle: ${titleEl.innerText}\n\nText: ${teaserEl.innerText}`;
        
        fetchFromGemini(promptText).then(data => {
            if (data.error) { btnEl.innerHTML = "[ ERROR ]"; card.dataset.translated = "none"; return; }
            const parts = data.candidates[0].content.parts[0].text.split("---");
            if (parts.length >= 2) {
                let transTitle = parts[0].trim();
                if(transTitle) titleEl.innerText = transTitle;
                teaserEl.innerText = parts[1].trim();
            } else {
                teaserEl.innerText = data.candidates[0].content.parts[0].text.trim();
            }
            titleEl.classList.add('translated'); btnEl.innerHTML = `[ ${t.btnDone} ]`; card.dataset.translated = "teaser";
        });
    } else {
        let rawText = contentEl.innerText;
        let paragraphs = rawText.split(/\n\n+/);
        let chunks = [];
        let currentChunk = "";

        for(let p of paragraphs) {
            if ((currentChunk.length + p.length) > 1800) {
                if(currentChunk) chunks.push(currentChunk.trim());
                currentChunk = p;
            } else {
                currentChunk += (currentChunk ? "\n\n" : "") + p;
            }
        }
        if(currentChunk) chunks.push(currentChunk.trim());

        contentEl.textContent = ""; 
        let isError = false;

        const processChunks = async () => {
            for (let i = 0; i < chunks.length; i++) {
                let progressText = chunks.length > 1 ? `[ ${t.btnLoading} ${i+1}/${chunks.length} ]` : `[ ${t.btnLoading} ]`;
                btnEl.innerHTML = `${starSpinner} <span style="margin-left: 8px;">${progressText}</span>`;

                let promptText = (i === 0) 
                    ? `Translate title and text fluently into ${zielSprache}.${genderInstruction} Separate with "---". \n\nTitle: ${titleEl.innerText}\n\nText: ${chunks[i]}`
                    : `Translate the following text continuation fluently into ${zielSprache}.${genderInstruction}\n\nText: ${chunks[i]}`;

                const data = await fetchFromGemini(promptText);
                if (data.error || !data.candidates || !data.candidates[0].content) {
                    const errorText = document.createElement('span');
                    errorText.style.color = '#FF0033';
                    errorText.textContent = '[ FEHLER: Übersetzung abgebrochen. ]';
                    if (contentEl.childNodes.length > 0) contentEl.append(document.createElement('br'), document.createElement('br'));
                    contentEl.append(errorText);
                    isError = true; break;
                }

                let resultText = data.candidates[0].content.parts[0].text.trim();

                if (i === 0) {
                    const parts = resultText.split("---");
                    if (parts.length >= 2) {
                        let transTitle = parts[0].trim();
                        if(transTitle) titleEl.innerText = transTitle;
                        appendMultilineText(contentEl, parts[1].trim());
                    } else {
                        appendMultilineText(contentEl, resultText);
                    }
                } else {
                    appendMultilineText(contentEl, resultText, true);
                }
            }

            if (!isError) {
                titleEl.classList.add('translated'); btnEl.innerHTML = `[ ${t.btnDone} ]`; card.dataset.translated = "full";
            } else {
                btnEl.innerHTML = `[ ERROR ]`; card.dataset.translated = "none";
            }
        };
        processChunks();
    }
}

window.addEventListener('scroll', () => {
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 800) {
        if (currentlyDisplayedCount < currentFilteredItems.length) { renderNextBatch(); }
    }
});

document.addEventListener('DOMContentLoaded', () => {
    try {
        let savedZoom = localStorage.getItem('wrn_font_zoom') || "115"; 
        document.documentElement.style.fontSize = savedZoom + "%";
        const fsSelect = document.getElementById('ui-fontsize');
        if (fsSelect) fsSelect.value = savedZoom;

        const savedLang = localStorage.getItem('wrn_system_lang'); const ls = document.getElementById('ui-language');
        if (savedLang && ls) { ls.value = savedLang; }
        
        let savedTheme = localStorage.getItem('wrn_theme_style') || 'theme-dark';
        if(savedTheme === "theme-neon" || savedTheme === "theme-terminal" || savedTheme === "theme-solarpunk") savedTheme = "theme-dark";
        const ut = document.getElementById('ui-theme'); if(ut) ut.value = savedTheme;
        
        changeTheme(savedTheme); changeLanguage(); initialisiereApp(); 

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(function(registrations) {
                for(let registration of registrations) { registration.unregister(); }
            });
        }
    } catch (e) {
        const stat = document.getElementById('status-container');
        if(stat) stat.innerText = "Kritischer Start-Fehler: " + e.message;
    }
});