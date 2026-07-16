/* World Revolution News – Offline Service Worker */
'use strict';

const APP_CACHE = 'wrn-app-v2026-07-16-phase1f';
const DATA_CACHE = 'wrn-data-v2026-07-16-phase1f';

const APP_SHELL = [
  './',
  './index.html',
  './styles.css',
  './config.js',
  './offline-db.js',
  './status-center.js',
  './utils.js',
  './accessibility.js',
  './media-player.js',
  './events.js',
  './reading-state.js',
  './audio-hub.js',
  './app.js',
  './manifest.json',
  './icon.svg'
];

const DATA_FILES = new Set([
  new URL('./news.json', self.location.href).pathname,
  new URL('./events.json', self.location.href).pathname,
  new URL('./source-health.json', self.location.href).pathname,
  new URL('./podcasts.json', self.location.href).pathname,
  new URL('./podcast-health.json', self.location.href).pathname,
  new URL('./radio-stations.json', self.location.href).pathname
]);

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(APP_CACHE);
    await cache.addAll(APP_SHELL);
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keep = new Set([APP_CACHE, DATA_CACHE]);
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.filter(name => !keep.has(name)).map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);

  // Nur eigene Dateien werden gespeichert. Fremde Artikelbilder und Webseiten
  // werden absichtlich nicht dauerhaft gecacht.
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith(networkFirstNavigation(request));
    return;
  }

  if (DATA_FILES.has(url.pathname)) {
    event.respondWith(networkFirstData(request));
    return;
  }

  if (['script', 'style', 'manifest', 'font'].includes(request.destination)) {
    event.respondWith(networkFirstAsset(request));
    return;
  }

  event.respondWith(fetch(request).catch(() => caches.match(request)));
});

async function networkFirstNavigation(request) {
  const cache = await caches.open(APP_CACHE);

  try {
    const response = await fetchWithTimeout(request, 5000);
    if (response?.ok) await cache.put('./index.html', response.clone());
    return response;
  } catch {
    return (await cache.match(request))
      || (await cache.match('./index.html'))
      || new Response('Offline: Die App-Oberfläche ist noch nicht gespeichert.', {
        status: 503,
        headers: { 'Content-Type': 'text/plain; charset=utf-8' }
      });
  }
}

async function networkFirstData(request) {
  const cache = await caches.open(DATA_CACHE);

  try {
    const response = await fetchWithTimeout(request, 8000);
    if (response?.ok) await cache.put(request, response.clone());
    return response;
  } catch {
    const cached = await cache.match(request, { ignoreSearch: true });
    return cached || new Response('[]', {
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
    return (await cache.match(request, { ignoreSearch: true }))
      || new Response('', { status: 504 });
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(APP_CACHE);
  const cached = await cache.match(request, { ignoreSearch: true });

  const updatePromise = fetch(request)
    .then(async response => {
      if (response?.ok) await cache.put(request, response.clone());
      return response;
    })
    .catch(() => null);

  if (cached) return cached;
  const networkResponse = await updatePromise;
  return networkResponse || new Response('', { status: 504 });
}

async function fetchWithTimeout(request, timeoutMs) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(request, { signal: controller.signal, cache: 'no-store' });
  } finally {
    clearTimeout(timeout);
  }
}
