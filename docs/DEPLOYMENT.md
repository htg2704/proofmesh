# Google Cloud deployment — verified October 17, 2026

Project: `project-9e0a8470-4ba3-458b-885` (ProofMesh), owned through the user-approved account. No billing upgrade or new billing account was created.

Portal: https://proofmesh-2god3tua3a-el.a.run.app/

## Resources

Cloud Run, Firestore Native, the task queue and private storage use `asia-south1` (Mumbai). Gemini 3.5 Flash uses the global Vertex AI endpoint; this is not an India-only residency guarantee.

- Cloud Run: zero minimum instances, one maximum instance, 1 CPU, 512 MiB, concurrency 8, request-based CPU, 300-second timeout.
- Firestore: reports, durable job documents and transactional daily/whole-window admission counts.
- Cloud Tasks: `proofmesh-investigations`, one concurrent dispatch, one dispatch/second, bounded delivery retry. The worker's persistent claim prevents duplicate inference.
- Private image bucket: upload for queued work, deletion after execution, one-day lifecycle backstop. Uniform bucket-level access and public-access prevention are enabled.
- Secret Manager: separate API and worker secrets. No service-account private keys are deployed.
- Build artifacts: a dedicated Artifact Registry repository and a private build-source bucket with three-day cleanup.

`proofmesh-runtime` has Vertex AI use, Firestore data access, service-use permission, image-bucket object access, secret-specific access and queue-specific enqueue permission. It can act as only the dedicated task-caller identity, which has Cloud Run Invoker on this service. The separate build identity has log writing, artifact writing and build-source reading. No Owner or Editor role is granted to these runtime/build identities.

## Access

The user explicitly approved public Cloud Run invocation. Public application routes serve the synthetic demo and three deliberately published recorded investigations. They cannot invoke paid inference or read the live registry. Paid jobs, job status and private reports require the team API token. The worker separately validates its worker secret and receives a Cloud Tasks OIDC token.

For team use, read `proofmesh-api-token` in this project's Secret Manager and enter it in the portal's Connection settings. Do not add it to the submission text or public repository. The installed Chrome extension has the cloud token stored with explicit user approval; local and cloud token slots are separate.

Public demo routes and new live-token routes are different. Judges can inspect the public examples immediately; running arbitrary new claims requires the team's access token. This is a shared hackathon token, not a complete multi-user authentication system.

## Live window and cost controls

The user requested one month of availability. New hosted live submissions are configured through **November 17, 2026 at 23:59:59 IST**. Four new attempts per UTC day and twelve attempts across the full window are admitted transactionally. Explicit retries count again. Four cloud attempts have been consumed, including two failed jobs; eight remain across the window. The October 17 reviewer job failed with provider 429 after both bounded stage attempts. The four-attempt UTC daily cap is reached; it resets October 18 at 00:00 UTC (05:30 IST). Cache matches and public recorded views do not consume inference admissions.

The approved spending limit remains **US$5 total**. An INR450 project-scoped monthly usage alert, excluding credits, notifies at 50%, 90% and 100% in the billing account's currency. The USD-denominated alert was rejected by the account; no duplicate USD budget was created. Workload caps, instance limits and alerts are not an absolute billing-account dollar cap. Actual billing can lag; model-token estimates in the evaluation are not receipts.

## Verified behavior

- Anonymous health and recorded-example reads: 200.
- Anonymous live registry/job reads, new paid jobs and worker calls: 401.
- Text job: the first provider request failed safely; one explicit retry completed in 10.531 seconds with three model calls. Firestore exact reuse: 104.5 ms, zero model calls.
- The report survived a separate Cloud Run revision restart.
- Image job: private upload, Vision lookup and Gemini completed in 22.892 seconds, supported; exact reuse took 178.7 ms with zero model calls. Its image key was cleared and the private bucket was empty afterward.
- Installed extension verified against the hosted synthetic feed and public `x.com/NASA`, with unknown posts left unverified.

## Rebuild

Run `scripts/provision.py` only against the named project after reviewing its scope. It creates missing named resources and reapplies scoped IAM; it does not change billing linkage. The checked-in `.gcloudignore` excludes credentials, `.env`, `data/`, dependencies and submission files from the build context. Docker copies only application and web assets. Build with `cloudbuild.yaml` and a versioned `_IMAGE` substitution, then update the existing Cloud Run service image. Keep all existing secret references and workload limits.

The initial unused project `proofmesh-htg2704-2026` was not altered during this deployment. No claim is made that it was deleted or unlinked from billing.

## v0.4 reviewer workspace

A separate Secret Manager reviewer credential creates an eight-hour HttpOnly, Secure, SameSite=Strict signed cookie. The private link is stored only in ignored `data/reviewer-access.txt`; do not publish it or the team token in the repo or public deck. Opening the link exchanges and removes its fragment. Six of the twelve global admissions are reserved for the shared review collection; one was consumed by the failed browser test. Reviewer sessions cannot read team reports/jobs or choose the live corpus. The same global daily/window/time limits apply. This is a shared evaluation workspace, not individual multi-user isolation.

Provider 429 can still exhaust the bounded retry. The service already uses the global endpoint; no paid capacity reservation or billing upgrade was added. The v0.4 hosted fresh-run test therefore remains an observed failure. Public recorded cases remain the reliable starting path.
