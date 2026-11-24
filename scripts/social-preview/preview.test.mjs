import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { apiRequests, deliver, gitHubLedger } from './delivery.mjs';
import { checkPublicTarget, HOME, prepare } from './preview.mjs';

const readJson = async (file) => JSON.parse(await readFile(new URL(file, import.meta.url), 'utf8'));
const selection = await readJson('./selection.json');
const feed = await readJson('./feed-sample.json');

test('renders all three source-attributed posts and uses UTF-8 facet offsets', async () => {
  const posts = await prepare(selection, feed);
  assert.equal(posts.length, 3);
  assert.deepEqual(posts.map(({ languages }) => languages), [['en', 'fr'], ['en'], ['en']]);
  for (const [i, post] of posts.entries()) {
    assert.match(post.text, /Source: /);
    assert.ok(post.text.includes(feed[i].quelleName));
    assert.ok(post.counts.mastodon <= 500 && post.counts.bluesky <= 300 && post.counts.bytes <= 3000);
    const [link] = post.facets;
    assert.equal(Buffer.from(post.text).subarray(link.index.byteStart, link.index.byteEnd).toString(), post.target.url);
    assert.equal(link.features[0].uri, post.target.url);
    assert.equal(new URL(post.target.url).origin, new URL(HOME).origin);
    assert.equal(post.original, feed[i].link);
  }
});

test('uses a verified specific page and falls back to the homepage for a false 200 or a redirect', async () => {
  const url = 'https://solinaridao.com/articles/wrn-example/';
  const draft = { ...selection[1], target: { url, marker: 'Correct article title' } };
  const html = (value) => new Response(value, { headers: { 'content-type': 'text/html' } });
  const request = (target) => target === url ? html('<title>Correct article title</title>') : html('<title>World Revolution News</title>');
  const [deep] = await prepare([draft], feed, (target) => checkPublicTarget(target, request));
  assert.equal(deep.target.url, url);
  const [fallback] = await prepare([draft], feed, (target) => checkPublicTarget(target, () => html('<title>World Revolution News</title>')));
  assert.deepEqual(fallback.target, { url: HOME, fallback: true });
  assert.equal(await checkPublicTarget({ url }, () => Response.redirect(HOME)), false);
  await assert.rejects(prepare([draft], feed, () => false), /homepage could not be verified/);
});

test('rejects oversized drafts, missing matches, and duplicates with alternate tracking URLs', async () => {
  const draft = selection[1];
  await assert.rejects(prepare([{ ...draft, english: '👩🏾‍💻'.repeat(300) }], feed), /exceeds a post limit/);
  await assert.rejects(prepare([{ ...draft, english: 'x' + '\u0301'.repeat(1700) }], feed), /exceeds a post limit/);
  await assert.rejects(prepare([draft], [feed[0]]), /found 0/);
  const alternate = `${draft.original.slice(0, -1)}?utm_source=rss#headline`;
  await assert.rejects(prepare([draft, { ...draft, original: alternate }], feed), /Duplicate selection/);
  await assert.rejects(prepare([draft], [...feed, { ...feed[1], link: alternate }]), /found 2/);
  const [plain] = await prepare([draft], feed);
  const [tracked] = await prepare([{ ...draft, original: alternate, english: 'Revised text.' }], feed);
  assert.equal(plain.id, tracked.id);
  assert.equal(apiRequests(plain).bluesky.body.rkey, apiRequests(tracked).bluesky.body.rkey);
  await assert.rejects(prepare([{ ...draft, target: { url: 'https://example.com/', marker: 'Example' } }], feed), /solinaridao.com/);
});

function fakeGitHub() {
  const files = new Map();
  const json = (value, status) => Response.json(value, { status });
  const request = async (href, options) => {
    const url = new URL(href);
    const old = files.get(url.pathname);
    if (options.method !== 'PUT') {
      assert.equal(url.searchParams.get('ref'), 'wrn-social-delivery');
      return json(old ?? {}, old ? 200 : 404);
    }
    const { content, branch, sha } = JSON.parse(options.body);
    assert.equal(branch, 'wrn-social-delivery');
    const state = JSON.parse(Buffer.from(content, 'base64').toString());
    if (old && old.sha !== sha) return json({}, 409);
    const updated = { ...state, sha: `${state.status}-sha` };
    files.set(url.pathname, updated);
    return json({ content: updated }, old ? 200 : 201);
  };
  return { files, request };
}

test('persists per-platform outcomes across reruns after the Bluesky response is lost', async () => {
  const [first, second] = await prepare(selection, feed);
  const { files, request } = fakeGitHub();
  let mastodonCalls = 0;
  let blueskyCalls = 0;
  const publishers = {
    mastodon: async ({ path, headers, body }) => {
      assert.equal(path, '/api/v1/statuses');
      assert.equal(headers['Idempotency-Key'], `wrn-${first.id}`);
      assert.equal(body.status, first.text);
      mastodonCalls++;
      return { id: '123' };
    },
    bluesky: async ({ path, body }) => {
      assert.equal(path, '/xrpc/com.atproto.repo.createRecord');
      assert.match(body.rkey, /^[2-7a-j][2-7a-z]{12}$/);
      assert.equal(body.record.text, first.text);
      assert.deepEqual(body.record.langs, ['en', 'fr']);
      blueskyCalls++;
      throw new Error('The connection was interrupted after the platform received the request.');
    },
  };
  const run = await deliver([first], gitHubLedger('test-token', request), publishers);
  assert.deepEqual(run.map(({ state }) => state), ['sent', 'pending-review']);
  const rerun = await deliver([first], gitHubLedger('test-token', request), publishers);
  assert.deepEqual(rerun.map(({ state }) => state), ['already-reserved', 'already-reserved']);
  assert.equal(mastodonCalls, 1);
  assert.equal(blueskyCalls, 1);
  assert.deepEqual([...files.values()].map(({ status }) => status), ['sent', 'pending']);

  const restored = await deliver([second], gitHubLedger('test-token', request), {
    bluesky: async ({ body }) => ({ uri: `at://${body.repo}/${body.collection}/${body.rkey}` }),
  });
  assert.equal(restored[0].state, 'sent');
});

test('a simultaneous reservation admits just one sender and a broken ledger sends nothing', async () => {
  const [post] = await prepare(selection, feed);
  const { request } = fakeGitHub();
  let calls = 0;
  const publishers = { mastodon: async () => { calls++; return { id: '123' }; } };
  const runs = await Promise.all([0, 1].map(() => deliver([post], gitHubLedger('test-token', request), publishers)));
  assert.deepEqual(runs.flat().map(({ state }) => state).sort(), ['already-reserved', 'sent']);
  assert.equal(calls, 1);

  const failing = gitHubLedger('test-token', async () => new Response(null, { status: 500 }));
  await assert.rejects(deliver([post], failing, publishers), /Cannot read delivery ledger/);
  assert.equal(calls, 1);
});

test('a successful post whose ledger confirmation fails remains reserved', async () => {
  const [post] = await prepare(selection, feed);
  const { request } = fakeGitHub();
  const ledger = gitHubLedger('test-token', (href, options) => {
    if (options.method === 'PUT' && JSON.parse(options.body).sha) return new Response(null, { status: 500 });
    return request(href, options);
  });
  let calls = 0;
  const publishers = { mastodon: async () => { calls++; return { id: '123' }; } };
  const [attempt] = await deliver([post], ledger, publishers);
  assert.equal(attempt.state, 'pending-review');
  await deliver([post], gitHubLedger('test-token', request), publishers);
  assert.equal(calls, 1);
});
