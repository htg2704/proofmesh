const $ = id => document.getElementById(id);
let imageBase64 = null;
let alternateClaim = '';
let currentReport = null;
function node(tag, text, className) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (className) n.className = className; return n; }
function notice(text, error = false) { $('notice').hidden = false; $('notice').textContent = text; $('notice').className = error ? 'error' : ''; }
function busy(value) { document.querySelectorAll('button').forEach(b => b.disabled = value); }
async function api(path, body) {
  const headers = { 'Content-Type': 'application/json' };
  const token = sessionStorage.getItem('proofmesh-token'); if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(path, { headers, ...(body !== undefined ? { method: 'POST', body: JSON.stringify(body) } : {}) });
  const data = await response.json(); if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Check the submitted claim and image.'); return data;
}
function payload() { return { claim: $('claim').value, image_base64: imageBase64, corpus: $('corpus').value }; }
function showImage(encoded) { imageBase64 = encoded; $('image-wrap').hidden = !encoded; if (encoded) $('image-preview').src = `data:image/png;base64,${encoded}`; else $('image-preview').removeAttribute('src'); }
function safeLink(url) { try { const parsed = new URL(url, location.origin); return parsed.protocol === 'https:' || (parsed.origin === location.origin && parsed.pathname.startsWith('/fixtures/')) ? parsed.href : null; } catch { return null; } }
function renderReport(report, reused = false) {
  currentReport = report;
  const root = $('result'); root.replaceChildren();
  root.append(node('span', report.corpus === 'demo' ? 'Synthetic demo · not real-world evidence' : 'Live investigation', `tag ${report.corpus === 'demo' ? 'demo' : ''}`));
  if (reused) root.append(node('span', 'Reused · 0 model calls', 'tag'));
  root.append(node('h3', report.assessment.summary, 'report-summary'));
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
    card.append(title, node('p', evidence.excerpt), node('small', evidence.kind === 'demo_fixture' ? 'SYNTHETIC FIXTURE' : 'SEARCH-GROUNDED MODEL SUMMARY · NOT A VERBATIM SOURCE QUOTE')); root.append(card);
  }
  root.append(node('h4', 'What remains uncertain', 'report-subhead'));
  const limits = node('ul', undefined, 'limit'); report.assessment.limitations.forEach(t => limits.append(node('li', t))); root.append(limits);
  const events = node('ol', undefined, 'timeline'); (report.events || []).forEach(e => events.append(node('li', `${e.stage}: ${e.detail}`))); root.append(events);
  if (report.search_attribution_html) {
    const frame = document.createElement('iframe'); frame.className = 'attribution'; frame.title = 'Google Search attribution'; frame.setAttribute('sandbox', 'allow-popups allow-popups-to-escape-sandbox');
    frame.srcdoc = '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src https: data:">' + report.search_attribution_html; root.append(frame);
  }
  const exportButton = node('button', 'Download evidence report ↓', 'text-button'); exportButton.type = 'button'; exportButton.addEventListener('click', () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(currentReport, null, 2)], { type: 'application/json' })); const a = node('a'); a.href = url; a.download = `proofmesh-${currentReport.id.slice(0, 12)}.json`; a.click(); URL.revokeObjectURL(url);
  }); root.append(exportButton);
}
function renderMatch(result) {
  if (result.report) { renderReport(result.report, true); notice('Exact image-and-claim context found. Retrieved with zero model calls.'); return; }
  const root = $('result'); root.replaceChildren(); const box = node('div', undefined, 'unknown-card');
  box.append(node('span', 'Unverified', 'tag'), node('h3', result.status === 'related_media' ? 'Familiar image. New question.' : 'An open question.'), node('p', result.status === 'related_media' ? 'Related media exists in the registry, but its assessment does not apply to this caption. Investigate this claim separately.' : 'No matching investigation exists in this collection. That does not establish whether the content is true or false.')); root.append(box);
  for (const item of result.related) { const button = node('button', `View related investigation: ${item.claim}`, 'text-button related-link'); button.addEventListener('click', async () => { try { renderReport(await api(`/api/investigations/${item.id}`)); notice('Viewing a related report. Its assessment is not an assessment of your current caption.'); } catch (e) { notice(e.message, true); } }); root.append(button); }
  notice(`${result.related.length} related investigation${result.related.length === 1 ? '' : 's'}. No verdict transferred. Zero model calls.`);
}
async function refresh() {
  const data = await api(`/api/investigations?corpus=${$('corpus').value}`); const root = $('registry-list'); root.replaceChildren();
  if (!data.reports.length) root.append(node('p', 'No investigations in this collection yet.', 'muted'));
  for (const report of data.reports) { const row = node('div', undefined, 'registry-row'); const button = node('button', report.claim, 'text-button'); button.addEventListener('click', () => renderReport(report)); row.append(button, node('small', `${report.corpus.toUpperCase()} · ${new Date(report.created_at).toLocaleDateString()}`)); root.append(row); }
}
async function run(action) { busy(true); try { await action(); } catch (e) { notice(e.message, true); } finally { busy(false); } }
$('investigation-form').addEventListener('submit', e => { e.preventDefault(); run(async () => { notice('Checking the shared evidence registry…'); renderMatch(await api('/api/matches', payload())); }); });
$('investigate-button').addEventListener('click', () => { if (!$('investigation-form').reportValidity()) return; run(async () => { notice('Researching sources, assessing the claim, and challenging the assessment. This may take a few minutes…'); const data = await api('/api/investigations', payload()); renderReport(data.report, data.reused); notice(`${data.reused ? 'Retrieved existing report' : 'Investigation complete'} · ${data.model_calls} model calls for this request.`); await refresh(); }); });
$('demo-button').addEventListener('click', () => run(async () => { const data = await api('/api/demo', {}); $('claim').value = data.claim; $('corpus').value = 'demo'; showImage(data.image_base64); alternateClaim = data.alternate_claim; $('alternate-button').hidden = false; renderReport(data.report); notice('Synthetic example loaded. Check shared evidence, then try the alternate caption.'); await refresh(); }));
$('alternate-button').addEventListener('click', () => run(async () => { $('claim').value = alternateClaim; $('corpus').value = 'demo'; renderMatch(await api('/api/matches', payload())); }));
$('image').addEventListener('change', async e => { const file = e.target.files[0]; if (!file) return; if (file.size > 5_000_000) { notice('Choose an image smaller than 5 MB.', true); e.target.value = ''; return; } const reader = new FileReader(); reader.onload = () => showImage(String(reader.result).split(',')[1]); reader.readAsDataURL(file); });
$('remove-image').addEventListener('click', () => { showImage(null); $('image').value = ''; });
$('save-token').addEventListener('click', () => { sessionStorage.setItem('proofmesh-token', $('token').value); $('token').value = ''; run(refresh); });
$('refresh-button').addEventListener('click', () => run(refresh));
$('corpus').addEventListener('change', () => run(refresh));
(async () => { try { const health = await api('/api/health'); $('connection').textContent = health.live_enabled ? 'Live pipeline enabled' : 'Local · demo ready'; if (!health.authentication_required || sessionStorage.getItem('proofmesh-token')) await refresh(); else notice('This server requires an API token. Open Connection settings to continue.'); const id = new URLSearchParams(location.search).get('report'); if (id) renderReport(await api(`/api/investigations/${encodeURIComponent(id)}`)); } catch (e) { notice(e.message, true); $('connection').textContent = 'Connection unavailable'; } })();
