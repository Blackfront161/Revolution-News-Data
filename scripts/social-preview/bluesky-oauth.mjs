import { buildAtprotoLoopbackClientMetadata, NodeOAuthClient, requestLocalLock } from '@atproto/oauth-client-node';
import { WRN_DID } from './delivery.mjs';

export const BLUESKY_HANDLE = 'wrnblackfront.bsky.social';
export const BLUESKY_SCOPE = 'atproto repo:app.bsky.feed.post?action=create';

function memoryStore(values) {
  return {
    async get(key) { return values.get(key); },
    async set(key, value) { values.set(key, value); },
    async del(key) { values.delete(key); },
  };
}

export function oauthClient(redirectUri, sessions) {
  if (!/^http:\/\/127\.0\.0\.1:[1-9]\d{0,4}\/oauth\/callback$/.test(redirectUri)
      || Number(new URL(redirectUri).port) > 65535) {
    throw new Error('A valid local Bluesky OAuth callback is required.');
  }
  return new NodeOAuthClient({
    clientMetadata: buildAtprotoLoopbackClientMetadata({ scope: BLUESKY_SCOPE, redirect_uris: [redirectUri] }),
    requestLock: requestLocalLock,
    stateStore: memoryStore(new Map()),
    sessionStore: memoryStore(sessions),
  });
}

export async function checkBlueskySession(session, now = Date.now()) {
  const info = await session.getTokenInfo(false);
  const scopes = typeof info.scope === 'string' ? info.scope.trim().split(/\s+/).sort() : [];
  if (session.did !== WRN_DID || info.sub !== WRN_DID || scopes.join(' ') !== BLUESKY_SCOPE) {
    throw new Error('Bluesky authorization must match the WRN account and the exact create-post scope.');
  }
  if (!(info.expiresAt?.getTime() > now + 75000)) {
    throw new Error('The Bluesky authorization expires too soon. Authorize this pilot run again.');
  }
}

export async function blueskyPublisher(secret, makeClient = oauthClient) {
  if (!secret) throw new Error('The protected environment is missing WRN_BLUESKY_OAUTH_SESSION.');
  let session;
  try {
    const { redirectUri, state } = JSON.parse(secret);
    if (!state || typeof state !== 'object') throw new Error('Missing session state.');
    const client = makeClient(redirectUri, new Map([[WRN_DID, state]]));
    session = await client.restore(WRN_DID, false);
    if (!session) throw new Error('Missing restored session.');
  } catch {
    throw new Error('Could not restore the Bluesky session. Authorize this pilot run again.');
  }
  await checkBlueskySession(session);

  return async ({ path, method, body }) => {
    const response = await session.fetchHandler(path, {
      method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      redirect: 'error', signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) throw new Error(`Bluesky returned HTTP ${response.status}.`);
    return response.json();
  };
}
