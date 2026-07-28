'use strict';

const CACHE_PREFIX = 'wrn-news-app-2-';
const CACHE_NAME = `${CACHE_PREFIX}v6`;
const SHELL = [
  './next.html',
  './news-app-2.css?preview=5',
  './prisoner-solidarity.css?preview=3',
  './news-app-2-config.js?preview=3',
  './news-app-2-core.js?preview=3',
  './news-app-2-specialty.js?preview=3',
  './news-app-2-media.js?preview=4',
  './shared-translation-client.js?preview=3',
  './stories-core.js?preview=3',
  './lexicon-tab.js?preview=3',
  './prisoner-solidarity.js?preview=3',
  './news-app-2.js?preview=5',
  './wrn-logo.webp'
];
const DATA_PATHS = new Set([
  new URL('./news-feed.json', self.location.href).pathname,
  new URL('./news.json', self.location.href).pathname,
  new URL('./events-feed.json', self.location.href).pathname,
  new URL('./prisoner-solidarity.json', self.location.href).pathname,
  new URL('./podcasts.json', self.location.href).pathname,
  new URL('./generated-podcasts.json', self.location.href).pathname,
  new URL('./radio-stations.json', self.location.href).pathname,
  new URL('./radio-health.json', self.location.href).pathname
]);

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await Promise.allSettled(SHELL.map(async resource => {
      const request = new Request(new URL(resource, self.location.href), { cache: 'reload' });
      const response = await fetch(request);
      if (response.ok) await cache.put(request, response);
    }));
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names
      .filter(name => name.startsWith(CACHE_PREFIX) && name !== CACHE_NAME)
      .map(name => caches.delete(name)));
    await self.clients.claim();
  })());
});

async function networkFirst(request, fallbackBody = '') {
  const cache = await caches.open(CACHE_NAME);
  try {
    const response = await fetch(request);
    if (response.ok) await cache.put(request, response.clone());
    return response;
  } catch {
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response(fallbackBody, {
      status: 200,
      headers: { 'Content-Type': 'application/json; charset=utf-8' }
    });
  }
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate' && url.pathname.endsWith('/next.html')) {
    event.respondWith(networkFirst(request));
    return;
  }

  if (DATA_PATHS.has(url.pathname)) {
    event.respondWith(networkFirst(request, url.pathname.includes('prisoner-')
      ? '{"schemaVersion":1,"profiles":[],"sources":[]}'
      : '[]'));
    return;
  }

  if (['script', 'style'].includes(request.destination)) {
    event.respondWith(networkFirst(request));
    return;
  }

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    if (cached) return cached;
    const response = await fetch(request);
    if (response.ok && ['script', 'style', 'image', 'font'].includes(request.destination)) {
      await cache.put(request, response.clone());
    }
    return response;
  })());
});
