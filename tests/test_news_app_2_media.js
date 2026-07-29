'use strict';

const assert = require('assert');
const path = require('path');
const media = require(path.resolve(__dirname, '..', 'news-app-2-media.js'));

const political = media.normalizePodcast({
  id: 'one',
  title: 'Prison solidarity and abolition',
  sourceName: 'Movement Radio',
  description: '<p>A discussion about writing to political prisoners.</p>',
  published: '2026-07-27T12:00:00Z',
  region: 'Europe',
  audioUrl: 'https://example.org/episode.mp3',
  episodeUrl: 'https://example.org/episode'
});

assert.strictEqual(political.category, 'politics');
assert.strictEqual(political.description, 'A discussion about writing to political prisoners.');
assert.strictEqual(media.isRelevantPodcast(political), true);
assert.strictEqual(media.safeUrl('javascript:alert(1)'), '');
assert.strictEqual(media.canonicalRegion('Europa'), 'Europe');
assert.strictEqual(media.canonicalRegion('DACH'), 'Europe');
assert.strictEqual(media.canonicalRegion('Lateinamerika'), 'Latin America');

const generated = media.normalizePodcast({
  id: 'podcasts/de/short/example.mp3',
  title: 'Generated episode',
  source: 'Movement Radio',
  createdAt: '2026-07-24T09:06:27.082Z',
  expiresAt: '2026-08-23T09:06:27.082Z',
  articleUrl: 'https://example.org/article',
  audioUrl: 'https://example.org/generated.mp3',
  language: 'de',
  mode: 'short',
  voiceLabel: 'Katja'
});
assert.strictEqual(generated.published, '2026-07-24T09:06:27.082Z');
assert.strictEqual(generated.timestamp, Date.parse('2026-07-24T09:06:27.082Z'));
assert.strictEqual(generated.episodeUrl, 'https://example.org/article');
assert.strictEqual(generated.expiresAt, '2026-08-23T09:06:27.082Z');
assert.strictEqual(generated.mode, 'short');
assert.strictEqual(generated.voiceLabel, 'Katja');

const radio = media.normalizeRadio({
  id: 'station',
  name: 'Free Radio',
  streamCandidates: ['javascript:alert(1)', 'https://example.org/live.mp3'],
  website: 'https://example.org'
});
assert.strictEqual(radio.streamUrl, 'https://example.org/live.mp3');
assert.strictEqual(radio.streams.length, 1);

const filtered = media.filterItems([political], {
  query: 'abolition',
  region: 'Europe',
  category: 'politics'
});
assert.strictEqual(filtered.length, 1);
assert(media.INFORMATION_VIDEOS.length >= 5);
assert(media.INFORMATION_VIDEOS.every(item => media.safeUrl(item.url)));

console.log('News App 2 media contracts: OK');
