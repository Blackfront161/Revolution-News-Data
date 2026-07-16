/* World Revolution News – zentrale, unveränderliche App-Konfiguration */
'use strict';

window.WRN_CONFIG = Object.freeze({
    appName: 'World Revolution News',
    version: '2026.07.16-phase1f',
    releasedAt: '2026-07-16T18:00:00Z',
    repository: 'Blackfront161/Revolution-News-Data',
    dataUrls: Object.freeze({
        news: 'https://blackfront161.github.io/Revolution-News-Data/news.json',
        events: 'https://blackfront161.github.io/Revolution-News-Data/events.json',
        podcasts: 'https://blackfront161.github.io/Revolution-News-Data/podcasts.json',
        radio: 'https://blackfront161.github.io/Revolution-News-Data/radio-stations.json',
        sourceHealth: 'https://blackfront161.github.io/Revolution-News-Data/source-health.json',
        podcastHealth: 'https://blackfront161.github.io/Revolution-News-Data/podcast-health.json'
    }),
    proxyUrl: 'https://revolution-proxy.paghklo.workers.dev'
});
