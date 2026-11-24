const COLLECTION = 'app.bsky.feed.post';
export const WRN_DID = 'did:plc:ppichy3vtbmvwgbapqvouc6i';
const TID_ALPHABET = '234567abcdefghijklmnopqrstuvwxyz';
const LEDGER_BRANCH = 'wrn-social-delivery';
const CONTENTS = 'https://api.github.com/repos/Blackfront161/Revolution-News-Data/contents/';

function recordKey(post) {
  const publicationMicros = BigInt(Date.parse(post.published)) * 1000n;
  const offset = BigInt(`0x${post.id.slice(0, 8)}`) % 1024000n;
  let value = (publicationMicros << 10n) + offset;
  let key = '';
  for (let digit = 0; digit < 13; digit += 1) {
    key = TID_ALPHABET[Number(value & 31n)] + key;
    value >>= 5n;
  }
  return key;
}

export function apiRequests(post, createdAt = new Date().toISOString()) {
  return {
    mastodon: {
      method: 'POST',
      path: '/api/v1/statuses',
      headers: { 'Idempotency-Key': `wrn-${post.id}` },
      body: { status: post.text, visibility: 'public', language: post.languages[0] },
    },
    bluesky: {
      method: 'POST',
      path: '/xrpc/com.atproto.repo.createRecord',
      body: {
        repo: WRN_DID,
        collection: COLLECTION,
        rkey: recordKey(post),
        validate: true,
        record: {
          $type: COLLECTION, text: post.text, langs: post.languages, facets: post.facets, createdAt,
        },
      },
    },
  };
}

// Publishers receive the request description through an authenticated transport.
// Reserve durably before sending. A pending entry is never retried automatically.
export async function deliver(posts, ledger, publishers) {
  const outcomes = [];
  for (const post of posts) {
    for (const [platform, request] of Object.entries(apiRequests(post))) {
      const send = publishers[platform];
      if (!send) continue;
      const key = `${platform}/${post.id}`;
      const reservation = await ledger.reserve(key);
      if (!reservation) {
        outcomes.push({ key, state: 'already-reserved' });
        continue;
      }
      try {
        const response = await send(request);
        const receipt = platform === 'mastodon' ? response?.id : response?.uri;
        const expectedUri = `at://${WRN_DID}/${COLLECTION}/${request.body.rkey}`;
        if (platform === 'mastodon' ? !/^\d+$/.test(receipt) : receipt !== expectedUri) {
          throw new Error('Unconfirmed publication.');
        }
        await ledger.confirm(key, reservation, receipt);
        outcomes.push({ key, state: 'sent' });
      } catch {
        outcomes.push({ key, state: 'pending-review' });
      }
    }
  }
  return outcomes;
}

export function gitHubLedger(token, request = fetch) {
  if (!token) throw new Error('The protected GitHub job token is required for delivery.');
  const headers = {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'Content-Type': 'application/json',
  };

  function endpoint(key) {
    if (!/^(mastodon|bluesky)\/[a-f0-9]{64}$/.test(key)) throw new Error('Invalid delivery key.');
    return `${CONTENTS}deliveries/${key}.json`;
  }

  function read(url) {
    return request(`${url}?ref=${LEDGER_BRANCH}`, { headers, redirect: 'error', signal: AbortSignal.timeout(10000) });
  }

  function write(url, state, sha) {
    const content = Buffer.from(JSON.stringify(state) + '\n').toString('base64');
    return request(url, {
      method: 'PUT', headers, redirect: 'error', signal: AbortSignal.timeout(10000),
      body: JSON.stringify({ branch: LEDGER_BRANCH, message: `Record social delivery ${state.status}`, content, sha }),
    });
  }

  return {
    async reserve(key) {
      const url = endpoint(key);
      const existing = await read(url);
      if (existing.status === 200) return null;
      if (existing.status !== 404) throw new Error(`Cannot read delivery ledger (HTTP ${existing.status}).`);
      const pending = await write(url, { status: 'pending' });
      if (pending.status === 201) {
        const result = await pending.json();
        if (result?.content?.sha) return result.content.sha;
      }
      if ([409, 422].includes(pending.status) && (await read(url)).status === 200) return null;
      throw new Error(`Cannot reserve delivery (HTTP ${pending.status}).`);
    },
    async confirm(key, sha, receipt) {
      const result = await write(endpoint(key), { status: 'sent', receipt }, sha);
      if (result.status !== 200) throw new Error(`Cannot confirm delivery (HTTP ${result.status}).`);
    },
  };
}
