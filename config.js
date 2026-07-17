/* World Revolution News – zentrale, unveränderliche App-Konfiguration */
'use strict';

window.WRN_CONFIG = Object.freeze({
    appName: 'World Revolution News',
    version: '1.4.5',
    build: '2026.07.17-background-visibility-fix',
    releasedAt: '2026-07-17T07:30:00Z',
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

/* 1.4.5 – robuster Hintergrund ohne negativen z-index. */
(() => {
    const style = document.createElement('style');
    style.id = 'wrn-background-visibility-fix';
    style.textContent = `
        body::before {
            display: none !important;
        }

        body {
            background-color: #050508 !important;
            background-image:
                linear-gradient(
                    180deg,
                    rgba(3, 5, 9, 0.20) 0%,
                    rgba(3, 5, 9, 0.36) 45%,
                    rgba(3, 5, 9, 0.52) 100%
                ),
                url('./app-background.webp?v=145') !important;
            background-position: 52% top !important;
            background-size: cover !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
        }

        body.theme-light,
        body.theme-soft {
            background-image:
                linear-gradient(
                    180deg,
                    rgba(244, 244, 249, 0.62) 0%,
                    rgba(244, 244, 249, 0.72) 48%,
                    rgba(244, 244, 249, 0.82) 100%
                ),
                url('./app-background.webp?v=145') !important;
        }
    `;
    document.head.appendChild(style);
})();
