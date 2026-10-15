/* Pure DOM extraction shared by the content script and regression tests. */
globalThis.ProofMeshCore = (() => {
  const API = 'http://127.0.0.1:8000';
  const PRIVATE_PATH = /^\/(?:messages|settings|compose|login|logout|account)(?:\/|$)|^\/i\/(?:chat|flow|account)(?:\/|$)/;
  function allowedPage(url) {
    try { const u = new URL(url); return !u.username && !u.password && ((u.protocol === 'https:' && u.hostname === 'x.com' && !PRIVATE_PATH.test(u.pathname)) || (u.origin === API && u.pathname === '/feed')); } catch { return false; }
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
    const urls = [...new Set(images.map(img => img.src).filter(Boolean))];
    if (urls.length > 1) return {kind:'unsupported', reason:'Multi-image posts need manual review'};
    // Publication time is not in the backend reuse key yet. Hold these X
    // captions for review rather than transfer an old relative-date verdict.
    if (new URL(pageUrl).hostname === 'x.com' && /\b(today|yesterday|tomorrow|tonight|right now|this (morning|evening|week|month|year))\b/i.test(claim)) return {kind:'unsupported', reason:'Relative-time caption needs publication-context review'};
    return {kind:'post', claim, imageUrl:urls[0] || null, postId:ids[0] || null, signature:JSON.stringify([claim, urls[0] || null, ids[0] || null])};
  }
  return {API, allowedPage, extractPost};
})();
