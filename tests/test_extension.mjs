import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const context = vm.createContext({URL, chrome: {runtime: {onMessage: {addListener() {}}}}, console});
vm.runInContext(fs.readFileSync(new URL('../extension/background.js', import.meta.url), 'utf8'), context);
test('worker accepts only intended page origins and excludes messages', () => {
  assert.equal(context.allowedSender('https://x.com/home'), true);
  assert.equal(context.allowedSender('https://x.com/messages/123'), false);
  assert.equal(context.allowedSender('https://evil.example/'), false);
  assert.equal(context.allowedSender('http://127.0.0.1:8000/feed'), true);
  assert.equal(context.allowedSender('http://127.0.0.1:8000/docs'), false);
});
test('image retrieval cannot act as an arbitrary URL fetcher', () => {
  assert.equal(context.allowedImage('https://pbs.twimg.com/media/example.jpg'), true);
  assert.equal(context.allowedImage('http://169.254.169.254/latest/meta-data/'), false);
  assert.equal(context.allowedImage('https://pbs.twimg.com.evil.example/media/a.jpg'), false);
  assert.equal(context.allowedImage('http://127.0.0.1:8000/api/investigations'), false);
});
test('manifest does not ask for tabs, history, cookies or all-host access', () => {
  const manifest = JSON.parse(fs.readFileSync(new URL('../extension/manifest.json', import.meta.url), 'utf8'));
  assert.deepEqual(manifest.permissions, ['storage']);
  assert.equal(manifest.host_permissions.includes('<all_urls>'), false);
});
