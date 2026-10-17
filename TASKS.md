# ProofMesh — release task board

Team: **Hounds of Singularity** — Harshwardhan Tripathi and Chennika.

Portal-verified prototype submission cutoff: **October 18, 2026, 11:59 PM IST**. Team formation has a separate October 17 cutoff; the portal already shows the two-member team. The user will submit; the agent must not submit the form.

A checked item records verified acceptance, not merely code written. Evidence: `docs/PRODUCT_QA.md`, `docs/EVALUATION.md`, `docs/DEPLOYMENT.md`.

## Harshwardhan — core intelligence and infrastructure

- [x] **B1 — API contract:** v0.2 job/polling contract and unchanged claim/image identity agreed in code and client tests.
- [x] **B2 — Registry/cache:** exact-context reuse, changed-caption isolation, expiry and restart persistence tested. Exact lookup no longer depends on a 1,000-row scan.
- [x] **B3 — Vertex AI:** project-local credentials, live Gemini, bounded output and no automatic SDK retries verified.
- [x] **B4 — Investigation quality:** supported, contradicted and unresolved selected cases plus critique-rejection tests. Provider failures and a missed incidental date error are documented; no general accuracy guarantee.
- [x] **B5 — Image-source retrieval:** Cloud Vision matching-page leads verified locally and in the hosted image job. Matching is not proof of caption or origin.
- [x] **B6 — Source grounding:** bounded HTTPS page retrieval, unsafe-address rejection, fetched-passage requirement, date/place critique and explicit provenance unknowns. C2PA/watermarks remain deferred.
- [x] **B7 — Google Cloud:** Cloud Run, Firestore, private temporary images, identities, secrets, workload caps and billing alert configured. Persistence across revision restart and upload deletion verified.
- [x] **B8 — Job lifecycle:** durable Cloud Tasks delivery, transactional deduplication, polling, explicit failure states and one bounded manual retry. Interrupted paid work is not silently repeated.
- [x] **B9 — Evaluation:** selected factual/context, no-evidence and injection cases; source support, real timings and provider usage recorded.
- [x] **B10 — Reuse evidence:** four local repeats and hosted text/image repeats made zero additional model calls; actual latency recorded.

## Chennika — extension and product

- [x] **F1 — Local portal/installed extension:** user loaded extension, enabled lookups and approved credential storage.
- [x] **F2 — Caption isolation:** hosted and local synthetic feed show exact reuse for the first caption and no inherited verdict for the second.
- [x] **F3 — X extraction:** actual public NASA feed checked; current markup, supported images and explicit video abstention verified.
- [x] **F4 — Portal states:** auth correction, offline behavior, upload errors, empty/unresolved evidence, export and 390px layout covered in the QA record.
- [x] **F5 — Hosted integration:** fixed Cloud Run origin, narrowly scoped permission, separate local/cloud settings, protected registry lookup and short job enqueue. Version 0.4.0 fixes synthetic-report deep links; final reload verification is recorded in the handoff.
- [x] **F6 — Evidence UX:** origin/context/findings separated, fetched passages distinguished from leads, retrieval/page dates labeled, uncertainty and a visible QA correction retained. Search attribution is sandboxed.
- [x] **F7 — Dynamic-feed handling:** stale-node responses, retries, route changes, disabling and refresh/concurrency controls have regression coverage.
- [ ] **F8 — Fingerprint-only lookup (deferred):** bounded five-minute image-byte cache added. Sending fingerprints without image bytes is not implemented; opted-in lookups still send visible post text and image to the selected backend.
- [ ] **F9 — Broader browser/accessibility QA (deferred):** Chrome 155.0.8059.80 public X and hosted fixtures verified. Full logged-in X variants and screen-reader coverage are not established.
- [x] **F10 — Demo asset:** 3:20 captioned walkthrough assembled from actual working-build captures. It is not a continuous narrated screen recording; review or replace it before submission if desired.

## Joint release and submission

- [x] **J1 — Shared repository:** public `https://github.com/htg2704/proofmesh`, code pushed and CI checked.
- [x] **J2 — Demo cases:** historical Earthrise caption, misleading caption on the same image and a genuinely inconclusive no-media assertion. Source/media attribution recorded.
- [x] **J3 — Submission pack:** official template adapted, PDF under 5 MB, editable PPTX, demo script/video and description prepared. Public links verified in the handoff.
- [x] **J4 — Feature freeze:** Instagram, video analysis, watermark verification and semantic claim matching remain outside this release.
- [x] **J5 — Final technical smoke:** public routes, authentication boundary, queued Gemini runs, image cleanup, restart persistence and zero-call reuse verified. The user should still review the presentation/video and replay the demo before submitting.
- [ ] **J6 — Submit (user only):** choose Media, Content & Digital Experiences, attach the official PDF, provide public prototype/repository/video links and brief description before the portal cutoff. No submission has been made by the agent.

## Scope limits

This is a working hackathon prototype, not a reliable universal real/fake or AI-origin classifier. Same-model critique can miss errors. Instagram browsing is unsupported; an image/caption can be submitted manually in the authenticated portal. No multi-image or video analysis is implemented. See the evaluation report for observed failures and the deployment record for access, expiry and quota details.

## v0.4 gap fixes — October 17

- [x] Fix completed-job polling recursion and stale reports after a new failure.
- [x] Isolate a reviewer collection; reserve six admissions; verify no access to team reports.
- [x] Carry publication timestamps through X extraction, jobs, cache identity and report display.
- [x] Validate exact source quotations; expose date/location/media checks and preserve origin uncertainty.
- [x] Run the prespecified twelve-case development set; publish the 11/12 result and original provider failures.
- [x] Add one bounded retry of a 429-failed stage, with attempt accounting.
- [x] Refresh the three public examples from actual v0.4 runs.
- [ ] Record and review the updated narrated walkthrough, refresh the official deck, and publish the final release.
- [ ] User: reload extension 0.4.0; review final materials and submit the hackathon form.

Fresh hosted reviewer inference hit provider 429 twice and failed safely. This remains an availability limitation; passing local live cases and regression tests do not erase that failure.
