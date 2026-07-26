'use strict';

const assert = require('node:assert/strict');
const core = require('../stories-core.js');

const now = Date.parse('2026-07-21T12:00:00Z');
const articles = [
  {
    title: 'Dockworkers strike expands across Hamburg port',
    quelleName: 'Labor Notes',
    pubDate: '2026-07-20T09:00:00Z',
    link: 'https://labornotes.example/a'
  },
  {
    title: 'Hamburg port strike spreads to more terminals',
    quelleName: 'Freedom News',
    pubDate: '2026-07-21T08:00:00Z',
    link: 'https://freedomnews.example/b'
  },
  {
    title: 'Workers in Hamburg extend port strike',
    quelleName: 'Unicorn Riot',
    pubDate: '2026-07-21T10:00:00Z',
    link: 'https://unicornriot.example/c'
  },
  {
    title: 'Community garden opens in Lisbon',
    quelleName: 'Other',
    pubDate: '2026-07-20T10:00:00Z',
    link: 'https://other.example/d'
  }
];

const stories = core.clusterStories(articles, {
  now,
  days: 7,
  minSources: 2,
  threshold: 0.2
});

assert.equal(stories.length, 1);
assert.equal(stories[0].itemCount, 3);
assert.equal(stories[0].sourceCount, 3);
assert.equal(stories[0].items[0].link, 'https://labornotes.example/a');
assert.equal(stories[0].items[2].link, 'https://unicornriot.example/c');

const falsePositiveStories = core.clusterStories([
  {
    title: 'Summer break at an independent magazine',
    quelleName: 'Magazine',
    pubDate: '2026-07-20T09:00:00Z',
    link: 'https://magazine.example/summer'
  },
  {
    title: 'Summer solidarity call for a housing protest',
    quelleName: 'Radar',
    pubDate: '2026-07-20T10:00:00Z',
    link: 'https://radar.example/call'
  },
  {
    title: 'July protest for neighbourhood solidarity',
    quelleName: 'Calendar A',
    pubDate: '2026-07-20T11:00:00Z',
    link: 'https://calendar-a.example/protest'
  },
  {
    title: 'July memorial event in another city',
    quelleName: 'Calendar B',
    pubDate: '2026-07-20T12:00:00Z',
    link: 'https://calendar-b.example/memorial'
  }
], { now, days: 7, minSources: 2 });

assert.equal(falsePositiveStories.length, 0);

const watchTerms = core.normalizeWatchTerms([
  'Hamburg',
  ' port strike ',
  'Hamburg'
]);

assert.deepEqual(watchTerms, ['Hamburg', 'port strike']);
assert.equal(
  core.matchesWatchlist(articles[0], watchTerms),
  true
);
assert.equal(
  core.matchesWatchlist(articles[3], watchTerms),
  false
);

const history = [
  {
    date: '2026-07-21',
    sections: [
      {
        id: 'overview',
        items: [
          {
            ...articles[2],
            isNew: true
          }
        ]
      }
    ]
  },
  {
    date: '2026-07-20',
    sections: [
      {
        id: 'overview',
        items: [
          {
            ...articles[0],
            isUpdated: true
          },
          {
            ...articles[1],
            isNew: true
          }
        ]
      }
    ]
  }
];

const week = core.weeklyInsights(history, {
  now,
  days: 7
});

assert.equal(week.daysCovered, 2);
assert.equal(week.itemCount, 3);
assert.equal(week.sourceCount, 3);
assert.equal(week.newCount, 2);
assert.equal(week.updatedCount, 1);
assert.ok(week.stories.length >= 1);

console.log('WRN stories core tests: OK');
