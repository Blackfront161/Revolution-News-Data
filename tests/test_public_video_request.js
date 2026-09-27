'use strict';

const assert = require('node:assert/strict');
const { EventEmitter } = require('node:events');
const { PassThrough } = require('node:stream');
const {
  UnsafeVideoUrl, isPublicAddress, assertPublicHttpsUrl,
  resolvePublicHost, createPublicRequester
} = require('../scripts/public_video_request.js');

assert.equal(isPublicAddress('169.254.169.254'), false);
assert.equal(isPublicAddress('127.0.0.1'), false);
assert.equal(isPublicAddress('10.2.3.4'), false);
assert.equal(isPublicAddress('192.168.1.1'), false);
assert.equal(isPublicAddress('::1'), false);
assert.equal(isPublicAddress('fe80::1'), false);
assert.equal(isPublicAddress('::ffff:169.254.169.254'), false);
assert.equal(isPublicAddress('93.184.216.34'), true);
assert.equal(isPublicAddress('2606:4700:4700::1111'), true);

for (const url of [
  'http://169.254.169.254/latest/meta-data/iam/security-credentials/x.mp4',
  'https://169.254.169.254/latest/meta-data/iam/security-credentials/x.mp4',
  'https://[::1]/latest/meta-data/iam/security-credentials/x.mp4',
  'https://[fe80::1]/video.mp4',
  'https://localhost/video.mp4', 'https://metadata.internal/video.mp4',
  'https://user:secret@media.example.org/video.mp4',
  'https://media.example.org:8443/video.mp4'
]) assert.throws(() => assertPublicHttpsUrl(url), UnsafeVideoUrl);

function fakeTransport(location, calls, pinnedAddresses) {
  return (url, options, onResponse) => {
    calls.push(url.href);
    options.lookup(url.hostname, {}, (_error, address) => pinnedAddresses.push(address));
    const req = new EventEmitter();
    req.end = () => process.nextTick(() => {
      const response = new PassThrough();
      response.statusCode = location ? 302 : 200;
      response.headers = location ? { location } : {};
      onResponse(response);
      response.end();
    });
    req.destroy = error => req.emit('error', error);
    return req;
  };
}

(async () => {
  const publicAnswer = async () => [{ address: '93.184.216.34', family: 4 }];
  await assert.rejects(
    resolvePublicHost('media.example.org', async () => [{ address: '169.254.169.254', family: 4 }]),
    UnsafeVideoUrl
  );
  await assert.rejects(
    resolvePublicHost('media.example.org', async () => [
      { address: '93.184.216.34', family: 4 },
      { address: '10.0.0.1', family: 4 }
    ]),
    UnsafeVideoUrl
  );

  for (const location of [
    'http://169.254.169.254/latest/meta-data/',
    'https://169.254.169.254/latest/meta-data/',
    'https://localhost/latest/meta-data/'
  ]) {
    const calls = [];
    const pins = [];
    const requester = createPublicRequester({
      lookup: publicAnswer,
      request: fakeTransport(location, calls, pins)
    });
    await assert.rejects(requester('https://media.example.org/video.mp4'), UnsafeVideoUrl);
    assert.equal(calls.length, 1, 'redirect target must never be connected');
    assert.deepEqual(pins, ['93.184.216.34']);
  }

  let lookups = 0;
  const calls = [];
  const pins = [];
  const requester = createPublicRequester({
    lookup: async host => {
      lookups += 1;
      return [{ address: host === 'private.example.org' || lookups > 2
        ? '169.254.169.254' : '93.184.216.34', family: 4 }];
    },
    request: fakeTransport('https://private.example.org/secret', calls, pins)
  });
  await assert.rejects(requester('https://media.example.org/video.mp4'), UnsafeVideoUrl);
  assert.equal(calls.length, 1, 'private DNS redirect must be rejected before connection');
  assert.deepEqual(pins, ['93.184.216.34']);
  assert.equal(lookups, 2, 'each hop gets exactly one safety lookup');

  const stableCalls = [];
  const stablePins = [];
  let rebindingLookups = 0;
  const stableRequester = createPublicRequester({
    lookup: async () => {
      rebindingLookups += 1;
      return [{ address: rebindingLookups === 1 ? '93.184.216.34' : '169.254.169.254', family: 4 }];
    },
    request: fakeTransport('', stableCalls, stablePins)
  });
  const result = await stableRequester('https://media.example.org/video.mp4', { method: 'HEAD' });
  assert.equal(result.ok, true);
  assert.equal(rebindingLookups, 1);
  assert.deepEqual(stablePins, ['93.184.216.34'], 'socket must use the vetted address');
  console.log('Public video requests reject private URLs, DNS and redirects: OK');
})().catch(error => { console.error(error); process.exitCode = 1; });
