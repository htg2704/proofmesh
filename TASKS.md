# ProofMesh — two-person task board

Working deadline: **October 17, 2026 (Asia/Kolkata)**. Start: October 14.
Selected concept: Project 01, ProofMesh, from the supplied buildercup brief.
Hackathon category: **Media, Content & Digital Experiences**.

This is the canonical task list. A checkbox means the acceptance condition was verified, not merely that code was written. Starter code exists for both owners; unverified features remain unchecked.

## Current focus — October 15

- **You:** start with B3 (Vertex AI configuration), then B4 (one live, source-grounded investigation). The local starter and public remote are ready; cloud/model access remains the immediate integration dependency.
- **Partner:** start with F1 and F2 (load the unpacked extension and verify the two-caption fixture), then F3 (real X extraction).
- **Both:** finish J2 (three attributable public demo cases) before expanding features. Keep October 16 for integration, evaluation and recording; October 17 remains the submission buffer.
- **Verified:** starter committed and pushed to public `htg2704/proofmesh`; 17 Python tests and 3 JavaScript tests pass locally, and the starter's GitHub Actions run passed.

## Ownership

| Owner | Owns | Main paths |
|---|---|---|
| You | Investigation engine, source validation, context matching, evidence registry, API and cloud deployment | `app/`, `tests/test_core.py`, `Dockerfile`, `docs/API.md` |
| Partner | Chrome extension, visible-post extraction, portal, evidence presentation and browser testing | `extension/`, `web/`, `tests/test_extension.mjs` |
| Both | API agreement, credible demo examples, integration, evaluation and submission | `docs/`, `README.md`, this board |

## October 14 — runnable foundation

### You
- [ ] **B1 — Accept API contract.** Read `docs/API.md`; confirm both clients send claim + optional image and treat `related_media` as unverified. Freeze endpoint names for today's integration.
- [x] **B2 — Verify registry and cache tests.** Passed locally October 14: same image + same claim reuses with zero inference, new caption never inherits a verdict, demo/live are isolated, and reports survive restart. Re-run after changes.
- [ ] **B3 — Configure Vertex AI.** Choose a Google Cloud project, region and available Gemini model; configure application-default credentials and a server token. Run one real search-grounded investigation and inspect every cited source. No paid cloud resources have been provisioned by the starter.
- [ ] **B4 — Inspect investigation quality.** Verify research -> assessment -> critique on supported, contradicted and unresolved cases. An empty search result must stay unresolved.

### Partner
- [ ] **F1 — Run the portal and extension locally.** Start the backend; load `extension/` unpacked in Chrome; enable lookups in its popup. Load the synthetic scenario in the portal, then open `/feed`.
- [ ] **F2 — Verify same-image/different-caption behavior.** First fixture post links to the synthetic report; second remains unverified and offers a separate investigation.
- [ ] **F3 — Test X extraction.** Inspect public X posts, dynamic scrolling and recycled post nodes. Fix selectors as needed. Exclude direct messages, nested quoted-post confusion, unsupported galleries and stale overlays.
- [ ] **F4 — Verify portal states.** Check file limits, token entry, empty evidence, offline server, unresolved results, citations and export on desktop and mobile.

### Both
- [x] **J1 — Create shared remote.** Public repository `https://github.com/htg2704/proofmesh` verified October 15; starter is pushed and GitHub Actions passed. Use `backend/*` and `product/*` feature branches for ongoing work.
- [ ] **J2 — Choose three public, attributable demonstration cases.** Include an old image with a false current caption, the same image with an accurate caption, and an inconclusive case. Verify sources manually and record media-use permissions.

## October 15 — live integration

### You
- [ ] **B5 — Add reliable image-source retrieval.** Integrate Cloud Vision Web Detection or another authorized retrieval source. Record matching pages; never treat similarity as proof of shared context. Current starter has local dHash matching but no reverse-image search.
- [ ] **B6 — Grounding and provenance.** Check source support, date/place relevance and conflicting evidence. Add C2PA parsing only if time permits. Current origin status deliberately remains unknown; no SynthID integration is assumed available.
- [ ] **B7 — Deploy on Google Cloud.** Configure Firestore, least-privilege runtime identity, secrets and Cloud Run. Validate persistence after restart. Set resource/spend limits and decide demo access. Current Dockerfile and adapter require live validation.
- [ ] **B8 — Improve job lifecycle if needed.** Move long investigations to job polling if request duration is unreliable. Keep bounded model calls and explicit failure states. Current route is synchronous with one local concurrent pipeline.

### Partner
- [ ] **F5 — Connect extension to deployed API.** Replace the development endpoint, update narrowly scoped permissions and authenticate requests. No cloud origin is included in the starter manifest.
- [ ] **F6 — Finish evidence UX.** Make origin, contextual claims and unknowns distinct; show source dates and critique limitations. Ensure Google Search attribution is rendered correctly.
- [ ] **F7 — Harden dynamic feed behavior.** Add retry after server recovery, refresh expired matches, cancel stale results, bound match concurrency and test SPA navigation. Confirm disabling lookups removes indicators and stops new requests.
- [ ] **F8 — Add extension matching efficiency.** Cache media fingerprints locally, avoid re-downloading repeated images and move towards fingerprint-only registry lookups. Current opted-in development build sends visible text and first image to localhost for matching.

## October 16 — freeze and verify

### You
- [ ] **B9 — Evaluation report.** Run a labeled set containing correct matches, misleading captions, similar-but-unrelated images, unsupported assertions and prompt-injection text. Record false verdicts, abstentions, source support, latency and actual model usage.
- [ ] **B10 — Reuse evidence.** Demonstrate repeated matching with zero additional model calls; measure fresh pipeline versus lookup latency. Do not fabricate impact metrics.

### Partner
- [ ] **F9 — Browser QA.** Record Chrome version; test real X, local fixtures, extension disabled/enabled, repeated scrolling and popup settings. Check mobile portal at 390 px width and keyboard interaction.
- [ ] **F10 — Demo recording.** Capture a video under three minutes: recognized post -> evidence -> unfamiliar claim investigation -> same image/new caption remains independent.

### Both
- [ ] **J3 — Submission assets.** Complete architecture, setup, limitations and evaluation documentation; create deck and export PDF; verify repository and video access.
- [ ] **J4 — Feature freeze.** Fix reliability issues only. Do not add video support, Instagram, large-scale monitoring or multimodal semantic search.

## October 17 — submission buffer

- [ ] **J5 — Final smoke test.** Fresh browser session, reachable deployed URL, persistent registry, working live Gemini request, source links and extension instructions.
- [ ] **J6 — Submit.** Confirm exact portal cutoff and timezone, select Media, Content & Digital Experiences, and submit deployed link, public repo, deck and video before your cutoff.

## Starter implementation status

- Code written: FastAPI API, SQLite/Firestore store adapters, normalized image identity and dHash candidates, context/date-scoped reuse, Gemini research/assessment/critique adapter, synthetic fixture, portal, MV3 extension and tests.
- Verified locally: 17 Python tests, 3 JavaScript boundary tests, portal loading, synthetic report, exact reuse and changed-caption uncertainty. See `docs/VERIFICATION.md`.
- Still to verify: installed extension on X, live Gemini, Firestore, Cloud Run, mobile/accessibility and real-world evidence quality.
- Not implemented: semantic claim matching, reverse-image web retrieval, provenance/watermark verification, multi-image posts, durable asynchronous jobs and a production sharing/moderation model.
- Semantic similarity, when added, should retrieve candidate evidence only. It must not automatically transfer a prior verdict.

## Pull request completion checklist

- [ ] Behavior and failure states tested.
- [ ] No verdict transferred from media identity alone.
- [ ] No fake sources, invented certainty or demo results presented as live.
- [ ] New secrets, logs and user submissions excluded from Git.
- [ ] Partner can run the change using README instructions.
