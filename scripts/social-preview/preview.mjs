import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';

export const HOME = 'https://solinaridao.com/';
const PUBLIC_FEED = 'https://blackfront161.github.io/Revolution-News-Data/news-feed.json';
const segmenter = new Intl.Segmenter('en', { granularity: 'grapheme' });
const graphemes = (text) => [...segmenter.segment(text)].length;
const TRACKING = /^(utm_.+|pk_(campaign|kwd|medium|source)|fbclid|gclid|mc_(cid|eid))$/i;
const noLinks = /(?:https?:\/\/|www\.)/i;

export function originalKey(value) {
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password) {
    throw new Error('An HTTPS original source URL is required.');
  }
  url.hash = '';
  for (const name of [...url.searchParams.keys()]) {
    if (TRACKING.test(name)) url.searchParams.delete(name);
  }
  url.searchParams.sort();
  if (url.pathname !== '/') url.pathname = url.pathname.replace(/\/+$/, '');
  return url.href;
}

function editorialLine(value, label) {
  if (typeof value !== 'string' || !value.trim() || /[\r\n\p{Cc}]/u.test(value) || noLinks.test(value)) {
    throw new Error(`${label} must be a single line of text without embedded URLs.`);
  }
  return value.trim().normalize('NFC');
}

function wrnTarget(target) {
  if (target === undefined) return { url: HOME };
  const url = new URL(target.url);
  if (url.origin !== HOME.slice(0, -1) || url.username || url.password || url.href === HOME) {
    throw new Error('A specific target must be an HTTPS solinaridao.com page.');
  }
  return { url: url.href, marker: editorialLine(target.marker, 'Target marker') };
}

function renderPost({ id, english, local, source, original, published, target }) {
  const body = [english, local?.text, `Source: ${source}`].filter(Boolean).join('\n\n');
  const prefix = `${body}\n\n`;
  const text = prefix + target.url;
  const mastodon = graphemes(prefix) + 23;
  const bluesky = graphemes(text);
  const bytes = Buffer.byteLength(text);
  if (mastodon > 500 || bluesky > 300 || bytes > 3000) {
    throw new Error(`${id.slice(0, 12)} exceeds a post limit (Mastodon ${mastodon}, Bluesky ${bluesky} / ${bytes} bytes).`);
  }
  return {
    id, original, published, target, text,
    languages: local ? ['en', local.language] : ['en'],
    counts: { mastodon, bluesky, bytes },
    facets: [{
      index: { byteStart: Buffer.byteLength(prefix), byteEnd: bytes },
      features: [{ $type: 'app.bsky.richtext.facet#link', uri: target.url }],
    }],
  };
}

export async function prepare(selection, feed, checkTarget) {
  if (!Array.isArray(feed) || !Array.isArray(selection) || selection.length < 1 || selection.length > 3) {
    throw new Error('The pilot requires a feed array and between one and three selected items.');
  }
  const entries = new Map();
  for (const entry of feed) {
    let key;
    try { key = originalKey(entry?.link); } catch { continue; }
    const group = entries.get(key) ?? [];
    group.push(entry);
    entries.set(key, group);
  }

  const seen = new Set();
  const posts = [];
  for (const draft of selection) {
    const original = originalKey(draft.original);
    if (seen.has(original)) throw new Error(`Duplicate selection for ${original}`);
    seen.add(original);
    const rows = entries.get(original) ?? [];
    if (rows.length !== 1) throw new Error(`Expected exactly one feed record for ${original}, found ${rows.length}.`);
    const [entry] = rows;
    if (typeof entry.pubDate !== 'string' || !Number.isFinite(Date.parse(entry.pubDate))) {
      throw new Error(`Invalid publication date for ${original}.`);
    }
    const published = new Date(entry.pubDate).toISOString();
    const source = editorialLine(entry.quelleName, 'Original publisher');
    const english = editorialLine(draft.english, 'English copy');
    let local;
    if (draft.local !== undefined) {
      if (typeof draft.local?.language !== 'string') throw new Error('Second language requires a BCP 47 tag.');
      const language = Intl.getCanonicalLocales(draft.local.language)[0];
      if (!language || language.split('-')[0] === 'en') throw new Error('Second language must be a non-English BCP 47 tag.');
      local = { language, text: editorialLine(draft.local.text, 'Local-language copy') };
    }
    let target = wrnTarget(draft.target);
    if (checkTarget && !await checkTarget(target)) {
      if (target.url === HOME || !await checkTarget({ url: HOME })) throw new Error('The WRN homepage could not be verified.');
      target = { url: HOME, fallback: true };
    }
    posts.push(renderPost({
      id: createHash('sha256').update(original).digest('hex'),
      english, local, source, original: new URL(draft.original).href, published, target,
    }));
  }
  return posts;
}

export async function checkPublicTarget(target, request = fetch) {
  try {
    const response = await request(target.url, { redirect: 'manual', signal: AbortSignal.timeout(8000) });
    if (!response.ok || !response.headers.get('content-type')?.includes('text/html')) return false;
    const html = await response.text();
    return target.marker ? html.includes(target.marker) : /<title>[^<]*World Revolution News/i.test(html);
  } catch {
    return false;
  }
}

const readJson = async (file) => JSON.parse(await readFile(file, 'utf8'));

async function readFeed(option) {
  if (option === 'snapshot') return readJson(new URL('./feed-sample.json', import.meta.url));
  if (option !== 'live') return readJson(option);
  const response = await fetch(PUBLIC_FEED, { redirect: 'error', signal: AbortSignal.timeout(15000) });
  if (!response.ok) throw new Error(`Public feed returned HTTP ${response.status}.`);
  return response.json();
}

export async function loadDrafts({ feed = 'snapshot', selection, checkLinks = false } = {}) {
  const drafts = await readJson(selection ?? new URL('./selection.json', import.meta.url));
  return prepare(drafts, await readFeed(feed), checkLinks ? checkPublicTarget : undefined);
}

export function reviewCode(post) {
  return createHash('sha256')
    .update(JSON.stringify([post.id, post.published, post.text, post.languages]))
    .digest('hex').slice(0, 24);
}

const markdown = (text) => text.replace(/[<>&]/g, (char) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;' })[char]);

async function main() {
  const { values } = parseArgs({ options: {
    feed: { type: 'string', default: 'snapshot' },
    selection: { type: 'string' },
    'check-links': { type: 'boolean' },
  } });
  const posts = await loadDrafts({ feed: values.feed, selection: values.selection, checkLinks: values['check-links'] });
  console.log(`# WRN social media preview\n\nFeed mode: ${markdown(values.feed)}. Link check: ${values['check-links'] ? 'live HTTP' : 'offline'}.\n`);
  for (const [index, post] of posts.entries()) {
    console.log(`## Draft ${index + 1} · ${post.languages.join(', ')}\n`);
    console.log(`    ${post.text.replaceAll('\n', '\n    ')}\n`);
    console.log(`- Mastodon ${post.counts.mastodon}/500 · Bluesky ${post.counts.bluesky}/300 graphemes, ${post.counts.bytes}/3000 bytes`);
    console.log(`- Review code \`${reviewCode(post)}\``);
    console.log(`- [WRN destination](${post.target.url}) · [Original source](${post.original})${post.target.fallback ? ' · homepage fallback' : ''}\n`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => { console.error(error.message); process.exitCode = 1; });
}
