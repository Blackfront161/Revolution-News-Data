/* World Revolution News – zentrale App-Konfiguration */
'use strict';


/* 1.7.7 – nicht blockierende Startanimation */
(() => {
    if (window.__wrnStartScreen177) return;
    window.__wrnStartScreen177 = true;

    const style = document.createElement('style');
    style.id = 'wrn-start-screen-style-177';
    style.textContent = `
        #wrn-start-screen {
            position: fixed;
            inset: 0;
            z-index: 2147483000;
            display: grid;
            place-items: center;
            pointer-events: none;
            background:
                linear-gradient(
                    180deg,
                    rgba(2,3,7,0.16),
                    rgba(2,3,7,0.38) 60%,
                    rgba(2,3,7,0.72)
                ),
                url('./app-background.webp?v=177') center top / cover no-repeat,
                #050508;
            opacity: 1;
            animation: wrnStartExit177 1350ms ease forwards;
        }

        #wrn-start-screen img {
            width: clamp(98px, 29vw, 150px);
            height: clamp(98px, 29vw, 150px);
            object-fit: cover;
            border-radius: 25px;
            filter: drop-shadow(0 13px 30px rgba(0,0,0,.58));
            animation: wrnStartLogo177 700ms cubic-bezier(.2,.82,.3,1.15) forwards;
        }

        @keyframes wrnStartLogo177 {
            from { opacity: 0; transform: scale(.75) rotate(-4deg); }
            to { opacity: 1; transform: scale(1) rotate(0); }
        }

        @keyframes wrnStartExit177 {
            0%, 62% { opacity: 1; visibility: visible; }
            100% { opacity: 0; visibility: hidden; }
        }

        @media (prefers-reduced-motion: reduce) {
            #wrn-start-screen {
                animation-duration: 500ms;
            }

            #wrn-start-screen img {
                animation: none;
            }
        }
    `;
    document.head.appendChild(style);

    const mount = () => {
        if (!document.body || document.getElementById('wrn-start-screen')) return;

        const screen = document.createElement('div');
        screen.id = 'wrn-start-screen';
        screen.setAttribute('aria-hidden', 'true');
        screen.innerHTML = `
            <img src="./wrn-logo.webp?v=177" alt="">
        `;
        document.body.appendChild(screen);

        window.setTimeout(() => screen.remove(), 1700);
    };

    if (document.body) mount();
    else document.addEventListener('DOMContentLoaded', mount, { once: true });
})();

window.WRN_CONFIG = Object.freeze({
    appName: 'World Revolution News',
    version: '1.7.7',
    build: '2026.07.19-news-workflow-and-safe-start',
    releasedAt: '2026-07-19T22:00:00Z',
    repository: 'Blackfront161/Revolution-News-Data',
    dataUrls: Object.freeze({
        news: 'https://blackfront161.github.io/Revolution-News-Data/news.json',
        events: 'https://blackfront161.github.io/Revolution-News-Data/events.json',
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
    /* Optional: URL des gemeinsamen Cache-Workers. Leer = bisheriger Ablauf. */
    sharedTranslationUrl: 'https://wrn-translation-cache.paghklo.workers.dev'
});

/* Sichtbarer Fahnenhintergrund */
(() => {
    const style = document.createElement('style');
    style.id = 'wrn-background-stronger';
    style.textContent = `
        body::before { display: none !important; }
        html { background: #050508 !important; }
        body {
            background-color: #050508 !important;
            background-image:
                linear-gradient(
                    180deg,
                    rgba(3, 5, 9, 0.08) 0%,
                    rgba(3, 5, 9, 0.16) 46%,
                    rgba(3, 5, 9, 0.30) 100%
                ),
                url('./app-background.webp?v=175') !important;
            background-position: 52% top !important;
            background-size: cover !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }
        .card {
            background-color: rgba(10, 10, 17, 0.72) !important;
            -webkit-backdrop-filter: blur(3px) !important;
            backdrop-filter: blur(3px) !important;
            box-shadow:
                0 8px 24px rgba(0, 0, 0, 0.35),
                0 0 10px var(--shadow-accent) !important;
        }
        .feedback-modal,
        .podcast-options-modal,
        .podcast-library-modal,
        .system-status-modal,
        .global-media-bar {
            background-color: rgba(13, 13, 20, 0.94) !important;
        }
        h1, .title, .teaser, .full-content, .meta {
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.9);
        }
        body.theme-light,
        body.theme-soft {
            background-image:
                linear-gradient(
                    180deg,
                    rgba(244, 244, 249, 0.44) 0%,
                    rgba(244, 244, 249, 0.54) 48%,
                    rgba(244, 244, 249, 0.66) 100%
                ),
                url('./app-background.webp?v=175') !important;
        }
        body.theme-light .card,
        body.theme-soft .card {
            background-color: rgba(255, 255, 255, 0.82) !important;
        }
        @media (max-width: 720px) {
            body { background-position: 50% top !important; }
            .card { background-color: rgba(10, 10, 17, 0.76) !important; }
        }
    `;
    document.head.appendChild(style);
})();

/* Briefing, Sprachsystem und Navigation fehlertolerant laden. */
(() => {
    if (window.__wrnInterfaceLoader177) return;
    window.__wrnInterfaceLoader177 = true;

    const VERSION = '177';

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

    const loadScript = (file, marker, timeoutMs = 8000) => new Promise(resolve => {
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

            existing.addEventListener('load', () => finish(true), { once: true });
            existing.addEventListener('error', () => finish(false), { once: true });
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
                console.warn(`WRN module could not be loaded: ${file}`, reason);
                window.WRNSafety?.record?.(
                    'module',
                    `Modul konnte nicht geladen werden: ${file}`,
                    file
                );
            }

            resolve(success);
        };

        const timeout = window.setTimeout(
            () => finish(false, 'timeout'),
            timeoutMs
        );

        script.addEventListener('load', () => {
            window.clearTimeout(timeout);
            finish(true);
        }, { once: true });

        script.addEventListener('error', () => {
            window.clearTimeout(timeout);
            finish(false, 'network error');
        }, { once: true });

        document.body.appendChild(script);
    });

    const loadList = async files => {
        for (const [file, marker] of files) {
            await loadScript(file, marker);
        }
    };

    const loadInterface = async () => {
        [
            ['release-1.5-nav.css', 'navigation-177'],
            ['briefing.css', 'briefing-177'],
            ['audio-catalog.css', 'audio-catalog-177'],
            ['article-summary.css', 'article-summary-177'],
            ['interface-qol.css', 'interface-qol-177'],
            ['shared-translation-status.css', 'shared-translation-status-177'],
            ['typography.css', 'typography-177'],
            ['app-diagnostics.css', 'app-diagnostics-177']
        ].forEach(([file, marker]) => addStyle(file, marker));

        /*
         * Kritische Oberfläche zuerst.
         * Fehlende Zusatzmodule dürfen Navigation und Artikel nicht blockieren.
         */
        await loadList([
            ['app-safety.js', 'app-safety-177'],
            ['wrn-i18n.js', 'i18n-177'],
            ['typography.js', 'typography-177'],
            ['language-qol.js', 'language-qol-177'],
            ['language-status.js', 'language-status-177'],
            ['voice-qol.js', 'voice-qol-177'],
            ['shared-translation-client.js', 'shared-translation-client-177'],
            ['briefing.js', 'briefing-177'],
            ['release-1.5-nav.js', 'navigation-177'],
            ['app-diagnostics.js', 'app-diagnostics-177']
        ]);

        if (!window.WRNSafety?.isActive?.()) {
            await loadList([
                ['shared-translation-status.js', 'shared-translation-status-177'],
                ['translation-dialog-l10n.js', 'translation-dialog-l10n-177'],
                ['article-summary-core.js', 'article-summary-core-177'],
                ['article-summary.js', 'article-summary-177'],
                ['audio-player-fixes.js', 'audio-player-fixes-177'],
                ['audio-catalog.js', 'audio-catalog-177']
            ]);
        }

        window.dispatchEvent(new CustomEvent('wrn-app-ready'));
    };

    if (document.readyState === 'complete') {
        loadInterface();
    } else {
        window.addEventListener('load', loadInterface, { once: true });
    }
})();
