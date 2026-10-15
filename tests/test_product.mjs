import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {JSDOM} from 'jsdom';
import vm from 'node:vm';

const root = new URL('../', import.meta.url);
const source = name => fs.readFileSync(new URL(name, root), 'utf8');
const legacy = (text = 'A bridge illustration from the archive.', image = '/fixtures/bridge.png') => `<article data-testid="tweet"><div data-testid="tweetText">${text}</div><div data-testid="tweetPhoto"><img src="${image}"></div></article>`;
const modern = `<article><img src="https://pbs.twimg.com/profile_images/avatar.jpg"><a href="/Example/status/123456789">1h</a><div dir="auto" class="text-body whitespace-pre-wrap">A mission launched on 12 October 2026.</div><img src="https://pbs.twimg.com/media/example?format=webp&amp;name=large"><a aria-label="View media" href="/Example/status/123456789/photo/1"></a></article>`;
const tick = () => new Promise(resolve => setImmediate(resolve));

function extraction(html, url = 'https://x.com/Example') {
  const dom = new JSDOM(html, {url, runScripts:'outside-only'});
  dom.window.eval(source('extension/core.js'));
  return {dom, result:dom.window.ProofMeshCore.extractPost(dom.window.document.querySelector('article'), url)};
}

function harness(html, respond = async () => ({data:{status:'unknown', report:null, related:[]}})) {
  const dom = new JSDOM(html, {url:'http://127.0.0.1:8000/feed', runScripts:'outside-only', pretendToBeVisual:true});
  const w = dom.window, timers = new Map(), calls = []; let timerId = 0, changed, clock = 1_000_000;
  w.Date.now = () => clock;
  w.setTimeout = fn => { timers.set(++timerId, fn); return timerId; };
  w.clearTimeout = id => timers.delete(id);
  w.setInterval = () => 1;
  w.HTMLElement.prototype.getBoundingClientRect = () => ({top:10,bottom:200});
  w.IntersectionObserver = class {observe() {} unobserve() {}};
  w.chrome = {storage:{local:{get:async()=>({enabled:true})},onChanged:{addListener:fn=>changed=fn}}, runtime:{sendMessage:message=>{calls.push(message); return respond(message);}}};
  w.eval(source('extension/core.js')); w.eval(source('extension/content.js'));
  async function flush() { for (let i=0;i<30;i++) { await tick(); if (!timers.size) {await tick(); if (!timers.size) return;} const pending=[...timers.values()]; timers.clear(); pending.forEach(fn=>fn()); } throw new Error('Content script did not settle'); }
  return {dom,w,calls,flush,change:value=>changed({enabled:{newValue:value}},'local'),advance:value=>clock+=value};
}

test('current public X markup extracts caption and media, excluding avatar', () => {
  const {dom,result} = extraction(modern);
  assert.equal(result.kind,'post'); assert.equal(result.claim,'A mission launched on 12 October 2026.');
  assert.equal(result.imageUrl,'https://pbs.twimg.com/media/example?format=webp&name=large');
  assert.equal(result.postId,'123456789'); dom.window.close();
});
test('legacy fixture resolves relative image URLs for the worker', () => {
  const {dom,result}=extraction(legacy(), 'http://127.0.0.1:8000/feed');
  assert.equal(result.imageUrl,'http://127.0.0.1:8000/fixtures/bridge.png'); dom.window.close();
});
test('quoted content cannot be merged into its parent caption', () => {
  const html=modern.replace('</article>','<a href="/Other/status/987654321">Quote</a><div dir="auto" class="whitespace-pre-wrap">Another claim</div></article>');
  const {dom,result}=extraction(html); assert.equal(result.kind,'unsupported'); assert.match(result.reason,/Quoted/); dom.window.close();
});
test('gallery and video posts remain explicitly unverified', () => {
  for (const suffix of ['<img src="https://pbs.twimg.com/media/second.jpg">','<video></video>']) {
    const {dom,result}=extraction(modern.replace('</article>',suffix+'</article>')); assert.equal(result.kind,'unsupported'); dom.window.close();
  }
});
test('private pages and relative-time X captions do not receive automatic verdict reuse', () => {
  for (const url of ['https://x.com/messages/123','https://x.com/i/chat/123','https://x.com/settings/account']) {
    const {dom,result}=extraction(modern,url); assert.equal(result.kind,'excluded'); dom.window.close();
  }
  const {dom,result}=extraction(modern.replace('A mission launched on 12 October 2026.','This event happened today.'));
  assert.match(result.reason,/publication-context/); dom.window.close();
});
test('same image with different caption keeps separate extension assessments', async () => {
  const h=harness(legacy('Original archive claim.')+legacy('A different caption about that image.'), async message=>({data:message.claim.startsWith('Original') ? {status:'exact_context',report:{id:'a'.repeat(64),corpus:'demo'}} : {status:'related_media',report:null,related:[{id:'a'.repeat(64)}]}}));
  await h.flush(); const posts=h.w.document.querySelectorAll('article');
  assert.match(posts[0].textContent,/existing investigation available/);
  assert.match(posts[1].textContent,/different claim — unverified/);
  assert.equal(posts[1].querySelector('a[href*="report="]'),null); assert.equal(h.calls.length,2); h.w.close();
});
test('a delayed response cannot attach to a recycled post node', async () => {
  const pending=[]; const h=harness(legacy('Original archive claim.'),()=>new Promise(resolve=>pending.push(resolve)));
  await h.flush(); h.w.document.querySelector('[data-testid="tweetText"]').textContent='New claim on a recycled node.';
  await h.flush(); assert.equal(pending.length,2);
  pending[0]({data:{status:'exact_context',report:{id:'a'.repeat(64),corpus:'demo'}}});
  await h.flush(); assert.equal(h.w.document.querySelector('a[href*="report="]'),null);
  pending[1]({data:{status:'unknown',report:null,related:[]}}); await h.flush();
  assert.match(h.w.document.body.textContent,/no matching investigation — unverified/); h.w.close();
});
test('an error exposes a retry and recovers when the server returns', async () => {
  let attempt=0; const h=harness(legacy(),async()=>++attempt===1 ? {error:'Offline'} : {data:{status:'unknown',report:null,related:[]}});
  await h.flush(); assert.match(h.w.document.body.textContent,/lookup unavailable/);
  h.w.document.querySelector('.proofmesh-context button').click(); await h.flush();
  assert.equal(h.calls.length,2); assert.match(h.w.document.body.textContent,/no matching investigation — unverified/); h.w.close();
});
test('disable removes indicators and ignores pending responses', async () => {
  let finish; const h=harness(legacy(),()=>new Promise(resolve=>finish=resolve)); await h.flush();
  h.change(false); await h.flush(); finish({data:{status:'exact_context',report:{id:'a'.repeat(64),corpus:'demo'}}}); await h.flush();
  assert.equal(h.w.document.querySelector('.proofmesh-context'),null); assert.equal(h.calls.length,1); h.w.close();
});
test('SPA navigation to direct messages clears indicators and stops new lookups', async () => {
  const h=harness(legacy()); await h.flush(); const count=h.calls.length;
  // Simulate SPA navigation without changing the test's origin.
  h.w.history.pushState({},'', '/messages'); h.w.dispatchEvent(new h.w.PopStateEvent('popstate')); await h.flush();
  assert.equal(h.w.document.querySelector('.proofmesh-context'),null); assert.equal(h.calls.length,count); h.w.close();
});
test('duplicate DOM activity does not repeat successful registry requests', async () => {
  const h=harness(legacy()); await h.flush();
  const marker=h.w.document.createElement('span'); h.w.document.body.append(marker); await h.flush();
  assert.equal(h.calls.length,1); h.w.close();
});

function worker(fetch, enabled=true) {
  const context=vm.createContext({URL,AbortSignal,btoa,fetch,chrome:{storage:{local:{get:async()=>({enabled,apiToken:'test-token'})}},runtime:{onMessage:{addListener(){}}}}});
  vm.runInContext(source('extension/background.js'),context); return context;
}
test('worker lookup sends authenticated demo JSON and makes no investigation request', async () => {
  const calls=[]; const w=worker(async(url,options)=>{calls.push({url,options}); return {ok:true,json:async()=>({status:'unknown',report:null})};});
  await w.handle({type:'match',claim:'A synthetic claim',imageUrl:null},{url:'http://127.0.0.1:8000/feed'});
  assert.equal(calls[0].url,'http://127.0.0.1:8000/api/matches'); assert.equal(calls[0].options.headers.Authorization,'Bearer test-token');
  assert.equal(JSON.parse(calls[0].options.body).corpus,'demo');
});
test('paused worker and private SPA sender cannot transmit posts', async () => {
  let requests=0; const fetch=async()=>{requests++;};
  await assert.rejects(worker(fetch,false).handle({type:'match',claim:'A private claim'},{url:'https://x.com/home'}),/paused/);
  await assert.rejects(worker(fetch).handle({type:'match',claim:'A private claim'},{url:'https://x.com/home',tab:{url:'https://x.com/i/chat/123'}}),/not allowed/);
  assert.equal(requests,0);
});
test('worker reports offline and non-JSON responses without publishing a verdict', async () => {
  const message={type:'match',claim:'A test claim',imageUrl:null},sender={url:'http://127.0.0.1:8000/feed'};
  await assert.rejects(worker(async()=>{throw new TypeError('Failed to fetch');}).handle(message,sender),/Cannot reach/);
  await assert.rejects(worker(async()=>({json:async()=>{throw new Error('html');}})).handle(message,sender),/unreadable/);
});
