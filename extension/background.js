const API = 'http://127.0.0.1:8000';
function allowedSender(url) {
  try { const u = new URL(url); return !u.username && !u.password && ((u.protocol === 'https:' && u.hostname === 'x.com' && !/^\/(?:messages|settings|compose|login|logout|account)(?:\/|$)|^\/i\/(?:chat|flow|account)(?:\/|$)/.test(u.pathname)) || (u.origin === API && u.pathname === '/feed')); } catch { return false; }
}
function allowedImage(url) {
  try { const u = new URL(url); return (u.protocol === 'https:' && u.hostname === 'pbs.twimg.com' && u.pathname.startsWith('/media/')) || (u.origin === API && u.pathname === '/fixtures/bridge.png'); } catch { return false; }
}
async function imageBytes(url) {
  if (!url) return null;
  if (!allowedImage(url)) throw new Error('Unsupported image host; open the portal to upload this image.');
  const response = await fetch(url, { credentials: 'omit', redirect: 'error', signal:AbortSignal.timeout(12_000) });
  if (!response.ok || !/^image\/(png|jpeg|webp)/.test(response.headers.get('content-type') || '')) throw new Error('Image unavailable.');
  const reader = response.body.getReader(); const chunks = []; let length = 0;
  while (true) { const { done, value } = await reader.read(); if (done) break; length += value.length; if (length > 5_000_000) { await reader.cancel(); throw new Error('Image exceeds 5 MB.'); } chunks.push(value); }
  let binary = ''; for (const chunk of chunks) { for (let offset = 0; offset < chunk.length; offset += 16384) binary += String.fromCharCode(...chunk.subarray(offset, offset + 16384)); }
  return btoa(binary);
}
async function handle(message, sender) {
  if (!allowedSender(sender.url) || (sender.tab?.url && !allowedSender(sender.tab.url)) || !['match', 'investigate'].includes(message.type)) throw new Error('Request not allowed.');
  const settings = await chrome.storage.local.get(['enabled', 'apiToken']);
  if (!settings.enabled) throw new Error('ProofMesh is paused.');
  if (typeof message.claim !== 'string' || message.claim.trim().length < 5 || message.claim.length > 3000) throw new Error('No supported claim found.');
  const corpus = new URL(sender.url).origin === API ? 'demo' : 'live';
  const body = { claim: message.claim, image_base64: await imageBytes(message.imageUrl), corpus };
  const headers = { 'Content-Type': 'application/json' };
  if (settings.apiToken) headers.Authorization = `Bearer ${settings.apiToken}`;
  let response;
  try { response = await fetch(`${API}/api/${message.type === 'match' ? 'matches' : 'investigations'}`, { method: 'POST', headers, body: JSON.stringify(body), signal:AbortSignal.timeout(message.type === 'match' ? 12_000 : 180_000) }); }
  catch { throw new Error('Cannot reach the local server. Start ProofMesh and retry.'); }
  let data;
  try { data = await response.json(); } catch { throw new Error('The local server returned an unreadable response.'); }
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Request failed.');
  return data;
}
chrome.runtime.onMessage.addListener((message, sender, reply) => { handle(message, sender).then(data => reply({ data }), error => reply({ error: error.message })); return true; });
