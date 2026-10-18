let publicRegistryShown = 20;
let personalGeminiKey = null;
let personalKeyEnabled = false;
const $ = id => document.getElementById(id);
let imageBase64 = null;
let alternateClaim = '';
let currentReport = null;
let imageVersion = 0;
let accessRole = 'none';
let authenticationRequired = false;
function node(tag, text, className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; }
function notice(text, error = false) { $('notice').hidden = false; $('notice').textContent = text; $('notice').className = error ? 'error' : ''; }
function busy(value) { document.querySelectorAll('button, #claim, #image, #corpus, #token, #published-at, #review-code, #gemini-key, #share-publicly').forEach(b => b.disabled = value); document.querySelector('.workspace').setAttribute('aria-busy', String(value)); $('use-gemini-key').disabled=value || !personalKeyEnabled; }
async function api(path, body) {
  const headers = { 'Content-Type': 'application/json' };
  const token = sessionStorage.getItem('proofmesh-token'); if (token) headers.Authorization = `Bearer ${token}`;
  let response;
  try { response = await fetch(path, { headers, ...(body !== undefined ? { method: 'POST', body: JSON.stringify(body) } : {}) }); }
  catch { throw new Error('Cannot reach ProofMesh. Start the local server and retry.'); }
  let data;
  try { data = await response.json(); } catch { throw new Error('ProofMesh returned an unreadable response. Please retry.'); }
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Check the submitted claim and image.'); return data;
}
function payload() { return { share_publicly: $('share-publicly').checked, claim: $('claim').value, image_base64: imageBase64, corpus: $('corpus').value, published_at:$('published-at').value ? new Date($('published-at').value + 'Z').toISOString() : null }; }
function showImage(encoded, mime = 'image/png') { imageBase64 = encoded; $('image-wrap').hidden = !encoded; if (encoded) $('image-preview').src = `data:${mime};base64,${encoded}`; else $('image-preview').removeAttribute('src'); }
function safeLink(url) { try { const parsed = new URL(url, location.origin); return parsed.protocol === 'https:' || (parsed.origin === location.origin && parsed.pathname.startsWith('/fixtures/')) ? parsed.href : null; } catch { return null; } }
function renderReport(report, reused = false) {
  currentReport = report;
  const root = $('result'); root.replaceChildren();
  const legacyCitationFailure = !report.assessment_status && report.events?.some(e => e.stage === 'citation_validation' && /failed/i.test(e.detail));
  root.append(node('span', report.corpus === 'demo' ? 'Synthetic demo · not real-world evidence' : report.recorded_example ? 'Recorded live investigation · inspect the original sources' : report.public_registry ? 'Public registry · shared automated assessment' : 'Live investigation', `tag ${report.corpus === 'demo' ? 'demo' : ''}`));
  if (reused) root.append(node('span', 'Reused · 0 model calls', 'tag'));
  if (report.assessment_status === 'validation_failed' || legacyCitationFailure) root.append(node('p', 'Assessment incomplete: ProofMesh could not validate its generated citations. This is a processing failure, not a finding that the underlying evidence is inconclusive.', 'assessment-warning'));
  else if (report.assessment_status === 'partial') root.append(node('p', 'Some assessment parts were withheld after citation or review checks. Validated findings remain below.', 'assessment-warning'));
  else if (report.assessment_status === 'review_rejected') root.append(node('p', 'The review did not accept the generated assessment. Inspect the source material and review notes below.', 'assessment-warning'));
  root.append(node('h3', legacyCitationFailure ? 'The earlier assessment could not complete citation validation. Its retrieved source material is available below.' : report.assessment.summary, 'report-summary'));
  if (report.corpus !== 'demo' && report.evidence_policy !== '0.6') root.append(node('p', 'Recorded under an earlier evidence policy. Start a new investigation to use the updated assessment checks.', 'muted'));
  if (report.assessment.interpreted_claim) root.append(node('p', `Assessed proposition: ${report.assessment.interpreted_claim}`, 'muted'));
  root.append(node('p', `Investigated ${new Date(report.created_at).toLocaleString()} · ${new Date(report.expires_at) <= new Date() ? 'Archived report; check current evidence before reuse.' : 'Assessment belongs to the claim below.'}`, 'muted'));
  const reported = report.origin.source_reporting;
  if (reported) {
    const names = {reported_ai_generated:'AI-generated', reported_edited:'edited', reported_authentic:'authentic', disputed:'disputed'};
    const card=node('section', undefined, 'finding');
    card.append(node('h4', report.origin.image_binding === 'not_established' ? `Related coverage reports: ${names[reported.classification] || reported.classification}` : `Sources report: ${names[reported.classification] || reported.classification}`));
    card.append(node('p', reported.explanation));
    if (reported.image_link_explanation) card.append(node('p', reported.image_link_explanation, 'muted'));
    card.append(node('p', report.origin.image_binding === 'not_established' ? 'The source coverage has not been tied conclusively to the uploaded image.' : `Image association: ${report.origin.image_binding} match lead. This is source-based attribution, not a forensic authenticity test.`, 'muted'));
    for (const q of reported.evidence_quotes || []) card.append(node('blockquote', `${q.evidence_id}: “${q.quote}”`));
    root.append(card);
  }
  root.append(node('p', 'Independent watermark / provenance verification: not performed.', 'muted'));
  if (report.publication_context?.published_at) root.append(node('p', `Post published: ${new Date(report.publication_context.published_at).toISOString()} · Supplied UTC context, not verified capture time.`, 'muted'));
  for (const check of report.assessment.context_checks || []) {
    const card=node('section', undefined, 'finding'); card.append(node('h4', `${check.dimension.replace('_',' ')} · ${check.status}`), node('p', `Claim: ${check.claimed}`), node('p', `Evidence: ${check.observed}`));
    for (const q of check.evidence_quotes || []) card.append(node('blockquote', `${q.evidence_id}: “${q.quote}”`)); root.append(card);
  }
  for (const finding of report.assessment.findings) {
    const label = finding.assessment_issue === 'citation_validation_failed' || legacyCitationFailure ? 'Not assessed · citation error' : finding.assessment_issue === 'review_rejected' ? 'Review not accepted' : finding.status;
    const card = node('section', undefined, 'finding'); card.append(node('span', label, `tag ${finding.status}`), node('h3', finding.claim), node('p', finding.explanation));
    if (finding.evidence_ids.length) card.append(node('small', `Evidence: ${finding.evidence_ids.join(', ')}`, 'muted'));
    for (const q of finding.evidence_quotes || []) card.append(node('blockquote', `${q.evidence_id}: “${q.quote}”`));
    root.append(card);
  }
  root.append(node('h4', 'Sources & evidence', 'report-subhead'));
  if (!report.evidence.length) root.append(node('p', 'No source-linked evidence available.', 'muted'));
  for (const evidence of report.evidence) {
    const card = node('div', undefined, 'source-card'); const href = safeLink(evidence.url);
    const title = node(href ? 'a' : 'span', `${evidence.id} / ${evidence.title}`);
    if (href) { title.href = href; title.target = '_blank'; title.rel = 'noopener noreferrer'; }
    card.append(title, node('p', evidence.excerpt), node('small', ({demo_fixture:'SYNTHETIC FIXTURE', source_page_excerpt:'FETCHED SOURCE PASSAGE', image_match_lead:'IMAGE MATCH LEAD · CAPTION UNVERIFIED', search_grounded_excerpt:'SEARCH-GROUNDED MODEL SUMMARY · NOT A VERBATIM SOURCE QUOTE'})[evidence.kind] || 'SOURCE LEAD')); if (evidence.retrieved_at) card.append(node('small', `Retrieved ${new Date(evidence.retrieved_at).toLocaleString()}${evidence.page_published_at ? ' · Page date: ' + evidence.page_published_at + ' (not capture date)' : ''}`, 'muted')); root.append(card);
  }
  root.append(node('h4', 'What remains uncertain', 'report-subhead'));
  const limits = node('ul', undefined, 'limit'); [...(report.qa_notes || []), ...(report.assessment.limitations.length ? report.assessment.limitations : ['Automated assessment; source links and a second model pass do not establish independent verification.'])].forEach(t => limits.append(node('li', t))); root.append(limits);
  if (report.validation?.diagnostics?.length) {
    root.append(node('h4', 'Assessment validation notes', 'report-subhead'));
    const list=node('ul', undefined, 'limit');
    for (const item of report.validation.diagnostics) list.append(node('li', `${item.phase || 'validation'} · ${item.kind} ${item.index + 1}${item.evidence_id ? ' / ' + item.evidence_id : ''}: ${item.message}`));
    root.append(list);
  }
  const events = node('ol', undefined, 'timeline'); (report.events || []).forEach(e => events.append(node('li', `${e.stage}: ${e.detail}`))); root.append(events);
  if (report.search_attribution_html) {
    const frame = document.createElement('iframe'); frame.className = 'attribution'; frame.title = 'Google Search attribution'; frame.setAttribute('sandbox', 'allow-popups allow-popups-to-escape-sandbox');
    frame.srcdoc = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src https: data:">' + report.search_attribution_html; root.append(frame);
  }
  if (report.public_registry) {
    const link=node('a','Shareable report link (while retained in the 200-report registry)','text-button');
    link.href=`/?public_report=${encodeURIComponent(report.id)}`; root.append(link);
  } else if (report.corpus !== 'demo' && !report.recorded_example && report.assessment_status === 'complete') {
    const actions=node('section',undefined,'publication-actions');
    const publication=report.registry_publication;
    if (publication?.status === 'published') {
      const link=node('a','View the public report ↗','text-button');link.href=`/?public_report=${encodeURIComponent(publication.id)}`;actions.append(link);
      const withdraw=node('button','Remove public snapshot','text-button');withdraw.type='button';
      withdraw.addEventListener('click',()=>run(async()=>{await api(`/api/registry/${publication.id}/withdraw`,{});report.registry_publication={status:'withdrawn'};renderReport(report);await refresh();notice('Public snapshot removed. Your private report remains.');}));actions.append(withdraw);
    } else {
      if (publication?.message) actions.append(node('p',publication.message,'muted'));
      actions.append(node('p','Publish the claim, report text and evidence links for everyone to reuse. Image files and credentials stay private.','muted'));
      const publish=node('button','Publish report to shared registry','text-button');publish.type='button';
      publish.addEventListener('click',()=>run(async()=>{report.registry_publication=await api(`/api/investigations/${report.id}/publish`,{});renderReport(report);await refresh();notice('Public report published. Other users can reuse matching fresh evidence with zero model calls.');}));actions.append(publish);
    }
    root.append(actions);
  }
  const exportButton = node('button', 'Download evidence report ↓', 'text-button'); exportButton.type = 'button'; exportButton.addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })); const a = node('a'); a.href = url; a.download = `proofmesh-${report.id.slice(0, 12)}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }); root.append(exportButton);
}
function renderMatch(result) {
  if (result.report) { renderReport(result.report, true); notice('Exact image-and-claim context found. Retrieved with zero model calls.'); return; }
  const root = $('result'); root.replaceChildren(); const box = node('div', undefined, 'unknown-card');
  box.append(node('span', 'Not assessed for this context', 'tag'), node('h3', result.status === 'related_media' ? 'Related report found.' : 'No reusable report found.'), node('p', `This is a registry lookup, not a new investigation. No AI assessment was run for the context currently entered. ${result.related.length ? 'Open a related report below, or start a new investigation.' : 'Start a new investigation to research this claim.'}`)); root.append(box);
  const reasons={caption_changed:'The caption differs from the stored report.',publication_time_changed:'The supplied publication time differs from the stored report.',similar_image_only:'The image is similar, but not identical.',report_expired:'The stored report has expired.',reference_date_changed:'The report needs a fresh check for the current reference date.',assessment_policy_changed:'The stored report uses an older assessment policy.'};
  const blockers=[...new Set(result.related.flatMap(item=>item.reuse_blockers || []))];
  if(blockers.length){const list=node('ul',undefined,'reuse-reasons');for(const reason of blockers)list.append(node('li',reasons[reason] || reason));box.append(node('h4','Why automatic reuse was blocked'),list);}

  for (const item of result.related) { const button = node('button', `View related investigation: ${item.claim}`, 'text-button related-link'); button.addEventListener('click', async () => { try { renderReport(await api($('corpus').value === 'demo' ? `/api/demo/reports/${item.id}` : item.public_registry ? `/api/registry/${item.id}` : `/api/investigations/${item.id}`)); notice('Viewing a related report. Its assessment is not an assessment of your current caption.'); } catch (e) { notice(e.message, true); } }); root.append(button); }
  const investigate=node('button','Start investigation for this context','button primary');investigate.type='button';investigate.addEventListener('click',startInvestigation);box.append(investigate,node('p','New AI research uses your trial allowance or active Gemini key.','muted'));
  if (result.needs_publication_time) { notice(result.message, true); return; }
  notice(`${result.related.length} related investigation${result.related.length === 1 ? '' : 's'}. No verdict transferred. Zero model calls.`);
}
async function refreshPublicRegistry() {
  const data=await api(`/api/registry?limit=50&offset=0`);
  const reports=[...(data.reports || [])];
  for(let offset=50; offset<Math.min(publicRegistryShown,data.size || 0); offset+=50){const page=await api(`/api/registry?limit=50&offset=${offset}`);reports.push(...(page.reports || []));}
  $('registry-capacity').textContent=`${data.size ?? reports.length} / ${data.capacity || 200} public reports`;
  const root=$('public-registry-list');root.replaceChildren();
  if(!reports.length)root.append(node('p','No public reports yet. Share a completed investigation to contribute.','muted'));
  for(const report of reports.slice(0,publicRegistryShown)){
    const row=node('div',undefined,'registry-row');const button=node('button',report.claim,'text-button');
    button.addEventListener('click',()=>run(async()=>{renderReport(await api(`/api/registry/${report.id}`));notice('Viewing a public automated report. Its conclusions apply only to its recorded context.');}));
    row.append(button,node('small',`${new Date(report.expires_at)<=new Date()?'EXPIRED · FRESH CHECK NEEDED':'PUBLIC'} · ${new Date(report.created_at).toLocaleDateString()}`));root.append(row);
  }
  $('registry-more').hidden=publicRegistryShown >= (data.size || 0);
}
$('registry-more').addEventListener('click',()=>run(async()=>{publicRegistryShown+=20;await refreshPublicRegistry();}));
async function refresh() {
  try { await refreshPublicRegistry(); } catch { $('public-registry-list').replaceChildren(node('p','Public registry temporarily unavailable. Your private workspace is separate.','muted')); }

  if (authenticationRequired && accessRole === 'none' && !sessionStorage.getItem('proofmesh-token') && $('corpus').value !== 'demo') { $('registry-list').replaceChildren(node('p', 'Your investigations will appear here.', 'muted')); return; }
  const data = $('corpus').value === 'demo' ? {reports: [(await api('/api/demo', {})).report]} : await api(`/api/investigations?corpus=${accessRole === 'review' ? 'review' : $('corpus').value}`); const root = $('registry-list'); root.replaceChildren();
  if (!data.reports.length) root.append(node('p', 'No investigations in this collection yet.', 'muted'));
  for (const report of data.reports) { const row = node('div', undefined, 'registry-row'); const button = node('button', report.claim, 'text-button'); button.addEventListener('click', () => { renderReport(report); notice('Viewing a stored investigation for the claim shown in its report.'); }); row.append(button, node('small', `${report.corpus.startsWith('client:')?'PRIVATE WORKSPACE':report.corpus.toUpperCase()} · ${new Date(report.created_at).toLocaleDateString()}`)); root.append(row); }
}
async function ensureAccess() {
  if (!authenticationRequired || !['none','review'].includes(accessRole) || sessionStorage.getItem('proofmesh-token') || $('corpus').value === 'demo') return;
  const session = await api('/api/access/guest', {}); accessRole = session.access; $('connection').textContent = 'Your workspace';
}
async function run(action) { busy(true); try { await action(); } catch (e) { notice(e.message, true); } finally { busy(false); } }
async function startInvestigation() {
  if (!$('investigation-form').reportValidity()) return;
  await run(async () => { await ensureAccess(); notice('Checking for fresh evidence, then researching this context when needed. This may take a few minutes…'); const submitted={...payload(),...(personalGeminiKey?{provider_api_key:personalGeminiKey}:{})}; $('result').replaceChildren(); const job=await api('/api/jobs',submitted);delete submitted.provider_api_key; sessionStorage.setItem('proofmesh-job',job.id);await pollJob(job.id,submitted); });
}
$('investigation-form').addEventListener('submit',e=>{e.preventDefault();startInvestigation();});
$('match-button').addEventListener('click',()=>{if(!$('investigation-form').reportValidity())return;run(async()=>{await ensureAccess();notice('Searching saved reports only. No new investigation is running…');renderMatch(await api($('corpus').value==='demo'?'/api/demo/matches':'/api/matches',payload()));});});
$('demo-button').addEventListener('click', () => run(async () => { const data = await api('/api/demo', {}); $('claim').value = data.claim; $('published-at').value = ''; $('corpus').value = 'demo'; showImage(data.image_base64); alternateClaim = data.alternate_claim; $('alternate-button').hidden = false; renderReport(data.report); notice('Synthetic example loaded. Check shared evidence, then try the alternate caption.'); await refresh(); }));
$('alternate-button').addEventListener('click', () => run(async () => { $('claim').value = alternateClaim; $('corpus').value = 'demo'; renderMatch(await api($('corpus').value === 'demo' ? '/api/demo/matches' : '/api/matches', payload())); }));
$('image').addEventListener('change', async e => {
  const version = ++imageVersion; const file = e.target.files[0]; showImage(null);
  if (!file) return;
  if (file.size > 5_000_000) { notice('Choose an image smaller than 5 MB.', true); e.target.value = ''; return; }
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) { notice('Choose a PNG, JPEG or WebP image.', true); e.target.value = ''; return; }
  busy(true);
  try {
    const bitmap = await createImageBitmap(file); const pixels = bitmap.width * bitmap.height; bitmap.close();
    if (pixels > 16_000_000) throw new Error('Choose an image with no more than 16 megapixels.');
    const data = await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result).split(',')[1]); reader.onerror = () => reject(new Error('Could not read this image.')); reader.readAsDataURL(file); });
    if (version === imageVersion) { showImage(data, file.type); notice('Image ready. Check the claim when you are ready.'); }
  } catch(error) { if (version === imageVersion) { showImage(null); e.target.value = ''; notice(error.message.includes('megapixels') ? error.message : 'This file could not be decoded as an image. Choose another file.', true); } }
  finally { if (version === imageVersion) busy(false); }
});
$('remove-image').addEventListener('click', () => { imageVersion++; showImage(null); $('image').value = ''; });
async function pollJob(id, submitted = null) {
  for (let count = 0; count < 120; count++) {
    const job = await api(`/api/jobs/${encodeURIComponent(id)}`);
    notice(`Investigation ${job.status}. You can close this page and return; the job is saved.`);
    if (job.status === 'failed') {
      sessionStorage.removeItem('proofmesh-job');
      if (submitted && (job.attempt || 1) < 2) {
        const retry = node('button', 'Retry once with Google Cloud', 'text-button');
        retry.addEventListener('click', () => run(async () => { const retryBody={...submitted}; delete retryBody.provider_api_key; if(personalGeminiKey) retryBody.provider_api_key=personalGeminiKey; const next = await api('/api/jobs?retry_failed=true', retryBody); await pollJob(next.id, submitted); })); $('result').append(retry);
      }
      throw new Error(job.error || 'Investigation failed.');
    }
    if (job.status === 'succeeded') {
      renderReport(await api(`/api/investigations/${job.report_id}`), job.reused);
      sessionStorage.removeItem('proofmesh-job');
      const route = new URL(location.href); route.searchParams.delete('job'); route.searchParams.delete('demo_report'); route.searchParams.delete('public_report'); route.searchParams.set('report', job.report_id); history.replaceState(null, '', route);
      notice(`Investigation complete · ${job.model_calls} model calls.`); await refresh(); return;
    }
    await new Promise(resolve => setTimeout(resolve, 3000));
  }
  throw new Error('Investigation is taking longer than expected. Reload to check the saved job.');
}
async function loadRouteReport() { const publicId=new URLSearchParams(location.search).get('public_report'); if(publicId) renderReport(await api(`/api/registry/${encodeURIComponent(publicId)}`)); const demo = new URLSearchParams(location.search).get('demo_report'); if (demo) renderReport(await api(`/api/demo/reports/${encodeURIComponent(demo)}`)); const id = new URLSearchParams(location.search).get('report'); if (id) renderReport(await api(`/api/investigations/${encodeURIComponent(id)}`)); const job = new URLSearchParams(location.search).get('job') || sessionStorage.getItem('proofmesh-job'); if (job) await pollJob(job); }
async function connectReview(code) {
  await api('/api/access/reviewer', {code});
  sessionStorage.removeItem('proofmesh-token');
  accessRole='review'; $('review-option').hidden=false; $('corpus').value='review';
  $('review-code').value=''; $('review-status').hidden=false; $('review-status').textContent='Reviewer workspace: a separate shared evaluation collection with reserved live allowance. Your browser session lasts eight hours.';
  await refresh(); notice('Reviewer access ready. Enter a claim and optional image to run a real investigation.');
}
$('connect-review').addEventListener('click', () => run(() => connectReview($('review-code').value.trim())));
$('open-judge-access').addEventListener('click',()=>{$('access-settings').open=true;$('token').focus();$('access-settings').scrollIntoView?.({block:'center',behavior:'smooth'});});
$('save-token').addEventListener('click', () => { sessionStorage.setItem('proofmesh-token', $('token').value.trim()); $('token').value = ''; run(async () => { const health=await api('/api/health'); showLimits(health); accessRole=health.access || 'none'; if (['team','judge'].includes(accessRole)) { $('corpus').value='live'; $('connection').textContent=accessRole==='judge'?'Judge workspace · application limits waived':'Team workspace · rate limits exempt'; } await refresh(); notice('Connected. The API token is kept only for this browser session.'); await loadRouteReport(); }); });
$('refresh-button').addEventListener('click', () => run(refresh));
$('corpus').addEventListener('change', () => run(refresh));
$('gemini-key').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();$('use-gemini-key').click();}});
$('use-gemini-key').addEventListener('click', () => {
  const value=$('gemini-key').value.trim();
  if (value.length < 20 || value.length > 512) { $('gemini-key-status').textContent='Paste a complete Gemini API key (20–512 characters).'; return; }
  personalGeminiKey=value; $('gemini-key').value=''; $('clear-gemini-key').hidden=false;
  $('gemini-key-status').textContent='Your Gemini key is active for new investigations. No daily ProofMesh check cap; usage is billed to your Google account. Reloading clears the key.';
});
$('clear-gemini-key').addEventListener('click', () => {
  personalGeminiKey=null; $('gemini-key').value=''; $('clear-gemini-key').hidden=true;
  $('gemini-key-status').textContent='Using the trial allowance. Your personal Gemini key has been cleared from page memory.';
});
function showLimits(health) {
  const rpm=health.client_requests_per_minute || 120, daily=health.client_daily_jobs || 10;
  const access=health.rate_limits_exempt ? 'Your current judge/team tester access is exempt from application request and daily-check caps.' : `Your current trial access permits ${daily} new checks per UTC day and ${rpm} API requests per minute.`;
  $('investigate-help').textContent=`Research this claim with AI; an exact fresh report is reused first with zero model calls. Trial clients get ${daily} new investigations per UTC day (reset 00:00 UTC) and ${rpm} API requests/minute, including polling. ${access} Personal Gemini keys remove the daily check cap. Google quotas and approved project-funded usage limits still apply.`;
  $('match-help').textContent=`Search saved private and shared public reports only. This does not investigate a new claim or consume a new-check admission. Trial clients have ${rpm} API requests/minute. Authorized team testers and judges are exempt from application rate limits. Related images do not transfer verdicts to a different context.`;

  $('trial-limits').textContent=health.rate_limits_exempt ? `${health.access === 'judge' ? 'Judge' : 'Team tester'} access: application request and daily trial limits are waived.` : `Trial: ${health.client_daily_jobs} new investigations per client per UTC day · ${health.client_requests_per_minute} API requests/minute. Daily allowance resets at 00:00 UTC.`;
  personalKeyEnabled=Boolean(health.personal_gemini_key_enabled);
  if (!personalKeyEnabled) {
    $('use-gemini-key').disabled=true;
    $('gemini-key-status').textContent='Personal Gemini keys are not configured on this deployment. See the deployment guide to enable encryption.';
  }
}
(async () => { try { const review = new URLSearchParams(location.hash.slice(1)).get('review'); if (review) { history.replaceState(null, '', location.pathname + location.search); await connectReview(review); } const health = await api('/api/health'); showLimits(health); accessRole=health.access || 'none'; authenticationRequired=health.authentication_required; if (accessRole === 'review') { $('review-option').hidden=false; $('corpus').value='review'; $('connection').textContent='Review workspace connected'; } $('connection').textContent = accessRole === 'review' ? 'Review workspace connected' : accessRole === 'team' ? 'Team workspace · rate limits exempt' : accessRole === 'judge' ? 'Judge workspace · application limits waived' : accessRole === 'client' ? 'Your workspace' : health.live_enabled ? 'Ready to investigate' : 'Local · demo ready'; if (health.authentication_required && accessRole !== 'review' && !sessionStorage.getItem('proofmesh-token')) { $('corpus').value = 'live'; notice('Ready. Enter a claim or try an example. Your limited workspace opens automatically when you check it.'); await refresh(); await loadRouteReport(); return; } await refresh(); await loadRouteReport(); } catch (e) { notice(e.message, true); $('connection').textContent = 'Connection unavailable'; } })();

async function loadExamples() {
  const {reports} = await api('/api/examples');
  const root = $('recorded-examples');
  if (reports.length) { $('judge-example').disabled=false; $('judge-example').addEventListener('click', () => $('recorded-examples').querySelector('button')?.click()); }
  for (const report of reports) {
    const label = {supported_history:'Accurate historical caption', misleading_caption:'Same image, misleading caption', unsupported_no_media:'Insufficient evidence'}[report.example_name] || 'Recorded case';
    const button=node('button', label, 'text-button');
    button.addEventListener('click', () => run(async () => {
      $('claim').value = report.claim; $('published-at').value = report.publication_context?.published_at?.slice(0,19) || ''; $('corpus').value = accessRole === 'review' ? 'review' : 'live'; showImage(null); $('image').value = '';
      if (report.example_image_url) {
        const response = await fetch(report.example_image_url); if (!response.ok) throw new Error('Recorded example image unavailable.');
        const bytes = new Uint8Array(await response.arrayBuffer()); let binary=''; for (let i=0;i<bytes.length;i+=16384) binary+=String.fromCharCode(...bytes.subarray(i,i+16384)); showImage(btoa(binary), 'image/jpeg');
      }
      renderReport(report); $('notice').scrollIntoView?.({block:'start',behavior:'smooth'}); notice('Recorded live run. Viewing this case makes zero model calls; its report belongs to the claim shown.'); })); root.append(button);
  }
}
loadExamples().catch(() => {});

// Help is available on hover, keyboard focus and tap; Escape dismisses it.
for (const help of document.querySelectorAll('.action-help')) {
  const button = help.querySelector('.info-button');
  button.addEventListener('focus', () => { delete help.dataset.dismissed; });
  button.addEventListener('click', () => { delete help.dataset.dismissed; help.dataset.open = ''; });
  help.addEventListener('keydown', event => { if (event.key === 'Escape') { delete help.dataset.open; help.dataset.dismissed = ''; button.blur(); } });
  help.addEventListener('mouseleave', () => { delete help.dataset.dismissed; delete help.dataset.open; });
  help.addEventListener('focusout', () => { delete help.dataset.open; });
}
