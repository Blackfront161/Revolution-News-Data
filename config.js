/* World Revolution News – 1.7.12 Click & Performance Repair */
'use strict';

window.WRN_EMERGENCY_MODE = true;

window.WRN_CONFIG = Object.freeze({
    appName: 'World Revolution News',
    version: '1.7.12',
    build: '2026.07.19-click-performance-repair',
    releasedAt: '2026-07-19T21:20:00+02:00',
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
    sharedTranslationUrl: 'https://wrn-translation-cache.paghklo.workers.dev'
});

/*
 * Feed-Bremse: Es werden keine Dateien oder gespeicherten Daten gelöscht.
 * ?full=1 lädt bei Bedarf wieder den vollständigen Feed.
 */
(() => {
    if (window.__wrnFeedGuard1712ClickFix) return;
    window.__wrnFeedGuard1712ClickFix = true;

    const wantsFullFeed = () =>
        new URLSearchParams(location.search).get('full') === '1';

    const nativeFetch = window.fetch.bind(window);

    window.fetch = async (...args) => {
        const response = await nativeFetch(...args);
        if (wantsFullFeed() || !response.ok) return response;

        const url = String(
            typeof args[0] === 'string'
                ? args[0]
                : args[0]?.url || ''
        );

        const limit = /news-feed\.json/i.test(url)
            ? 160
            : (/events-feed\.json/i.test(url) ? 220 : 0);

        if (!limit) return response;

        try {
            const rows = await response.clone().json();
            if (!Array.isArray(rows) || rows.length <= limit) {
                return response;
            }

            const headers = new Headers(response.headers);
            headers.set('content-type', 'application/json; charset=utf-8');
            headers.delete('content-length');

            return new Response(JSON.stringify(rows.slice(0, limit)), {
                status: response.status,
                statusText: response.statusText,
                headers
            });
        } catch {
            return response;
        }
    };
})();

/*
 * Reine CSS-Notbremse. Keine Schleife über sämtliche Seitenelemente bei Klicks.
 */
(() => {
    if (document.getElementById('wrn-click-fix-style-1712')) return;

    const style = document.createElement('style');
    style.id = 'wrn-click-fix-style-1712';
    style.textContent = `
        html,
        body {
            pointer-events: auto !important;
        }

        button,
        a,
        input,
        select,
        textarea,
        summary,
        label,
        [role="button"] {
            pointer-events: auto;
        }

        #wrn-start-screen,
        .wrn-start-screen,
        .wrn-start-leaving,
        .app-start-screen,
        .wrn-article-detail[hidden],
        .wrn-more-panel[hidden],
        .wrn-search-panel[hidden],
        .wrn-subtabs-wrap[hidden],
        [hidden] {
            pointer-events: none !important;
        }

        @media (max-width: 820px) {
            html,
            body {
                background-color: #050508 !important;
                background-image: none !important;
                background-attachment: scroll !important;
                scroll-behavior: auto !important;
            }

            html,
            body,
            body * {
                animation-duration: 0.001ms !important;
                animation-iteration-count: 1 !important;
                transition-duration: 0.001ms !important;
            }

            body::before,
            body::after,
            #wrn-start-screen,
            .wrn-start-screen,
            .wrn-start-leaving,
            .app-start-screen {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
            }

            body,
            .card,
            .feedback-modal,
            .podcast-options-modal,
            .podcast-library-modal,
            .system-status-modal,
            .global-media-bar {
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
                contain-intrinsic-size: 240px;
            }

            #feed-container img,
            #archive-container img,
            #feed-container picture,
            #archive-container picture,
            #feed-container video,
            #archive-container video,
            .article-image,
            .article-thumbnail,
            .news-image,
            .card-image {
                display: none !important;
            }
        }
    `;
    document.head.appendChild(style);
})();

/*
 * Einmalige Freigabe statt einer teuren DOM-Schleife bei jedem pointerdown.
 */
(() => {
    if (window.__wrnSingleInteractionRelease1712) return;
    window.__wrnSingleInteractionRelease1712 = true;

    const release = () => {
        document.documentElement.classList.remove(
            'wrn-booting',
            'wrn-app-entering'
        );

        document.documentElement.style.pointerEvents = 'auto';

        if (document.body) {
            document.body.style.pointerEvents = 'auto';
        }

        const startScreen = document.getElementById('wrn-start-screen');
        if (startScreen) startScreen.remove();
    };

    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            release,
            { once: true }
        );
    } else {
        release();
    }

    window.addEventListener('pageshow', release, { once: true });
    window.setTimeout(release, 800);
    window.setTimeout(release, 2600);

    window.WRNReleaseInteraction = release;
})();

/*
 * Offline-Speicher bleibt erhalten, darf den Start aber nicht blockieren.
 */
(() => {
    if (window.__wrnStorageGuard1712ClickFix) return;
    window.__wrnStorageGuard1712ClickFix = true;

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

    document.addEventListener('DOMContentLoaded', () => {
        const storage = window.WRNStorage;
        if (!storage || storage.__clickFixGuard1712) return;

        const original = {
            migrateLegacyLocalStorage:
                storage.migrateLegacyLocalStorage?.bind(storage),
            requestPersistentStorage:
                storage.requestPersistentStorage?.bind(storage),
            getDataset:
                storage.getDataset?.bind(storage),
            putDataset:
                storage.putDataset?.bind(storage)
        };

        storage.__clickFixGuard1712 = true;

        storage.migrateLegacyLocalStorage = () =>
            original.migrateLegacyLocalStorage
                ? timeout(
                    original.migrateLegacyLocalStorage(),
                    1000,
                    false
                )
                : Promise.resolve(false);

        storage.requestPersistentStorage = () =>
            original.requestPersistentStorage
                ? timeout(
                    original.requestPersistentStorage(),
                    700,
                    false
                )
                : Promise.resolve(false);

        storage.getDataset = key =>
            original.getDataset
                ? timeout(original.getDataset(key), 1000, null)
                : Promise.resolve(null);

        storage.putDataset = (key, data) => {
            if (original.putDataset) {
                window.setTimeout(() => {
                    void timeout(
                        original.putDataset(key, data),
                        1600,
                        false
                    );
                }, 0);
            }
            return Promise.resolve(false);
        };
    }, { once: true });
})();

/*
 * Stabile Kernoberfläche:
 * Navigation und Sprache werden geladen. Schwere Komfortmodule starten nicht
 * mehr automatisch gemeinsam. Dadurch bleiben Hauptthread und Klicks frei.
 */
(() => {
    if (window.__wrnCoreInterface1712ClickFix) return;
    window.__wrnCoreInterface1712ClickFix = true;

    const VERSION = '1712-clickfix';

    const addStyle = (file, marker) => {
        if (document.querySelector(
            `link[data-wrn-style="${marker}"]`
        )) return;

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `./${file}?v=${VERSION}`;
        link.dataset.wrnStyle = marker;
        link.addEventListener('error', () => {
            console.warn(`WRN stylesheet missing: ${file}`);
        }, { once: true });
        document.head.appendChild(link);
    };

    const loadScript = (file, marker, timeoutMs = 8000) =>
        new Promise(resolve => {
            const current = document.querySelector(
                `script[data-wrn-module="${marker}"]`
            );

            if (current?.dataset.loaded === 'true') {
                resolve(true);
                return;
            }

            const script = current || document.createElement('script');

            if (!current) {
                script.src = `./${file}?v=${VERSION}`;
                script.dataset.wrnModule = marker;
            }

            let finished = false;

            const finish = success => {
                if (finished) return;
                finished = true;
                script.dataset.loaded = success ? 'true' : 'false';
                resolve(success);
            };

            const timer = window.setTimeout(
                () => finish(false),
                timeoutMs
            );

            script.addEventListener('load', () => {
                window.clearTimeout(timer);
                finish(true);
            }, { once: true });

            script.addEventListener('error', () => {
                window.clearTimeout(timer);
                finish(false);
            }, { once: true });

            if (!current) document.body.appendChild(script);
        });

    const loadSequentially = async files => {
        for (const [file, marker] of files) {
            await loadScript(file, marker);
        }
    };

    const loadCore = async () => {
        [
            ['release-1.5-nav.css', 'navigation-clickfix'],
            ['typography.css', 'typography-clickfix'],
            ['briefing.css', 'briefing-clickfix'],
            ['audio-catalog.css', 'audio-catalog-clickfix'],
            ['article-summary.css', 'summary-clickfix'],
            ['interface-qol.css', 'interface-clickfix']
        ].forEach(([file, marker]) => addStyle(file, marker));

        await loadSequentially([
            ['app-safety.js', 'safety-clickfix'],
            ['wrn-i18n.js', 'i18n-clickfix'],
            ['typography.js', 'typography-clickfix'],
            ['release-1.5-nav.js', 'navigation-clickfix']
        ]);

        window.dispatchEvent(
            new CustomEvent('wrn-app-ready')
        );
    };

    /*
     * Briefing wird erst bei einem echten Klick auf den Briefing-Reiter geladen.
     * Es blockiert dadurch weder Start noch andere Schaltflächen.
     */
    let briefingLoading = null;

    const loadBriefing = () => {
        if (window.WRNBriefing) {
            window.WRNBriefing.show?.();
            return Promise.resolve(true);
        }

        if (briefingLoading) return briefingLoading;

        briefingLoading = loadScript(
            'briefing.js',
            'briefing-lazy-clickfix',
            12000
        ).then(success => {
            if (success) window.WRNBriefing?.show?.();
            return success;
        });

        return briefingLoading;
    };

    document.addEventListener('click', event => {
        const tab = event.target.closest?.(
            '.wrn-top-tab[data-key="briefing"]'
        );
        if (tab) void loadBriefing();
    });

    if (document.readyState === 'complete') {
        void loadCore();
    } else {
        window.addEventListener(
            'load',
            () => void loadCore(),
            { once: true }
        );
    }
})();

/*
 * Text-Rückfall nur dann, wenn die normale App tatsächlich hängen bleibt.
 */
(() => {
    if (window.__wrnRescueFeed1712ClickFix) return;
    window.__wrnRescueFeed1712ClickFix = true;

    const run = async () => {
        await new Promise(resolve => {
            window.setTimeout(resolve, 8500);
        });

        const status = document.getElementById('status-container');
        const feed = document.getElementById('feed-container');

        const loading = /Lade Nachrichten|Loading news|Connecting/i.test(
            String(status?.textContent || '')
        );

        if (!feed || !loading || feed.children.length > 0) return;

        const controller = new AbortController();
        const timer = window.setTimeout(
            () => controller.abort(),
            7000
        );

        try {
            const response = await fetch(
                `./news-feed.json?rescue=${Date.now()}`,
                {
                    cache: 'no-store',
                    signal: controller.signal
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const rows = await response.json();

            if (!Array.isArray(rows) || rows.length === 0) {
                throw new Error('Leerer Feed');
            }

            feed.textContent = '';

            rows.slice(0, 30).forEach(item => {
                const card = document.createElement('article');
                card.className = 'card wrn-rescue-card';

                const meta = document.createElement('div');
                meta.className = 'meta';
                meta.textContent = [
                    item.quelleName || 'World Revolution News',
                    item.pubDate
                        ? String(item.pubDate).slice(0, 10)
                        : ''
                ].filter(Boolean).join(' · ');

                const title = document.createElement('div');
                title.className = 'title';
                title.textContent = String(
                    item.title || 'Nachricht'
                );

                const teaser = document.createElement('div');
                teaser.className = 'teaser';
                teaser.textContent = String(
                    item.content || ''
                ).slice(0, 420);

                card.append(meta, title, teaser);

                if (item.link) {
                    const link = document.createElement('a');
                    link.className = 'btn-translate';
                    link.href = String(item.link);
                    link.target = '_blank';
                    link.rel = 'noopener noreferrer';
                    link.textContent = '[ Original öffnen ]';
                    card.appendChild(link);
                }

                feed.appendChild(card);
            });

            if (status) {
                status.style.color = 'var(--color-green)';
                status.textContent = 'Nachrichten geladen';
            }
        } catch (error) {
            if (status) {
                status.style.color = '#ff334f';
                status.textContent =
                    'Nachrichten konnten nicht geladen werden.';
            }
            console.error('WRN Rettungsfeed:', error);
        } finally {
            window.clearTimeout(timer);
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            () => void run(),
            { once: true }
        );
    } else {
        void run();
    }
})();
