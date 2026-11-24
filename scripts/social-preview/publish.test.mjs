import assert from 'node:assert/strict';
import test from 'node:test';
import { BLUESKY_SCOPE, blueskyPublisher, checkBlueskySession, oauthClient } from './bluesky-oauth.mjs';
import { apiRequests, WRN_DID } from './delivery.mjs';
import { loadDrafts, reviewCode } from './preview.mjs';
import { mastodonPublisher, selectReviewedDraft } from './publish.mjs';

const drafts = await loadDrafts();
const post = drafts[0];

test('publish selection binds the review code to the selected post and rendered destination', () => {
  const review = { draft: '1', code: reviewCode(post), platform: 'mastodon' };
  assert.equal(selectReviewedDraft(drafts, review), post);
  assert.throws(() => selectReviewedDraft(drafts, { ...review, draft: '2' }), /draft has changed/);
  assert.throws(() => selectReviewedDraft(drafts, { ...review, platform: 'reddit' }), /supported publishing platform/);
  assert.throws(() => selectReviewedDraft([{ ...post, text: post.text + ' revised' }], review), /draft has changed/);
});

test('Mastodon uses the exact account, the live length limits, and the official status endpoint', async () => {
  const calls = [];
  const request = async (url, options) => {
    calls.push({ url, options });
    if (url.endsWith('/verify_credentials')) return Response.json({ id: '117672173722272702', acct: 'BlackfrontWRN' });
    if (url.endsWith('/instance')) return Response.json({ configuration: { statuses: { max_characters: 500, characters_reserved_per_url: 23 } } });
    return Response.json({ id: '1234' });
  };
  const publish = await mastodonPublisher('fake-token', post, request);
  const plan = apiRequests(post).mastodon;
  assert.deepEqual(await publish(plan), { id: '1234' });
  assert.deepEqual(calls.map(({ url }) => url), [
    'https://mastodon.social/api/v1/accounts/verify_credentials',
    'https://mastodon.social/api/v2/instance',
    'https://mastodon.social/api/v1/statuses',
  ]);
  assert.equal(calls[0].options.headers.Authorization, 'Bearer fake-token');
  assert.equal(calls[1].options.headers, undefined);
  assert.equal(calls[2].options.method, 'POST');
  assert.equal(calls[2].options.headers['Idempotency-Key'], plan.headers['Idempotency-Key']);
  assert.equal(JSON.parse(calls[2].options.body).status, post.text);

  await assert.rejects(mastodonPublisher('', post, request), /missing WRN_MASTODON_TOKEN/);
  await assert.rejects(mastodonPublisher('fake-token', post, async () => Response.json({ id: '123', acct: 'SomeoneElse' })), /different account/);
  await assert.rejects(mastodonPublisher('fake-token', { ...post, counts: { mastodon: 501 } }, request), /instance limits/);
});

test('Bluesky restores the scoped WRN OAuth session and signs the XRPC create-record request', async () => {
  const callback = 'http://127.0.0.1:43123/oauth/callback';
  assert.equal(oauthClient(callback, new Map()).clientMetadata.scope, BLUESKY_SCOPE);
  assert.throws(() => oauthClient('https://example.test/oauth/callback', new Map()), /valid local/);

  const info = { sub: WRN_DID, scope: BLUESKY_SCOPE, expiresAt: new Date(Date.now() + 120000) };
  const session = {
    did: WRN_DID,
    async getTokenInfo(refresh) { assert.equal(refresh, false); return info; },
    async fetchHandler(path, options) {
      assert.equal(path, '/xrpc/com.atproto.repo.createRecord');
      assert.equal(options.method, 'POST');
      assert.equal(options.redirect, 'error');
      const { repo, collection, rkey, record } = JSON.parse(options.body);
      assert.equal(repo, WRN_DID);
      assert.equal(record.text, post.text);
      return Response.json({ uri: `at://${repo}/${collection}/${rkey}` });
    },
  };
  const publisher = await blueskyPublisher(JSON.stringify({ redirectUri: callback, state: { markers: ['fake'] } }), (url, store) => {
    assert.equal(url, callback);
    assert.deepEqual(store.get(WRN_DID), { markers: ['fake'] });
    return { async restore(did, refresh) { assert.equal(did, WRN_DID); assert.equal(refresh, false); return session; } };
  });
  const plan = apiRequests(post).bluesky;
  assert.equal((await publisher(plan)).uri, `at://${WRN_DID}/app.bsky.feed.post/${plan.body.rkey}`);
  await assert.rejects(checkBlueskySession(session, Date.now() + 90000), /expires too soon/);
  await assert.rejects(checkBlueskySession({ ...session, did: 'did:plc:other' }), /exact create-post scope/);
  await assert.rejects(checkBlueskySession({ ...session, getTokenInfo: async () => ({ ...info, scope: `${BLUESKY_SCOPE} transition:generic` }) }), /exact create-post scope/);
  await assert.rejects(blueskyPublisher('invalid JSON'), /Could not restore/);
});
