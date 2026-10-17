# ProofMesh submission pack

Team: **Hounds of Singularity**

Members: **Harshwardhan and Chennika**

Category: Media, Content & Digital Experiences

## Short description

ProofMesh adds reusable, source-linked context to media claims. Its Chrome extension recognizes previously investigated posts, while its portal researches unfamiliar claims with Gemini, Cloud Vision and fetched source pages. Matching an image never transfers another caption's verdict. Missing evidence stays unresolved, and AI origin remains unknown unless actually verified.

## Problem

A genuine photograph can be paired with a false date or story. Readers often have to leave their feed and repeat research someone else already performed. ProofMesh separates the identity of the image from the exact claim and reuses only investigations belonging to the same context.

## Implementation

Cloud Run hosts a FastAPI portal and API. Firestore persists reports, job state and admission limits. Cloud Tasks delivers durable investigations; a private Cloud Storage bucket holds temporary uploads. Cloud Vision finds matching-page leads, while Gemini on Vertex AI researches, assesses retrieved passages and challenges conclusions. Secret Manager and attached service identities keep credentials out of source code.

## Demonstrated behavior

The selected evaluation contains a supported historical caption, a contradicted caption on the same image, an unresolved private assertion with no evidence, and an injection that attempts to invent a source ID. All four exact repeats used zero additional model calls. This is a small demonstration, not a representative accuracy benchmark. Provider failures and evaluation limits are documented in `docs/EVALUATION.md`.

## Links and final fields

- Repository: https://github.com/htg2704/proofmesh
- Hosted portal: https://proofmesh-2god3tua3a-el.a.run.app
- Deck: `proofmesh-hounds-pitch.pptx` / `proofmesh-hounds-pitch.pdf`
- Demo recording: see `DEMO_SCRIPT.md`; attach the final video link after recording/upload.
- Team name: Hounds of Singularity. Member details: enter the exact names from your registration.
- User-confirmed cutoff: midnight between October 18 and 19, 2026, India time (October 19 at 00:00 IST). Verify the form is complete before the cutoff.

## Known limitations

No watermark or universal AI detector, semantic claim reuse, video support or multi-image analysis. Critique uses the same model. Logged-in X layouts need broader validation. Public examples are saved runs; paid live endpoints require team credentials and have a time limit. Budget alerts and instance limits are not an absolute billing cap.
