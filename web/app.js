const $ = id => document.getElementById(id);
let imageBase64 = null;
let alternateClaim = '';
let currentReport = null;
let imageVersion = 0;
function node(tag, text, className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; }
function notice(text, error = false) { $('notice').hidden = false; $('notice').textContent = text; $('notice').className = error ? 'error' : ''; }
function busy(value) { document.querySelectorAll('button, #claim, #image, #corpus, #token').forEach(b => b.disabled = value); document.querySelector('.workspace').setAttribute('aria-busy', String(value)); }
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
function payload() { return { claim: $('claim').value, image_base64: imageBase64, corpus: $('corpus').value }; }
function showImage(encoded, mime = 'image/png') { imageBase64 = encoded; $('image-wrap').hidden = !encoded; if (encoded) $('image-preview').src = `data:${mime};base64,${encoded}`; else $('image-preview').removeAttribute('src'); }
function safeLink(url) { try { const parsed = new URL(url, location.origin); return parsed.protocol === 'https:' || (parsed.origin === location.origin && parsed.pathname.startsWith('/fixtures/')) ? parsed.href : null; } catch { return null; } }
function renderReport(report, reused = false) {
  currentReport = report;
  const root = $('result'); root.replaceChildren();
  root.append(node('span', report.corpus === 'demo' ? 'Synthetic demo · not real-world evidence' : report.recorded_example ? 'Recorded live investigation · inspect the original sources' : 'Live investigation', `tag ${report.corpus === 'demo' ? 'demo' : ''}`));
  if (reused) root.append(node('span', 'Reused · 0 model calls', 'tag'));
  root.append(node('h3', report.assessment.summary, 'report-summary'));
  root.append(node('p', `Investigated ${new Date(report.created_at).toLocaleString()} · ${new Date(report.expires_at) <= new Date() ? 'Archived report; check current evidence before reuse.' : 'Assessment belongs to the claim below.'}`, 'muted'));
  root.append(node('p', `Media origin: ${report.origin.status}. ${report.origin.explanation}`, 'muted'));
  for (const finding of report.assessment.findings) {
    const card = node('section', undefined, 'finding'); card.append(node('span', finding.status, `tag ${finding.status}`), node('h3', finding.claim), node('p', finding.explanation));
    if (finding.evidence_ids.length) card.append(node('small', `Evidence: ${finding.evidence_ids.join(', ')}`, 'muted'));
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
  const limits = node('ul', undefined, 'limit'); report.assessment.limitations.forEach(t => limits.append(node('li', t))); root.append(limits);
  const events = node('ol', undefined, 'timeline'); (report.events || []).forEach(e => events.append(node('li', `${e.stage}: ${e.detail}`))); root.append(events);
  if (report.search_attribution_html) {
    const frame = document.createElement('iframe'); frame.className = 'attribution'; frame.title = 'Google Search attribution'; frame.setAttribute('sandbox', 'allow-popups allow-popups-to-escape-sandbox');
    frame.srcdoc = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src https: data:">' + report.search_attribution_html; root.append(frame);
  }
  const exportButton = node('button', 'Download evidence report ↓', 'text-button'); exportButton.type = 'button'; exportButton.addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })); const a = node('a'); a.href = url; a.download = `proofmesh-${report.id.slice(0, 12)}.json`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }); root.append(exportButton);
}
function renderMatch(result) {
  if (result.report) { renderReport(result.report, true); notice('Exact image-and-claim context found. Retrieved with zero model calls.'); return; }
  const root = $('result'); root.replaceChildren(); const box = node('div', undefined, 'unknown-card');
  box.append(node('span', 'Unverified', 'tag'), node('h3', result.status === 'related_media' ? 'Familiar image. New question.' : 'An open question.'), node('p', result.status === 'related_media' ? 'Related media exists in the registry, but its assessment does not apply to this caption. Investigate this claim separately.' : 'No matching investigation exists in this collection. That does not establish whether the content is true or false.')); root.append(box);
  for (const item of result.related) { const button = node('button', `View related investigation: ${item.claim}`, 'text-button related-link'); button.addEventListener('click', async () => { try { renderReport(await api($('corpus').value === 'demo' ? `/api/demo/reports/${item.id}` : `/api/investigations/${item.id}`)); notice('Viewing a related report. Its assessment is not an assessment of your current caption.'); } catch (e) { notice(e.message, true); } }); root.append(button); }
  notice(`${result.related.length} related investigation${result.related.length === 1 ? '' : 's'}. No verdict transferred. Zero model calls.`);
}
async function refresh() {
  const data = $('corpus').value === 'demo' ? {reports: [(await api('/api/demo', {})).report]} : await api('/api/investigations?corpus=live'); const root = $('registry-list'); root.replaceChildren();
  if (!data.reports.length) root.append(node('p', 'No investigations in this collection yet.', 'muted'));
  for (const report of data.reports) { const row = node('div', undefined, 'registry-row'); const button = node('button', report.claim, 'text-button'); button.addEventListener('click', () => { renderReport(report); notice('Viewing a stored investigation for the claim shown in its report.'); }); row.append(button, node('small', `${report.corpus.toUpperCase()} · ${new Date(report.created_at).toLocaleDateString()}`)); root.append(row); }
}
async function run(action) { busy(true); try { await action(); } catch (e) { notice(e.message, true); } finally { busy(false); } }
$('investigation-form').addEventListener('submit', e => { e.preventDefault(); run(async () => { notice('Checking the shared evidence registry…'); renderMatch(await api($('corpus').value === 'demo' ? '/api/demo/matches' : '/api/matches', payload())); }); });
$('investigate-button').addEventListener('click', () => { if (!$('investigation-form').reportValidity()) return; run(async () => { notice('Researching sources, assessing the claim, and challenging the assessment. This may take a few minutes…'); const job = await api('/api/jobs', payload()); sessionStorage.setItem('proofmesh-job', job.id); await pollJob(job.id); }); });
$('demo-button').addEventListener('click', () => run(async () => { const data = await api('/api/demo', {}); $('claim').value = data.claim; $('corpus').value = 'demo'; showImage(data.image_base64); alternateClaim = data.alternate_claim; $('alternate-button').hidden = false; renderReport(data.report); notice('Synthetic example loaded. Check shared evidence, then try the alternate caption.'); await refresh(); }));
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
async function pollJob(id) {
  for (let count = 0; count < 120; count++) {
    const job = await api(`/api/jobs/${encodeURIComponent(id)}`);
    notice(`Investigation ${job.status}. You can close this page and return; the job is saved.`);
    if (job.status === 'failed') {
      sessionStorage.removeItem('proofmesh-job');
      if ((job.attempt || 1) < 2) {
        const retry = node('button', 'Retry once with Google Cloud', 'text-button');
        retry.addEventListener('click', () => run(async () => { const next = await api('/api/jobs?retry_failed=true', payload()); await pollJob(next.id); })); $('result').append(retry);
      }
      throw new Error(job.error || 'Investigation failed.');
    }
    if (job.status === 'succeeded') {
      renderReport(await api(`/api/investigations/${job.report_id}`), job.reused);
      sessionStorage.removeItem('proofmesh-job'); notice(`Investigation complete · ${job.model_calls} model calls.`); await refresh(); return;
    }
    await new Promise(resolve => setTimeout(resolve, 3000));
  }
  throw new Error('Investigation is taking longer than expected. Reload to check the saved job.');
}
async function loadRouteReport() { const id = new URLSearchParams(location.search).get('report'); if (id) renderReport(await api(`/api/investigations/${encodeURIComponent(id)}`)); const job = new URLSearchParams(location.search).get('job') || sessionStorage.getItem('proofmesh-job'); if (job) await pollJob(job); }
$('save-token').addEventListener('click', () => { sessionStorage.setItem('proofmesh-token', $('token').value.trim()); $('token').value = ''; run(async () => { await refresh(); notice('Connected. The API token is kept only for this browser session.'); await loadRouteReport(); }); });
$('refresh-button').addEventListener('click', () => run(refresh));
$('corpus').addEventListener('change', () => run(refresh));
(async () => { try { const health = await api('/api/health'); $('connection').textContent = health.live_enabled ? 'Live pipeline enabled' : 'Local · demo ready'; if (health.authentication_required && !sessionStorage.getItem('proofmesh-token')) { $('corpus').value = 'demo'; notice('Public synthetic demo ready. Live investigations require your team API token in Connection settings.'); await refresh(); return; } await refresh(); await loadRouteReport(); } catch (e) { notice(e.message, true); $('connection').textContent = 'Connection unavailable'; } })();

async function loadExamples() {
  const {reports} = await api('/api/examples');
  const root = $('recorded-examples');
  for (const report of reports) {
    const label = {supported_history:'Accurate historical caption', misleading_caption:'Same image, misleading caption', unsupported_no_media:'Insufficient evidence'}[report.example_name] || 'Recorded case';
    const button=node('button', label, 'text-button');
    button.addEventListener('click', () => { renderReport(report); notice('Recorded live run. Viewing this case makes zero model calls; it does not assess the text currently in the input.'); }); root.append(button);
  }
}
loadExamples().catch(() => {});
