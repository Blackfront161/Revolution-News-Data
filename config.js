/* World Revolution News – 1.7.19 Audio Tab, Multilingual Sources and Zine Designer
 *
 * Ziel dieser Stufe:
 * - Original-Podcasts, erzeugte Podcasts und Live-Radio direkt im Audio-Reiter anzeigen
 * - Podcast-Einleitungen auf einen erklärenden Satz begrenzen
 * - einen einzigen fortlaufenden Player mit Play/Pause bzw. Radio-Stop verwenden
 * - geprüfte Audioergebnisse gegenüber veralteten Podcast-Statusdateien priorisieren
 * - die freigegebenen mehrsprachigen Quellen ohne Löschung bestehender Quellen ergänzen
 * - Sprachabdeckung transparent prüfen
 * - dem Zine-Reiter anpassbare Flyer-Formate und Gestaltungsstile geben
 * - die Startanimation und alle bisherigen Stabilitätsreparaturen beibehalten
 */
'use strict';

/*
 * Frühe, unabhängige Startanimation.
 * Ein harter Watchdog entfernt sie immer, selbst wenn andere Module ausfallen.
 */
(() => {
    if (window.__wrnIntroBootstrap1718) return;
    window.__wrnIntroBootstrap1718 = true;

    const style = document.createElement('link');
    style.rel = 'stylesheet';
    style.href = './intro-screen.css?v=1718';
    style.dataset.wrnIntroAsset = 'style';
    document.head.appendChild(style);

    const script = document.createElement('script');
    script.src = './intro-screen.js?v=1718';
    script.dataset.wrnIntroAsset = 'script';
    script.defer = true;

    const target = document.head || document.documentElement;
    target.appendChild(script);
})();


window.WRN_EMERGENCY_MODE = false;

window.WRN_CONFIG = Object.freeze({
    appName: 'World Revolution News',
    version: '1.7.19',
    build: '2026.07.20-audio-tab-multilingual-zine',
    releasedAt: '2026-07-20T23:40:00+02:00',
    repository: 'Blackfront161/Revolution-News-Data',
    emergencyMode: false,
    recoveryStage: 8,
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
        radioSources: 'https://blackfront161.github.io/Revolution-News-Data/radio-sources.json',
        audioHealth: 'https://blackfront161.github.io/Revolution-News-Data/audio-health.json',
        featureAudit: 'https://blackfront161.github.io/Revolution-News-Data/feature-audit.json',
        languageSourceAudit: 'https://blackfront161.github.io/Revolution-News-Data/language-source-audit.json',
        generatedPodcasts: 'https://blackfront161.github.io/Revolution-News-Data/generated-podcasts.json'
    }),
    proxyUrl: 'https://revolution-proxy.paghklo.workers.dev',
    sharedTranslationUrl: 'https://wrn-translation-cache.paghklo.workers.dev'
});

/*
 * Nur Geräte mit begrenztem Bildschirm oder wenig Arbeitsspeicher erhalten
 * einen verkleinerten Feed. Auf Desktop wird news-feed.json vollständig genutzt.
 * Mit ?full=1 kann die Begrenzung auch auf Mobilgeräten testweise aufgehoben werden.
 */
(() => {
    if (window.__wrnRecoveryFeedGuard1719) return;
    window.__wrnRecoveryFeedGuard1719 = true;

    const wantsFullFeed = () =>
        new URLSearchParams(location.search).get('full') === '1';

    const isConstrainedDevice = () => {
        const narrow = window.matchMedia('(max-width: 820px)').matches;
        const memory = Number(navigator.deviceMemory || 0);
        return narrow || (memory > 0 && memory <= 4);
    };

    const nativeFetch = window.fetch.bind(window);

    window.fetch = async (...args) => {
        const response = await nativeFetch(...args);

        if (
            wantsFullFeed()
            || !isConstrainedDevice()
            || !response.ok
        ) {
            return response;
        }

        const url = String(
            typeof args[0] === 'string'
                ? args[0]
                : args[0]?.url || ''
        );

        const limit = /news-feed\.json/i.test(url)
            ? 180
            : (/events-feed\.json/i.test(url) ? 220 : 0);

        if (!limit) return response;

        try {
            const rows = await response.clone().json();

            if (!Array.isArray(rows) || rows.length <= limit) {
                return response;
            }

            const headers = new Headers(response.headers);
            headers.set(
                'content-type',
                'application/json; charset=utf-8'
            );
            headers.delete('content-length');

            return new Response(
                JSON.stringify(rows.slice(0, limit)),
                {
                    status: response.status,
                    statusText: response.statusText,
                    headers
                }
            );
        } catch {
            return response;
        }
    };
})();

/*
 * Reine CSS-Leistungsbremse für Smartphones.
 * Keine DOM-Gesamtsuche bei Klicks und keine Entfernung von App-Funktionen.
 */
(() => {
    if (document.getElementById('wrn-recovery-stage-8-style')) return;

    const style = document.createElement('style');
    style.id = 'wrn-recovery-stage-8-style';
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
            body *:not(.wrn-intro-screen-1718):not(.wrn-intro-screen-1718 *) {
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

/* Startbildschirm und alte Blockadeklassen nur einmal entfernen. */
(() => {
    if (window.__wrnRecoveryInteractionRelease1719) return;
    window.__wrnRecoveryInteractionRelease1719 = true;

    const release = () => {
        document.documentElement.classList.remove(
            'wrn-booting',
            'wrn-app-entering'
        );

        document.documentElement.style.pointerEvents = 'auto';

        if (document.body) {
            document.body.style.pointerEvents = 'auto';
        }

        document.getElementById('wrn-start-screen')?.remove();
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
    window.setTimeout(release, 700);
    window.setTimeout(release, 2400);

    window.WRNReleaseInteraction = release;
})();

/*
 * Nur auf leistungsschwächeren Geräten dürfen Offline-Zugriffe den Start nicht
 * blockieren. Der bestehende Inhalt wird nicht gelöscht.
 */
(() => {
    if (window.__wrnRecoveryStorageGuard1719) return;
    window.__wrnRecoveryStorageGuard1719 = true;

    const shouldGuardStorage = () => {
        const narrow = window.matchMedia('(max-width: 820px)').matches;
        const memory = Number(navigator.deviceMemory || 0);
        return narrow || (memory > 0 && memory <= 4);
    };

    if (!shouldGuardStorage()) return;

    const timeout = (promise, milliseconds, fallback) =>
        new Promise(resolve => {
            let finished = false;

            const timer = window.setTimeout(() => {
                if (finished) return;
                finished = true;
                resolve(fallback);
            }, milliseconds);

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

        if (!storage || storage.__recoveryStage8Guard) return;

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

        storage.__recoveryStage8Guard = true;

        storage.migrateLegacyLocalStorage = () =>
            original.migrateLegacyLocalStorage
                ? timeout(
                    original.migrateLegacyLocalStorage(),
                    1100,
                    false
                )
                : Promise.resolve(false);

        storage.requestPersistentStorage = () =>
            original.requestPersistentStorage
                ? timeout(
                    original.requestPersistentStorage(),
                    800,
                    false
                )
                : Promise.resolve(false);

        storage.getDataset = key =>
            original.getDataset
                ? timeout(
                    original.getDataset(key),
                    1200,
                    null
                )
                : Promise.resolve(null);

        storage.putDataset = (key, data) => {
            if (original.putDataset) {
                window.setTimeout(() => {
                    void timeout(
                        original.putDataset(key, data),
                        1800,
                        false
                    );
                }, 0);
            }

            return Promise.resolve(false);
        };
    }, { once: true });
})();

/*
 * Wiederherstellungsstufe 8:
 * - Sicherheitsmodul
 * - Sprache und Typografie
 * - horizontale Hauptnavigation
 * - kompakter futuristischer Header
 * - gemeinsamer Übersetzungs-Cache
 * - bereinigtes Quellenprüfungszentrum mit Feed-Erkennung
 * - echtes Briefing als Lazy-Load
 * - fairer Hinweis vor externen Originalquellen
 * - responsive Dreierspalten für Artikelaktionen
 * - feststehende Dialog-Kopfzeilen
 * - vorhandenes Systemstatuszentrum
 *
 * Geschichten, Zeitleisten, Video-Hub, Aktionsradar,
 * Push-Mitteilungen und schwere Diagnose werden noch nicht automatisch geladen.
 */
(() => {
    if (window.__wrnRecoveryCoreLoader1719) return;
    window.__wrnRecoveryCoreLoader1719 = true;

    const VERSION = '1719-audio-tab-multilingual-zine';

    const addStyle = (file, marker) => {
        if (
            document.querySelector(
                `link[data-wrn-style="${marker}"]`
            )
        ) {
            return;
        }

        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `./${file}?v=${VERSION}`;
        link.dataset.wrnStyle = marker;
        link.addEventListener('error', () => {
            console.warn(`WRN stylesheet missing: ${file}`);
        }, { once: true });

        document.head.appendChild(link);
    };

    const loadScript = (
        file,
        marker,
        timeoutMilliseconds = 9000
    ) => new Promise(resolve => {
        const existing = document.querySelector(
            `script[data-wrn-module="${marker}"]`
        );

        if (existing?.dataset.loaded === 'true') {
            resolve(true);
            return;
        }

        const script = existing || document.createElement('script');

        if (!existing) {
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
            timeoutMilliseconds
        );

        script.addEventListener('load', () => {
            window.clearTimeout(timer);
            finish(true);
        }, { once: true });

        script.addEventListener('error', () => {
            window.clearTimeout(timer);
            finish(false);
        }, { once: true });

        if (!existing) {
            document.body.appendChild(script);
        }
    });

    const loadSequentially = async files => {
        for (const [file, marker] of files) {
            await loadScript(file, marker);
        }
    };

    const openStartTab = () => {
        if (typeof window.WRNActivateTab === 'function') {
            window.WRNActivateTab('start');
            return;
        }

        const button = document.querySelector(
            '.wrn-top-tab[data-key="start"]'
        );

        if (button instanceof HTMLElement) {
            button.click();
            return;
        }

        if (typeof window.ladeKontinentNews === 'function') {
            window.ladeKontinentNews('Global');
        }
    };

    const loadCore = async () => {
        [
            ['release-1.5-nav.css', 'navigation-recovery-8'],
            ['typography.css', 'typography-recovery-8'],
            ['interface-qol.css', 'interface-recovery-8'],
            ['shared-translation-status.css', 'translation-status-recovery-8'],
            ['wrn-header.css', 'future-header-recovery-8'],
            ['source-verification.css', 'source-verification-recovery-8'],
            ['briefing-loader.css', 'briefing-loader-recovery-8'],
            ['article-actions.css', 'article-actions-recovery-8'],
            ['sticky-dialogs.css', 'sticky-dialogs-recovery-8'],
            ['audio-tab.css', 'audio-tab-recovery-8'],
            ['audio-reliability.css', 'audio-reliability-recovery-8'],
            ['runtime-selftest.css', 'runtime-selftest-recovery-8'],
            ['recovery-audit.css', 'recovery-audit-recovery-8'],
            ['language-source-status.css', 'language-source-status-recovery-8'],
            ['zine-designer.css', 'zine-designer-recovery-8']
        ].forEach(([file, marker]) => addStyle(file, marker));

        await loadSequentially([
            ['app-safety.js', 'safety-recovery-8'],
            ['wrn-i18n.js', 'i18n-recovery-8'],
            ['typography.js', 'typography-recovery-8'],
            ['wrn-header.js', 'future-header-recovery-8'],
            ['release-1.5-nav.js', 'navigation-recovery-8'],
            ['source-verification.js', 'source-verification-recovery-8'],
            ['briefing-loader.js', 'briefing-loader-recovery-8'],
            ['article-actions.js', 'article-actions-recovery-8'],
            ['sticky-dialogs.js', 'sticky-dialogs-recovery-8'],
            ['audio-tab.js', 'audio-tab-recovery-8'],
            ['audio-reliability.js', 'audio-reliability-recovery-8'],
            ['runtime-selftest.js', 'runtime-selftest-recovery-8'],
            ['recovery-audit.js', 'recovery-audit-recovery-8'],
            ['language-source-status.js', 'language-source-status-recovery-8'],
            ['zine-designer.js', 'zine-designer-recovery-8'],
            ['shared-translation-client.js', 'translation-client-recovery-8'],
            ['translation-dialog-l10n.js', 'translation-dialog-recovery-8']
        ]);

        /*
         * Der vorherige Stand öffnete standardmäßig "Briefing", obwohl das
         * Briefing im Notfallmodus noch nicht geladen wird. Das führte zu einer
         * scheinbar leeren oder sehr dünnen Startansicht.
         */
        openStartTab();
        window.setTimeout(openStartTab, 700);

        /*
         * Nur ein leichter Gesundheitscheck wird verzögert gestartet.
         * Keine Diagnosebeobachter und keine Audio-/Briefing-Module.
         */
        window.setTimeout(() => {
            void loadScript(
                'shared-translation-status.js',
                'translation-status-recovery-8',
                9000
            );
        }, 1400);

        window.dispatchEvent(
            new CustomEvent('wrn-app-ready')
        );
    };

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
 * Rettungsfeed nur, falls die normale Haupt-App nach mehreren Sekunden weiterhin
 * keine Karte erzeugt hat.
 */
(() => {
    if (window.__wrnRecoveryRescueFeed1719) return;
    window.__wrnRecoveryRescueFeed1719 = true;

    const run = async () => {
        await new Promise(resolve => {
            window.setTimeout(resolve, 9000);
        });

        const status = document.getElementById('status-container');
        const feed = document.getElementById('feed-container');

        const stillLoading =
            /Lade Nachrichten|Loading news|Connecting/i.test(
                String(status?.textContent || '')
            );

        if (
            !feed
            || !stillLoading
            || feed.children.length > 0
        ) {
            return;
        }

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
