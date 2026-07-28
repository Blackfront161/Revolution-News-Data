/* Public, secret-free configuration for the isolated News App 2 preview. */
'use strict';

window.WRN_CONFIG = Object.freeze({
  version: '2.0.0-rc.1',
  build: '2026.07.28-news-app-2-rc1',
  dataUrls: Object.freeze({
    newsFeed: 'news-feed.json',
    news: 'news.json',
    events: 'events-feed.json',
    podcasts: 'podcasts.json',
    generatedPodcasts: 'generated-podcasts.json',
    radio: 'radio-stations.json',
    radioHealth: 'radio-health.json',
    sourceHealth: 'source-health.json',
    sourceCatalog: 'sources-registry.json',
    editorialReview: 'editorial-review.json',
    audioHealth: 'audio-health.json',
    podcastHealth: 'podcast-health.json'
  }),
  sharedTranslationUrl: 'https://wrn-translation-cache.paghklo.workers.dev',
  proxyUrl: 'https://revolution-proxy.paghklo.workers.dev'
});
