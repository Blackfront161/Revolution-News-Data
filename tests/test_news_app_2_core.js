'use strict';

const assert = require('assert');
const path = require('path');
const core = require(path.resolve(__dirname, '..', 'news-app-2-core.js'));

const articles = core.normalizeArticles([
  {
    title: 'Newest A',
    quelleName: 'Source A',
    link: 'https://example.org/a-1',
    pubDate: '2026-07-27T12:00:00Z',
    content: '<p>First introduction with <strong>safe text</strong>.</p>',
    primaryRegion: 'Australia & NZ',
    primaryTopic: 'Antifascism'
  },
  {
    title: 'Newest A again',
    quelleName: 'Source A',
    link: 'https://example.org/a-2',
    pubDate: '2026-07-27T11:00:00Z',
    content: 'Second introduction.',
    primaryRegion: 'Europe',
    primaryTopic: 'Antifascism'
  },
  {
    title: 'Source B',
    quelleName: 'Source B',
    link: 'https://example.org/b',
    pubDate: '2026-07-27T10:00:00Z',
    content: 'Third introduction.',
    primaryRegion: 'Asia',
    primaryTopic: 'Labor Struggles'
  },
  {
    title: 'Source C',
    quelleName: 'Source C',
    link: 'javascript:alert(1)',
    pubDate: '2026-07-27T09:00:00Z',
    content: 'Video https://kolektiva.media/w/abc',
    primaryRegion: 'Latin America',
    primaryTopic: 'Antiracism'
  }
]);

assert.strictEqual(articles.length, 4);
assert.strictEqual(articles[0].primaryRegion, 'Oceania');
assert.strictEqual(articles[0].intro, 'First introduction with safe text.');
assert.strictEqual(articles[3].link, '', 'unsafe article URLs must be removed');
assert.strictEqual(core.hasVideo(articles[3]), true);

const balanced = core.balanceBySource(articles, 4, 2);
assert.strictEqual(balanced.length, 4);
for (let index = 1; index < balanced.length; index += 1) {
  assert.notStrictEqual(
    balanced[index - 1].source,
    balanced[index].source,
    'the same publisher must not appear twice in a row when alternatives exist'
  );
}
assert(
  [...balanced.reduce((counts, article) => {
    counts.set(article.source, (counts.get(article.source) || 0) + 1);
    return counts;
  }, new Map()).values()].every(count => count <= 2),
  'the home selection must respect the per-source ceiling'
);

const personalized = articles.filter(article => core.matchesPreferences(article, {
  regions: ['Asia'],
  topics: ['Antiracism'],
  sources: [],
  blockedSources: []
}));
assert.deepStrictEqual(
  personalized.map(article => article.title),
  ['Source B', 'Source C']
);

const filtered = core.filterArticles(articles, { query: 'safe text' });
assert.strictEqual(filtered.length, 1);
assert.strictEqual(filtered[0].title, 'Newest A');

assert.deepStrictEqual(
  core.splitTranslatedTeaser('Übersetzter Titel\n---\nÜbersetzte Einleitung'),
  { title: 'Übersetzter Titel', intro: 'Übersetzte Einleitung' }
);

console.log('News App 2 core contracts: OK');
