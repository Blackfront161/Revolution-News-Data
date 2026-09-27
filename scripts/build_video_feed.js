'use strict';

const fs = require('node:fs');
const path = require('node:path');
const pipeline = require('../video-pipeline-core.js');
const { createPublicRequester, UnsafeVideoUrl } = require('./public_video_request.js');

const root = path.resolve(__dirname, '..');
const args = new Set(process.argv.slice(2));
const requestPublicHttps = createPublicRequester();

function readJson(name) {
  return JSON.parse(fs.readFileSync(path.join(root, name), 'utf8'));
}

function writeJson(name, value) {
  fs.writeFileSync(path.join(root, name), `${JSON.stringify(value, null, 2)}\n`, 'utf8');
}

async function checkUrl(url) {
  try {
    let response = await requestPublicHttps(url, { method: 'HEAD' });
    if ([403, 405].includes(response.status)) {
      response = await requestPublicHttps(url, { method: 'GET', headers: { Range: 'bytes=0-1024' } });
    }
    return { ok: response.ok, status: response.status, finalUrl: response.url };
  } catch (error) {
    return {
      ok: false,
      status: 0,
      unsafe: error instanceof UnsafeVideoUrl,
      error: String(error?.message || error)
    };
  }
}

async function mapLimited(rows, limit, worker) {
  const results = new Array(rows.length);
  let cursor = 0;
  async function consume() {
    while (cursor < rows.length) {
      const index = cursor;
      cursor += 1;
      results[index] = await worker(rows[index]);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, rows.length) }, consume));
  return results;
}

async function platformMetadata(item) {
  if (item.platform === 'YouTube' && item.platformId) {
    try {
      const response = await requestPublicHttps(item.originalUrl, {
        readBody: true,
        headers: { 'Accept-Language': 'en' }
      });
      if (!response.ok) return null;
      const page = response.body;
      const publishedAt = page.match(/"publishDate":"([^"]+)"/u)?.[1] || item.publishedAt;
      const durationSeconds = Number(page.match(/"lengthSeconds":"(\d+)"/u)?.[1] || 0) || item.durationSeconds;
      const availability = page.match(/"playabilityStatus":\{"status":"([^"]+)"/u)?.[1] || 'unknown';
      const playabilityReason = page.match(/"playabilityStatus":\{"status":"[^"]+","reason":"([^"]+)"/u)?.[1] || '';
      return {
        publishedAt,
        durationSeconds,
        subtitlesAvailable: /"captionTracks":\[/u.test(page),
        availability,
        playabilityReason
      };
    } catch {
      return null;
    }
  }
  if (!['PeerTube', 'Kolektiva'].includes(item.platform) || !item.platformId) return null;
  const origin = new URL(item.originalUrl).origin;
  try {
    const metadataUrl = `${origin}/api/v1/videos/${encodeURIComponent(item.platformId)}`;
    const response = await requestPublicHttps(metadataUrl, { readBody: true });
    if (!response.ok) return null;
    const metadata = JSON.parse(response.body);
    const captionsResponse = await requestPublicHttps(`${metadataUrl}/captions`, { readBody: true });
    const captions = captionsResponse.ok ? JSON.parse(captionsResponse.body) : { data: [] };
    return {
      durationSeconds: Number(metadata.duration || 0) || item.durationSeconds,
      thumbnailUrl: metadata.thumbnailPath ? new URL(metadata.thumbnailPath, origin).href : item.thumbnailUrl,
      language: metadata.language?.id || item.language,
      publishedAt: metadata.originallyPublishedAt || metadata.publishedAt || item.publishedAt,
      subtitlesAvailable: Array.isArray(captions.data) ? captions.data.length > 0 : item.subtitlesAvailable,
      availability: 'OK',
      playabilityReason: ''
    };
  } catch {
    return null;
  }
}

async function main() {
  const generatedAt = new Date().toISOString();
  const registry = readJson('video-sources-registry.json');
  const seed = readJson('video-editorial-seed.json');
  const articles = readJson('news-feed.json');
  const built = pipeline.buildVideoFeed({ registry, seeds: seed.items, articles });
  let metadataEnriched = 0;
  if (args.has('--check-network')) {
    const metadata = await mapLimited(built.items, 4, platformMetadata);
    built.items = built.items.map((item, index) => {
      if (!metadata[index]) return item;
      metadataEnriched += 1;
      const publishedAt = metadata[index].publishedAt || item.publishedAt;
      return { ...item, ...metadata[index], publishedAt, timestamp: Date.parse(publishedAt) || item.timestamp };
    });
  }
  const feed = {
    schemaVersion: 1,
    generatedAt,
    dataMode: 'branch-snapshot',
    stats: built.stats,
    items: built.items
  };
  let networkChecks = { mode: 'not-run', checked: 0, reachable: 0, failed: 0, sources: { results: [] }, items: { results: [] } };
  if (args.has('--check-network')) {
    const sourceTargets = registry.sources.filter(source => source.enabled !== false && source.homepage);
    const sourceResults = await mapLimited(sourceTargets, 4, async source => ({
      sourceId: source.id,
      url: source.homepage,
      ...(await checkUrl(source.homepage))
    }));
    const itemResults = await mapLimited(feed.items, 4, async item => ({
      canonicalId: item.canonicalId,
      original: { url: item.originalUrl, ...(await checkUrl(item.originalUrl)) },
      embed: item.embedUrl
        ? { url: item.embedUrl, ...(await checkUrl(item.embedUrl)) }
        : null
    }));
    const requestResults = [
      ...sourceResults,
      ...itemResults.flatMap(result => [result.original, result.embed].filter(Boolean))
    ];
    networkChecks = {
      mode: 'sources-and-items',
      checked: requestResults.length,
      reachable: requestResults.filter(result => result.ok).length,
      failed: requestResults.filter(result => !result.ok).length,
      metadataEnriched,
      sources: {
        checked: sourceResults.length,
        reachable: sourceResults.filter(result => result.ok).length,
        failed: sourceResults.filter(result => !result.ok).length,
        results: sourceResults
      },
      items: {
        checked: itemResults.length,
        reachable: itemResults.filter(result => result.original.ok).length,
        failed: itemResults.filter(result => !result.original.ok).length,
        embedChecked: itemResults.filter(result => result.embed).length,
        results: itemResults
      }
    };
  }
  const health = pipeline.buildVideoHealth(built, registry, { generatedAt, networkChecks });
  writeJson('video-feed.json', feed);
  writeJson('video-health.json', health);
  process.stdout.write(`Video feed: ${feed.items.length} items, ${built.stats.duplicateCount} duplicates, ${built.stats.rejectedCount} rejected\n`);
  process.stdout.write(`Video health: ${health.status}; network ${networkChecks.mode}\n`);
}

main().catch(error => {
  process.stderr.write(`${error?.stack || error}\n`);
  process.exitCode = 1;
});
