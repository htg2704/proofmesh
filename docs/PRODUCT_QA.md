# Product QA — October 15, 2026

Scope: partner's October 14 tasks F1–F4. The user requested completing these tasks and pushing the result to GitHub.

## Installed extension

The user manually loaded the unpacked extension because automation cannot navigate Chrome's internal extension manager. Version **0.2.0** was then exercised in Chrome through the normal popup and ordinary web pages.

- Enabled visible-post lookups through the installed popup.
- Stored the existing local ProofMesh API token only after explicit user approval. Google credentials were not copied into the browser.
- Used a separate synthetic QA SQLite database. Model calls were disabled throughout product QA.
- Verified the first `/feed` post shows an existing synthetic investigation and links to its report.
- Scrolled to the second post: the same image with another caption shows **related image, different claim — unverified**. It does not receive the first report's verdict.
- Restarted the backend with normal API-token protection and verified both results again through the installed extension.

## Public X inspection

Inspected `https://x.com/NASA` and scrolled its public page. The observed public layout has `article` elements but no `data-testid` attributes. The original starter therefore missed these posts.

The extractor now supports both legacy tweet test IDs and the observed public structure: unambiguous `div[dir="auto"].whitespace-pre-wrap` caption nodes, canonical status links and `pbs.twimg.com/media/` images. Profile avatars are excluded. After reloading X with the installed extension, a visible image post received an unknown/unverified indicator; a video post was held for manual review.

The runtime limits simultaneous lookups, rechecks after expiry, provides retry after failure, and rejects results whose post signature or enablement generation has changed. Disabled/private routes clear indicators. Multi-image, quoted and video posts remain unverified.

Because publication timestamps are not in the backend's reuse key, common English relative-time captions on X (such as “today” or “yesterday”) are held for context review. This guard is not a complete multilingual temporal interpretation system.

## Portal browser checks

| Case | Observed result |
|---|---|
| Wrong token, then correct token | Unauthorized notice, then successful connection; old error replaced; password field cleared. |
| Server stopped | Clear offline message; controls remain usable for retry. |
| Valid PNG | Image ready, preview shown, matching control enabled. |
| Replacement larger than 5 MB | Rejected; earlier selected image is cleared rather than silently retained. |
| Corrupt `.png` | Decode error, no retained preview. |
| 4,100 × 4,100 image | Rejected by the 16-megapixel limit. |
| Synthetic unresolved report | Unresolved label, unknown origin, no invented evidence or source links. |
| Mobile, 390 × 844 viewport | Document width equals viewport width; no horizontal overflow. Temporary viewport override restored. |
| Citation | Readable synthetic archive page opens, labels itself fictional, and explains the fixture. Legacy `.txt` URL retained for older reports. |
| JSON export | Both unresolved and contradicted fixture reports created valid downloaded JSON. IDs, statuses and evidence counts checked; no token/credential fields included. |

Chrome upload automation required an additional file-URL permission, so file-input cases were tested in the in-app browser. Native download files were verified directly because the automation's download event observer timed out even though downloads completed.

## Regression checks

**20 Python tests + 21 JavaScript tests pass.** JavaScript tests use jsdom for dynamic DOM fixtures and mocked extension messaging. They cover current/legacy extraction, image URL resolution, quoted/gallery/video exclusions, private routes, temporal guard, two-caption independence, recycled nodes, stale responses, disablement, SPA navigation, retry, duplicate scans, worker request boundaries, token recovery and image-state validation.

The source-page route is also checked through the Python API test. CI installs locked Node development dependencies with lifecycle scripts disabled.

## Verification limits

- Actual X verification covers the public logged-out NASA page observed on this date. It does not establish compatibility with every logged-in layout, account, locale or future X redesign.
- Recycled-node, gallery, quote and private-route edge cases are covered by controlled DOM regression fixtures, not by modifying actual X content or opening private messages.
- The QA registry is synthetic. No new live investigations or paid Google model calls were made during this product pass.
- Google Search attribution styling, durable asynchronous investigations, deployed extension configuration, semantic matching, Firestore and Cloud Run remain separate work.

## Hosted release verification — October 17

Chrome version: 155.0.8059.80. The installed extension used its fixed Cloud Run origin, with its separate cloud API token saved only after explicit user approval. The hosted synthetic feed reused the first caption and left the second as related media without a transferred verdict. Actual public `x.com/NASA` image posts completed authenticated registry lookups and displayed unknown/unverified; videos remained unverified with manual-review text. These lookups did not invoke inference. No social post was published, liked, shared or changed.

Public portal recorded cases were inspected with their own caption/image, source links, page-date labels, unresolved state and the visible QA note about an incidental model date error. The selected examples are frozen outputs, not live inference triggered by opening them. `docs/EVALUATION.md` and `docs/DEPLOYMENT.md` contain the fresh cloud-job evidence.

Broader logged-in X variants, complete keyboard/screen-reader behavior, Instagram and other browsers remain unverified. Version 0.4.0 contains the final public synthetic deep-link and popup workspace-link fixes; reload the unpacked extension after updating its files.

## v0.4 action clarity and installed-extension verification

Both actions now have information controls that expose explanations on hover, focus or tap, with Escape dismissal. Permanent helper text distinguishes zero-model lookup from new AI work that consumes the cloud allowance. Click/focus behavior and dismissal were checked in Chrome; full screen-reader coverage is not claimed. The portal presents the web workspace and extension as clients of a shared evidence rail, with SDK/MCP, platform and Android/Gemini integrations explicitly marked as proposals.

After the user reloaded version 0.4.0, the hosted synthetic feed retrieved an existing report for the first caption, left the second as related media/unverified, and opened the corrected `demo_report` public link successfully. These checks made no model calls. Current regression suite: 47 Python + 27 JavaScript.

## v0.5 no-code browser flow

The normal app has examples in its own workspace; collection selection, the synthetic developer fixture and reviewer-code input are hidden from the primary UI. First use creates a limited HttpOnly guest session automatically. A browser test on Cloud Run reused an example, completed a fresh private visitor investigation and then retrieved it with zero model calls, without entering a key or code. Developer keys live under `/developers`; trusted team keys are optional advanced connection settings. The hosted legacy reviewer secret and its reserved allowance are disabled.

## Real-X follow-up and extension 0.4.1 — October 18

The earlier real-X checks established DOM extraction and no-match lookups, not a positive real-post match. The positive example at that time was the labeled synthetic feed. A later inspection found the installed extension set to Local development; the user switched it to Google Cloud demo and saved the existing token.

The real NASA post selected for end-to-end verification is https://x.com/NASA/status/2111093273800356092. Its exact caption, one image and `2026-10-16T13:53:53Z` publication context were read from the actual X DOM. A bounded hosted investigation completed with three model calls, supported findings and a public snapshot. Reopening the post exposed a separate mismatch: X changed the displayed CDN image size from `900x900` to `medium`, altering the strict decoded-pixel fingerprint. Extension 0.4.1 canonicalizes the same allowed `pbs.twimg.com/media/` asset to `name=large` before fetching and building its signature, so display-size changes do not alter its input. It does not replace exact identity with perceptual verdict matching; different captions/media still require their own context. A new canonical-size run is recorded separately in local verification data.

0.4.1 also reacts immediately to cloud-token/server changes, uses `public_report` links for public registry matches, and makes on-demand publication explicit with “Investigate and share evidence.” Shared jobs open through minimal public status handoff and then the published snapshot; private jobs and reports remain credential-protected. This avoids a mismatch between an extension credential and a different web-workspace cookie. Ineligible/failed publication is explicit and never exposes the private report. No-match badges say “not assessed” instead of presenting a truth verdict. No new browser permissions are requested; the unpacked extension must be manually reloaded.

Videos, galleries, ambiguous/quoted posts and some Community Notes layouts remain outside the supported extraction path. This is a rehearsed single-image case, not blanket compatibility with every X feed. Installed-browser positive-match and report-opening verification must be distinguished from backend/mocked checks in the follow-up verification record.
