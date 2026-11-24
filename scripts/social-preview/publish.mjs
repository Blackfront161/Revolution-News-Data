import { parseArgs } from 'node:util';
import { pathToFileURL } from 'node:url';
import { deliver, gitHubLedger } from './delivery.mjs';
import { loadDrafts, reviewCode } from './preview.mjs';

const MASTODON = 'https://mastodon.social';
const ACCOUNT_ID = '117672173722272702';

export async function mastodonPublisher(token, post, request = fetch) {
  if (!token) throw new Error('The protected environment is missing WRN_MASTODON_TOKEN.');
  const authorization = { Authorization: `Bearer ${token}` };

  async function api(path, options = {}) {
    const response = await request(`${MASTODON}${path}`, {
      ...options, redirect: 'error', signal: AbortSignal.timeout(10000),
    });
    if (!response.ok) throw new Error(`Mastodon returned HTTP ${response.status}.`);
    return response.json();
  }

  const account = await api('/api/v1/accounts/verify_credentials', { headers: authorization });
  if (account.id !== ACCOUNT_ID || account.acct?.toLowerCase() !== 'blackfrontwrn') {
    throw new Error('The Mastodon token belongs to a different account.');
  }
  const instance = await api('/api/v2/instance');
  const limits = instance.configuration?.statuses;
  if (!Number.isInteger(limits?.max_characters) || !Number.isInteger(limits?.characters_reserved_per_url)
      || post.counts.mastodon - 23 + limits.characters_reserved_per_url > limits.max_characters) {
    throw new Error('The draft could not be validated against the current Mastodon instance limits.');
  }

  return ({ method, path, headers, body }) => api(path, {
    method, headers: { ...headers, ...authorization, 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
}

export function selectReviewedDraft(posts, { draft, code, platform }) {
  if (!['mastodon', 'bluesky'].includes(platform)) throw new Error('Choose a supported publishing platform.');
  if (!/^[1-3]$/.test(draft) || !/^[a-f0-9]{24}$/.test(code)) throw new Error('A valid draft number and review code are required.');
  const post = posts[Number(draft) - 1];
  if (!post || reviewCode(post) !== code) throw new Error('The draft has changed. Review a fresh live-feed preview.');
  return post;
}

async function main() {
  const { values } = parseArgs({ options: { verify: { type: 'boolean' } } });
  const { WRN_DRAFT: draft, WRN_PLATFORM: platform, WRN_REVIEW_CODE: code } = process.env;
  const post = selectReviewedDraft(await loadDrafts({ feed: 'live', checkLinks: true }), { draft, code, platform });
  if (values.verify) {
    console.log(`# Approval requested for ${platform}\n\nDraft ${draft} · \`${code}\`\n`);
    console.log(`    ${post.text.replaceAll('\n', '\n    ')}`);
    return;
  }
  if (process.env.GITHUB_ACTIONS !== 'true' || process.env.GITHUB_EVENT_NAME !== 'workflow_dispatch'
      || process.env.GITHUB_REPOSITORY !== 'Blackfront161/Revolution-News-Data'
      || process.env.GITHUB_WORKFLOW_REF !== 'Blackfront161/Revolution-News-Data/.github/workflows/social-publish.yml@refs/heads/main') {
    throw new Error('Publication requires the protected GitHub workflow on the default branch.');
  }

  const publisher = platform === 'mastodon'
    ? await mastodonPublisher(process.env.WRN_MASTODON_TOKEN, post)
    : await (await import('./bluesky-oauth.mjs')).blueskyPublisher(process.env.WRN_BLUESKY_OAUTH_SESSION);
  const [outcome] = await deliver([post], gitHubLedger(process.env.WRN_LEDGER_TOKEN), { [platform]: publisher });
  console.log(`## ${platform} · draft ${draft}\n\nDelivery status: \`${outcome.state}\``);
  if (outcome.state === 'pending-review') {
    throw new Error('Delivery is uncertain. Check the platform account and the durable reservation before intervening.');
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => { console.error(error.message); process.exitCode = 1; });
}
