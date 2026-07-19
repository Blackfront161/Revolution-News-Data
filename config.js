/* World Revolution News – 1.7.12 Emergency Compatibility Mode */
'use strict';

window.WRN_EMERGENCY_MODE = true;

window.WRN_CONFIG = Object.freeze({
    appName: 'World Revolution News',
    version: '1.7.12',
    build: '2026.07.19-emergency-compatible',
    releasedAt: '2026-07-19T20:45:00+02:00',
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
 * Mobile Notbremse:
 * Die vollständige Oberfläche bleibt vorhanden. Auf kleinen Geräten werden nur
 * teure Darstellungs-Effekte abgeschaltet und große Feed-Antworten begrenzt.
 */
(() => {
    if (window.__wrnEmergencyCompatibility1712) return;
    window.__wrnEmergencyCompatibility1712 = true;

    const isMobile = () => window.matchMedia('(max-width: 820px)').matches;
    const fullFeedRequested = () =>
        new URLSearchParams(window.location.search).get('full') === '1';

    const nativeFetch = window.fetch.bind(window);
    window.fetch = async (...args) => {
        const response = await nativeFetch(...args);

        if (!isMobile() || fullFeedRequested() || !response.ok) {
            return response;
        }

        const requestUrl = String(
            typeof args[0] === 'string' ? args[0] : args[0]?.url || ''
        );
        const limit = /news-feed\.json/i.test(requestUrl)
            ? 120
            : (/events-feed\.json/i.test(requestUrl) ? 200 : 0);

        if (!limit) return response;

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
        } catch {
            return response;
        }
    };

    const style = document.createElement('style');
    style.id = 'wrn-emergency-compatible-style-1712';
    style.textContent = `
        @media (max-width: 820px) {
            html, body {
                background-color: #050508 !important;
                background-image: none !important;
                background-attachment: scroll !important;
                scroll-behavior: auto !important;
            }

            html, body, body * {
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
                pointer-events: none !important;
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

/* Offline-Speicher darf den Start nicht blockieren; vorhandene Daten bleiben erhalten. */
(() => {
    if (window.__wrnStorageStartGuard1712) return;
    window.__wrnStorageStartGuard1712 = true;

    const timeout = (promise, ms, fallback) => new Promise(resolve => {
        let done = false;
        const timer = window.setTimeout(() => {
            if (done) return;
            done = true;
            resolve(fallback);
        }, ms);

        Promise.resolve(promise).then(value => {
            if (done) return;
            done = true;
            window.clearTimeout(timer);
            resolve(value);
        }).catch(() => {
            if (done) return;
            done = true;
            window.clearTimeout(timer);
            resolve(fallback);
        });
    });

    document.addEventListener('DOMContentLoaded', () => {
        const storage = window.WRNStorage;
        if (!storage || storage.__startGuard1712) return;

        const original = {
            migrateLegacyLocalStorage:
                storage.migrateLegacyLocalStorage?.bind(storage),
            requestPersistentStorage:
                storage.requestPersistentStorage?.bind(storage),
            putDataset: storage.putDataset?.bind(storage),
            getDataset: storage.getDataset?.bind(storage)
        };

        storage.__startGuard1712 = true;

        storage.migrateLegacyLocalStorage = () =>
            original.migrateLegacyLocalStorage
                ? timeout(original.migrateLegacyLocalStorage(), 1200, false)
                : Promise.resolve(false);

        storage.requestPersistentStorage = () =>
            original.requestPersistentStorage
                ? timeout(original.requestPersistentStorage(), 800, false)
                : Promise.resolve(false);

        storage.getDataset = key =>
            original.getDataset
                ? timeout(original.getDataset(key), 1200, null)
                : Promise.resolve(null);

        storage.putDataset = (key, data) => {
            if (original.putDataset) {
                window.setTimeout(() => {
                    timeout(original.putDataset(key, data), 1800, false)
                        .catch(() => false);
                }, 0);
            }
            return Promise.resolve(false);
        };
    }, { once: true });
})();

/* Klicks zuverlässig freigeben, ohne Elemente oder Funktionen zu entfernen. */
(() => {
    if (window.__wrnInteractionRelease1712) return;
    window.__wrnInteractionRelease1712 = true;

    const releaseInteraction = () => {
        document.documentElement.classList.remove(
            'wrn-booting',
            'wrn-app-entering'
        );

        document.documentElement.style.pointerEvents = 'auto';
        if (document.body) document.body.style.pointerEvents = 'auto';

        const startScreen = document.getElementById('wrn-start-screen');
        if (startScreen) {
            startScreen.style.pointerEvents = 'none';
            startScreen.setAttribute('aria-hidden', 'true');
            startScreen.remove();
        }

        document.querySelectorAll(
            'button, a, select, input, textarea, summary, '
            + '.wrn-top-tabs, .wrn-top-tab, .wrn-subtabs, .wrn-subtab, '
            + '#feed-container, #archive-container, '
            + '#feed-container .card, #archive-container .card'
        ).forEach(element => {
            element.style.pointerEvents = 'auto';
        });

        document.querySelectorAll(
            '[hidden], [aria-hidden="true"].wrn-start-leaving'
        ).forEach(element => {
            element.style.pointerEvents = 'none';
        });
    };

    const scheduleRelease = () => {
        releaseInteraction();
        window.setTimeout(releaseInteraction, 700);
        window.setTimeout(releaseInteraction, 2200);
        window.setTimeout(releaseInteraction, 5000);
    };

    document.addEventListener(
        'pointerdown',
        releaseInteraction,
        { capture: true, passive: true }
    );
    document.addEventListener(
        'touchstart',
        releaseInteraction,
        { capture: true, passive: true }
    );
    window.addEventListener('pageshow', scheduleRelease);

    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            scheduleRelease,
            { once: true }
        );
    } else {
        scheduleRelease();
    }

    window.WRNReleaseInteraction = releaseInteraction;
})();

/*
 * Vollständige Zusatzoberfläche aus 1.7.11 wieder laden.
 * Auf Mobilgeräten werden Komfort- und Medienmodule zeitversetzt geladen.
 */
(() => {
    if (window.__wrnInterfaceLoader1712) return;
    window.__wrnInterfaceLoader1712 = true;

    const VERSION = '1712';

    const addStyle = (file, marker) => {
        if (document.querySelector(`link[data-wrn-style="${marker}"]`)) return;

        const stylesheet = document.createElement('link');
        stylesheet.rel = 'stylesheet';
        stylesheet.href = `./${file}?v=${VERSION}`;
        stylesheet.dataset.wrnStyle = marker;
        stylesheet.addEventListener('error', () => {
            console.warn(`WRN stylesheet could not be loaded: ${file}`);
        }, { once: true });
        document.head.appendChild(stylesheet);
    };

    const loadScript = (file, marker, timeoutMs = 10000) =>
        new Promise(resolve => {
            const existing = document.querySelector(
                `script[data-wrn-module="${marker}"]`
            );

            if (existing?.dataset.loaded === 'true') {
                resolve(true);
                return;
            }

            if (existing) {
                let done = false;
                const finish = success => {
                    if (done) return;
                    done = true;
                    resolve(success);
                };
                existing.addEventListener(
                    'load',
                    () => finish(true),
                    { once: true }
                );
                existing.addEventListener(
                    'error',
                    () => finish(false),
                    { once: true }
                );
                window.setTimeout(() => finish(false), timeoutMs);
                return;
            }

            const script = document.createElement('script');
            script.src = `./${file}?v=${VERSION}`;
            script.dataset.wrnModule = marker;

            let done = false;
            const finish = (success, reason = '') => {
                if (done) return;
                done = true;
                script.dataset.loaded = success ? 'true' : 'false';

                if (!success) {
                    console.warn(
                        `WRN module could not be loaded: ${file}`,
                        reason
                    );
                    window.WRNSafety?.record?.(
                        'module',
                        `Modul konnte nicht geladen werden: ${file}`,
                        file
                    );
                }
                resolve(success);
            };

            const timer = window.setTimeout(
                () => finish(false, 'timeout'),
                timeoutMs
            );

            script.addEventListener('load', () => {
                window.clearTimeout(timer);
                finish(true);
            }, { once: true });

            script.addEventListener('error', () => {
                window.clearTimeout(timer);
                finish(false, 'network error');
            }, { once: true });

            document.body.appendChild(script);
        });

    const loadList = async files => {
        for (const [file, marker] of files) {
            await loadScript(file, marker);
        }
    };

    const delayWork = callback => {
        if ('requestIdleCallback' in window) {
            window.requestIdleCallback(callback, { timeout: 2200 });
        } else {
            window.setTimeout(callback, 900);
        }
    };

    const loadInterface = async () => {
        [
            ['release-1.5-nav.css', 'navigation-1712'],
            ['briefing.css', 'briefing-1712'],
            ['audio-catalog.css', 'audio-catalog-1712'],
            ['article-summary.css', 'article-summary-1712'],
            ['interface-qol.css', 'interface-qol-1712'],
            ['shared-translation-status.css', 'shared-translation-status-1712'],
            ['typography.css', 'typography-1712'],
            ['app-diagnostics.css', 'app-diagnostics-1712']
        ].forEach(([file, marker]) => addStyle(file, marker));

        await loadList([
            ['app-safety.js', 'app-safety-1712'],
            ['wrn-i18n.js', 'i18n-1712'],
            ['typography.js', 'typography-1712'],
            ['release-1.5-nav.js', 'navigation-1712'],
            ['app-diagnostics.js', 'app-diagnostics-1712']
        ]);

        delayWork(() => {
            void loadList([
                ['language-qol.js', 'language-qol-1712'],
                ['language-status.js', 'language-status-1712'],
                ['voice-qol.js', 'voice-qol-1712'],
                ['shared-translation-client.js', 'shared-translation-client-1712'],
                ['briefing.js', 'briefing-1712']
            ]);
        });

        delayWork(() => {
            if (window.WRNSafety?.isActive?.()) return;
            void loadList([
                ['shared-translation-status.js', 'shared-translation-status-1712'],
                ['translation-dialog-l10n.js', 'translation-dialog-l10n-1712'],
                ['article-summary-core.js', 'article-summary-core-1712'],
                ['article-summary.js', 'article-summary-1712'],
                ['audio-player-fixes.js', 'audio-player-fixes-1712'],
                ['audio-catalog.js', 'audio-catalog-1712']
            ]);
        });

        window.dispatchEvent(new CustomEvent('wrn-app-ready'));
    };

    if (document.readyState === 'complete') {
        void loadInterface();
    } else {
        window.addEventListener(
            'load',
            () => void loadInterface(),
            { once: true }
        );
    }
})();

/* Sichtbarer Text-Rückfallfeed, nur wenn die normale Hauptlogik hängen bleibt. */
(() => {
    if (window.__wrnRescueFeed1712) return;
    window.__wrnRescueFeed1712 = true;

    const renderRescue = async () => {
        await new Promise(resolve => window.setTimeout(resolve, 7500));

        const status = document.getElementById('status-container');
        const feed = document.getElementById('feed-container');
        const stillLoading = /Lade Nachrichten|Loading news|Connecting/i.test(
            String(status?.textContent || '')
        );

        if (!feed || !stillLoading || feed.children.length > 0) return;

        const controller = new AbortController();
        const timer = window.setTimeout(() => controller.abort(), 7000);

        try {
            const response = await fetch(
                `./news-feed.json?rescue=${Date.now()}`,
                { cache: 'no-store', signal: controller.signal }
            );
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const items = await response.json();
            if (!Array.isArray(items) || items.length === 0) {
                throw new Error('Leerer Feed');
            }

            feed.textContent = '';

            items.slice(0, 30).forEach(item => {
                const card = document.createElement('article');
                card.className = 'card wrn-rescue-card';

                const meta = document.createElement('div');
                meta.className = 'meta';
                meta.textContent = [
                    item.quelleName || 'World Revolution News',
                    item.pubDate ? String(item.pubDate).slice(0, 10) : ''
                ].filter(Boolean).join(' · ');

                const title = document.createElement('div');
                title.className = 'title';
                title.textContent = String(item.title || 'Nachricht');

                const teaser = document.createElement('div');
                teaser.className = 'teaser';
                teaser.textContent = String(item.content || '').slice(0, 420);

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
            console.error('WRN Rettungsfeed fehlgeschlagen:', error);
        } finally {
            window.clearTimeout(timer);
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            () => void renderRescue(),
            { once: true }
        );
    } else {
        void renderRescue();
    }
})();
