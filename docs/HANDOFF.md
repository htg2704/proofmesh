# ProofMesh handoff — Hounds of Singularity

The normal app is deployed. No hackathon submission was made; the user will record their own final demo and submit.

## User experience

Open https://proofmesh-2god3tua3a-el.a.run.app/. Enter a claim/image or prefill an example in the same workspace. No reviewer code, developer key or separate demo page is required. A limited browser workspace is created automatically on demand. New reports are isolated by client; deliberately published examples can be reused only when their exact context is fresh.

The former reviewer credential and reserved allowance are disabled on the hosted service. The separate public synthetic fixture remains only as a developer regression tool, not the main user flow.

## Team testing and third parties

Harshwardhan, Chennika and authorized Codex tests have distinct private testing credentials in ignored `data/TEAM_ACCESS.md`. Use the assigned key once in Connection settings; existing owner API credentials also work. Those credentials bypass application request/daily limits. They are team credentials, so never share them with third-party integrations.

Third parties can obtain a limited REST key at `/developers`, or run their own deployment. Defaults: 120 requests/minute and ten new investigations per UTC day per credential. Keys expire after 30 days, can be revoked, and cannot access other clients' or team reports. See `THIRD_PARTY.md` for commands, CORS, errors and owner administration.

The approved US$5 financial guard is preserved: twelve total job admissions across the live window, five consumed and seven remaining at verification. Trusted rate exemptions do not bypass that shared guard, provider capacity or the November 17, 2026, 23:59:59 IST expiry. Recorded results and exact reuse require no extra model calls. Workload controls are not an absolute Google billing cap.

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
