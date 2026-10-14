(() => {
  let enabled = false, timer;
  const seen = new WeakMap();
  const inFlight = new WeakMap();
  function send(type, claim, imageUrl) { return chrome.runtime.sendMessage({ type, claim, imageUrl }); }
  function badge(article) { let el = article.querySelector('.proofmesh-context'); if (!el) { el = document.createElement('aside'); el.className = 'proofmesh-context'; el.setAttribute('aria-label', 'ProofMesh context'); article.append(el); } return el; }
  function clear() { document.querySelectorAll('.proofmesh-context').forEach(el => el.remove()); document.querySelectorAll('article[data-testid="tweet"]').forEach(a => seen.delete(a)); }
  async function inspect(article) {
    if (!enabled || location.pathname.startsWith('/messages')) return;
    const claim = article.querySelector('[data-testid="tweetText"]')?.textContent?.trim();
    if (!claim || claim.length < 5 || claim.length > 3000) return;
    // Do not conflate a gallery or quoted post with the first image's context.
    if (article.querySelectorAll('[data-testid="tweetPhoto"] img').length > 1 || article.querySelector('[data-testid="quoteTweet"]')) {
      badge(article).textContent = 'ProofMesh · multi-image and quoted posts need manual review';
      return;
    }
    // This first version supports one image per post.
    const imageUrl = article.querySelector('[data-testid="tweetPhoto"] img')?.src || null;
    const signature = JSON.stringify([claim, imageUrl]);
    if (seen.get(article) === signature || inFlight.get(article) === signature) return;
    inFlight.set(article, signature); seen.set(article, signature);
    const el = badge(article); el.textContent = 'ProofMesh · checking shared evidence…';
    try {
      const response = await send('match', claim, imageUrl);
      if (!enabled || seen.get(article) !== signature || !article.isConnected) return;
      if (response.error) throw new Error(response.error);
      const data = response.data; el.replaceChildren();
      const label = document.createElement('span');
      label.textContent = data.status === 'exact_context' ? 'ProofMesh · existing investigation available' : data.status === 'related_media' ? 'ProofMesh · related image, different claim — unverified' : 'ProofMesh · no matching investigation — unverified';
      el.append(label);
      if (data.report) {
        const link = document.createElement('a'); link.href = `http://127.0.0.1:8000/?report=${encodeURIComponent(data.report.id)}`; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = data.report.corpus === 'demo' ? 'Read synthetic report ↗' : 'Read the evidence ↗'; el.append(link);
      } else {
        const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Investigate with Google Cloud';
        button.addEventListener('click', async event => { event.preventDefault(); event.stopPropagation(); button.disabled = true; button.textContent = 'Investigating…';
          try { const result = await send('investigate', claim, imageUrl); if (result.error) throw new Error(result.error); if (!enabled || seen.get(article) !== signature) return; const link = document.createElement('a'); link.href = `http://127.0.0.1:8000/?report=${encodeURIComponent(result.data.report.id)}`; link.target = '_blank'; link.rel = 'noopener noreferrer'; link.textContent = 'Open investigation ↗'; button.replaceWith(link); }
          catch(error) { button.textContent = 'Investigation unavailable'; button.title = error.message; button.disabled = false; }
        }); el.append(button);
      }
    } catch (error) { if (enabled && seen.get(article) === signature) el.textContent = `ProofMesh · lookup unavailable: ${error.message}`; }
    finally { if (inFlight.get(article) === signature) inFlight.delete(article); }
  }
  const visible = new IntersectionObserver(entries => { for (const entry of entries) if (entry.isIntersecting) inspect(entry.target); }, { threshold: 0.3 });
  const observed = new WeakSet();
  function scan() { if (!enabled) return; document.querySelectorAll('article[data-testid="tweet"]').forEach(article => { if (article.closest('[data-testid="quoteTweet"]')) return; if (!observed.has(article)) { visible.observe(article); observed.add(article); } const r = article.getBoundingClientRect(); if (r.top < innerHeight && r.bottom > 0) inspect(article); }); }
  function schedule() { clearTimeout(timer); timer = setTimeout(scan, 250); }
  const observer = new MutationObserver(mutations => { if (mutations.some(m => !m.target.closest?.('.proofmesh-context'))) schedule(); });
  observer.observe(document.body, { childList: true, subtree: true, characterData: true, attributes: true, attributeFilter: ['src'] });
  chrome.storage.local.get('enabled').then(s => { enabled = Boolean(s.enabled); schedule(); });
  chrome.storage.onChanged.addListener((changes, area) => { if (area === 'local' && changes.enabled) { enabled = Boolean(changes.enabled.newValue); if (!enabled) clear(); else schedule(); } });
})();
