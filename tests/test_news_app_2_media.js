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
