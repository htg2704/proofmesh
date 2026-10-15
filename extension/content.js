(() => {
  const core = globalThis.ProofMeshCore;
  const states = new WeakMap();
  const articles = new Set();
  let enabled = false, epoch = 0, active = 0, timer, route = location.href;
  function badge(article) {
    let el = article.querySelector(':scope > .proofmesh-context');
    if (!el) { el = document.createElement('aside'); el.className = 'proofmesh-context'; el.setAttribute('aria-label', 'ProofMesh context'); article.append(el); }
    return el;
  }
  function clear() { epoch++; for (const article of articles) { states.delete(article); article.querySelector(':scope > .proofmesh-context')?.remove(); } }
  function schedule(delay = 120) { clearTimeout(timer); timer = setTimeout(scan, delay); }
  function current(article, state) {
    return enabled && state.epoch === epoch && article.isConnected && states.get(article) === state && core.allowedPage(location.href) && core.extractPost(article, location.href).signature === state.signature;
  }
  async function send(type, post) {
    const response = await chrome.runtime.sendMessage({type, claim:post.claim, imageUrl:post.imageUrl});
    if (!response || response.error) throw new Error(response?.error || 'The extension connection was interrupted. Reload this page.');
    return response.data;
  }
  function portalLink(text, reportId) {
    const link = document.createElement('a'); link.textContent = text;
    link.href = reportId ? `${core.API}/?report=${encodeURIComponent(reportId)}` : core.API;
    link.target = '_blank'; link.rel = 'noopener noreferrer'; return link;
  }
  function render(article, state, data) {
    if (!current(article, state)) return;
    const el = badge(article); el.replaceChildren();
    const label = document.createElement('span');
    const exact = data.status === 'exact_context' && data.report;
    label.textContent = exact ? 'ProofMesh · existing investigation available' : data.status === 'related_media' ? 'ProofMesh · related image, different claim — unverified' : 'ProofMesh · no matching investigation — unverified';
    el.append(label);
    if (exact) { el.append(portalLink(data.report.corpus === 'demo' ? 'Read synthetic report ↗' : 'Read the evidence ↗', data.report.id)); return; }
    if (location.origin === core.API) { el.append(portalLink('Review the new caption in the workspace ↗')); return; }
    const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Investigate with Google Cloud';
    button.addEventListener('click', async event => {
      event.preventDefault(); event.stopPropagation();
      if (!current(article, state)) return;
      button.disabled = true; button.textContent = 'Investigating…';
      try { const result = await send('investigate', state.post); if (current(article, state)) button.replaceWith(portalLink('Open investigation ↗', result.report.id)); }
      catch (error) { if (current(article, state)) { button.textContent = 'Retry investigation'; button.title = error.message; button.disabled = false; } }
    }); el.append(button);
  }
  async function inspect(article) {
    if (!enabled || !core.allowedPage(location.href)) return;
    const post = core.extractPost(article, location.href);
    const previous = states.get(article);
    if (post.kind !== 'post') {
      if (previous?.signature !== `${post.kind}:${post.reason}`) {
        states.set(article, {signature:`${post.kind}:${post.reason}`, epoch});
        if (post.kind === 'unsupported') badge(article).textContent = `ProofMesh · ${post.reason} — unverified`;
        else article.querySelector(':scope > .proofmesh-context')?.remove();
      }
      return;
    }
    const now = Date.now();
    if (previous?.signature === post.signature && previous.epoch === epoch && (previous.pending || now < previous.retryAt || now - previous.checkedAt < 60_000)) return;
    if (active >= 2) return;
    const state = {signature:post.signature, post, epoch, pending:true, checkedAt:0, retryAt:0};
    states.set(article, state); active++;
    badge(article).textContent = 'ProofMesh · checking shared evidence…';
    try { const data = await send('match', post); if (current(article, state)) { state.checkedAt = Date.now(); render(article, state, data); } }
    catch (error) {
      if (current(article, state)) {
        state.retryAt = Date.now() + 10_000;
        const el = badge(article); el.replaceChildren();
        const message = document.createElement('span'); message.textContent = `ProofMesh · lookup unavailable: ${error.message}`;
        const retry = document.createElement('button'); retry.type = 'button'; retry.textContent = 'Retry lookup';
        retry.addEventListener('click', event => { event.preventDefault(); event.stopPropagation(); if (current(article, state)) { states.delete(article); schedule(0); } });
        el.append(message, retry);
      }
    } finally { state.pending = false; active--; schedule(); }
  }
  const visible = new IntersectionObserver(entries => { for (const entry of entries) if (entry.isIntersecting) inspect(entry.target); }, {threshold:0.3});
  function scan() {
    if (route !== location.href) { route = location.href; clear(); }
    if (!enabled || !core.allowedPage(location.href)) { clear(); return; }
    for (const article of articles) if (!article.isConnected) { visible.unobserve(article); articles.delete(article); }
    document.querySelectorAll('article').forEach(article => {
      if (article.parentElement?.closest('article')) return;
      if (!articles.has(article)) { articles.add(article); visible.observe(article); }
      const r = article.getBoundingClientRect(); if (r.top < innerHeight && r.bottom > 0) inspect(article);
    });
  }
  const observer = new MutationObserver(mutations => {
    if (mutations.some(m => !(m.target.nodeType === 1 ? m.target : m.target.parentElement)?.closest('.proofmesh-context'))) schedule();
  });
  observer.observe(document.body, {childList:true, subtree:true, characterData:true, attributes:true, attributeFilter:['src','srcset']});
  chrome.storage.local.get('enabled').then(s => { enabled = Boolean(s.enabled); schedule(); });
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && (changes.enabled || changes.apiToken)) { if (changes.enabled) enabled = Boolean(changes.enabled.newValue); clear(); schedule(); }
  });
  window.addEventListener('popstate', () => schedule(0));
  setInterval(() => schedule(), 10_000);
})();
