import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {JSDOM} from 'jsdom';

const read = name => fs.readFileSync(new URL(`../${name}`, import.meta.url),'utf8');
const tick = () => new Promise(resolve=>setImmediate(resolve));
const report = {id:'b'.repeat(64),claim:'A synthetic unresolved claim.',corpus:'demo',created_at:'2026-10-15T00:00:00Z',expires_at:'2026-10-16T00:00:00Z',origin:{status:'unknown',explanation:'No detector ran.'},assessment:{summary:'No evidence available.',findings:[{claim:'A synthetic unresolved claim.',status:'unresolved',explanation:'No supporting evidence.',evidence_ids:[]}],limitations:['Synthetic fixture.']},evidence:[],events:[],model_calls:0};

function harness({auth=false, offline=false, bitmap}={}) {
  const dom=new JSDOM(read('web/index.html'),{url:'http://127.0.0.1:8000/',runScripts:'outside-only'}), w=dom.window, requests=[];
  w.createImageBitmap=bitmap || (async()=>({width:960,height:540,close(){}}));
  w.fetch=async(path,options)=>{
    if(offline) throw new TypeError('network failed');
    requests.push({path,options});
    if(path==='/api/health') return {ok:true,json:async()=>({live_enabled:false,authentication_required:auth})};
    if(auth && options.headers.Authorization!=='Bearer good-test-token') return {ok:false,json:async()=>({detail:'API token required'})};
    if(path==='/api/demo') return {ok:true,json:async()=>({claim:'A synthetic claim about a bridge.',alternate_claim:'A different bridge caption.',image_base64:'c3ludGhldGlj',report})};
    if((path==='/api/matches'||path==='/api/demo/matches')) return {ok:true,json:async()=>({status:'unknown',report:null,related:[]})};
    return {ok:true,json:async()=>({reports:[report]})};
  };
  w.eval(read('web/app.js'));
  return {dom,w,requests,settle:async()=>{for(let i=0;i<5;i++)await tick();},file:value=>{const input=w.document.getElementById('image');Object.defineProperty(input,'files',{value:[value],configurable:true});input.dispatchEvent(new w.Event('change'));}};
}

test('oversized replacement clears both preview and submitted image identity',async()=>{
  const h=harness(); await h.settle(); h.w.document.getElementById('demo-button').click(); await h.settle();
  assert.equal(h.w.document.getElementById('image-wrap').hidden,false);
  h.file({size:5_000_001,type:'image/png'}); await h.settle();
  assert.equal(h.w.document.getElementById('image-wrap').hidden,true);
  h.w.document.getElementById('investigation-form').dispatchEvent(new h.w.Event('submit',{cancelable:true})); await h.settle();
  const request=h.requests.find(r=>r.path==='/api/demo/matches');
  assert.equal(JSON.parse(request.options.body).image_base64,null); h.w.close();
});
test('pixel limit rejects an image before base64 submission',async()=>{
  const h=harness({bitmap:async()=>({width:4100,height:4100,close(){}})}); await h.settle();
  h.file({size:1000,type:'image/png'}); await h.settle();
  assert.match(h.w.document.getElementById('notice').textContent,/16 megapixels/);
  assert.equal(h.w.document.getElementById('image-wrap').hidden,true);
  assert.equal(h.w.document.getElementById('match-button').disabled,false); h.w.close();
});
test('successful token correction replaces the old authentication error',async()=>{
  const h=harness({auth:true}); await h.settle();
  const input=h.w.document.getElementById('token'),button=h.w.document.getElementById('save-token');
  input.value='bad-test-token'; button.click(); await h.settle(); assert.equal(h.w.document.getElementById('notice').textContent,'API token required');
  input.value='good-test-token'; button.click(); await h.settle(); assert.match(h.w.document.getElementById('notice').textContent,/Connected/);
  assert.equal(input.value,''); h.w.close();
});
test('offline startup is understandable and unresolved records have no invented sources',async()=>{
  const offline=harness({offline:true}); await offline.settle(); assert.match(offline.w.document.getElementById('notice').textContent,/Cannot reach ProofMesh/); offline.w.close();
  const h=harness(); await h.settle(); h.w.document.querySelector('#registry-list button').click(); await h.settle();
  assert.match(h.w.document.getElementById('result').textContent,/unresolved/);
  assert.match(h.w.document.getElementById('result').textContent,/No source-linked evidence available/);
  assert.equal(h.w.document.querySelectorAll('#result .source-card a').length,0); h.w.close();
});
