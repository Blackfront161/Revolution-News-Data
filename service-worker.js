/* World Revolution News – Offline Service Worker · asset refresh 2026-07-23 */
'use strict';

const APP_CACHE = 'wrn-app-v1.8.4-release-2';
const DATA_CACHE = 'wrn-data-v1.8.4-release-2';
const WRN_CACHE_PREFIX = 'wrn-';

const APP_SHELL = [
  './',
  './index.html',
  './mobile-repair.html',
  './source-check.html',
  './audio-check.html',
  './app-check.html',
  './styles.css',
  './release-1.4.css',
  './release-1.5-nav.css',
  './briefing.css',
  './briefing-2.css',
  './stories-timeline.css',
  './video-hub.css',
  './lexicon-tab.css',
  './about-tab.css',
  './audio-catalog.css',
  './article-summary.css',
  './interface-qol.css',
  './shared-translation-status.css',
  './typography.css',
  './app-background.css',
  './wrn-header.css',
  './source-verification.css',
  './briefing-loader.css',
  './article-actions.css',
  './sticky-dialogs.css',
  './audio-tab.css',
  './audio-tab-183.css',
  './interface-block3.css',
  './source-recovery-ui-183.css',
  './audio-reliability.css',
  './runtime-selftest.css',
  './intro-screen.css',
  './recovery-audit.css',
  './language-source-status.css',
  './zine-designer.css',
  './light-theme.css',
  './app-diagnostics.css',
  './app-background.webp',
  './wrn-logo.webp',
  './wrn-future-header.webp',
  './wrn-future-header.png',
  './wrn-future-header-white.png',
  './wrn-header-banner.webp',
  './config.js',
  './wrn-origin-safety.js',
  './offline-db.js',
  './data-control.js',
  './status-center.js',
  './utils.js',
  './source-profiles.js',
  './source-filters.js',
  './translation-tools.js',
  './accessibility.js',
  './media-player.js',
  './audio-tools.js',
  './events.js',
  './reading-state.js',
  './audio-hub.js',
  './release-1.4.js',
  './release-1.5-nav.js',
  './wrn-i18n.js',
  './audio-region-core.js',
  './language-qol.js',
  './language-status.js',
  './shared-translation-client.js',
  './shared-translation-status.js',
  './translation-dialog-l10n.js',
  './typography.js',
  './wrn-header.js',
  './source-verification.js',
  './briefing-loader.js',
  './stories-core.js',
  './briefing-2.js',
  './stories-timeline.js',
  './video-hub.js',
  './lexicon-tab.js',
  './about-tab.js',
  './article-actions.js',
  './sticky-dialogs.js',
  './audio-tab.js',
  './audio-tab-183.js',
  './interface-block3.js',
  './source-recovery-ui-183.js',
  './audio-reliability.js',
  './runtime-selftest.js',
  './intro-screen.js',
  './recovery-audit.js',
  './language-source-status.js',
  './zine-designer.js',
  './app-safety.js',
  './app-diagnostics.js',
  './article-summary-core.js',
  './article-summary.js',
  './briefing.js',
  './audio-player-fixes.js',
  './audio-catalog.js',
  './app.js',
  './manifest.json',
  './icon.svg'
];

const JSON_FALLBACKS = new Map([
  [new URL('./news.json', self.location.href).pathname, '[]'],
  [new URL('./news-feed.json', self.location.href).pathname, '[]'],
  [new URL('./events.json', self.location.href).pathname, '[]'],
  [new URL('./events-feed.json', self.location.href).pathname, '[]'],
  [new URL('./podcasts.json', self.location.href).pathname, '[]'],
  [new URL('./generated-podcasts.json', self.location.href).pathname, '[]'],
  [new URL('./radio-stations.json', self.location.href).pathname, '[]'],
  [new URL('./source-health.json', self.location.href).pathname, '{}'],
  [new URL('./source-catalog.json', self.location.href).pathname, '[]'],
  [new URL('./podcast-health.json', self.location.href).pathname, '{}'],
  [new URL('./radio-health.json', self.location.href).pathname, '{}'],
  [new URL('./podcast-sources.json', self.location.href).pathname, '[]'],
  [new URL('./radio-sources.json', self.location.href).pathname, '[]'],
  [new URL('./audio-health.json', self.location.href).pathname, '{}'],
  [new URL('./feature-audit.json', self.location.href).pathname, '{}'],
  [new URL('./language-source-audit.json', self.location.href).pathname, '{}'],
  [new URL('./multilingual-source-registry.json', self.location.href).pathname, '{}']
]);

const DATA_FILES = new Set([
  new URL('./news.json', self.location.href).pathname,
  new URL('./news-feed.json', self.location.href).pathname,
  new URL('./events.json', self.location.href).pathname,
  new URL('./events-feed.json', self.location.href).pathname,
  new URL('./source-health.json', self.location.href).pathname,
  new URL('./source-catalog.json', self.location.href).pathname,
  new URL('./podcasts.json', self.location.href).pathname,
  new URL('./generated-podcasts.json', self.location.href).pathname,
  new URL('./podcast-health.json', self.location.href).pathname,
  new URL('./radio-stations.json', self.location.href).pathname,
  new URL('./radio-health.json', self.location.href).pathname,
  new URL('./podcast-sources.json', self.location.href).pathname,
  new URL('./radio-sources.json', self.location.href).pathname,
  new URL('./audio-health.json', self.location.href).pathname,
  new URL('./feature-audit.json', self.location.href).pathname,
  new URL('./language-source-audit.json', self.location.href).pathname,
  new URL('./multilingual-source-registry.json', self.location.href).pathname
]);

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(APP_CACHE);
    const results = await Promise.allSettled(
      APP_SHELL.map(async resource => {
        const request = new Request(
          new URL(resource, self.location.href),
          { cache: 'reload' }
        );
        const response = await fetch(request);
        if (!response.ok) {
          throw new Error(`${resource}: HTTP ${response.status}`);
        }
        await cache.put(request, response);
      })
    );

    const failed = results.filter(result => result.status === 'rejected');
    if (failed.length) {
      console.warn(
        `WRN offline cache: ${failed.length} optionale Dateien `
        + 'konnten nicht gespeichert werden.'
      );
    }
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keep = new Set([APP_CACHE, DATA_CACHE]);
    const cacheNames = await caches.keys();

    await Promise.all(
      cacheNames
        .filter(name =>
          name.startsWith(WRN_CACHE_PREFIX)
          && !keep.has(name)
        )
        .map(name => caches.delete(name))
    );

    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(request));
    return;
  }

  if (DATA_FILES.has(url.pathname)) {
    event.respondWith(networkFirstData(request));
    return;
  }

  if (['script', 'style', 'manifest', 'font'].includes(
    request.destination
  )) {
    event.respondWith(networkFirstAsset(request));
    return;
  }

  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});

async function networkFirstNavigation(request) {
  const cache = await caches.open(APP_CACHE);
  const requestUrl = new URL(request.url);
  const rootPath = new URL('./', self.location.href).pathname;
  const indexPath = new URL('./index.html', self.location.href).pathname;
  const isIndexNavigation = (
    requestUrl.pathname === rootPath
    || requestUrl.pathname === indexPath
  );

  try {
    const response = await fetchWithTimeout(request, 5000);
    if (response?.ok) {
      await cache.put(
        isIndexNavigation ? './index.html' : request,
        response.clone()
      );
    }
    return response;
  } catch {
    return (await cache.match(request, { ignoreSearch: true }))
      || (await cache.match('./index.html'))
      || new Response(
        'Offline: Die App-Oberfläche ist noch nicht gespeichert.',
        {
          status: 503,
          headers: {
            'Content-Type': 'text/plain; charset=utf-8'
          }
        }
      );
  }
}

async function networkFirstData(request) {
  const cache = await caches.open(DATA_CACHE);
  try {
    const response = await fetchWithTimeout(request, 8000);
    if (response?.ok) await cache.put(request, response.clone());
    return response;
  } catch {
    const cached = await cache.match(
      request,
      { ignoreSearch: true }
    );
    const url = new URL(request.url);
    const fallback = JSON_FALLBACKS.get(url.pathname) || 'null';
    return cached || new Response(fallback, {
      status: 200,
      headers: {
        'Content-Type': 'application/json; charset=utf-8',
        'X-WRN-Offline-Fallback': 'empty'
      }
    });
  }
}

async function networkFirstAsset(request) {
  const cache = await caches.open(APP_CACHE);
  try {
    const response = await fetchWithTimeout(request, 5000);
    if (response?.ok) await cache.put(request, response.clone());
    return response;
  } catch {
    return (await cache.match(
      request,
      { ignoreSearch: true }
    )) || new Response('', { status: 504 });
  }
}

async function fetchWithTimeout(request, timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    timeoutMs
  );
  try {
    return await fetch(request, {
      signal: controller.signal,
      cache: 'no-store'
    });
  } finally {
    clearTimeout(timeout);
  }
}
