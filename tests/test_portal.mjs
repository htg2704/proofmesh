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
  h.w.document.getElementById('match-button').click(); await h.settle();
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

test('completed deep-linked job is read once, becomes a report URL and does not restart polling',async()=>{
  const id='a'.repeat(64), dom=new JSDOM(read('web/index.html'),{url:'https://proofmesh.example/?job='+id,runScripts:'outside-only'}), w=dom.window;
  let jobs=0,reads=0;
  w.fetch=async path=>{
    if(path==='/api/health')return {ok:true,json:async()=>({live_enabled:true,authentication_required:false})};
    if(path==='/api/jobs/'+id){jobs++;if(jobs>2)throw new Error('Polling loop');return {ok:true,json:async()=>({status:'succeeded',report_id:report.id,reused:false,model_calls:3})};}
    if(path==='/api/investigations/'+report.id){reads++;return {ok:true,json:async()=>report};}
    return {ok:true,json:async()=>({reports:[]})};
  };
  w.sessionStorage.setItem('proofmesh-job',id);
  w.eval(read('web/app.js'));
  for(let i=0;i<10;i++)await tick();
  assert.equal(jobs,1);assert.equal(reads,1);
  assert.equal(new URL(w.location.href).searchParams.get('job'),null);
  assert.equal(new URL(w.location.href).searchParams.get('report'),report.id);
  assert.equal(w.sessionStorage.getItem('proofmesh-job'),null);
  assert.match(w.document.getElementById('notice').textContent,/Investigation complete/);
  w.close();
});

test('private reviewer link exchanges its code for a session and removes the credential fragment',async()=>{
 const code='review-code-abcdefghijklmnopqrstuvwxyz',dom=new JSDOM(read('web/index.html'),{url:'https://proofmesh.example/#review='+code,runScripts:'outside-only'}),w=dom.window,requests=[];
 w.fetch=async(path,options)=>{requests.push({path,options});if(path==='/api/health')return {ok:true,json:async()=>({live_enabled:true,authentication_required:true,access:'review'})};return {ok:true,json:async()=>({access:'review',reports:[]})};};
 w.eval(read('web/app.js'));for(let i=0;i<10;i++)await tick();
 const exchange=requests.find(r=>r.path==='/api/access/reviewer');assert.equal(JSON.parse(exchange.options.body).code,code);
 assert.equal(w.location.hash,'');assert.equal(w.sessionStorage.getItem('proofmesh-token'),null);
 assert.equal(w.document.getElementById('corpus').value,'review');assert.match(w.document.getElementById('connection').textContent,/Review workspace/);
 w.close();
});

test('a new failed investigation clears the previously displayed report',async()=>{
 const h=harness();await h.settle();
 h.w.document.getElementById('demo-button').click();await h.settle();
 assert.match(h.w.document.getElementById('result').textContent,/No evidence available/);
 h.w.fetch=async path=>({ok:true,json:async()=>path==='/api/jobs'?{id:'c'.repeat(64)}:{status:'failed',attempt:1,error:'Model capacity temporarily unavailable'}});
 h.w.document.getElementById('corpus').value='live';
 h.w.document.getElementById('investigate-button').click();await h.settle();
 assert.doesNotMatch(h.w.document.getElementById('result').textContent,/No evidence available/);
 assert.match(h.w.document.getElementById('notice').textContent,/capacity/);
 h.w.close();
});

test('a visitor starts work without entering a reviewer code or developer key',async()=>{
 const dom=new JSDOM(read('web/index.html'),{url:'https://proofmesh.example/',runScripts:'outside-only'}),w=dom.window,paths=[];
 w.fetch=async(path,options)=>{paths.push(path);if(path==='/api/health')return {ok:true,json:async()=>({live_enabled:true,authentication_required:true,access:'none'})};if(path==='/api/access/guest')return {ok:true,json:async()=>({access:'client'})};if(path==='/api/jobs')return {ok:true,json:async()=>({id:'c'.repeat(64)})};if(path.startsWith('/api/jobs/'))return {ok:true,json:async()=>({status:'succeeded',report_id:report.id,model_calls:0,reused:true})};if(path.startsWith('/api/investigations/'))return {ok:true,json:async()=>report};return {ok:true,json:async()=>({reports:[]})};};
 w.eval(read('web/app.js'));for(let i=0;i<6;i++)await tick();
 w.document.getElementById('claim').value='A visitor supplied claim';w.document.getElementById('investigate-button').click();for(let i=0;i<12;i++)await tick();
 assert.ok(paths.indexOf('/api/access/guest')<paths.indexOf('/api/jobs'));
 assert.match(w.document.getElementById('notice').textContent,/Investigation complete/);
 assert.equal(w.document.getElementById('review-access').hidden,true);assert.equal(w.sessionStorage.getItem('proofmesh-token'),null);w.close();
});

test('source-reported AI generation and absent forensic testing are displayed separately',async()=>{
 const h=harness();await h.settle();const r={...report,corpus:'live',evidence_policy:'0.6',origin:{status:'reported_ai_generated',image_binding:'partial',source_reporting:{classification:'reported_ai_generated',explanation:'Published fact-check coverage reports AI generation.',evidence_quotes:[{evidence_id:'E1',quote:'The circulated selfie is AI-generated.'}]}},assessment:{...report.assessment,limitations:[]}};
 h.w.fetch=async()=>({ok:true,json:async()=>({claim:r.claim,image_base64:'c3ludGhldGlj',report:r,reports:[]})});h.w.document.getElementById('demo-button').click();await h.settle();
 const text=h.w.document.getElementById('result').textContent;assert.match(text,/Sources report: AI-generated/);assert.match(text,/Independent watermark \/ provenance verification: not performed/);assert.doesNotMatch(text,/Media origin remains unknown/);h.w.close();
});

test('the pasted legacy validation failure is shown as processing failure, not ambiguous evidence',async()=>{
 const h=harness();await h.settle();const r={...report,corpus:'live',events:[{stage:'citation_validation',detail:'Assessment downgraded: exact source support failed.'}],assessment:{...report.assessment,summary:'The claim remains unresolved because its source quotations could not be verified.'}};
 h.w.fetch=async()=>({ok:true,json:async()=>({claim:r.claim,image_base64:'c3ludGhldGlj',report:r,reports:[]})});h.w.document.getElementById('demo-button').click();await h.settle();
 const text=h.w.document.getElementById('result').textContent;assert.match(text,/processing failure/);assert.match(text,/Not assessed · citation error/);assert.doesNotMatch(h.w.document.querySelector('.report-summary').textContent,/claim remains unresolved/);h.w.close();
});

test('personal Gemini key is memory-only, sent only to new jobs and clearable',async()=>{
 const h=harness();await h.settle();const w=h.w,d=w.document,key='AIza-personal-browser-test-key';
 w.fetch=async(path,options)=>{h.requests.push({path,options});if(path==='/api/jobs')return {ok:true,json:async()=>({id:'e'.repeat(64)})};if(path.startsWith('/api/jobs/'))return {ok:true,json:async()=>({status:'succeeded',report_id:report.id,model_calls:3})};if(path.startsWith('/api/investigations/'))return {ok:true,json:async()=>report};return {ok:true,json:async()=>({reports:[],report:null,related:[],status:'unknown'})};};
 d.getElementById('use-gemini-key').disabled=false;
 d.getElementById('gemini-key').value=key;d.getElementById('use-gemini-key').click();
 assert.equal(d.getElementById('gemini-key').value,'');assert.equal(w.sessionStorage.length,0);assert.equal(w.localStorage.length,0);
 d.getElementById('claim').value='A browser personal key claim';
 d.getElementById('match-button').click();await h.settle();
 const lookup=h.requests.find(r=>r.path==='/api/matches');assert.ok(!lookup.options.body.includes(key));
 d.getElementById('investigate-button').click();await h.settle();
 const posted=h.requests.filter(r=>r.path==='/api/jobs');assert.equal(JSON.parse(posted[0].options.body).provider_api_key,key);
 assert.ok(h.requests.every(r=>!r.path.includes(key)));
 assert.ok(!JSON.stringify({...w.sessionStorage}).includes(key));
 d.getElementById('clear-gemini-key').click();d.getElementById('claim').value='Another browser check without key';
 d.getElementById('investigate-button').click();await h.settle();
 const last=h.requests.filter(r=>r.path==='/api/jobs').at(-1);assert.equal(JSON.parse(last.options.body).provider_api_key,undefined);
 assert.match(d.getElementById('gemini-key-status').textContent,/cleared/);w.close();
});

test('primary form submission investigates and lookup miss explains the exact blocker',async()=>{
 const h=harness();await h.settle();const w=h.w,d=w.document;
 assert.equal(d.getElementById('investigate-button').type,'submit');assert.ok(d.getElementById('investigate-button').classList.contains('primary'));
 assert.equal(d.getElementById('match-button').type,'button');assert.ok(d.getElementById('investigate-button').compareDocumentPosition(d.getElementById('match-button')) & w.Node.DOCUMENT_POSITION_FOLLOWING);
 d.getElementById('claim').value='A claim that needs an investigation';
 w.fetch=async(path,options)=>{h.requests.push({path,options});if(path==='/api/jobs')return {ok:true,json:async()=>({id:'f'.repeat(64)})};if(path.startsWith('/api/jobs/'))return {ok:true,json:async()=>({status:'succeeded',report_id:report.id,model_calls:3})};if(path.startsWith('/api/investigations/'))return {ok:true,json:async()=>report};if(path==='/api/matches')return {ok:true,json:async()=>({status:'related_media',report:null,related:[{id:'a'.repeat(64),claim:'A previous claim',reuse_blockers:['assessment_policy_changed','publication_time_changed']}]})};return {ok:true,json:async()=>({reports:[],size:0,capacity:200})};};
 d.getElementById('investigation-form').dispatchEvent(new w.Event('submit',{cancelable:true}));await h.settle();
 const job=h.requests.find(r=>r.path==='/api/jobs');assert.ok(job);assert.equal(JSON.parse(job.options.body).share_publicly,true);
 d.getElementById('share-publicly').checked=false;d.getElementById('match-button').click();await h.settle();
 const text=d.getElementById('result').textContent;assert.match(text,/Not assessed for this context/);assert.match(text,/older assessment policy/);assert.match(text,/publication time differs/);assert.doesNotMatch(text,/Unverified/);
 const start=[...d.querySelectorAll('#result button')].find(b=>b.textContent==='Start investigation for this context');assert.ok(start);start.click();await h.settle();
 const last=h.requests.filter(r=>r.path==='/api/jobs').at(-1);assert.equal(JSON.parse(last.options.body).share_publicly,false);w.close();
});

test('public registry browsing is accessible without a private workspace and report links use its public endpoint',async()=>{
 const dom=new JSDOM(read('web/index.html'),{url:'https://proofmesh.example/?public_report='+report.id,runScripts:'outside-only'}),w=dom.window,paths=[];
 w.fetch=async(path,options)=>{paths.push(path);if(path==='/api/health')return {ok:true,json:async()=>({authentication_required:true,access:'none',live_enabled:true,client_daily_jobs:10,client_requests_per_minute:120})};if(path.startsWith('/api/registry?'))return {ok:true,json:async()=>({reports:[{...report,corpus:'public',public_registry:true}],size:1,capacity:200})};if(path==='/api/registry/'+report.id)return {ok:true,json:async()=>({...report,corpus:'public',public_registry:true})};return {ok:true,json:async()=>({reports:[]})};};
 w.eval(read('web/app.js'));for(let i=0;i<10;i++)await tick();
 assert.match(w.document.getElementById('registry-capacity').textContent,/1 \/ 200/);
 assert.match(w.document.getElementById('result').textContent,/Public registry/);
 assert.ok(paths.includes('/api/registry/'+report.id));assert.ok(!paths.includes('/api/access/guest'));w.close();
});

test('judge entry is discoverable and info popovers state client limits and judge exemptions',async()=>{
 const h=harness();await h.settle();const d=h.w.document;
 d.getElementById('open-judge-access').click();assert.equal(d.getElementById('access-settings').open,true);assert.equal(d.activeElement.id,'token');
 h.w.fetch=async path=>({ok:true,json:async()=>path==='/api/health'?{access:'judge',authentication_required:true,rate_limits_exempt:true,client_daily_jobs:10,client_requests_per_minute:120,personal_gemini_key_enabled:true}:{reports:[],size:0,capacity:200}});
 d.getElementById('token').value='judge-fixture-not-a-real-key';d.getElementById('save-token').click();await h.settle();
 assert.match(d.getElementById('connection').textContent,/Judge workspace/);
 assert.match(d.getElementById('trial-limits').textContent,/Judge access.*waived/);
 assert.match(d.getElementById('investigate-help').textContent,/10 new investigations/);assert.match(d.getElementById('investigate-help').textContent,/120 API requests/);assert.match(d.getElementById('investigate-help').textContent,/judge\/team tester access is exempt/);
 assert.match(d.getElementById('match-help').textContent,/120 API requests/);h.w.close();
});

test('extension public job handoff opens a published report without using a different workspace credential',async()=>{
 const id='a'.repeat(64),dom=new JSDOM(read('web/index.html'),{url:'https://proofmesh.example/?public_job='+id,runScripts:'outside-only'}),w=dom.window,paths=[];
 w.fetch=async path=>{paths.push(path);if(path==='/api/health')return {ok:true,json:async()=>({authentication_required:true,access:'none',live_enabled:true,client_daily_jobs:10,client_requests_per_minute:120})};if(path==='/api/public-jobs/'+id)return {ok:true,json:async()=>({status:'succeeded',public_report_id:report.id,model_calls:3,reused:false})};if(path==='/api/registry/'+report.id)return {ok:true,json:async()=>({...report,corpus:'public',public_registry:true})};return {ok:true,json:async()=>({reports:[],size:0,capacity:200})};};
 w.eval(read('web/app.js'));for(let i=0;i<15;i++)await tick();
 assert.ok(paths.includes('/api/public-jobs/'+id));assert.ok(!paths.some(p=>p.startsWith('/api/jobs/')));
 assert.equal(new URL(w.location.href).searchParams.get('public_report'),report.id);
 assert.equal(new URL(w.location.href).searchParams.get('public_job'),null);
 assert.match(w.document.getElementById('notice').textContent,/Shared investigation complete/);w.close();
});
