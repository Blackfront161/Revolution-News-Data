/* World Revolution News – zentrale App-Konfiguration */
'use strict';


/* 1.7.1 – Startbild zuerst, App erst nach geladenen Inhalten einblenden */
(() => {
    if (window.__wrnStartScreen171) return;
    window.__wrnStartScreen171 = true;

    const html = document.documentElement;
    html.classList.add('wrn-booting');

    const earlyStyle = document.createElement('style');
    earlyStyle.id = 'wrn-start-screen-style-171';
    earlyStyle.textContent = `
        #mobile-more-menu,
        .mobile-more-menu,
        #language-beta-note {
            display: none !important;
            visibility: hidden !important;
        }

        html.wrn-booting {
            overflow: hidden !important;
            background: #050508 !important;
        }

        html.wrn-booting body > *:not(#wrn-start-screen):not(script):not(style) {
            visibility: hidden !important;
            opacity: 0 !important;
        }

        #wrn-start-screen {
            position: fixed;
            inset: 0;
            z-index: 2147483000;
            display: grid;
            place-items: center;
            overflow: hidden;
            background:
                linear-gradient(
                    180deg,
                    rgba(2,3,7,0.18),
                    rgba(2,3,7,0.42) 62%,
                    rgba(2,3,7,0.72)
                ),
                url('./app-background.webp?v=171') center top / cover no-repeat,
                #050508;
            opacity: 1;
            transition: opacity 520ms ease, visibility 520ms ease;
        }

        #wrn-start-screen.wrn-start-leaving {
            opacity: 0;
            visibility: hidden;
            pointer-events: none;
        }

        .wrn-start-content {
            width: min(82vw, 390px);
            display: grid;
            justify-items: center;
            gap: 13px;
            padding: 24px;
            text-align: center;
        }

        .wrn-start-logo {
            width: clamp(100px, 30vw, 154px);
            height: clamp(100px, 30vw, 154px);
            object-fit: cover;
            border-radius: 26px;
            opacity: 0;
            transform: scale(.74) rotate(-4deg);
            filter: drop-shadow(0 13px 30px rgba(0,0,0,.58));
            animation: wrnEarlyLogo171 680ms cubic-bezier(.2,.82,.3,1.15) 240ms forwards;
        }

        .wrn-start-title {
            margin: 0;
            color: #00f0ff;
            font: 850 clamp(1.05rem, 5.4vw, 1.65rem)/1.06 system-ui, sans-serif;
            letter-spacing: .015em;
            text-shadow: 0 2px 10px rgba(0,0,0,.96);
            opacity: 0;
            transform: translateY(10px);
            animation: wrnEarlyText171 480ms ease-out 610ms forwards;
        }

        .wrn-start-loader {
            width: min(210px, 58vw);
            height: 3px;
            margin-top: 4px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(255,255,255,.12);
            opacity: 0;
            animation: wrnEarlyText171 380ms ease-out 760ms forwards;
        }

        .wrn-start-loader::after {
            content: '';
            display: block;
            width: 42%;
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #ff334f, #00f0ff);
            animation: wrnEarlyLoad171 1050ms ease-in-out infinite alternate;
        }

        @keyframes wrnEarlyLogo171 {
            from { opacity: 0; transform: scale(.74) rotate(-4deg); }
            to { opacity: 1; transform: scale(1) rotate(0); }
        }

        @keyframes wrnEarlyText171 {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes wrnEarlyLoad171 {
            from { transform: translateX(-110%); }
            to { transform: translateX(245%); }
        }
    `;
    document.head.appendChild(earlyStyle);

    let mountedAt = performance.now();
    let finished = false;

    const mount = () => {
        if (!document.body || document.getElementById('wrn-start-screen')) return;

        const screen = document.createElement('section');
        screen.id = 'wrn-start-screen';
        screen.setAttribute('aria-label', 'World Revolution News wird geladen');
        screen.innerHTML = `
            <div class="wrn-start-content">
                <img
                    class="wrn-start-logo"
                    src="./wrn-logo.webp?v=171"
                    alt="World Revolution News">
                <h1 class="wrn-start-title">World Revolution News</h1>
                <div class="wrn-start-loader" aria-hidden="true"></div>
            </div>
        `;
        document.body.appendChild(screen);
        mountedAt = performance.now();
    };

    const finish = () => {
        if (finished) return;
        finished = true;

        const elapsed = performance.now() - mountedAt;
        const wait = Math.max(0, 1250 - elapsed);

        window.setTimeout(() => {
            const screen = document.getElementById('wrn-start-screen');
            html.classList.remove('wrn-booting');
            html.classList.add('wrn-app-entering');

            if (screen) screen.classList.add('wrn-start-leaving');

            window.setTimeout(() => {
                screen?.remove();
                html.classList.remove('wrn-app-entering');
            }, 560);
        }, wait);
    };

    if (document.body) mount();
    else document.addEventListener('DOMContentLoaded', mount, { once: true });

    window.addEventListener('wrn-app-ready', finish, { once: true });

    /* Sicherheitsfallback bei blockierter Verbindung oder altem Browser. */
    window.setTimeout(finish, 12000);
})();

window.WRN_CONFIG = Object.freeze({
    appName: 'World Revolution News',
    version: '1.7.1',
    build: '2026.07.18-audio-catalog-health-and-submenus',
    releasedAt: '2026-07-18T17:15:00Z',
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
    proxyUrl: 'https://revolution-proxy.paghklo.workers.dev'
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
                url('./app-background.webp?v=171') !important;
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
                url('./app-background.webp?v=171') !important;
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

/* Briefing, Sprachsystem und Navigation automatisch laden. */
(() => {
    if (window.__wrnInterfaceLoader171) return;
    window.__wrnInterfaceLoader171 = true;

    const addStyle = (href, marker) => {
        if (document.querySelector(`link[data-wrn-style="${marker}"]`)) return;
        const stylesheet = document.createElement('link');
        stylesheet.rel = 'stylesheet';
        stylesheet.href = href;
        stylesheet.dataset.wrnStyle = marker;
        document.head.appendChild(stylesheet);
    };

    const loadScript = (src, marker) => new Promise((resolve, reject) => {
        const existing = document.querySelector(`script[data-wrn-module="${marker}"]`);
        if (existing) {
            if (existing.dataset.loaded === 'true') resolve();
            else existing.addEventListener('load', resolve, { once: true });
            return;
        }

        const script = document.createElement('script');
        script.src = src;
        script.dataset.wrnModule = marker;
        script.addEventListener('load', () => {
            script.dataset.loaded = 'true';
            resolve();
        }, { once: true });
        script.addEventListener('error', reject, { once: true });
        document.body.appendChild(script);
    });

    const loadInterface = async () => {
        addStyle('./release-1.5-nav.css?v=171', 'navigation-171');
        addStyle('./briefing.css?v=171', 'briefing-171');
        addStyle('./audio-catalog.css?v=171', 'audio-catalog-171');

        try {
            await loadScript('./wrn-i18n.js?v=171', 'i18n-171');
            await loadScript('./briefing.js?v=171', 'briefing-171');
            await loadScript('./audio-player-fixes.js?v=171', 'audio-player-fixes-171');
            await loadScript('./audio-catalog.js?v=171', 'audio-catalog-171');
            await loadScript('./release-1.5-nav.js?v=171', 'navigation-171');
        } catch (error) {
            console.error('WRN interface modules could not be loaded:', error);
            window.dispatchEvent(new CustomEvent('wrn-app-ready'));
        }
    };

    if (document.readyState === 'complete') loadInterface();
    else window.addEventListener('load', loadInterface, { once: true });
})();
