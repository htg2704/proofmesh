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
