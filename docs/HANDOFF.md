# ProofMesh handoff — Hounds of Singularity

Core prototype implementation is complete and deployed. No hackathon form fields, uploads or submission action were performed. The user will review and submit.

## Copy into the submission form

- Challenge: **Media, Content & Digital Experiences**
- Prototype: https://proofmesh-2god3tua3a-el.a.run.app/
- Public repository: https://github.com/htg2704/proofmesh
- Video: https://proofmesh-2god3tua3a-el.a.run.app/assets/demo.mp4
- PDF: `submission/proofmesh-official.pdf` (official organizer template, 15 pages, about 2.53 MB, below the 5 MB limit)
- Editable deck: `submission/proofmesh-submission.pptx`
- Brief: copy `submission/BRIEF.txt` (938 characters, below 1,024)
- Portal cutoff: **October 18, 2026 at 11:59 PM IST**, verified in the actual form.

The video is a 3:20 captioned walkthrough assembled from genuine captures of the deployed product. It has no narration and is not a continuous live screen recording. It labels recorded model examples and does not simulate new inference. Review it before using it; the script is available if you prefer to record your own narrated version.

## Team use

Public demo examples work without a token. New arbitrary live investigations and the private registry require the team API token in Connection settings. The cloud token is in this project's Secret Manager, not in source control. It was saved to the installed Chrome extension only with explicit approval.

The extension files are version 0.4.0. Reload the unpacked extension after updating, choose **Google Cloud demo** and enable visible-post lookups. Local/cloud token slots stay separate. The final 0.4.0 patch fixes anonymous synthetic-report deep links and the popup workspace link.

## Availability and remaining scope

Live jobs are configured through **November 17, 2026, 23:59:59 IST**, with four attempts per UTC day and twelve total across the window. Four cloud attempts were consumed through October 17; eight remain across the window. The October 17 UTC daily cap is reached; new admissions resume October 18 at 00:00 UTC (05:30 IST). This is bounded access under the approved US$5 total, not unlimited model use. Public recorded examples and registry matches make zero additional model calls.

Automatic Instagram detection is not implemented. You can manually upload a supported image and caption through the authenticated portal. Video/Reels, galleries, watermark checks, semantic claim matching, fingerprint-only requests and broader logged-in X/accessibility validation are deferred. The task board keeps those gaps explicit rather than marking every planned enhancement complete.

Current checks: 47 Python and 27 JavaScript tests. See `EVALUATION.md`, `PRODUCT_QA.md` and `DEPLOYMENT.md` for actual model, browser, persistence and cost-control evidence, including failures and limitations.
