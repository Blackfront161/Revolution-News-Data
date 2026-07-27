/* Public, secret-free configuration for the isolated News App 2 preview. */
'use strict';

window.WRN_CONFIG = Object.freeze({
  dataUrls: Object.freeze({
    newsFeed: 'news-feed.json',
    news: 'news.json'
  }),
  sharedTranslationUrl: 'https://wrn-translation-cache.paghklo.workers.dev',
  proxyUrl: 'https://revolution-proxy.paghklo.workers.dev'
});
