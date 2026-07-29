/* Public, secret-free configuration for the isolated News App 2 preview. */
'use strict';

const WRN_PREVIEW_PARAMETERS = new URLSearchParams(window.location.search);
const WRN_RELEASE_CHANNEL = window.location.pathname.endsWith('/next.html')
  ? 'preview'
  : 'production';
const WRN_PREVIEW_LIVE_DATA = WRN_RELEASE_CHANNEL === 'preview'
  && WRN_PREVIEW_PARAMETERS.get('data') === 'live';
const WRN_PREVIEW_DATA_BASE = WRN_PREVIEW_LIVE_DATA
  ? 'https://blackfront161.github.io/Revolution-News-Data/'
  : '';
const wrnPreviewDataUrl = filename => `${WRN_PREVIEW_DATA_BASE}${filename}`;

window.WRN_CONFIG = Object.freeze({
  version: WRN_RELEASE_CHANNEL === 'production' ? '2.0.0' : '2.0.0-rc.1',
  build: WRN_RELEASE_CHANNEL === 'production'
    ? '2026.07.29-news-app-2'
    : '2026.07.29-news-app-2-rc1',
  releaseChannel: WRN_RELEASE_CHANNEL,
  dataMode: WRN_RELEASE_CHANNEL === 'production'
    ? 'same-origin-production'
    : WRN_PREVIEW_LIVE_DATA
      ? 'live-readonly'
      : 'branch-snapshot',
  dataUrls: Object.freeze({
    newsFeed: wrnPreviewDataUrl('news-feed.json'),
    news: wrnPreviewDataUrl('news.json'),
    events: wrnPreviewDataUrl('events-feed.json'),
    podcasts: wrnPreviewDataUrl('podcasts.json'),
    generatedPodcasts: wrnPreviewDataUrl('generated-podcasts.json'),
    radio: wrnPreviewDataUrl('radio-stations.json'),
    radioHealth: wrnPreviewDataUrl('radio-health.json'),
    sourceHealth: wrnPreviewDataUrl('source-health.json'),
    sourceCatalog: wrnPreviewDataUrl('sources-registry.json'),
    editorialReview: wrnPreviewDataUrl('editorial-review.json'),
    audioHealth: wrnPreviewDataUrl('audio-health.json'),
    podcastHealth: wrnPreviewDataUrl('podcast-health.json')
  }),
  sharedTranslationUrl: 'https://wrn-translation-cache.paghklo.workers.dev',
  proxyUrl: 'https://revolution-proxy.paghklo.workers.dev'
});
