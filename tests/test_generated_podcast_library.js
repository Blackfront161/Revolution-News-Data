'use strict';

const assert = require('assert');
const fs = require('fs');

const source = fs.readFileSync('news-app-2.js', 'utf8');

assert(
  source.includes("libraryUrl.searchParams.set('action', 'podcasts.list')"),
  'News App 2 does not load the generated podcast library from the worker'
);
assert(
  source.includes("loadGeneratedPodcasts(dataUrls.generatedPodcasts || 'generated-podcasts.json')"),
  'News App 2 does not retain the static generated podcast fallback'
);
assert(
  source.includes("console.warn('Generated podcast library unavailable; using static fallback'"),
  'News App 2 does not report when it uses the static generated podcast fallback'
);

console.log('Generated podcast library loading contract: OK');
