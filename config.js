/* World Revolution News – zentrale App-Konfiguration */
'use strict';

window.WRN_CONFIG = Object.freeze({
    appName: 'World Revolution News',
    version: '1.5.9',
    build: '2026.07.17-extra-compact-sticky-actions',
    releasedAt: '2026-07-17T13:35:00Z',
    repository: 'Blackfront161/Revolution-News-Data',
    dataUrls: Object.freeze({
        news: 'https://blackfront161.github.io/Revolution-News-Data/news.json',
        events: 'https://blackfront161.github.io/Revolution-News-Data/events.json',
        podcasts: 'https://blackfront161.github.io/Revolution-News-Data/podcasts.json',
        radio: 'https://blackfront161.github.io/Revolution-News-Data/radio-stations.json',
        sourceHealth: 'https://blackfront161.github.io/Revolution-News-Data/source-health.json',
        sourceCatalog: 'https://blackfront161.github.io/Revolution-News-Data/source-catalog.json',
        podcastHealth: 'https://blackfront161.github.io/Revolution-News-Data/podcast-health.json'
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
                url('./app-background.webp?v=159') !important;
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
                url('./app-background.webp?v=159') !important;
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

/* Navigation automatisch laden – index.html muss nicht geändert werden. */
(() => {
    if (window.__wrnNavigationLoader159) return;
    window.__wrnNavigationLoader159 = true;

    const stylesheet = document.createElement('link');
    stylesheet.rel = 'stylesheet';
    stylesheet.href = './release-1.5-nav.css?v=159';
    document.head.appendChild(stylesheet);

    const loadNavigation = () => {
        if (document.querySelector('script[data-wrn-nav="159"]')) return;
        const script = document.createElement('script');
        script.src = './release-1.5-nav.js?v=159';
        script.dataset.wrnNav = '159';
        document.body.appendChild(script);
    };

    if (document.readyState === 'complete') loadNavigation();
    else window.addEventListener('load', loadNavigation, { once: true });
})();
