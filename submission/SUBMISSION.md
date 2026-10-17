# ProofMesh submission pack

Team: **Hounds of Singularity**

Members: **Harshwardhan and Chennika**

Category: Media, Content & Digital Experiences

## Short description

ProofMesh is a shared evidence rail for media claims. Its web workspace and X extension are the first applications on a common API. Its Chrome extension recognizes previously investigated posts, while its portal researches unfamiliar claims with Gemini, Cloud Vision and fetched source pages. Matching an image never transfers another caption's verdict. Missing evidence stays unresolved, and AI origin remains unknown unless actually verified.

## Problem

A genuine photograph can be paired with a false date or story. Readers often have to leave their feed and repeat research someone else already performed. ProofMesh separates the identity of the image from the exact claim and reuses only investigations belonging to the same context.

## Rail and reference applications

The shared API exposes context lookup, queued investigation and report retrieval. Cloud Run hosts this service and its reference web workspace. Firestore persists reports, job state and admission limits. Cloud Tasks delivers durable investigations; a private Cloud Storage bucket holds temporary uploads. Cloud Vision finds matching-page leads, while Gemini on Vertex AI researches, assesses retrieved passages and challenges conclusions. Secret Manager and attached service identities keep credentials out of source code.

## Demonstrated behavior

Twelve prespecified development cases produced 11 expected outcomes, nine conclusive findings and three abstentions. All twelve exact repeats used zero additional model calls. Three first attempts hit provider 429 and required explicit bounded reruns. One known false flag assertion stayed unresolved because source-quotation validation failed. A fresh hosted reviewer job also hit 429 twice and failed safely. These are engineering checks, not representative detection accuracy. See `docs/EVALUATION.md`.

## Links and final fields

- Repository: https://github.com/htg2704/proofmesh
- Hosted portal: https://proofmesh-2god3tua3a-el.a.run.app
- Deck: `proofmesh-submission.pptx` / `proofmesh-official.pdf`
- Final demo video: **User will record and supply the final link.**
- Draft reference only: https://drive.google.com/file/d/1XFfp6bKjPRfR-LIW3-YX574ly6-6Nizc/view?usp=sharing
- Draft MP4 reference: https://proofmesh-2god3tua3a-el.a.run.app/assets/demo.mp4 (3:20, edited UI walkthrough with synthetic narration and recorded model results; local portal and hosted extension footage). The approved Google Drive file is shared with anyone holding the link as Viewer.
- Team name: Hounds of Singularity. Member details: enter the exact names from your registration.
- Portal-verified cutoff: October 18, 2026 at 11:59 PM IST. Deck must follow the official template, PDF under 5 MB; video must be 3–4 minutes. The form is left for the user to submit.

## Known limitations

No watermark or universal AI detector, semantic claim reuse, video support or multi-image analysis. Critique uses the same model. Logged-in X layouts need broader validation. Public examples are saved runs; new live checks require team credentials or a scoped reviewer session and have a time limit. Budget alerts and instance limits are not an absolute billing cap.

## Integration roadmap

Future SDK/MCP adapters could let agents consume the same context-bound evidence. Social-platform and Android/Gemini integrations are proposed consumers, not existing integrations or partnerships. The prototype does not yet provide production tenant isolation, a stable versioned external API or a moderation workflow. See `docs/RAIL.md`.

Demo/voiceover work is frozen at the user's request. The existing draft uses screen captures, slides and synthetic narration, not a continuous screen recording. Do not use it as the final submission video without the user's decision.
