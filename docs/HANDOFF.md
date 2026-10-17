# ProofMesh handoff — Hounds of Singularity

Core prototype implementation is complete and deployed. No hackathon form fields, uploads or submission action were performed. The user will review and submit.

## Copy into the submission form

- Challenge: **Media, Content & Digital Experiences**
- Prototype: https://proofmesh-2god3tua3a-el.a.run.app/
- Public repository: https://github.com/htg2704/proofmesh
- Video: https://proofmesh-2god3tua3a-el.a.run.app/assets/demo.mp4
- PDF: `submission/proofmesh-official.pdf` (official organizer template, 15 pages, 2,530,169 bytes, below the 5 MB limit)
- Editable deck: `submission/proofmesh-submission.pptx`
- Brief: copy `submission/BRIEF.txt` (below 1,024 characters)
- Portal cutoff: **October 18, 2026 at 11:59 PM IST**, verified in the actual form.

The video is a 3:20 narrated, edited UI walkthrough. It combines actual actions sampled at approximately two frames per second, recorded live outputs and architecture/evaluation slides; pauses are adjusted. Portal footage uses the local v0.4 interface, and the extension footage uses the hosted fixture. Narration is the built-in macOS Samantha voice, not a team member. It labels recorded cases and does not simulate fresh successful inference. Review it before submitting. The organizer lists YouTube, Vimeo or public Google Drive as video hosts; mirror the final MP4 to one of those destinations before using that link in the form.

## Team use

Public examples work without a token. The private reviewer link is saved in ignored `data/reviewer-access.txt`; it creates an eight-hour browser session in a separate shared review collection. Six admissions were reserved for reviewers, of which one failed. Do not publish the team API token or reviewer code in the repository/deck. The team registry still uses the team API token in Connection settings. The cloud token is in this project's Secret Manager, not in source control. It was saved to the installed Chrome extension only with explicit approval.

The extension files are version 0.4.0. Reload the unpacked extension after updating, choose **Google Cloud demo** and enable visible-post lookups. Local/cloud token slots stay separate. Version 0.4.0 adds timestamp-aware caption context and regression coverage; it also retains the public synthetic deep-link fixes. The user reloaded the installed extension, and its hosted fixture now shows exact reuse, changed-caption abstention and the corrected public report link. Broader X layout coverage remains limited.

## Availability and remaining scope

Live jobs are configured through **November 17, 2026, 23:59:59 IST**, with four attempts per UTC day and twelve total across the window. Four cloud attempts were consumed through October 17; eight remain across the window. The October 17 UTC daily cap is reached; new admissions resume October 18 at 00:00 UTC (05:30 IST). This is bounded access under the approved US$5 total, not unlimited model use. Public recorded examples and registry matches make zero additional model calls.

Automatic Instagram detection is not implemented. You can manually upload a supported image and caption through the authenticated portal. Video/Reels, galleries, watermark checks, semantic claim matching, fingerprint-only requests and broader logged-in X/accessibility validation are deferred. The task board keeps those gaps explicit rather than marking every planned enhancement complete.

Current checks: 47 Python and 27 JavaScript tests. See `EVALUATION.md`, `PRODUCT_QA.md` and `DEPLOYMENT.md` for actual model, browser, persistence and cost-control evidence, including failures and limitations.

Fresh hosted inference remains subject to Vertex capacity: the latest reviewer job failed with provider 429 twice and published no report. Start a judging walkthrough with the public recorded cases, then attempt a new reviewer check when the UTC daily cap permits. No guarantee of fresh inference availability is claimed.
