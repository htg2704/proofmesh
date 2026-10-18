# ProofMesh handoff — Hounds of Singularity

The normal app is deployed. No hackathon submission was made; the user will record their own final demo and submit.

## User experience

Open https://proofmesh-2god3tua3a-el.a.run.app/. Enter a claim/image or prefill an example in the same workspace. No reviewer code, developer key or separate demo page is required. A limited browser workspace is created automatically on demand. New reports are isolated by client; deliberately published examples can be reused only when their exact context is fresh.

The former reviewer credential and reserved allowance are disabled on the hosted service. The separate public synthetic fixture remains only as a developer regression tool, not the main user flow.

## Team testing and third parties

Harshwardhan, Chennika and authorized Codex tests have distinct private testing credentials in ignored `data/TEAM_ACCESS.md`. Use the assigned key once in Connection settings; existing owner API credentials also work. Those credentials bypass application request/daily limits. They are team credentials, so never share them with third-party integrations.

Third parties can obtain a limited REST key at `/developers`, or run their own deployment. Defaults: 120 requests/minute and ten new investigations per UTC day per credential. Keys expire after 30 days, can be revoked, and cannot access other clients' or team reports. See `THIRD_PARTY.md` for commands, CORS, errors and owner administration.

Current v0.6 policy supersedes the earlier count guard: US$10 total project approval, no shared investigation-count cap, 10 trial-funded checks/client/UTC day, 120 API requests/minute. Personal Gemini keys bypass the daily cap and project model-funds circuit; Google bills their owner. Trusted team testing remains application-rate-exempt. See THIRD_PARTY.md for key handling and deployment limits.

## Code and verification

Application image: `3d62817`. Editable diagram correction: `66e7b74`. All 61 Python and 28 JavaScript tests pass; GitHub CI passed. Hosted checks verified real Firestore-backed 429/Retry-After, independent client counters, team-report isolation, immediate revocation, browser CORS and all three trusted exemptions. A fresh ordinary visitor investigation completed with three model calls and one provider attempt per stage; its repeat used zero model calls. Earlier provider 429 failures remain documented in `EVALUATION.md`.

## Materials for the user

- Category: Media, Content & Digital Experiences.
- Repository: https://github.com/htg2704/proofmesh
- Brief: `submission/BRIEF.txt` (953 characters).
- Editable architecture: `docs/diagrams/proofmesh-architecture.drawio`; matching PNG/SVG previews are alongside it. It uses grouped native shapes, datastore cylinders and embedded service icons, and was inspected in draw.io's native viewer.
- Existing official-template presentation: `submission/proofmesh-submission.pptx` and `submission/proofmesh-official.pdf`. These predate the v0.5 access change and new architecture; use the supplied architecture preview when revising the slide. The PDF is 15 pages and below 5 MB.
- Final demo video: user will record it. Existing Drive draft: https://drive.google.com/file/d/1XFfp6bKjPRfR-LIW3-YX574ly6-6Nizc/view?usp=sharing. It is a reference assembled from captures/slides and synthetic narration, not a continuous recording. Demo production is frozen; no further agent voiceover or video work is pending.
- Portal cutoff previously verified in the form: October 18, 2026, 11:59 PM IST. The user submits.

## Remaining product limits

No Instagram adapter, video/Reels or gallery analysis, watermark/C2PA validation, universal AI-origin detector, semantic claim reuse, MCP server or SDK is implemented. Platform/Android/Gemini integrations are proposals. Same-model critique can miss errors. Guest/key isolation is not verified human identity, account recovery, Sybil resistance or production DDoS protection. Broader logged-in X and accessibility coverage remains deferred.

## v0.6 delivered

The hosted main app supports personal Gemini keys, shows per-client trial limits, and no longer imposes a shared investigation-count cap. Citation failures now retain valid findings and distinguish processing errors from insufficient evidence. A live rerun of the private BRICS selfie completed with source-reported AI generation and a partial image association. All 110 automated checks and GitHub CI pass. The supplied real personal key succeeds for plain Gemini inference, but Search-grounded requests return Google 429 RESOURCE_EXHAUSTED. A full personal-key investigation remains blocked by that provider quota. Hosted quota bypass, failure handling and encrypted-key cleanup are verified. Details and limitations are in VERIFICATION.md. The demo/video remains frozen and no submission was made.

## v0.7 delivered: public MVP registry and judge access

The normal app now has **Start a new investigation** as its primary/default form action; it automatically reuses exact fresh reports before inference. **Find an existing report** is secondary and lookup misses offer a direct investigation CTA with clear reuse blockers. Both info popovers describe client quotas and tester/judge exemptions.

The shared public registry has a hard ceiling of **200 snapshots**, with oldest/expired public entries replaced as needed and private copies preserved. New browser reports have a visible sharing choice; REST calls stay private unless explicitly opted in. Existing private reports were not retroactively published. Public listing/links, cross-client zero-call reuse, withdrawal and private-report isolation are verified on Cloud Run/Firestore. The editable architecture and API/deployment docs are updated.

The separately scoped judge token is active; the owner can retrieve its value and submission instructions from ignored **data/JUDGE_ACCESS.md**. Judges have no application request/daily caps, team-report access or administrative privileges. Google quotas and project-funded spending approval still apply. The token expires November 17, 2026, 23:59:59 IST. No token was added to GitHub or a public URL, and no submission was made. Current suite: **126 checks passed**, with GitHub CI green for source `5eebaf2`.

## Final public-access policy change

At the owner's request, application client request, daily investigation and public-registration caps are disabled. Judges can use the normal app with automatic guest access and no special token. The separate judge credential still works for an isolated workspace through Advanced access, but its public shortcut is hidden. The owner explicitly approved **US$50 total project-funded usage** from existing trial credits, superseding the US$10/US$20 approvals. At authorization US$7.50 was reserved under the conservative US$0.50/attempt circuit, leaving 85 fresh attempt reservations; these figures are not an invoice. Provider quotas, workload bounds, the existing live window and private-data isolation remain. Update slide 9 if it still describes the retired 10-check client limit.
