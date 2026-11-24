import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { createServer } from 'node:http';
import { BLUESKY_HANDLE, BLUESKY_SCOPE, checkBlueskySession, oauthClient } from './bluesky-oauth.mjs';
import { WRN_DID } from './delivery.mjs';

function saveSecret(value) {
  return new Promise((resolve, reject) => {
    const error = new Error('GitHub did not save the environment secret. Check gh auth status.');
    const gh = spawn('gh', ['secret', 'set', 'WRN_BLUESKY_OAUTH_SESSION',
      '--repo', 'Blackfront161/Revolution-News-Data', '--env', 'wrn-social-production'], {
      stdio: ['pipe', 'ignore', 'ignore'], windowsHide: true,
    });
    const timer = setTimeout(() => { gh.kill(); reject(error); }, 15000);
    gh.on('close', (code) => {
      clearTimeout(timer);
      if (code === 0) resolve();
      else reject(error);
    });
    gh.on('error', () => { clearTimeout(timer); reject(error); });
    gh.stdin.on('error', () => reject(error));
    gh.stdin.end(JSON.stringify(value));
  });
}

async function main() {
  const server = createServer();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const redirectUri = `http://127.0.0.1:${server.address().port}/oauth/callback`;
  const sessions = new Map();
  let timer;
  try {
    const client = oauthClient(redirectUri, sessions);
    const consent = await client.authorize(BLUESKY_HANDLE, { scope: BLUESKY_SCOPE, signal: AbortSignal.timeout(15000) });
    await new Promise((resolve, reject) => {
      let started = false;
      timer = setTimeout(() => reject(new Error('Zeitlimit der Bluesky-Autorisierung erreicht.')), 180000);
      server.on('request', async (request, response) => {
        const url = new URL(request.url, redirectUri);
        response.setHeader('Content-Type', 'text/plain; charset=utf-8');
        response.setHeader('Cache-Control', 'no-store');
        response.setHeader('Referrer-Policy', 'no-referrer');
        if (request.method !== 'GET' || url.pathname !== '/oauth/callback' || started) {
          response.writeHead(404).end();
          return;
        }
        started = true;
        try {
          const { session } = await client.callback(url.searchParams);
          await checkBlueskySession(session);
          const state = sessions.get(WRN_DID);
          if (!state) throw new Error('Missing session state.');
          await saveSecret({ redirectUri, state });
          response.end('Bluesky-Autorisierung in der geschützten GitHub-Umgebung gespeichert.');
          resolve();
        } catch {
          response.writeHead(400).end('Die Autorisierung konnte nicht gespeichert werden.');
          reject(new Error('Bluesky-Autorisierung fehlgeschlagen. Prüfe das Bluesky-Konto und die GitHub-Anmeldung.'));
        }
      });
      console.log(`Öffne diese Adresse im Browser und autorisiere ${BLUESKY_HANDLE}:\n${consent.href}`);
    });
    console.log('WRN_BLUESKY_OAUTH_SESSION ist in GitHub gespeichert.');
  } finally {
    clearTimeout(timer);
    server.close();
  }
}

main().catch(() => {
  console.error('Bluesky-Autorisierung konnte nicht abgeschlossen werden. Prüfe dein Konto und gh auth status.');
  process.exitCode = 1;
});
