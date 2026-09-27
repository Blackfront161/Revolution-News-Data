'use strict';

const dns = require('node:dns').promises;
const https = require('node:https');
const net = require('node:net');

const blocked = new net.BlockList();
for (const [address, prefix, family] of [
  ['0.0.0.0', 8, 'ipv4'], ['10.0.0.0', 8, 'ipv4'],
  ['100.64.0.0', 10, 'ipv4'], ['127.0.0.0', 8, 'ipv4'],
  ['169.254.0.0', 16, 'ipv4'], ['172.16.0.0', 12, 'ipv4'],
  ['192.0.0.0', 24, 'ipv4'], ['192.0.2.0', 24, 'ipv4'],
  ['192.168.0.0', 16, 'ipv4'], ['198.18.0.0', 15, 'ipv4'],
  ['198.51.100.0', 24, 'ipv4'], ['203.0.113.0', 24, 'ipv4'],
  ['224.0.0.0', 4, 'ipv4'], ['240.0.0.0', 4, 'ipv4'],
  ['::', 128, 'ipv6'], ['::1', 128, 'ipv6'],
  ['64:ff9b::', 96, 'ipv6'],
  ['100::', 64, 'ipv6'], ['2001::', 32, 'ipv6'],
  ['2001:db8::', 32, 'ipv6'], ['2002::', 16, 'ipv6'],
  ['fc00::', 7, 'ipv6'], ['fe80::', 10, 'ipv6'], ['ff00::', 8, 'ipv6']
]) blocked.addSubnet(address, prefix, family);

class UnsafeVideoUrl extends Error {
  constructor(message) {
    super(message);
    this.name = 'UnsafeVideoUrl';
    this.code = 'UNSAFE_VIDEO_URL';
  }
}

function isPublicAddress(address) {
  const family = net.isIP(address);
  if (!family) return false;
  if (family === 6) {
    // 2000::/3 is global unicast; reject its reserved subranges above.
    return /^[23][0-9a-f]*:/iu.test(address) && !blocked.check(address, 'ipv6');
  }
  return !blocked.check(address, 'ipv4');
}

function assertPublicHttpsUrl(raw) {
  let url;
  try {
    url = new URL(String(raw || ''));
  } catch {
    throw new UnsafeVideoUrl('Invalid URL');
  }
  const host = url.hostname.toLowerCase().replace(/\.$/u, '');
  const literal = host.startsWith('[') && host.endsWith(']') ? host.slice(1, -1) : host;
  if (url.protocol !== 'https:' || url.username || url.password ||
      (url.port && url.port !== '443') || !host || net.isIP(literal) ||
      /(^|\.)(?:localhost|local|internal|test|invalid|example)$/u.test(host)) {
    throw new UnsafeVideoUrl('Only public HTTPS hostnames on port 443 are allowed');
  }
  return url;
}

async function resolvePublicHost(hostname, lookup = dns.lookup) {
  let answers;
  try {
    answers = await lookup(hostname, { all: true, verbatim: true });
  } catch (error) {
    throw new Error(`DNS lookup failed: ${error?.code || error?.message || error}`);
  }
  if (!Array.isArray(answers) || !answers.length ||
      answers.some(answer => !isPublicAddress(answer?.address))) {
    throw new UnsafeVideoUrl('DNS resolved to a non-public address');
  }
  return answers[0];
}

function createPublicRequester({ lookup = dns.lookup, request = https.request } = {}) {
  async function once(url, { method, headers, timeoutMs, maxBytes, readBody }) {
    // The URL is checked before DNS, and every DNS answer is checked before
    // using a pinned address in the socket lookup. This avoids DNS rebinding
    // between the safety check and the actual connection.
    const address = await resolvePublicHost(url.hostname, lookup);
    return new Promise((resolve, reject) => {
      let settled = false;
      const finish = (error, result) => {
        if (settled) return;
        settled = true;
        if (error) reject(error);
        else resolve(result);
      };
      const req = request(url, {
        method, headers, timeout: timeoutMs, family: address.family,
        lookup: (_host, _options, callback) => callback(null, address.address, address.family)
      }, response => {
        const base = { status: response.statusCode || 0, headers: response.headers || {} };
        if (!readBody || (base.status >= 300 && base.status < 400)) {
          finish(null, { ...base, body: '' });
          response.destroy();
          return;
        }
        const chunks = [];
        let size = 0;
        response.on('data', chunk => {
          size += chunk.length;
          if (size > maxBytes) {
            finish(new Error('Response exceeds size limit'));
            response.destroy();
          } else chunks.push(chunk);
        });
        response.on('end', () => finish(null, { ...base, body: Buffer.concat(chunks).toString('utf8') }));
        response.on('error', error => finish(error));
      });
      req.on('timeout', () => req.destroy(new Error('timeout')));
      req.on('error', error => finish(error));
      req.end();
    });
  }

  return async function requestPublicHttps(raw, options = {}) {
    const method = options.method || 'GET';
    const timeoutMs = options.timeoutMs || 8000;
    const maxBytes = options.maxBytes || 3_000_000;
    const readBody = options.readBody === true;
    let url = assertPublicHttpsUrl(raw);
    const visited = new Set();
    for (let hop = 0; hop <= 4; hop += 1) {
      if (visited.has(url.href)) throw new UnsafeVideoUrl('Redirect loop');
      visited.add(url.href);
      const result = await once(url, { method, timeoutMs, maxBytes, readBody, headers: options.headers || {} });
      if (result.status < 300 || result.status >= 400 || !result.headers.location) {
        return { ...result, url: url.href, ok: result.status >= 200 && result.status < 300 };
      }
      url = assertPublicHttpsUrl(new URL(result.headers.location, url).href);
    }
    throw new UnsafeVideoUrl('Too many redirects');
  };
}

module.exports = { UnsafeVideoUrl, isPublicAddress, assertPublicHttpsUrl, resolvePublicHost, createPublicRequester };
