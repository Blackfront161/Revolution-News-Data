/* World Revolution News – 1.7.12 Emergency Mode */
'use strict';

window.WRN_EMERGENCY_MODE = true;
window.WRN_CONFIG = Object.freeze({
    appName: 'World Revolution News',
    version: '1.7.12',
    build: '2026.07.19-emergency-mobile-repair',
    releasedAt: '2026-07-19T20:00:00+02:00',
    repository: 'Blackfront161/Revolution-News-Data',
    emergencyMode: true,
    dataUrls: Object.freeze({
        news: 'https://blackfront161.github.io/Revolution-News-Data/news-feed.json',
        events: 'https://blackfront161.github.io/Revolution-News-Data/events-feed.json',
        podcasts: 'https://blackfront161.github.io/Revolution-News-Data/podcasts.json',
        radio: 'https://blackfront161.github.io/Revolution-News-Data/radio-stations.json',
        sourceHealth: 'https://blackfront161.github.io/Revolution-News-Data/source-health.json',
        sourceCatalog: 'https://blackfront161.github.io/Revolution-News-Data/source-catalog.json',
        podcastHealth: 'https://blackfront161.github.io/Revolution-News-Data/podcast-health.json',
        radioHealth: 'https://blackfront161.github.io/Revolution-News-Data/radio-health.json',
        podcastSources: 'https://blackfront161.github.io/Revolution-News-Data/podcast-sources.json',
        radioSources: 'https://blackfront161.github.io/Revolution-News-Data/radio-sources.json'
    }),
    proxyUrl: 'https://revolution-proxy.paghklo.workers.dev',
    sharedTranslationUrl: ''
});

(() => {
    if (window.__wrnEmergency1712) return;
    window.__wrnEmergency1712 = true;

    /* Begrenze die großen JSON-Antworten, bevor app.js hunderte Karten erzeugt. */
    const nativeFetch = window.fetch.bind(window);
    window.fetch = async (...args) => {
        const response = await nativeFetch(...args);
        const requestUrl = String(
            typeof args[0] === 'string' ? args[0] : args[0]?.url || ''
        );
        const limit = /news-feed\.json/i.test(requestUrl)
            ? 80
            : (/events-feed\.json/i.test(requestUrl) ? 160 : 0);
        if (!limit || !response.ok) return response;

        try {
            const data = await response.clone().json();
            if (!Array.isArray(data) || data.length <= limit) return response;
            const headers = new Headers(response.headers);
            headers.set('content-type', 'application/json; charset=utf-8');
            headers.delete('content-length');
            return new Response(JSON.stringify(data.slice(0, limit)), {
                status: response.status,
                statusText: response.statusText,
                headers
            });
        } catch (_) {
            return response;
        }
    };

    const MAX_VISIBLE_CARDS = 60;
    const style = document.createElement('style');
    style.id = 'wrn-emergency-style-1712';
    style.textContent = `
        :root { color-scheme: dark; }
        html, body {
            background: #050508 !important;
            background-image: none !important;
            background-attachment: scroll !important;
            scroll-behavior: auto !important;
        }
        html, body, body * {
            animation: none !important;
            transition: none !important;
        }
        body::before, body::after,
        #wrn-start-screen,
        .wrn-start-screen,
        .wrn-start-leaving,
        .app-start-screen {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        body, .card, .feedback-modal, .podcast-options-modal,
        .podcast-library-modal, .system-status-modal, .global-media-bar {
            -webkit-backdrop-filter: none !important;
            backdrop-filter: none !important;
            filter: none !important;
            box-shadow: none !important;
            text-shadow: none !important;
        }
        .card {
            background: #101017 !important;
            border: 1px solid #30303a !important;
            content-visibility: auto;
            contain-intrinsic-size: 220px;
        }
        #feed-container img,
        #archive-container img,
        .card picture,
        .card video,
        .article-image,
        .article-thumbnail,
        .news-image,
        .card-image {
            display: none !important;
        }
        .btn-podcast-nav,
        #btn-podcast-library,
        #btn-open-zine,
        .quick-nav-zine,
        .global-media-bar,
        .audio-hub,
        .audio-catalog,
        .briefing-panel,
        .briefing-card,
        .article-summary,
        .summary-panel,
        .shared-translation-status,
        .wrn-diagnostics-overlay,
        [data-feature="briefing"],
        [data-feature="audio"],
        [data-feature="summary"] {
            display: none !important;
        }
        .top-action-bar {
            position: static !important;
        }
        .filter-bar,
        .nav-bar,
        .quick-nav-bar {
            background: #0b0b10 !important;
            box-shadow: none !important;
        }
        #feed-container, #archive-container {
            contain: layout style;
        }
        #wrn-emergency-notice {
            margin: 8px 0 12px;
            padding: 8px 10px;
            border: 1px solid #ff334f;
            background: #18060b;
            color: #fff;
            font: 600 13px/1.35 system-ui, sans-serif;
        }
        #wrn-emergency-notice a { color: #7ee7ff; }
        @media (max-width: 720px) {
            body { padding-left: 8px !important; padding-right: 8px !important; }
            header { margin-bottom: 10px !important; }
            .card { margin-bottom: 10px !important; padding: 12px !important; }
            .teaser, .full-content { max-height: 16em; overflow: hidden; }
        }
    `;
    document.head.appendChild(style);

    const timeout = (promise, ms, fallback) => new Promise(resolve => {
        let finished = false;
        const timer = window.setTimeout(() => {
            if (finished) return;
            finished = true;
            resolve(fallback);
        }, ms);
        Promise.resolve(promise).then(value => {
            if (finished) return;
            finished = true;
            window.clearTimeout(timer);
            resolve(value);
        }).catch(() => {
            if (finished) return;
            finished = true;
            window.clearTimeout(timer);
            resolve(fallback);
        });
    });

    const patchStorage = () => {
        const storage = window.WRNStorage;
        if (!storage || storage.__emergency1712) return;
        storage.__emergency1712 = true;

        const getDataset = storage.getDataset?.bind(storage);
        storage.migrateLegacyLocalStorage = () => Promise.resolve(false);
        storage.requestPersistentStorage = () => Promise.resolve(false);
        storage.putDataset = () => Promise.resolve(false);
        storage.getDataset = key => getDataset
            ? timeout(getDataset(key), 700, null)
            : Promise.resolve(null);
    };

    const stripHeavyMedia = root => {
        if (!root?.querySelectorAll) return;
        root.querySelectorAll(
            '#feed-container img, #archive-container img, '
            + '#feed-container video, #archive-container video, audio'
        ).forEach(media => {
            try {
                if (typeof media.pause === 'function') media.pause();
                media.removeAttribute('autoplay');
                media.removeAttribute('src');
                media.querySelectorAll?.('source').forEach(source => source.removeAttribute('src'));
                if ('preload' in media) media.preload = 'none';
            } catch (_) {
                // Notfallmodus darf bei einzelnen Medien nie abbrechen.
            }
        });
    };

    const trimFeed = () => {
        ['feed-container', 'archive-container'].forEach(id => {
            const container = document.getElementById(id);
            if (!container) return;
            const cards = Array.from(container.querySelectorAll(':scope > .card'));
            cards.slice(MAX_VISIBLE_CARDS).forEach(card => card.remove());
            stripHeavyMedia(container);
        });
    };

    const releaseUi = () => {
        document.documentElement.classList.remove('wrn-booting', 'wrn-app-entering');
        document.documentElement.style.pointerEvents = 'auto';
        if (document.body) {
            document.body.classList.add('wrn-emergency-mode');
            document.body.dataset.motion = 'reduced';
            document.body.style.pointerEvents = 'auto';
        }
        document.querySelectorAll(
            '#wrn-start-screen, .wrn-start-screen, .wrn-start-leaving, .app-start-screen'
        ).forEach(element => element.remove());
        patchStorage();
        trimFeed();
    };

    const addNotice = () => {
        if (!document.body || document.getElementById('wrn-emergency-notice')) return;
        const notice = document.createElement('div');
        notice.id = 'wrn-emergency-notice';
        notice.setAttribute('role', 'status');
        notice.innerHTML = 'Notfallmodus 1.7.12 aktiv – reduzierte Darstellung für Smartphones. '
            + '<a href="./mobile-repair.html">Leichten Direkt-Feed öffnen</a>';
        const header = document.querySelector('header');
        (header?.parentNode || document.body).insertBefore(notice, header?.nextSibling || document.body.firstChild);
    };

    const renderFallbackFeed = async () => {
        await new Promise(resolve => window.setTimeout(resolve, 2800));
        const feed = document.getElementById('feed-container');
        if (!feed || feed.querySelector('.card')) return;

        const controller = new AbortController();
        const timer = window.setTimeout(() => controller.abort(), 6500);
        try {
            const response = await fetch(`./news-feed.json?emergency=${Date.now()}`, {
                cache: 'no-store',
                signal: controller.signal
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const items = await response.json();
            if (!Array.isArray(items) || items.length === 0) throw new Error('Leerer Feed');

            const fragment = document.createDocumentFragment();
            items.slice(0, 40).forEach(item => {
                const card = document.createElement('article');
                card.className = 'card wrn-emergency-card';

                const meta = document.createElement('div');
                meta.className = 'meta';
                meta.textContent = [item.quelleName, item.pubDate ? String(item.pubDate).slice(0, 10) : '']
                    .filter(Boolean).join(' · ');

                const title = document.createElement('h2');
                title.className = 'title';
                title.textContent = String(item.title || 'Nachricht');

                const teaser = document.createElement('p');
                teaser.className = 'teaser';
                teaser.textContent = String(item.content || '').slice(0, 520);

                card.append(meta, title, teaser);
                if (item.link) {
                    const link = document.createElement('a');
                    link.href = String(item.link);
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    link.textContent = 'Original öffnen';
                    card.appendChild(link);
                }
                fragment.appendChild(card);
            });
            feed.replaceChildren(fragment);

            const status = document.getElementById('status-container');
            if (status) status.textContent = 'Notfall-Feed geladen';
        } catch (error) {
            const status = document.getElementById('status-container');
            if (status) status.textContent = 'Notfall-Feed konnte nicht geladen werden.';
            console.error('WRN Emergency Feed:', error);
        } finally {
            window.clearTimeout(timer);
        }
    };

    const start = () => {
        releaseUi();
        addNotice();
        stripHeavyMedia(document);

        const observer = new MutationObserver(mutations => {
            for (const mutation of mutations) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.ELEMENT_NODE) stripHeavyMedia(node);
                });
            }
            trimFeed();
        });
        observer.observe(document.body, { childList: true, subtree: true });

        window.setTimeout(releaseUi, 500);
        window.setTimeout(releaseUi, 1800);
        window.setTimeout(releaseUi, 4200);
        renderFallbackFeed();
    };

    document.addEventListener('pointerdown', releaseUi, { capture: true, passive: true });
    document.addEventListener('touchstart', releaseUi, { capture: true, passive: true });
    window.addEventListener('pageshow', releaseUi);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', start, { once: true });
    } else {
        start();
    }
})();
