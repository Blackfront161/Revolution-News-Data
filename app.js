// World Revolution News – robuste Radar-Orts- und Zeitraumfilter, Version 2026-07
window.onerror = function(msg, url, line, col, error) {
    const stat = document.getElementById('status-container');
    if (stat) { stat.style.color = '#FF0033'; stat.innerText = `CRASH GEFUNDEN: ${msg} (Zeile ${line})`; }
    return false;
};

// Nachrichten und Veranstaltungen werden getrennt aktualisiert.
const GITHUB_NEWS_URL = "https://blackfront161.github.io/Revolution-News-Data/news.json";
const GITHUB_EVENTS_URL = "https://blackfront161.github.io/Revolution-News-Data/events.json";
const PROXY_URL = "https://revolution-proxy.paghklo.workers.dev";
let capVal1 = 0; let capVal2 = 0;

function getClientId() {
    const storageKey = "wrn_client_id";
    let value = localStorage.getItem(storageKey);
    if (value) return value;

    value = (window.crypto?.randomUUID?.() || `wrn-${Date.now()}-${Math.random().toString(36).slice(2)}`);
    localStorage.setItem(storageKey, value);
    return value;
}

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

// Gibt alle Kategorien eines Artikels zurück.
// Neue Daten verwenden "categories" als Liste. Alte Daten besitzen nur "kontinent".
// Dadurch bleiben bereits vorhandene news.json-Dateien und alte Lesezeichen kompatibel.
function getArticleCategories(article) {
    const result = [];

    if (article && Array.isArray(article.categories)) {
        article.categories.forEach(category => {
            const cleanCategory = String(category ?? "").trim();
            if (cleanCategory && !result.includes(cleanCategory)) {
                result.push(cleanCategory);
            }
        });
    }

    const oldCategory = String(article?.kontinent ?? "").trim();
    if (oldCategory && !result.includes(oldCategory)) {
        result.push(oldCategory);
    }

    return result;
}

// Prüft, ob ein Artikel zu einer bestimmten Kategorie gehört.
function articleMatchesCategory(article, category) {
    return getArticleCategories(article).includes(category);
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

function extractTranslationText(data) {
    if (!data) return "";

    if (typeof data === "string") {
        return data.trim();
    }

    // Normale Gemini-Antwort
    const geminiText = data?.candidates?.[0]?.content?.parts
        ?.map(part => typeof part?.text === "string" ? part.text : "")
        .join("")
        .trim();
    if (geminiText) return geminiText;

    // Unterstützt auch vereinfachte Antworten eines eigenen Workers.
    const possibleTexts = [
        data.text,
        data.translation,
        data.translatedText,
        data.result?.text,
        data.data?.text,
        data.output?.text,
        data.choices?.[0]?.message?.content,
        data.choices?.[0]?.text
    ];

    for (const value of possibleTexts) {
        if (typeof value === "string" && value.trim()) {
            return value.trim();
        }
    }

    return "";
}

// Entfernt typische KI-Vorsätze wie „Hier ist die deutsche Übersetzung:“.
// Das ist nur ein Sicherheitsnetz; der Worker fordert die Modelle zusätzlich
// ausdrücklich auf, ohne Einleitung direkt mit der Übersetzung zu beginnen.
function cleanTranslationOutput(value) {
    let text = String(value ?? "").trim();

    // Entfernt versehentlich ausgegebene Markdown-Codeblöcke.
    text = text
        .replace(/^```(?:text|markdown)?\s*/i, "")
        .replace(/\s*```$/i, "")
        .trim();

    const unwantedIntroductions = [
        /^(?:\*\*)?\s*Hier ist (?:die )?(?:ins Deutsche übersetzte(?: Fassung| Version)?|deutsche Übersetzung|Übersetzung)(?: des Textes)?\s*:?\s*(?:\*\*)?\s*/i,
        /^(?:\*\*)?\s*Hier folgt (?:die )?(?:deutsche Übersetzung|Übersetzung)\s*:?\s*(?:\*\*)?\s*/i,
        /^(?:\*\*)?\s*Deutsche Übersetzung\s*:?\s*(?:\*\*)?\s*/i,
        /^(?:\*\*)?\s*Here is (?:the )?(?:German translation|translation|translated version)(?: of the text)?\s*:?\s*(?:\*\*)?\s*/i,
        /^(?:\*\*)?\s*Translation\s*:?\s*(?:\*\*)?\s*/i
    ];

    for (const pattern of unwantedIntroductions) {
        text = text.replace(pattern, "").trim();
    }

    return text;
}

function extractTranslationError(data, status) {
    const possibleMessages = [
        data?.error?.message,
        typeof data?.error === "string" ? data.error : "",
        data?.message,
        data?.detail,
        data?.error_description
    ];

    for (const value of possibleMessages) {
        if (typeof value === "string" && value.trim()) {
            return value.trim();
        }
    }

    if (status === 401 || status === 403) {
        return "Der Übersetzungsserver lehnt den Zugriff ab. Secret oder Worker-Einstellungen prüfen.";
    }
    if (status === 429) {
        return "Das kostenlose Übersetzungslimit wurde vorübergehend erreicht. Bitte später erneut versuchen.";
    }
    if (status >= 500) {
        return "Der Übersetzungsserver oder Gemini ist vorübergehend nicht erreichbar.";
    }

    return `Unbekannter Übersetzungsfehler (HTTP ${status || "ohne Status"}).`;
}

const LEGACY_APP_SECRET = "revolution161";

const TRANSLATION_LANGUAGE_NAMES = {
    en: "English",
    de: "German",
    es: "Spanish",
    fr: "French",
    it: "Italian",
    pt: "Portuguese",
    ru: "Russian",
    el: "Greek",
    tr: "Turkish"
};

function buildLegacyTranslationPrompt({ title = "", text = "", mode = "title_and_text" }) {
    const languageName = TRANSLATION_LANGUAGE_NAMES[currentLang] || "English";
    const genderInstruction = currentLang === "de"
        ? " Verwende konsequent geschlechtergerechte deutsche Sprache mit Gendersternchen, zum Beispiel Aktivist*innen, Arbeiter*innen und Autor*innen. Vermeide das generische Maskulinum. Verändere Eigennamen, Organisationsnamen und direkte Zitate nicht."
        : "";

    const rules = `Translate fluently into ${languageName}.${genderInstruction} Return only the translation. Do not add an introduction, explanation, heading, commentary, quotation marks or closing sentence. Preserve paragraph breaks and meaning.`;

    if (mode === "continuation") {
        return `${rules}\n\nText:\n${text}`;
    }

    return `${rules} Return exactly two sections separated by three hyphens: translated title---translated text.\n\nTitle:\n${title}\n\nText:\n${text}`;
}

async function performTranslationFetch({ headers, body, timeoutMs = 45000 }) {
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(PROXY_URL, {
            method: "POST",
            headers,
            body: JSON.stringify(body),
            signal: controller.signal
        });

        const rawResponse = await response.text();
        let data = {};

        if (rawResponse.trim()) {
            try {
                data = JSON.parse(rawResponse);
            } catch {
                data = rawResponse;
            }
        }

        const translatedText = cleanTranslationOutput(extractTranslationText(data));
        if (response.ok && translatedText) {
            return {
                error: false,
                text: translatedText,
                status: response.status,
                provider: data?.provider || ""
            };
        }

        return {
            error: true,
            message: extractTranslationError(data, response.status),
            status: response.status,
            data
        };
    } catch (error) {
        return {
            error: true,
            message: error?.name === "AbortError"
                ? "Die Übersetzung hat länger als 45 Sekunden gedauert und wurde abgebrochen."
                : `Der Übersetzungsserver konnte nicht erreicht werden: ${error?.message || error}`,
            status: 0,
            networkError: true
        };
    } finally {
        window.clearTimeout(timeoutId);
    }
}

function shouldTryLegacyTranslation(result) {
    if (!result?.error) return false;

    // Status 0 entsteht häufig, wenn ein älterer Worker den neuen
    // X-Client-Id-Header beim CORS-Preflight noch nicht erlaubt.
    if (result.status === 0) return true;

    // Diese Statuscodes deuten auf ein nicht passendes Anfrageformat
    // beziehungsweise den noch veröffentlichten älteren Worker hin.
    return [400, 403, 405, 415].includes(result.status);
}

async function fetchTranslationRequest({ title = "", text = "", mode = "title_and_text" }) {
    const safeTitle = String(title || "").slice(0, 500);
    const safeText = String(text || "").slice(0, 6000);

    // Neues, eingeschränktes Protokoll.
    const structuredResult = await performTranslationFetch({
        headers: {
            "Content-Type": "application/json",
            "X-Client-Id": getClientId()
        },
        body: {
            action: "translate",
            targetLanguage: currentLang,
            mode,
            title: safeTitle,
            text: safeText
        }
    });

    if (!structuredResult.error) {
        return structuredResult;
    }

    // Übergangsreserve: Damit die Übersetzung auch funktioniert, wenn auf
    // Cloudflare noch der ältere Worker veröffentlicht ist.
    if (shouldTryLegacyTranslation(structuredResult)) {
        const legacyPrompt = buildLegacyTranslationPrompt({
            title: safeTitle,
            text: safeText,
            mode
        });

        const legacyResult = await performTranslationFetch({
            headers: {
                "Content-Type": "application/json",
                "X-App-Secret": LEGACY_APP_SECRET
            },
            body: {
                contents: [{ parts: [{ text: legacyPrompt }] }]
            }
        });

        if (!legacyResult.error) {
            return legacyResult;
        }

        console.error("Neue und alte Übersetzungsschnittstelle fehlgeschlagen:", {
            structured: structuredResult,
            legacy: legacyResult
        });

        return {
            ...legacyResult,
            message: legacyResult.message || structuredResult.message
        };
    }

    console.error("Übersetzungsserver-Fehler:", structuredResult);
    return structuredResult;
}

function showTranslationError(buttonElement, cardElement, result) {
    const message = result?.message || "Unbekannter Übersetzungsfehler.";
    const shortLabel = currentLang === "de"
        ? "[ ÜBERSETZUNG FEHLER ]"
        : "[ TRANSLATION ERROR ]";

    if (buttonElement) {
        buttonElement.textContent = shortLabel;
        buttonElement.title = message;
    }

    if (cardElement) {
        cardElement.dataset.translated = "none";
    }

    const statusElement = document.getElementById("status-container");
    if (statusElement) {
        statusElement.style.color = "#FF0033";
        statusElement.textContent = currentLang === "de"
            ? `Übersetzung fehlgeschlagen: ${message}`
            : `Translation failed: ${message}`;
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
        radarSummary: "Events", radarCat: "Events",
        infoBody: `<p><strong>Passion Project:</strong> This is an independent, non-commercial passion project. It may contain errors. Please report bugs or broken sources via the "Contact" section.</p><p><strong>Local app data:</strong> This app does not require user accounts and does not intentionally set advertising or analytics cookies. Bookmarks and settings are stored locally in your browser. News, events, and generated translations are stored in IndexedDB for offline use.</p><p><strong>External connections:</strong> Loading news data, article images, translations, original articles, and PayPal may connect your browser to external providers. Those providers can receive normal technical connection data such as an IP address.</p><p><strong>Content & AI translations:</strong> This app aggregates external RSS content. AI-generated translations may contain errors. Please check the original source when accuracy is important.</p>`
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
        radarSummary: "Events", radarCat: "Events",
        infoBody: `<p><strong>Aus Leidenschaft:</strong> Dieses Projekt ist ein unabhängiges Leidenschaftsprojekt von und für Aktivist*innen. Bitte melde Bugs oder fehlerhafte Quellen über den Kontakt-Bereich.</p><p><strong>Lokale App-Daten:</strong> Die App benötigt keine Benutzer*innenkonten und setzt selbst keine beabsichtigten Werbe- oder Analyse-Cookies. Lesezeichen und Einstellungen werden lokal im Browser gespeichert. Nachrichten, Events und bereits erzeugte Übersetzungen werden für die Offline-Nutzung in IndexedDB gespeichert.</p><p><strong>Externe Verbindungen:</strong> Beim Laden der Nachrichtendaten, externer Artikelbilder, Übersetzungen, Originalartikel oder von PayPal kann dein Browser Verbindungen zu anderen Anbietern herstellen. Diese Anbieter können dabei übliche technische Verbindungsdaten wie eine IP-Adresse erhalten.</p><p><strong>Inhalte und KI-Übersetzungen:</strong> Die App bündelt fremde RSS-Inhalte. KI-generierte Übersetzungen können Fehler enthalten. Prüfe bei wichtigen Angaben bitte die Originalquelle.</p>`
    },
    es: { btnTranslate: "Traducir", catGlobal: "Global", catEurope: "Europa", searchRegion: "🌍 Región", searchTopic: "🏷️ Tema", radarSummary: "Events", radarCat: "Events" },
    fr: { btnTranslate: "Traduire", catGlobal: "Global", catEurope: "Europe", searchRegion: "🌍 Région", searchTopic: "🏷️ Thème", radarSummary: "Events", radarCat: "Events" },
    it: { btnTranslate: "Traduci", catGlobal: "Globale", catEurope: "Europa", searchRegion: "🌍 Regione", searchTopic: "🏷️ Tema", radarSummary: "Events", radarCat: "Events" },
    pt: { btnTranslate: "Traduzir", catGlobal: "Global", catEurope: "Europa", searchRegion: "🌍 Região", searchTopic: "🏷️ Tema", radarSummary: "Events", radarCat: "Events" },
    ru: { btnTranslate: "Перевести", catGlobal: "Мир", catEurope: "Европа", searchRegion: "🌍 Регион", searchTopic: "🏷️ Тема", radarSummary: "Events", radarCat: "Events" },
    el: { btnTranslate: "Μετάφραση", catGlobal: "Παγκόσμια", catEurope: "Ευρώπη", searchRegion: "🌍 Περιοχή", searchTopic: "🏷️ Θέμα", radarSummary: "Events", radarCat: "Events" },
    tr: { btnTranslate: "Çevir", catGlobal: "Küresel", catEurope: "Avrupa", searchRegion: "🌍 Bölge", searchTopic: "🏷️ Konu", radarSummary: "Events", radarCat: "Events" }
};

const fallbackLang = uiTexte['en'];
Object.keys(uiTexte).forEach(lang => {
    Object.keys(fallbackLang).forEach(key => {
        if (uiTexte[lang][key] === undefined) { uiTexte[lang][key] = fallbackLang[key]; }
    });
});


const eventUiTexte = {
    en: { eventFilterTitle:"Event filters", eventDate:"Period", eventUpcoming:"Upcoming", eventToday:"Today", eventTomorrow:"Tomorrow", eventWeekend:"This weekend", event7days:"Next 7 days", event14days:"Next 14 days", eventNextMonth:"Next calendar month", event30days:"Next 30 days", eventAllDates:"All dates", eventFrom:"From", eventTo:"To", eventCountry:"Country", eventCity:"City", eventPostal:"Postal code", eventCategory:"Category", eventTag:"Tag", eventGroup:"Group", eventPrice:"Price", eventMode:"Format", eventAll:"All", eventFree:"Free", eventPaid:"Paid", eventUnknown:"Unknown", eventOnline:"Online", eventOffline:"In person", eventReset:"Reset filters", eventStarts:"START:", eventPlace:"PLACE:", eventCategoriesLabel:"CATEGORIES:", eventTagsLabel:"TAGS:", eventGroupsLabel:"GROUPS:", eventPriceLabel:"PRICE:", eventStatusLabel:"STATUS:", eventSortSoon:"Soonest", eventSortLate:"Latest", eventCount:"events" },
    de: { eventFilterTitle:"Event-Filter", eventDate:"Zeitraum", eventUpcoming:"Kommende", eventToday:"Heute", eventTomorrow:"Morgen", eventWeekend:"Dieses Wochenende", event7days:"Nächste 7 Tage", event14days:"Nächste 14 Tage", eventNextMonth:"Nächster Kalendermonat", event30days:"Nächste 30 Tage", eventAllDates:"Alle Termine", eventFrom:"Von", eventTo:"Bis", eventCountry:"Land", eventCity:"Stadt", eventPostal:"Postleitzahl", eventCategory:"Kategorie", eventTag:"Tag", eventGroup:"Gruppe", eventPrice:"Preis", eventMode:"Format", eventAll:"Alle", eventFree:"Kostenlos", eventPaid:"Kostenpflichtig", eventUnknown:"Unbekannt", eventOnline:"Online", eventOffline:"Vor Ort", eventReset:"Filter zurücksetzen", eventStarts:"BEGINN:", eventPlace:"ORT:", eventCategoriesLabel:"KATEGORIEN:", eventTagsLabel:"TAGS:", eventGroupsLabel:"GRUPPEN:", eventPriceLabel:"PREIS:", eventStatusLabel:"STATUS:", eventSortSoon:"Nächste zuerst", eventSortLate:"Spätere zuerst", eventCount:"Events" },
    es: { eventFilterTitle:"Filtros de eventos", eventDate:"Período", eventUpcoming:"Próximos", eventToday:"Hoy", eventTomorrow:"Mañana", eventWeekend:"Este fin de semana", event7days:"Próximos 7 días", event14days:"Próximos 14 días", eventNextMonth:"Próximo mes natural", event30days:"Próximos 30 días", eventAllDates:"Todas las fechas", eventFrom:"Desde", eventTo:"Hasta", eventCountry:"País", eventCity:"Ciudad", eventPostal:"Código postal", eventCategory:"Categoría", eventTag:"Etiqueta", eventGroup:"Grupo", eventPrice:"Precio", eventMode:"Formato", eventAll:"Todos", eventFree:"Gratis", eventPaid:"De pago", eventUnknown:"Desconocido", eventOnline:"En línea", eventOffline:"Presencial", eventReset:"Restablecer filtros", eventStarts:"INICIO:", eventPlace:"LUGAR:", eventCategoriesLabel:"CATEGORÍAS:", eventTagsLabel:"ETIQUETAS:", eventGroupsLabel:"GRUPOS:", eventPriceLabel:"PRECIO:", eventStatusLabel:"ESTADO:", eventSortSoon:"Próximos", eventSortLate:"Más tarde", eventCount:"eventos" },
    fr: { eventFilterTitle:"Filtres d’événements", eventDate:"Période", eventUpcoming:"À venir", eventToday:"Aujourd’hui", eventTomorrow:"Demain", eventWeekend:"Ce week-end", event7days:"7 prochains jours", event14days:"14 prochains jours", eventNextMonth:"Mois civil suivant", event30days:"30 prochains jours", eventAllDates:"Toutes les dates", eventFrom:"Du", eventTo:"Au", eventCountry:"Pays", eventCity:"Ville", eventPostal:"Code postal", eventCategory:"Catégorie", eventTag:"Tag", eventGroup:"Groupe", eventPrice:"Prix", eventMode:"Format", eventAll:"Tous", eventFree:"Gratuit", eventPaid:"Payant", eventUnknown:"Inconnu", eventOnline:"En ligne", eventOffline:"Sur place", eventReset:"Réinitialiser", eventStarts:"DÉBUT :", eventPlace:"LIEU :", eventCategoriesLabel:"CATÉGORIES :", eventTagsLabel:"TAGS :", eventGroupsLabel:"GROUPES :", eventPriceLabel:"PRIX :", eventStatusLabel:"STATUT :", eventSortSoon:"Plus proches", eventSortLate:"Plus tard", eventCount:"événements" },
    it: { eventFilterTitle:"Filtri eventi", eventDate:"Periodo", eventUpcoming:"In arrivo", eventToday:"Oggi", eventTomorrow:"Domani", eventWeekend:"Questo fine settimana", event7days:"Prossimi 7 giorni", event14days:"Prossimi 14 giorni", eventNextMonth:"Prossimo mese di calendario", event30days:"Prossimi 30 giorni", eventAllDates:"Tutte le date", eventFrom:"Da", eventTo:"A", eventCountry:"Paese", eventCity:"Città", eventPostal:"CAP", eventCategory:"Categoria", eventTag:"Tag", eventGroup:"Gruppo", eventPrice:"Prezzo", eventMode:"Formato", eventAll:"Tutti", eventFree:"Gratis", eventPaid:"A pagamento", eventUnknown:"Sconosciuto", eventOnline:"Online", eventOffline:"In presenza", eventReset:"Reimposta filtri", eventStarts:"INIZIO:", eventPlace:"LUOGO:", eventCategoriesLabel:"CATEGORIE:", eventTagsLabel:"TAG:", eventGroupsLabel:"GRUPPI:", eventPriceLabel:"PREZZO:", eventStatusLabel:"STATO:", eventSortSoon:"Più vicini", eventSortLate:"Più tardi", eventCount:"eventi" },
    pt: { eventFilterTitle:"Filtros de eventos", eventDate:"Período", eventUpcoming:"Próximos", eventToday:"Hoje", eventTomorrow:"Amanhã", eventWeekend:"Este fim de semana", event7days:"Próximos 7 dias", event14days:"Próximos 14 dias", eventNextMonth:"Próximo mês civil", event30days:"Próximos 30 dias", eventAllDates:"Todas as datas", eventFrom:"De", eventTo:"Até", eventCountry:"País", eventCity:"Cidade", eventPostal:"Código postal", eventCategory:"Categoria", eventTag:"Tag", eventGroup:"Grupo", eventPrice:"Preço", eventMode:"Formato", eventAll:"Todos", eventFree:"Grátis", eventPaid:"Pago", eventUnknown:"Desconhecido", eventOnline:"Online", eventOffline:"Presencial", eventReset:"Limpar filtros", eventStarts:"INÍCIO:", eventPlace:"LOCAL:", eventCategoriesLabel:"CATEGORIAS:", eventTagsLabel:"TAGS:", eventGroupsLabel:"GRUPOS:", eventPriceLabel:"PREÇO:", eventStatusLabel:"ESTADO:", eventSortSoon:"Mais próximos", eventSortLate:"Mais tarde", eventCount:"eventos" },
    ru: { eventFilterTitle:"Фильтры событий", eventDate:"Период", eventUpcoming:"Предстоящие", eventToday:"Сегодня", eventTomorrow:"Завтра", eventWeekend:"Эти выходные", event7days:"Следующие 7 дней", event14days:"Следующие 14 дней", eventNextMonth:"Следующий календарный месяц", event30days:"Следующие 30 дней", eventAllDates:"Все даты", eventFrom:"С", eventTo:"До", eventCountry:"Страна", eventCity:"Город", eventPostal:"Индекс", eventCategory:"Категория", eventTag:"Тег", eventGroup:"Группа", eventPrice:"Цена", eventMode:"Формат", eventAll:"Все", eventFree:"Бесплатно", eventPaid:"Платно", eventUnknown:"Неизвестно", eventOnline:"Онлайн", eventOffline:"Очно", eventReset:"Сбросить фильтры", eventStarts:"НАЧАЛО:", eventPlace:"МЕСТО:", eventCategoriesLabel:"КАТЕГОРИИ:", eventTagsLabel:"ТЕГИ:", eventGroupsLabel:"ГРУППЫ:", eventPriceLabel:"ЦЕНА:", eventStatusLabel:"СТАТУС:", eventSortSoon:"Ближайшие", eventSortLate:"Поздние", eventCount:"событий" },
    el: { eventFilterTitle:"Φίλτρα εκδηλώσεων", eventDate:"Περίοδος", eventUpcoming:"Επερχόμενα", eventToday:"Σήμερα", eventTomorrow:"Αύριο", eventWeekend:"Αυτό το Σαββατοκύριακο", event7days:"Επόμενες 7 ημέρες", event14days:"Επόμενες 14 ημέρες", eventNextMonth:"Επόμενος ημερολογιακός μήνας", event30days:"Επόμενες 30 ημέρες", eventAllDates:"Όλες οι ημερομηνίες", eventFrom:"Από", eventTo:"Έως", eventCountry:"Χώρα", eventCity:"Πόλη", eventPostal:"Ταχυδρομικός κώδικας", eventCategory:"Κατηγορία", eventTag:"Ετικέτα", eventGroup:"Ομάδα", eventPrice:"Τιμή", eventMode:"Μορφή", eventAll:"Όλα", eventFree:"Δωρεάν", eventPaid:"Με πληρωμή", eventUnknown:"Άγνωστο", eventOnline:"Online", eventOffline:"Με φυσική παρουσία", eventReset:"Επαναφορά φίλτρων", eventStarts:"ΕΝΑΡΞΗ:", eventPlace:"ΤΟΠΟΣ:", eventCategoriesLabel:"ΚΑΤΗΓΟΡΙΕΣ:", eventTagsLabel:"ΕΤΙΚΕΤΕΣ:", eventGroupsLabel:"ΟΜΑΔΕΣ:", eventPriceLabel:"ΤΙΜΗ:", eventStatusLabel:"ΚΑΤΑΣΤΑΣΗ:", eventSortSoon:"Πλησιέστερα", eventSortLate:"Αργότερα", eventCount:"εκδηλώσεις" },
    tr: { eventFilterTitle:"Etkinlik filtreleri", eventDate:"Dönem", eventUpcoming:"Yaklaşan", eventToday:"Bugün", eventTomorrow:"Yarın", eventWeekend:"Bu hafta sonu", event7days:"Sonraki 7 gün", event14days:"Sonraki 14 gün", eventNextMonth:"Sonraki takvim ayı", event30days:"Sonraki 30 gün", eventAllDates:"Tüm tarihler", eventFrom:"Başlangıç", eventTo:"Bitiş", eventCountry:"Ülke", eventCity:"Şehir", eventPostal:"Posta kodu", eventCategory:"Kategori", eventTag:"Etiket", eventGroup:"Grup", eventPrice:"Fiyat", eventMode:"Biçim", eventAll:"Tümü", eventFree:"Ücretsiz", eventPaid:"Ücretli", eventUnknown:"Bilinmiyor", eventOnline:"Çevrimiçi", eventOffline:"Yüz yüze", eventReset:"Filtreleri sıfırla", eventStarts:"BAŞLANGIÇ:", eventPlace:"YER:", eventCategoriesLabel:"KATEGORİLER:", eventTagsLabel:"ETİKETLER:", eventGroupsLabel:"GRUPLAR:", eventPriceLabel:"FİYAT:", eventStatusLabel:"DURUM:", eventSortSoon:"En yakın", eventSortLate:"Daha sonra", eventCount:"etkinlik" }
};

Object.keys(uiTexte).forEach(lang => {
    Object.assign(uiTexte[lang], eventUiTexte[lang] || eventUiTexte.en);
});

const podcastUiTexte = {
    en: { btnPodcast:"Podcast", podcastTitle:"Podcast player", podcastPreparing:"Preparing article…", podcastTranslating:"Translating full article…", podcastSpeaking:"Playing", podcastPaused:"Paused", podcastFinished:"Finished", podcastPlay:"Play", podcastReady:"Ready – press Play", podcastPause:"Pause", podcastResume:"Resume", podcastStop:"Stop", podcastVoice:"Voice", podcastSpeed:"Speed", podcastAutoVoice:"Automatic voice", podcastNoVoice:"No matching voice is installed; the browser default will be used.", podcastUnsupported:"Text-to-speech is not supported by this browser.", podcastTranslationFailed:"The article could not be translated for playback.", podcastLocal:"local", podcastOnline:"online" },
    de: { btnPodcast:"Podcast", podcastTitle:"Podcast-Player", podcastPreparing:"Artikel wird vorbereitet…", podcastTranslating:"Vollständiger Artikel wird übersetzt…", podcastSpeaking:"Wiedergabe läuft", podcastPaused:"Pausiert", podcastFinished:"Beendet", podcastPlay:"Abspielen", podcastReady:"Bereit – bitte auf Abspielen drücken", podcastPause:"Pause", podcastResume:"Weiter", podcastStop:"Stopp", podcastVoice:"Stimme", podcastSpeed:"Tempo", podcastAutoVoice:"Automatische Stimme", podcastNoVoice:"Keine passende Stimme installiert; die Standardstimme des Browsers wird verwendet.", podcastUnsupported:"Dieser Browser unterstützt keine Vorlesefunktion.", podcastTranslationFailed:"Der Artikel konnte für die Wiedergabe nicht übersetzt werden.", podcastLocal:"lokal", podcastOnline:"online" },
    es: { btnPodcast:"Pódcast", podcastTitle:"Reproductor de pódcast", podcastPreparing:"Preparando el artículo…", podcastTranslating:"Traduciendo el artículo completo…", podcastSpeaking:"Reproduciendo", podcastPaused:"En pausa", podcastFinished:"Finalizado", podcastPlay:"Reproducir", podcastReady:"Listo – pulsa Reproducir", podcastPause:"Pausa", podcastResume:"Continuar", podcastStop:"Detener", podcastVoice:"Voz", podcastSpeed:"Velocidad", podcastAutoVoice:"Voz automática", podcastNoVoice:"No hay una voz adecuada instalada; se usará la voz predeterminada del navegador.", podcastUnsupported:"Este navegador no admite la lectura en voz alta.", podcastTranslationFailed:"No se pudo traducir el artículo para la reproducción.", podcastLocal:"local", podcastOnline:"en línea" },
    fr: { btnPodcast:"Podcast", podcastTitle:"Lecteur podcast", podcastPreparing:"Préparation de l’article…", podcastTranslating:"Traduction de l’article complet…", podcastSpeaking:"Lecture en cours", podcastPaused:"En pause", podcastFinished:"Terminé", podcastPlay:"Lire", podcastReady:"Prêt – appuyez sur Lire", podcastPause:"Pause", podcastResume:"Continuer", podcastStop:"Arrêter", podcastVoice:"Voix", podcastSpeed:"Vitesse", podcastAutoVoice:"Voix automatique", podcastNoVoice:"Aucune voix adaptée n’est installée ; la voix par défaut du navigateur sera utilisée.", podcastUnsupported:"Ce navigateur ne prend pas en charge la lecture vocale.", podcastTranslationFailed:"L’article n’a pas pu être traduit pour la lecture.", podcastLocal:"locale", podcastOnline:"en ligne" },
    it: { btnPodcast:"Podcast", podcastTitle:"Lettore podcast", podcastPreparing:"Preparazione dell’articolo…", podcastTranslating:"Traduzione dell’articolo completo…", podcastSpeaking:"Riproduzione in corso", podcastPaused:"In pausa", podcastFinished:"Terminato", podcastPlay:"Riproduci", podcastReady:"Pronto – premi Riproduci", podcastPause:"Pausa", podcastResume:"Continua", podcastStop:"Stop", podcastVoice:"Voce", podcastSpeed:"Velocità", podcastAutoVoice:"Voce automatica", podcastNoVoice:"Non è installata una voce adatta; verrà usata la voce predefinita del browser.", podcastUnsupported:"Questo browser non supporta la lettura vocale.", podcastTranslationFailed:"Non è stato possibile tradurre l’articolo per la riproduzione.", podcastLocal:"locale", podcastOnline:"online" },
    pt: { btnPodcast:"Podcast", podcastTitle:"Leitor de podcast", podcastPreparing:"A preparar o artigo…", podcastTranslating:"A traduzir o artigo completo…", podcastSpeaking:"A reproduzir", podcastPaused:"Em pausa", podcastFinished:"Terminado", podcastPlay:"Reproduzir", podcastReady:"Pronto – prima Reproduzir", podcastPause:"Pausa", podcastResume:"Continuar", podcastStop:"Parar", podcastVoice:"Voz", podcastSpeed:"Velocidade", podcastAutoVoice:"Voz automática", podcastNoVoice:"Não está instalada uma voz adequada; será usada a voz predefinida do navegador.", podcastUnsupported:"Este navegador não suporta leitura em voz alta.", podcastTranslationFailed:"Não foi possível traduzir o artigo para reprodução.", podcastLocal:"local", podcastOnline:"online" },
    ru: { btnPodcast:"Подкаст", podcastTitle:"Проигрыватель подкаста", podcastPreparing:"Подготовка статьи…", podcastTranslating:"Перевод полной статьи…", podcastSpeaking:"Воспроизведение", podcastPaused:"Пауза", podcastFinished:"Завершено", podcastPlay:"Воспроизвести", podcastReady:"Готово — нажмите «Воспроизвести»", podcastPause:"Пауза", podcastResume:"Продолжить", podcastStop:"Стоп", podcastVoice:"Голос", podcastSpeed:"Скорость", podcastAutoVoice:"Автоматический голос", podcastNoVoice:"Подходящий голос не установлен; будет использован голос браузера по умолчанию.", podcastUnsupported:"Этот браузер не поддерживает озвучивание текста.", podcastTranslationFailed:"Не удалось перевести статью для воспроизведения.", podcastLocal:"локальный", podcastOnline:"онлайн" },
    el: { btnPodcast:"Podcast", podcastTitle:"Αναπαραγωγή podcast", podcastPreparing:"Προετοιμασία άρθρου…", podcastTranslating:"Μετάφραση ολόκληρου του άρθρου…", podcastSpeaking:"Αναπαραγωγή", podcastPaused:"Παύση", podcastFinished:"Ολοκληρώθηκε", podcastPlay:"Αναπαραγωγή", podcastReady:"Έτοιμο – πατήστε Αναπαραγωγή", podcastPause:"Παύση", podcastResume:"Συνέχεια", podcastStop:"Διακοπή", podcastVoice:"Φωνή", podcastSpeed:"Ταχύτητα", podcastAutoVoice:"Αυτόματη φωνή", podcastNoVoice:"Δεν υπάρχει εγκατεστημένη κατάλληλη φωνή· θα χρησιμοποιηθεί η προεπιλεγμένη φωνή του προγράμματος περιήγησης.", podcastUnsupported:"Αυτό το πρόγραμμα περιήγησης δεν υποστηρίζει εκφώνηση κειμένου.", podcastTranslationFailed:"Το άρθρο δεν μπόρεσε να μεταφραστεί για αναπαραγωγή.", podcastLocal:"τοπική", podcastOnline:"online" },
    tr: { btnPodcast:"Podcast", podcastTitle:"Podcast oynatıcı", podcastPreparing:"Makale hazırlanıyor…", podcastTranslating:"Makalenin tamamı çevriliyor…", podcastSpeaking:"Oynatılıyor", podcastPaused:"Duraklatıldı", podcastFinished:"Bitti", podcastPlay:"Oynat", podcastReady:"Hazır – Oynat düğmesine basın", podcastPause:"Duraklat", podcastResume:"Devam", podcastStop:"Durdur", podcastVoice:"Ses", podcastSpeed:"Hız", podcastAutoVoice:"Otomatik ses", podcastNoVoice:"Uygun bir ses yüklü değil; tarayıcının varsayılan sesi kullanılacak.", podcastUnsupported:"Bu tarayıcı sesli okumayı desteklemiyor.", podcastTranslationFailed:"Makale oynatma için çevrilemedi.", podcastLocal:"yerel", podcastOnline:"çevrimiçi" }
};

Object.keys(uiTexte).forEach(lang => {
    Object.assign(uiTexte[lang], podcastUiTexte[lang] || podcastUiTexte.en);
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

const translationCache = new Map();
const speechLanguageTags = {
    en: 'en-US', de: 'de-DE', es: 'es-ES', fr: 'fr-FR', it: 'it-IT',
    pt: 'pt-PT', ru: 'ru-RU', el: 'el-GR', tr: 'tr-TR'
};
let podcastVoices = [];
let podcastState = {
    articleId: null,
    chunks: [],
    index: 0,
    paused: false,
    loading: false,
    stopped: true,
    started: false,
    utterance: null
};

function setTxt(id, text) { const e = document.getElementById(id); if (e && text) e.innerText = text; }
function setHtml(id, html) { const e = document.getElementById(id); if (e && html) e.innerHTML = html; }
function setPh(id, text) { const e = document.getElementById(id); if (e && text) e.placeholder = text; }

function getTargetLanguageName() {
    const languageSelect = document.getElementById('ui-language');
    return languageSelect?.options?.[languageSelect.selectedIndex]?.text || 'English';
}

function getGenderInstruction() {
    return currentLang === 'de'
        ? ' Verwende konsequent geschlechtergerechte deutsche Sprache mit Gendersternchen, zum Beispiel Aktivist*innen, Arbeiter*innen und Autor*innen. Vermeide das generische Maskulinum. Verändere Eigennamen, Organisationsnamen und direkte Zitate nicht.'
        : '';
}

function createArticleChunks(rawText, maxLength = 1800) {
    const paragraphs = String(rawText || '').split(/\n\n+/).map(value => value.trim()).filter(Boolean);
    const chunks = [];
    let currentChunk = '';

    for (const paragraph of paragraphs) {
        if (paragraph.length > maxLength) {
            if (currentChunk) {
                chunks.push(currentChunk);
                currentChunk = '';
            }
            for (let start = 0; start < paragraph.length; start += maxLength) {
                chunks.push(paragraph.slice(start, start + maxLength));
            }
            continue;
        }

        if (currentChunk && currentChunk.length + paragraph.length + 2 > maxLength) {
            chunks.push(currentChunk);
            currentChunk = paragraph;
        } else {
            currentChunk += (currentChunk ? '\n\n' : '') + paragraph;
        }
    }

    if (currentChunk) chunks.push(currentChunk);
    return chunks;
}

function translationCacheKey(article) {
    return `${article?.link || article?.title || 'article'}::${currentLang}`;
}

function parseTranslatedTitleAndText(value, fallbackTitle = '') {
    const cleanValue = cleanTranslationOutput(value);
    const parts = cleanValue.split('---');
    if (parts.length >= 2) {
        return {
            title: parts.shift().trim() || fallbackTitle,
            text: parts.join('---').trim()
        };
    }
    return { title: fallbackTitle, text: cleanValue };
}

async function translateFullArticleForLanguage(idNum, onProgress = null) {
    const article = currentFilteredItems[idNum];
    if (!article) return { error: true, message: 'Artikel nicht gefunden.' };

    const key = translationCacheKey(article);
    if (translationCache.has(key)) {
        return { error: false, ...translationCache.get(key), cached: true };
    }

    if (window.WRNStorage) {
        try {
            const storedTranslation = await window.WRNStorage.getTranslation(key);
            if (storedTranslation?.text) {
                translationCache.set(key, storedTranslation);
                return { error: false, ...storedTranslation, cached: true };
            }
        } catch (error) {
            console.warn("Gespeicherte Übersetzung konnte nicht gelesen werden:", error);
        }
    }

    const originalTitle = String(article.title || '').trim();
    const originalText = String(article.content || '').trim();
    if (!originalText) {
        return {
            error: true,
            message: currentLang === 'de'
                ? 'Dieser Artikel enthält keinen übersetzbaren Text.'
                : 'This article contains no text to translate.'
        };
    }

    const chunks = createArticleChunks(originalText);
    let translatedTitle = originalTitle;
    const translatedParts = [];

    for (let index = 0; index < chunks.length; index++) {
        if (typeof onProgress === 'function') onProgress(index + 1, chunks.length);

        const result = await fetchTranslationRequest({
            title: index === 0 ? originalTitle : "",
            text: chunks[index],
            mode: index === 0 ? "title_and_text" : "continuation"
        });
        if (result.error || !result.text) return result;

        if (index === 0) {
            const parsed = parseTranslatedTitleAndText(result.text, originalTitle);
            translatedTitle = parsed.title;
            if (parsed.text) translatedParts.push(parsed.text);
        } else {
            translatedParts.push(cleanTranslationOutput(result.text));
        }
    }

    const translated = {
        title: translatedTitle,
        text: translatedParts.filter(Boolean).join('\n\n'),
        language: currentLang
    };
    translationCache.set(key, translated);
    if (window.WRNStorage) {
        window.WRNStorage.putTranslation(key, translated).catch(error => {
            console.warn("Übersetzung konnte nicht offline gespeichert werden:", error);
        });
    }
    return { error: false, ...translated };
}

function applyFullTranslationToCard(idNum, translated) {
    const titleEl = document.getElementById(`title-${idNum}`);
    const teaserEl = document.getElementById(`teaser-${idNum}`);
    const contentEl = document.getElementById(`content-${idNum}`);
    const btnEl = document.getElementById(`btn-${idNum}`);
    const card = document.getElementById(`card-${idNum}`);
    const t = uiTexte[currentLang] || uiTexte.en;

    if (titleEl && translated.title) {
        titleEl.textContent = translated.title;
        titleEl.classList.add('translated');
    }
    if (contentEl) {
        contentEl.textContent = translated.text || '';
    }
    if (teaserEl) {
        const sentence = String(translated.text || '').match(/[^.!?]+[.!?]+/)?.[0];
        teaserEl.textContent = sentence || String(translated.text || '').slice(0, 180) + (translated.text?.length > 180 ? '…' : '');
    }
    if (btnEl) {
        btnEl.innerHTML = `[ ${t.btnDone} ]`;
        btnEl.removeAttribute('title');
    }
    if (card) {
        card.dataset.translated = 'full';
        card.dataset.translationLanguage = currentLang;
    }
}

function splitTextForSpeech(value, maxLength = 280) {
    const cleanText = String(value || '')
        .replace(/\s+/g, ' ')
        .replace(/https?:\/\/\S+/g, '')
        .trim();
    if (!cleanText) return [];

    const sentences = cleanText.match(/[^.!?…]+[.!?…]+|[^.!?…]+$/g) || [cleanText];
    const chunks = [];
    let current = '';

    for (const sentenceRaw of sentences) {
        const sentence = sentenceRaw.trim();
        if (!sentence) continue;

        if (sentence.length > maxLength) {
            if (current) {
                chunks.push(current);
                current = '';
            }
            const words = sentence.split(/\s+/);
            let wordChunk = '';
            for (const word of words) {
                if (wordChunk && wordChunk.length + word.length + 1 > maxLength) {
                    chunks.push(wordChunk);
                    wordChunk = word;
                } else {
                    wordChunk += (wordChunk ? ' ' : '') + word;
                }
            }
            if (wordChunk) chunks.push(wordChunk);
            continue;
        }

        if (current && current.length + sentence.length + 1 > maxLength) {
            chunks.push(current);
            current = sentence;
        } else {
            current += (current ? ' ' : '') + sentence;
        }
    }

    if (current) chunks.push(current);
    return chunks;
}

function updatePodcastUiText() {
    const t = uiTexte[currentLang] || uiTexte.en;
    setTxt('txt-podcast-voice', t.podcastVoice);
    setTxt('txt-podcast-speed', t.podcastSpeed);
    setTxt('btn-podcast-stop', t.podcastStop);
    const pauseButton = document.getElementById('btn-podcast-pause');
    if (pauseButton) {
        const readyToStart = !podcastState.loading && !podcastState.stopped && !podcastState.started;
        pauseButton.textContent = readyToStart
            ? (t.podcastPlay || 'Play')
            : (podcastState.paused ? t.podcastResume : t.podcastPause);
        pauseButton.disabled = podcastState.loading || podcastState.stopped;
    }
    const title = document.getElementById('podcast-player-title');
    if (title && podcastState.articleId === null) title.textContent = t.podcastTitle;
}

function refreshPodcastVoices() {
    if (!('speechSynthesis' in window)) return;
    podcastVoices = window.speechSynthesis.getVoices() || [];
    populatePodcastVoiceOptions();
}

function populatePodcastVoiceOptions() {
    const select = document.getElementById('podcast-voice-select');
    if (!select) return;
    const t = uiTexte[currentLang] || uiTexte.en;
    const previous = localStorage.getItem(`wrn_podcast_voice_${currentLang}`) || select.value;
    const languagePrefix = (speechLanguageTags[currentLang] || currentLang).split('-')[0].toLowerCase();

    const matching = podcastVoices
        .filter(voice => String(voice.lang || '').toLowerCase().startsWith(languagePrefix))
        .sort((a, b) => Number(b.localService) - Number(a.localService) || a.name.localeCompare(b.name));
    const otherVoices = podcastVoices
        .filter(voice => !String(voice.lang || '').toLowerCase().startsWith(languagePrefix))
        .sort((a, b) => String(a.lang || '').localeCompare(String(b.lang || '')) || a.name.localeCompare(b.name));

    select.textContent = '';
    const autoOption = document.createElement('option');
    autoOption.value = '';
    autoOption.textContent = t.podcastAutoVoice;
    select.append(autoOption);

    const appendVoice = voice => {
        const option = document.createElement('option');
        option.value = voice.voiceURI || `${voice.name}::${voice.lang}`;
        option.textContent = `${voice.name} (${voice.lang}, ${voice.localService ? t.podcastLocal : t.podcastOnline})`;
        select.append(option);
    };

    matching.forEach(appendVoice);

    // Auf manchen Smartphones liefert der Browser nur sehr wenige Stimmen für
    // die ausgewählte Sprache. Deshalb werden danach auch die übrigen
    // installierten Stimmen angeboten, statt das Auswahlfeld praktisch leer zu lassen.
    if (otherVoices.length > 0) {
        const separator = document.createElement('option');
        separator.disabled = true;
        separator.textContent = '──────────';
        select.append(separator);
        otherVoices.forEach(appendVoice);
    }

    if ([...select.options].some(option => option.value === previous)) {
        select.value = previous;
    }
}

function getPodcastVoice() {
    const selected = document.getElementById('podcast-voice-select')?.value || '';
    const languagePrefix = (speechLanguageTags[currentLang] || currentLang).split('-')[0].toLowerCase();
    if (selected) {
        const exact = podcastVoices.find(voice =>
            (voice.voiceURI || `${voice.name}::${voice.lang}`) === selected
        );
        if (exact) return exact;
    }
    return podcastVoices.find(voice => voice.localService && String(voice.lang || '').toLowerCase().startsWith(languagePrefix))
        || podcastVoices.find(voice => String(voice.lang || '').toLowerCase().startsWith(languagePrefix))
        || null;
}

function setPodcastStatus(text, progress = '') {
    const status = document.getElementById('podcast-player-status');
    const progressEl = document.getElementById('podcast-player-progress');
    if (status) status.textContent = text || '';
    if (progressEl) progressEl.textContent = progress || '';
}

function speakCurrentPodcastChunk() {
    if (!('speechSynthesis' in window) || podcastState.stopped || podcastState.paused) return;
    const t = uiTexte[currentLang] || uiTexte.en;

    if (podcastState.index >= podcastState.chunks.length) {
        podcastState.stopped = true;
        podcastState.started = false;
        podcastState.utterance = null;
        setPodcastStatus(t.podcastFinished, `${podcastState.chunks.length}/${podcastState.chunks.length}`);
        updatePodcastUiText();
        return;
    }

    const utterance = new SpeechSynthesisUtterance(podcastState.chunks[podcastState.index]);
    utterance.lang = speechLanguageTags[currentLang] || currentLang;
    utterance.rate = Number(document.getElementById('podcast-rate-select')?.value || 1);
    const voice = getPodcastVoice();
    if (voice) utterance.voice = voice;

    podcastState.utterance = utterance;
    podcastState.started = true;
    podcastState.paused = false;

    utterance.onend = () => {
        // Wenn Stimme oder Tempo geändert wurden, ist diese alte Äußerung nicht
        // mehr die aktuelle. Dann darf sie den Abschnittszähler nicht erhöhen.
        if (podcastState.stopped || podcastState.utterance !== utterance) return;
        podcastState.utterance = null;
        podcastState.index += 1;
        speakCurrentPodcastChunk();
    };
    utterance.onerror = event => {
        if (podcastState.utterance !== utterance) return;
        if (podcastState.stopped || event.error === 'canceled' || event.error === 'interrupted') return;
        podcastState.stopped = true;
        podcastState.started = false;
        podcastState.utterance = null;
        setPodcastStatus(`${t.podcastUnsupported} (${event.error || 'error'})`);
        updatePodcastUiText();
    };

    setPodcastStatus(t.podcastSpeaking, `${podcastState.index + 1}/${podcastState.chunks.length}`);
    updatePodcastUiText();
    window.speechSynthesis.speak(utterance);
}

async function startPodcast(idNum) {
    const t = uiTexte[currentLang] || uiTexte.en;
    if (!('speechSynthesis' in window) || typeof SpeechSynthesisUtterance === 'undefined') {
        alert(t.podcastUnsupported);
        return;
    }

    stopPodcast(false);
    podcastState.articleId = idNum;
    podcastState.loading = true;
    podcastState.stopped = false;
    podcastState.paused = true;
    podcastState.started = false;

    const player = document.getElementById('podcast-player');
    const playerTitle = document.getElementById('podcast-player-title');
    const article = currentFilteredItems[idNum];
    const podcastButton = document.getElementById(`podcast-${idNum}`);
    const card = document.getElementById(`card-${idNum}`);
    if (player) player.hidden = false;
    if (playerTitle) playerTitle.textContent = article?.title || t.podcastTitle;
    if (podcastButton) podcastButton.innerHTML = `${starSpinner} <span>[ ${t.podcastPreparing} ]</span>`;
    setPodcastStatus(t.podcastTranslating, '0%');

    const result = await translateFullArticleForLanguage(idNum, (current, total) => {
        const percent = Math.round((current - 1) / Math.max(total, 1) * 100);
        setPodcastStatus(t.podcastTranslating, `${percent}%`);
    });

    if (result.error || !result.text) {
        podcastState.loading = false;
        podcastState.stopped = true;
        if (podcastButton) podcastButton.innerHTML = `[ 🎧 ${t.btnPodcast} ]`;
        setPodcastStatus(`${t.podcastTranslationFailed} ${result.message || ''}`.trim());
        showTranslationError(document.getElementById(`btn-${idNum}`), card, result);
        return;
    }

    applyFullTranslationToCard(idNum, result);
    if (playerTitle) playerTitle.textContent = result.title || article?.title || t.podcastTitle;
    if (podcastButton) podcastButton.innerHTML = `[ 🎧 ${t.btnPodcast} ]`;

    const voice = getPodcastVoice();
    if (!voice) {
        setPodcastStatus(t.podcastNoVoice);
    }

    podcastState.chunks = splitTextForSpeech(`${result.title}. ${result.text}`);
    podcastState.index = 0;
    podcastState.loading = false;
    podcastState.stopped = false;
    podcastState.paused = true;
    podcastState.started = false;
    podcastState.utterance = null;
    window.speechSynthesis.cancel();
    setPodcastStatus(t.podcastReady || 'Ready – press Play', `0/${podcastState.chunks.length}`);
    updatePodcastUiText();
}

function togglePodcastPause() {
    if (!('speechSynthesis' in window) || podcastState.loading || podcastState.stopped) return;
    const t = uiTexte[currentLang] || uiTexte.en;

    // Der erste Klick startet die vorbereitete Aufnahme. Nach der Übersetzung
    // wird nichts mehr automatisch abgespielt.
    if (!podcastState.started) {
        podcastState.paused = false;
        speakCurrentPodcastChunk();
        return;
    }

    if (podcastState.paused) {
        window.speechSynthesis.resume();
        podcastState.paused = false;
        setPodcastStatus(t.podcastSpeaking, `${podcastState.index + 1}/${podcastState.chunks.length}`);
    } else {
        window.speechSynthesis.pause();
        podcastState.paused = true;
        setPodcastStatus(t.podcastPaused, `${podcastState.index + 1}/${podcastState.chunks.length}`);
    }
    updatePodcastUiText();
}

function stopPodcast(hidePlayer = true) {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    podcastState = {
        articleId: null,
        chunks: [],
        index: 0,
        paused: false,
        loading: false,
        stopped: true,
        started: false,
        utterance: null
    };
    const player = document.getElementById('podcast-player');
    if (player && hidePlayer) player.hidden = true;
    setPodcastStatus('');
    updatePodcastUiText();
}

function restartPodcastChunkAfterSettingChange() {
    if (!('speechSynthesis' in window) || podcastState.loading || podcastState.stopped || !podcastState.started) return;

    const wasPlaying = !podcastState.paused;
    podcastState.utterance = null;
    window.speechSynthesis.cancel();

    if (wasPlaying) {
        window.setTimeout(() => {
            podcastState.started = false;
            podcastState.paused = false;
            speakCurrentPodcastChunk();
        }, 120);
    } else {
        podcastState.started = false;
        podcastState.paused = true;
        const t = uiTexte[currentLang] || uiTexte.en;
        setPodcastStatus(t.podcastReady || 'Ready – press Play', `${podcastState.index + 1}/${podcastState.chunks.length}`);
        updatePodcastUiText();
    }
}

function changePodcastRate(value) {
    localStorage.setItem('wrn_podcast_rate', String(value || 1));
    restartPodcastChunkAfterSettingChange();
}

function changePodcastVoice() {
    const value = document.getElementById('podcast-voice-select')?.value || '';
    localStorage.setItem(`wrn_podcast_voice_${currentLang}`, value);
    restartPodcastChunkAfterSettingChange();
}

function initializePodcast() {
    const rateSelect = document.getElementById('podcast-rate-select');
    const savedRate = localStorage.getItem('wrn_podcast_rate') || '1';
    if (rateSelect && [...rateSelect.options].some(option => option.value === savedRate)) {
        rateSelect.value = savedRate;
    }
    updatePodcastUiText();
    refreshPodcastVoices();
    if ('speechSynthesis' in window) {
        window.speechSynthesis.addEventListener('voiceschanged', refreshPodcastVoices);
        // Safari und manche Android-Browser stellen die Stimmen erst verspätet bereit.
        [150, 600, 1500, 3000].forEach(delay => window.setTimeout(refreshPodcastVoices, delay));
    }
}


function isEventArticle(article) {
    return article?.type === "event" || articleMatchesCategory(article, "Radar");
}

function normalizedStringArray(value) {
    const source = Array.isArray(value) ? value : (value ? [value] : []);
    return [...new Set(source.map(item => String(item ?? "").trim()).filter(Boolean))];
}

function parseDateMs(value) {
    if (!value) return 0;
    const numberValue = Number(value);
    if (Number.isFinite(numberValue) && numberValue > 1000000000) {
        return numberValue < 100000000000 ? numberValue * 1000 : numberValue;
    }
    const parsed = new Date(value).getTime();
    return Number.isFinite(parsed) ? parsed : 0;
}

function getEventStartMs(article) {
    return parseDateMs(article?.eventStart || article?.pubDate);
}

function getEventEndMs(article) {
    return parseDateMs(article?.eventEnd) || getEventStartMs(article);
}

// Liefert den Kalendertag eines Events als YYYY-MM-DD.
// Radar-API-Einträge besitzen dafür das Feld eventDate. Bei älteren
// Eventquellen wird der Tag aus eventStart beziehungsweise pubDate abgeleitet.
function getEventDateKey(article) {
    const storedDate = String(article?.eventDate || '').trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(storedDate)) return storedDate;

    const rawStart = String(article?.eventStart || article?.pubDate || '').trim();
    const isoMatch = rawStart.match(/^(\d{4}-\d{2}-\d{2})/);
    if (isoMatch) return isoMatch[1];

    const startMs = getEventStartMs(article);
    if (!startMs) return '';
    return new Date(startMs).toISOString().slice(0, 10);
}

function getLocalDayBounds(date) {
    const start = new Date(date);
    start.setHours(0, 0, 0, 0);
    const end = new Date(start);
    end.setDate(end.getDate() + 1);
    return [start.getTime(), end.getTime()];
}

function eventOverlaps(article, fromMs, toMs) {
    const start = getEventStartMs(article);
    const end = getEventEndMs(article) || start;
    if (!start) return false;
    return end >= fromMs && start < toMs;
}

function eventIsFree(article) {
    const values = [
        article?.eventPrice,
        ...normalizedStringArray(article?.eventPriceCategories)
    ].join(" ").toLowerCase();
    return /(^|\b)(free|kostenlos|gratis|frei|0(?:[.,]00)?)(\b|$)/i.test(values);
}

function eventMatchesSpecialFilters(article) {
    if (!isEventArticle(article)) return false;

    // Abgelaufene Termine werden ohne zusätzlichen Filterknopf ausgeblendet.
    // Der zweistündige Puffer verhindert, dass ein gerade laufendes Event sofort verschwindet.
    const end = getEventEndMs(article);
    if (end && end < Date.now() - (2 * 60 * 60 * 1000)) return false;

    const exactChecks = [
        ['event-country-filter', String(article?.eventCountry || '')],
        ['event-city-filter', String(article?.eventCity || '')]
    ];
    for (const [id, articleValue] of exactChecks) {
        const selected = document.getElementById(id)?.value || '';
        if (selected && articleValue.trim().toLocaleLowerCase() !== selected.trim().toLocaleLowerCase()) return false;
    }

    const period = document.getElementById('event-date-filter')?.value || 'upcoming';
    const now = new Date();
    const nowMs = now.getTime();

    if (period === 'today') {
        const [from, to] = getLocalDayBounds(now);
        if (!eventOverlaps(article, from, to)) return false;
    } else if (period === 'tomorrow') {
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const [from, to] = getLocalDayBounds(tomorrow);
        if (!eventOverlaps(article, from, to)) return false;
    } else if (period === '7days' && !eventOverlaps(article, nowMs - 7200000, nowMs + 7 * 86400000)) {
        return false;
    } else if (period === '14days' && !eventOverlaps(article, nowMs - 7200000, nowMs + 14 * 86400000)) {
        return false;
    } else if (period === '30days' && !eventOverlaps(article, nowMs - 7200000, nowMs + 30 * 86400000)) {
        return false;
    } else if (period === 'nextmonth') {
        const from = new Date(now.getFullYear(), now.getMonth() + 1, 1, 0, 0, 0, 0);
        const to = new Date(now.getFullYear(), now.getMonth() + 2, 1, 0, 0, 0, 0);
        if (!eventOverlaps(article, from.getTime(), to.getTime())) return false;
    }

    const arrayChecks = [
        ['event-category-filter', article?.eventCategories],
        ['event-group-filter', article?.eventGroups]
    ];
    for (const [id, values] of arrayChecks) {
        const selected = document.getElementById(id)?.value || '';
        if (selected && !normalizedStringArray(values).includes(selected)) return false;
    }

    return true;
}

function displayCountryName(value) {
    if (!value) return '';
    if (String(value).length === 2 && typeof Intl.DisplayNames === 'function') {
        try {
            return new Intl.DisplayNames([currentLang], { type: 'region' }).of(String(value).toUpperCase()) || value;
        } catch (error) {}
    }
    return value;
}

function getRadarFacetMetadata() {
    const metadata = allNewsData.find(item => item?.sourceType === 'radar-api-meta');
    return metadata?.radarFacets && typeof metadata.radarFacets === 'object'
        ? metadata.radarFacets
        : {};
}

function normalizeFilterOption(value, label = value, count = 0) {
    const cleanValue = String(value ?? '').trim();
    const cleanLabel = String(label ?? cleanValue).trim();
    if (!cleanValue || !cleanLabel) return null;
    return {
        value: cleanValue,
        label: cleanLabel,
        count: Number.isFinite(Number(count)) ? Number(count) : 0
    };
}

function mergeFilterOptions(primaryOptions, fallbackValues, valueKey = 'value') {
    const map = new Map();

    const add = option => {
        if (!option) return;
        const normalized = typeof option === 'string'
            ? normalizeFilterOption(option)
            : normalizeFilterOption(option[valueKey] ?? option.value, option.label ?? option.formatted, option.count);
        if (!normalized) return;
        const key = normalized.value.toLocaleLowerCase();
        const old = map.get(key);
        if (!old || normalized.count > old.count) map.set(key, normalized);
    };

    (Array.isArray(primaryOptions) ? primaryOptions : []).forEach(add);
    (Array.isArray(fallbackValues) ? fallbackValues : []).forEach(add);

    return [...map.values()].sort((a, b) => a.label.localeCompare(b.label, currentLang));
}

function setDynamicSelectOptions(id, values, allLabel, labelFormatter = value => value) {
    const select = document.getElementById(id);
    if (!select) return;
    const previous = select.value;
    select.textContent = '';

    const allOption = document.createElement('option');
    allOption.value = '';
    allOption.textContent = allLabel;
    select.append(allOption);

    values.forEach(item => {
        const optionData = typeof item === 'object'
            ? normalizeFilterOption(item.value, item.label, item.count)
            : normalizeFilterOption(item, labelFormatter(item));
        if (!optionData) return;

        const option = document.createElement('option');
        option.value = optionData.value;
        const visibleLabel = labelFormatter(optionData.label);
        option.textContent = optionData.count > 0
            ? `${visibleLabel} (${optionData.count})`
            : visibleLabel;
        select.append(option);
    });

    if ([...select.options].some(option => option.value === previous)) {
        select.value = previous;
    }
}

function populateEventFilters() {
    const t = uiTexte[currentLang] || uiTexte.en;
    const events = allNewsData.filter(article => articleMatchesCategory(article, 'Radar') && isEventArticle(article));
    const facets = getRadarFacetMetadata();

    const arrayValues = key => [...new Set(
        events.flatMap(event => normalizedStringArray(event?.[key]))
    )].sort((a, b) => a.localeCompare(b, currentLang));

    const scalarValues = key => [...new Set(
        events.map(event => String(event?.[key] || '').trim()).filter(Boolean)
    )].sort((a, b) => a.localeCompare(b, currentLang));

    // Länder: offizieller Radar-Code (z. B. DE) plus Werte aus den Eventdaten.
    const countryOptions = mergeFilterOptions(facets.country, scalarValues('eventCountry'));
    setDynamicSelectOptions('event-country-filter', countryOptions, t.eventAll, displayCountryName);

    // Städte: zuerst die tatsächlich geladenen Eventdaten, zusätzlich die
    // offiziellen Radar-Stadtfacetten. So bleibt die Liste auch dann gefüllt,
    // wenn einzelne ältere Events keine vollständige Ortsadresse besitzen.
    const selectedCountry = document.getElementById('event-country-filter')?.value || '';
    const cityEvents = selectedCountry
        ? events.filter(event => String(event?.eventCountry || '').trim().toUpperCase() === selectedCountry.toUpperCase())
        : events;
    const eventCities = [...new Set(cityEvents
        .map(event => String(event?.eventCity || '').trim())
        .filter(Boolean))]
        .sort((a, b) => a.localeCompare(b, currentLang));

    // Ist zu einem Land noch keine sichere Stadt-Land-Zuordnung vorhanden,
    // werden wenigstens die offiziellen Radar-Städte angeboten statt nur „Alle“.
    const cityOptions = eventCities.length > 0
        ? mergeFilterOptions([], eventCities)
        : mergeFilterOptions(facets.city, scalarValues('eventCity'));
    setDynamicSelectOptions('event-city-filter', cityOptions, t.eventAll);

    // Radar liefert diese Facetten offiziell. Zusätzlich werden Werte anderer
    // Eventquellen aufgenommen, damit z. B. Stressfaktor/Kontrapolis nicht fehlen.
    const categoryOptions = mergeFilterOptions(facets.category, arrayValues('eventCategories'));
    const groupOptions = mergeFilterOptions(facets.group, arrayValues('eventGroups'));

    setDynamicSelectOptions('event-category-filter', categoryOptions, t.eventAll);
    setDynamicSelectOptions('event-group-filter', groupOptions, t.eventAll);

    // Der Zeitraum ist ein Auswahlmenü mit verständlichen Presets.
    const periodSelect = document.getElementById('event-date-filter');
    if (periodSelect) {
        const previousPeriod = periodSelect.value || 'upcoming';
        const periodOptions = [
            ['upcoming', t.eventUpcoming],
            ['today', t.eventToday],
            ['tomorrow', t.eventTomorrow],
            ['7days', t.event7days],
            ['14days', t.event14days],
            ['30days', t.event30days],
            ['nextmonth', t.eventNextMonth]
        ];
        periodSelect.textContent = '';
        for (const [value, label] of periodOptions) {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = label;
            periodSelect.append(option);
        }
        periodSelect.value = periodOptions.some(([value]) => value === previousPeriod)
            ? previousPeriod
            : 'upcoming';
    }
}


function handleEventCountryChange() {
    const citySelect = document.getElementById('event-city-filter');
    if (citySelect) citySelect.value = '';
    populateEventFilters();
    applyFilters();
}

function resetEventFilters() {
    const ids = [
        'event-country-filter',
        'event-city-filter',
        'event-date-filter',
        'event-category-filter',
        'event-group-filter'
    ];
    ids.forEach(id => {
        const element = document.getElementById(id);
        if (!element) return;
        element.value = id === 'event-date-filter' ? 'upcoming' : '';
    });
    populateEventFilters();
    applyFilters();
}

function updateEventUiVisibility() {
    const panel = document.getElementById('event-filter-panel');
    if (panel) panel.hidden = activeKontinent !== 'Radar';
}

function updateSortLabels() {
    const t = uiTexte[currentLang] || uiTexte.en;
    setTxt('opt-sort-new', activeKontinent === 'Radar' ? t.eventSortSoon : t.sortNew);
    setTxt('opt-sort-old', activeKontinent === 'Radar' ? t.eventSortLate : t.sortOld);
}

function formatEventDateRange(article) {
    const startMs = getEventStartMs(article);
    if (!startMs) return '';
    const endMs = getEventEndMs(article);
    const start = new Date(startMs);
    const end = endMs ? new Date(endMs) : null;
    const dateFormatter = new Intl.DateTimeFormat(currentLang, { weekday:'short', year:'numeric', month:'2-digit', day:'2-digit' });
    const timeFormatter = new Intl.DateTimeFormat(currentLang, { hour:'2-digit', minute:'2-digit' });
    let text = `${dateFormatter.format(start)}, ${timeFormatter.format(start)}`;
    if (end && endMs !== startMs) {
        const sameDay = start.toDateString() === end.toDateString();
        text += sameDay ? `–${timeFormatter.format(end)}` : ` – ${dateFormatter.format(end)}, ${timeFormatter.format(end)}`;
    }
    return text;
}

function buildEventDetailsHtml(article, t) {
    if (!isEventArticle(article)) return '';
    const lines = [];
    const dateText = formatEventDateRange(article);
    const locationParts = [article?.eventVenue, article?.eventAddress || article?.eventCity].filter(Boolean);
    if (dateText) lines.push(`<div><strong>${escapeHtml(t.eventStarts)}</strong> ${escapeHtml(dateText)}</div>`);
    if (locationParts.length) lines.push(`<div><strong>${escapeHtml(t.eventPlace)}</strong> ${escapeHtml([...new Set(locationParts)].join(' · '))}</div>`);
    if (article?.eventPrice || normalizedStringArray(article?.eventPriceCategories).length) {
        const priceText = [article.eventPrice, ...normalizedStringArray(article.eventPriceCategories)].filter(Boolean).join(' · ');
        lines.push(`<div><strong>${escapeHtml(t.eventPriceLabel)}</strong> ${escapeHtml(priceText)}</div>`);
    }
    if (article?.eventStatus) lines.push(`<div><strong>${escapeHtml(t.eventStatusLabel)}</strong> ${escapeHtml(article.eventStatus)}</div>`);

    const badges = [
        ...normalizedStringArray(article?.eventCategories),
        ...normalizedStringArray(article?.eventTags)
    ];
    const badgeHtml = badges.length
        ? `<div class="event-badges">${badges.slice(0, 12).map(value => `<span class="event-badge">${escapeHtml(value)}</span>`).join('')}</div>`
        : '';

    return `<div class="event-facts">${lines.join('')}${badgeHtml}</div>`;
}

function changeTheme(themeName) {
    const body = document.getElementById('app-body');
    if(body) {
        body.classList.remove('theme-dark', 'theme-light'); body.classList.add(themeName);
        localStorage.setItem('wrn_theme_style', themeName);
    }
}

async function clearAllData() {
    const confirmTxt = currentLang === "de"
        ? "Möchtest du wirklich alle Lesezeichen, Einstellungen, Offline-Nachrichten und gespeicherten Übersetzungen löschen?"
        : "Delete all bookmarks, settings, offline news and saved translations?";

    if (!confirm(confirmTxt)) return;

    localStorage.clear();

    if (window.WRNStorage) {
        try { await window.WRNStorage.clearAll(); } catch (error) { console.warn(error); }
    }

    if ('caches' in window) {
        try {
            const names = await caches.keys();
            await Promise.all(names.map(name => caches.delete(name)));
        } catch (error) {
            console.warn("Browser-Caches konnten nicht vollständig gelöscht werden:", error);
        }
    }

    window.location.reload();
}

function changeLanguage() {
    const previousLang = currentLang;
    const langSelect = document.getElementById('ui-language');
    if(langSelect) { currentLang = langSelect.value; }
    if (previousLang !== currentLang && podcastState.articleId !== null) stopPodcast();
    localStorage.setItem('wrn_system_lang', currentLang); 
    
    const t = uiTexte[currentLang] || uiTexte['en'];
    document.documentElement.lang = currentLang;
    
    setTxt('txt-lang-label', t.langLabel); setTxt('txt-theme-label', t.themeLabel); setTxt('opt-theme-dark', t.themeDark); setTxt('opt-theme-light', t.themeLight); setTxt('btn-clear-cache', t.clearBtn); setTxt('txt-region-summary', t.searchRegion); setTxt('txt-topic-summary', t.searchTopic); setTxt('txt-archive-title', t.archiveTitle); setTxt('txt-contact-label', t.contactLabel); setTxt('opt-sort-new', t.sortNew); setTxt('opt-sort-old', t.sortOld); setTxt('txt-top-bookmarks', t.topBookmarks); setTxt('txt-donate-btn', t.btnDonateTop); setTxt('txt-donate-title', t.donateTitle); setTxt('txt-donate-body', t.donateBody); setTxt('txt-donate-warning', t.donateWarning); setTxt('btn-paypal', t.btnPaypal); setTxt('btn-donate-cancel', t.btnDonateCancel); setPh('search-input', t.searchPlace);
    
    setTxt('btn-glob', t.catGlobal); setTxt('btn-eur', t.catEurope); setTxt('btn-afr', t.catAfrica); setTxt('btn-nam', t.catNorthAmerica); setTxt('btn-lam', t.catLatinAmerica); setTxt('btn-asi', t.catAsia); setTxt('btn-aus', t.catAustralia);
    setTxt('cat-labor', t.catLabor); setTxt('cat-antifascism', t.catAntifascism); setTxt('cat-antisexism', t.catAntisexism); setTxt('cat-queer', t.catQueer); setTxt('cat-antiracism', t.catAntiracism); setTxt('cat-noborders', t.catNoBorders); setTxt('cat-anticapitalism', t.catAnticapitalism); setTxt('cat-theory', t.catTheory); setTxt('cat-anticolonialism', t.catAnticolonialism); setTxt('cat-antiimperialism', t.catAntiimperialism); setTxt('cat-squatting', t.catSquatting); setTxt('cat-demos', t.catDemos); setTxt('cat-antirepression', t.catAntirepression); setTxt('cat-cyber', t.catCyber); setTxt('cat-nowar', t.catNoWar); setTxt('cat-animal', t.catAnimal); setTxt('cat-eco', t.catEco); setTxt('cat-indigenous', t.catIndigenous); setTxt('cat-health', t.catHealth); setTxt('btn-lib', t.catLibraries); 
    setTxt('txt-radar-summary', t.radarSummary);

    setTxt('btn-open-info', "ℹ️ " + t.infoBtn); setTxt('txt-info-title', t.infoTitle); setHtml('txt-info-body', t.infoBody); setTxt('btn-open-feedback', t.fbBtn); setTxt('txt-fb-title', t.fbTitle); setPh('fb-text', t.fbPlace); setTxt('txt-captcha-q', t.fbCaptcha); setTxt('btn-fb-cancel', t.fbCancel); setTxt('btn-fb-send', t.fbSend);

    setTxt('txt-event-filter-title', t.eventFilterTitle); setTxt('txt-event-country', t.eventCountry); setTxt('txt-event-city', t.eventCity); setTxt('txt-event-category', t.eventCategory); setTxt('txt-event-date', t.eventDate); setTxt('txt-event-group', t.eventGroup); setTxt('btn-event-reset', t.eventReset);
    updateSortLabels();
    updatePodcastUiText();
    populatePodcastVoiceOptions();
    if (allNewsData.length > 0) populateEventFilters();
    
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
    updateEventUiVisibility();
    updateSortLabels();
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
        : allNewsData.filter(item => articleMatchesCategory(item, activeKontinent));

    const portals = [...new Set(baseList.map(item => item.quelleName).filter(Boolean))].sort();
    portals.forEach(portal => {
        listContainer.append(createSourceButton(portal, portal, currentSourceFilter === portal));
    });
}

function filterBySource(sourceName) { currentSourceFilter = sourceName; closeAllModals(); applyFilters(); }

async function fetchJsonFile(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
        throw new Error(`${url}: HTTP ${response.status}`);
    }
    const data = await response.json();
    if (!Array.isArray(data)) {
        throw new Error(`${url}: JSON ist keine Liste.`);
    }
    return data;
}

async function loadDatasetWithOfflineFallback(datasetKey, url, legacyLocalStorageKey) {
    try {
        const freshData = await fetchJsonFile(url);
        if (window.WRNStorage) {
            await window.WRNStorage.putDataset(datasetKey, freshData);
        }
        return { data: freshData, source: "network" };
    } catch (networkError) {
        console.warn(`${datasetKey} konnte nicht aktualisiert werden:`, networkError);

        if (window.WRNStorage) {
            try {
                const stored = await window.WRNStorage.getDataset(datasetKey);
                if (Array.isArray(stored) && stored.length > 0) {
                    return { data: stored, source: "indexeddb", error: networkError };
                }
            } catch (storageError) {
                console.warn(`${datasetKey} konnte nicht aus IndexedDB gelesen werden:`, storageError);
            }
        }

        // Nur für die erste Migration von älteren App-Versionen.
        try {
            const legacy = JSON.parse(localStorage.getItem(legacyLocalStorageKey) || "[]");
            if (Array.isArray(legacy) && legacy.length > 0) {
                return { data: legacy, source: "legacy", error: networkError };
            }
        } catch {}

        return { data: [], source: "none", error: networkError };
    }
}

async function initialisiereApp() {
    setTxt('status-container', "Lade Nachrichten und Events...");

    if (window.WRNStorage) {
        try {
            await window.WRNStorage.migrateLegacyLocalStorage();
            window.WRNStorage.requestPersistentStorage().catch(() => false);
        } catch (error) {
            console.warn("Offline-Speicher konnte nicht vorbereitet werden:", error);
        }
    }

    const [newsResult, eventsResult] = await Promise.all([
        loadDatasetWithOfflineFallback('news', GITHUB_NEWS_URL, 'cached_news_articles'),
        loadDatasetWithOfflineFallback('events', GITHUB_EVENTS_URL, 'cached_event_data')
    ]);

    const newsItems = newsResult.data;
    const eventItems = eventsResult.data;
    allNewsData = [...newsItems, ...eventItems];

    if (allNewsData.length === 0) {
        setTxt('status-container', "[ FEHLER ] Es sind weder Online- noch Offline-Daten vorhanden.");
        return;
    }

    populateEventFilters();
    ladeKontinentNews("Global");

    const offlineSources = [];
    if (newsResult.source !== 'network') offlineSources.push('Nachrichten');
    if (eventsResult.source !== 'network') offlineSources.push('Events');

    if (offlineSources.length > 0) {
        const status = document.getElementById('status-container');
        if (status) {
            status.style.color = 'var(--color-accent)';
            status.textContent = `${offlineSources.join(' und ')} werden aus dem Offline-Speicher angezeigt.`;
        }
    }
}

function ladeKontinentNews(kontinent) {
    if(kontinent === "Bookmarks") return ladeBookmarks();
    activeKontinent = kontinent; currentSourceFilter = "ALL"; 
    
    document.querySelectorAll('.btn-nav').forEach(btn => btn.classList.remove('active'));
    const btnMap = { 'Global': 'btn-glob', 'Europe': 'btn-eur', 'Africa': 'btn-afr', 'North America': 'btn-nam', 'Latin America': 'btn-lam', 'Asia': 'btn-asi', 'Australia & NZ': 'btn-aus', 'Labor Struggles': 'cat-labor', 'Antifascism': 'cat-antifascism', 'Antisexism': 'cat-antisexism', 'Queer-Feminism': 'cat-queer', 'Antiracism': 'cat-antiracism', 'No Borders': 'cat-noborders', 'Anticapitalism': 'cat-anticapitalism', 'Theory & Strategy': 'cat-theory', 'Anticolonialism': 'cat-anticolonialism', 'Anti-Imperialism': 'cat-antiimperialism', 'Squatting & Housing': 'cat-squatting', 'Demonstrations': 'cat-demos', 'Anti-Rep & Prisons': 'cat-antirepression', 'Cyberactivism': 'cat-cyber', 'No War': 'cat-nowar', 'Animal Liberation': 'cat-animal', 'Eco-Anarchism': 'cat-eco', 'Indigenous Struggles': 'cat-indigenous', 'Radical Health & Disability': 'cat-health', 'Libraries': 'btn-lib', 'Radar': 'cat-radar' };
    if(btnMap[kontinent]) { const b = document.getElementById(btnMap[kontinent]); if(b) b.classList.add('active'); }

    updateEventUiVisibility();
    updateSortLabels();
    if (kontinent === 'Radar') populateEventFilters();

    const t = uiTexte[currentLang] || uiTexte['en']; setTxt('status-container', t.latestNews);
    applyFilters();
}

function applyFilters(isBookmark = false) {
    const iSel = document.getElementById('search-input');
    const selPortal = currentSourceFilter || "ALL"; 
    const searchQuery = iSel ? iSel.value.toLowerCase().trim() : "";
    const sortOrder = document.getElementById('sort-select') ? document.getElementById('sort-select').value : "new";
    
    let baseList = (activeKontinent === "Bookmarks" || isBookmark) ? getSavedBookmarks() : allNewsData.filter(item => articleMatchesCategory(item, activeKontinent));
    let filtered = (selPortal === "ALL") ? baseList : baseList.filter(a => a.quelleName === selPortal);

    if (activeKontinent === 'Radar') {
        filtered = filtered.filter(eventMatchesSpecialFilters);
    }
    
    if (searchQuery !== "") { filtered = filtered.filter(a => (a.title && a.title.toLowerCase().includes(searchQuery)) || (a.content && a.content.toLowerCase().includes(searchQuery)) || normalizedStringArray(a.eventTags).join(' ').toLowerCase().includes(searchQuery) || normalizedStringArray(a.eventCategories).join(' ').toLowerCase().includes(searchQuery) || String(a.eventCity || '').toLowerCase().includes(searchQuery)); }

    filtered.sort((a, b) => {
        if (activeKontinent === 'Radar') {
            const da = getEventStartMs(a); const db = getEventStartMs(b);
            return sortOrder === 'old' ? db - da : da - db;
        }
        let da = 0; let db = 0;
        if(a.pubDate) da = new Date(a.pubDate).getTime(); if(b.pubDate) db = new Date(b.pubDate).getTime();
        if (sortOrder === "old") return (isNaN(da) ? 0 : da) - (isNaN(db) ? 0 : db); 
        else return (isNaN(db) ? 0 : db) - (isNaN(da) ? 0 : da); 
    });

    if (activeKontinent === 'Radar') {
        const t = uiTexte[currentLang] || uiTexte.en;
        setTxt('event-filter-count', `${filtered.length} ${t.eventCount}`);
    }
    
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
        const isEvent = isEventArticle(item);
        let formatDatum = "LIVE"; let isOld = false;
        try {
            const dateValue = isEvent ? (item.eventStart || item.pubDate) : item.pubDate;
            if (dateValue) {
                const articleDate = new Date(dateValue);
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
        
        let isRadar = articleMatchesCategory(item, "Radar");
        // Der grüne Look für die Termine
        let cardStyle = isRadar ? `style="border: 1px solid var(--color-green); box-shadow: 0 0 15px rgba(0, 255, 0, 0.15);"` : "";
        let titleColor = isRadar ? `color: var(--color-green);` : "";
        const eventDetailsHtml = buildEventDetailsHtml(item, t);
        const cancelledClass = String(item.eventStatus || '').toLowerCase().includes('cancel') ? 'event-cancelled' : '';
        
        let metaHtml = `<span class="meta-label">${escapeHtml(t.publisherLabel)}</span> <span style="color:var(--text-main);">${escapeHtml(publisherName)}</span> <br>`;
        if (authorName !== "" && authorName.toLowerCase() !== "unknown" && authorName.toLowerCase() !== publisherName.toLowerCase()) {
            metaHtml += `<span class="meta-label">${escapeHtml(t.authorLabel)}</span> <span style="color:var(--text-main);">${escapeHtml(authorName)}</span> <br>`;
        }
        const metaDateText = isEvent ? formatEventDateRange(item) : formatDatum;
        metaHtml += `<span class="meta-label">${escapeHtml(isEvent ? t.eventStarts : t.dateLabel)}</span> <span style="color:var(--text-main);">${escapeHtml(metaDateText || formatDatum)}</span>`;

        let articleHTML = `
            <div class="card ${isReadClass} ${cancelledClass}" id="card-${globalIndex}" data-translated="none" ${cardStyle}>
                <div class="meta">${metaHtml}</div>
                <div class="title" id="title-${globalIndex}" style="${titleColor}">${escapeHtml(item.title || 'No Title')}</div>
                ${eventDetailsHtml}
                ${imgHtml}
                <div class="teaser" id="teaser-${globalIndex}">${safeTeaserText}</div>
                <div class="full-content" id="content-${globalIndex}">${safeFullText}</div>
                <div class="button-row">
                    <button class="btn-expand" id="expand-${globalIndex}" onclick="toggleArticle(${globalIndex}, event)">${t.btnExpand}</button>
                    <button class="btn-translate" id="btn-${globalIndex}" onclick="translateArticle(${globalIndex})"><span>[ ${t.btnTranslate} ]</span></button>
                    <button class="btn-translate btn-podcast" id="podcast-${globalIndex}" onclick="startPodcast(${globalIndex})"><span>[ 🎧 ${escapeHtml(t.btnPodcast)} ]</span></button>
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


async function translateArticle(idNum) {
    const titleEl = document.getElementById(`title-${idNum}`);
    const teaserEl = document.getElementById(`teaser-${idNum}`);
    const contentEl = document.getElementById(`content-${idNum}`);
    const btnEl = document.getElementById(`btn-${idNum}`);
    const card = document.getElementById(`card-${idNum}`);
    const article = currentFilteredItems[idNum];

    if (!titleEl || !teaserEl || !contentEl || !btnEl || !card || !article) return;
    const t = uiTexte[currentLang] || uiTexte.en;

    if (card.dataset.translated === 'translating') return;
    if (card.dataset.translated === 'full' && card.dataset.translationLanguage === currentLang) return;

    try { markAsRead(article.link, idNum); } catch (error) {}
    card.dataset.translated = 'translating';

    const isExpanded = card.dataset.expanded === 'true' || contentEl.style.display === 'block';
    if (!isExpanded) {
        btnEl.innerHTML = `${starSpinner} <span style="margin-left: 8px;">[ ${t.btnLoading} ]</span>`;

        const originalText = String(article.content || '').trim();
        let originalTeaser = originalText.slice(0, 500);
        const sentence = originalText.match(/[^.!?]+[.!?]+/)?.[0];
        if (sentence) originalTeaser = sentence;

        const result = await fetchTranslationRequest({
            title: article.title || "",
            text: originalTeaser,
            mode: "title_and_text"
        });

        if (result.error || !result.text) {
            showTranslationError(btnEl, card, result);
            return;
        }

        const parsed = parseTranslatedTitleAndText(result.text, article.title || '');
        if (parsed.title) titleEl.textContent = parsed.title;
        if (parsed.text) teaserEl.textContent = parsed.text;
        titleEl.classList.add('translated');
        btnEl.innerHTML = `[ ${t.btnDone} ]`;
        btnEl.removeAttribute('title');
        card.dataset.translated = 'teaser';
        card.dataset.translationLanguage = currentLang;
        return;
    }

    btnEl.innerHTML = `${starSpinner} <span style="margin-left: 8px;">[ ${t.btnLoading} ]</span>`;
    const result = await translateFullArticleForLanguage(idNum, (current, total) => {
        const progressText = total > 1 ? `[ ${t.btnLoading} ${current}/${total} ]` : `[ ${t.btnLoading} ]`;
        btnEl.innerHTML = `${starSpinner} <span style="margin-left: 8px;">${progressText}</span>`;
    });

    if (result.error || !result.text) {
        showTranslationError(btnEl, card, result);
        return;
    }

    applyFullTranslationToCard(idNum, result);
}

window.addEventListener('scroll', () => {
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 800) {
        if (currentlyDisplayedCount < currentFilteredItems.length) { renderNextBatch(); }
    }
});

window.addEventListener('offline', () => {
    const status = document.getElementById('status-container');
    if (status) {
        status.style.color = 'var(--color-accent)';
        status.textContent = currentLang === 'de'
            ? 'Offline: Gespeicherte Nachrichten und Events bleiben verfügbar.'
            : 'Offline: Saved news and events remain available.';
    }
});

window.addEventListener('online', () => {
    const status = document.getElementById('status-container');
    if (status) {
        status.style.color = 'var(--color-green)';
        status.textContent = currentLang === 'de'
            ? 'Wieder online. Daten werden beim nächsten Laden aktualisiert.'
            : 'Back online. Data will refresh on the next load.';
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
        
        changeTheme(savedTheme); changeLanguage(); initializePodcast(); initialisiereApp(); 

        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('./service-worker.js')
                .then(registration => {
                    registration.update().catch(() => {});
                })
                .catch(error => {
                    console.warn('Service Worker konnte nicht registriert werden:', error);
                });
        }
    } catch (e) {
        const stat = document.getElementById('status-container');
        if(stat) stat.innerText = "Kritischer Start-Fehler: " + e.message;
    }
});