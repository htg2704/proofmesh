/* Pure DOM extraction shared by the content script and regression tests. */
globalThis.ProofMeshCore = (() => {
  const API = 'http://127.0.0.1:8000';
  const CLOUD = 'https://proofmesh-2god3tua3a-el.a.run.app';
  const PRIVATE_PATH = /^\/(?:messages|settings|compose|login|logout|account)(?:\/|$)|^\/i\/(?:chat|flow|account)(?:\/|$)/;
  function allowedPage(url) {
    try { const u = new URL(url); return !u.username && !u.password && ((u.protocol === 'https:' && u.hostname === 'x.com' && !PRIVATE_PATH.test(u.pathname)) || ([API,CLOUD].includes(u.origin) && u.pathname === '/feed')); } catch { return false; }
  }
  function canonicalImage(url) {
    if (!url) return null;
    try { const u=new URL(url); if(u.protocol==='https:' && u.hostname==='pbs.twimg.com' && u.pathname.startsWith('/media/'))u.searchParams.set('name','large');return u.href; } catch { return url; }
  }
  function postId(href) { try { return new URL(href, 'https://x.com').pathname.match(/^\/[^/]+\/status\/(\d+)(?:\/|$)/)?.[1] || null; } catch { return null; } }
  function extractPost(article, pageUrl) {
    if (!allowedPage(pageUrl)) return {kind:'excluded', reason:'Private or unsupported page'};
    if (article.parentElement?.closest('article')) return {kind:'excluded', reason:'Nested post'};
    const own = selector => [...article.querySelectorAll(selector)].filter(e => e.closest('article') === article);
    const legacy = own('[data-testid="tweetText"]');
    // Observed on public X on October 15: articles without test IDs.
    const texts = legacy.length ? legacy : own('div[dir="auto"].whitespace-pre-wrap');
    const ids = [...new Set(own('a[href*="/status/"]').map(a => postId(a.getAttribute('href'))).filter(Boolean))];
    if (article.querySelector('article, [data-testid="quoteTweet"]') || texts.length > 1 || ids.length > 1) return {kind:'unsupported', reason:'Quoted posts need manual review'};
    if (texts.length !== 1) return {kind:'excluded', reason:'No unambiguous post text'};
    const claim = texts[0].textContent.trim();
    if (claim.length < 5 || claim.length > 3000) return {kind:'excluded', reason:'Unsupported claim length'};
    if (own('video, [data-testid="videoPlayer"]').length) return {kind:'unsupported', reason:'Video posts need manual review'};
    const images = own('[data-testid="tweetPhoto"] img, img[src^="https://pbs.twimg.com/media/"], img[src^="http://127.0.0.1:8000/fixtures/"]');
    const urls = [...new Set(images.map(img => canonicalImage(img.src)).filter(Boolean))];
    if (urls.length > 1) return {kind:'unsupported', reason:'Multi-image posts need manual review'};
    const stamps = [...new Set(own('time[datetime]').map(e => e.getAttribute('datetime')).filter(value => /(?:Z|[+-]\d{2}:\d{2})$/i.test(value || '') && Number.isFinite(Date.parse(value))).map(value => new Date(value).toISOString()))];
    const publishedAt = stamps.length === 1 ? stamps[0] : null;
    const statusLink = own('a[href*="/status/"]').map(e => new URL(e.getAttribute('href'), pageUrl)).find(u => u.hostname === 'x.com' && /^\/[^/]+\/status\/\d+/.test(u.pathname));
    const sourceUrl = statusLink ? 'https://x.com' + statusLink.pathname.match(/^\/[^/]+\/status\/\d+/)[0] : null;
    if (new URL(pageUrl).hostname === 'x.com' && !publishedAt && /\b(today|yesterday|tomorrow|tonight|right now|this (morning|evening|week|month|year))\b/i.test(claim)) return {kind:'unsupported', reason:'Relative-time caption needs publication-context review'};
    return {kind:'post', claim, imageUrl:urls[0] || null, postId:ids[0] || null, publishedAt, sourceUrl, signature:JSON.stringify([claim, urls[0] || null, ids[0] || null, publishedAt])};
  }
  return {API, CLOUD, allowedPage, extractPost, canonicalImage};
})();
