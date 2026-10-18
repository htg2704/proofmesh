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

The main app creates a scoped guest cookie on first use; judges can run their own claims without a reviewer code. Developer integrations use scoped bearer credentials. Public examples are deliberately published; private reports remain scoped.

## Live window and cost controls

Project-funded live checks remain configured through **November 17, 2026 at 23:59:59 IST**. Current per-client and personal-key policy is below; older shared daily/window counts are no longer enforced. Exact cached reuse and recorded views make no inference calls.

The approved project spending limit is **US$10 total**. An INR450 project-scoped monthly usage alert, excluding credits, notifies at 50%, 90% and 100% in the billing account's currency. The USD-denominated alert was rejected by the account; no duplicate USD budget was created. Workload caps, instance limits and alerts are not an absolute billing-account dollar cap. Actual billing can lag; model-token estimates in the evaluation are not receipts.

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

The legacy reviewer-code flow is retired on the hosted deployment. No reviewer secret is injected; normal visitors receive individual guest credentials.

## v0.5 access policy update

Ordinary visitors no longer need the legacy reviewer code. Set `PROOFMESH_SELF_REGISTRATION=true` for automatic guest sessions and developer-key registration. Client request counters, hashed credentials and per-client daily admission state persist in Firestore. Existing collection namespaces isolate private client reports/jobs from each other and from team data. `PROOFMESH_CLIENT_REQUESTS_PER_MINUTE=120`, `PROOFMESH_CLIENT_DAILY_JOBS=10`, `PROOFMESH_REGISTRATIONS_PER_HOUR=30` are the defaults.

`PROOFMESH_TRUSTED_TOKENS` is a JSON map injected from `proofmesh-trusted-tokens:1` in Secret Manager; the runtime identity receives access only to that secret. It contains separate credentials for Harshwardhan, Chennika and authorized Codex testing. Application request/daily/reviewer-reservation limits are bypassed for trusted team callers. There is no shared investigation-count cap. Project-funded work has a monetary reservation circuit under the US$10 approval; personal-key model work uses the caller’s Google account. The hosted legacy reviewer credential and its reserved allowance are disabled. The former shared four-per-day cap does not apply to ordinary browser/developer clients or the team. Existing owner tokens are also rate-exempt.

The public credential issuance cap is shared. This is not verified individual identity or hardened public abuse prevention. Use owner-issued keys by setting self-registration false when you need a controlled pilot. All fresh local and hosted inference now uses jobs so the synchronous endpoint cannot bypass admission controls.

## v0.6 quota and evidence update

Third-party defaults increase from 60 to 120 requests/minute, from two to ten new investigations/UTC day per credential, and from five to thirty new credentials/hour across the deployment. Existing counters persist; limits are not bypassed by a revision restart. The shared count guard has been removed; see the current personal-key configuration below. A citation-repair stage can add one logical model call to a job; it is not a new research loop or automatic whole-job retry.

## Personal Gemini keys and current trial policy (v0.6)

Inject `PROOFMESH_CREDENTIAL_ENCRYPTION_KEY` from a separate Secret Manager secret containing a Fernet key. Grant the runtime identity secret accessor on that secret only; never put it in an image or committed env file. For local development generate a key with `Fernet.generate_key()` and keep it in ignored `.env`. Set `GEMINI_API_MODEL=gemini-3.6-flash`. `PROOFMESH_ENABLE_LIVE=true` controls both inference paths.

`PROOFMESH_TOTAL_JOBS` and reviewer reservation counters no longer restrict admission. Remove their deployment configuration. Per-client limits are 120 requests/minute and 10 trial-funded investigations/UTC day; personal-key jobs bypass the daily check cap, not request/provider quotas. Configure `PROOFMESH_PROJECT_BUDGET_USD=10`, `PROOFMESH_BUDGET_BASELINE_USD=4` and `PROOFMESH_JOB_RESERVE_USD=0.50` for the current conservative trial-funds circuit. Its transactional `proofmesh_limits/project_funds` ledger persists across restarts; do not reset it to create additional spending authority. The baseline reserves earlier costs rather than asserting an invoice total. It does not reserve funds for personal-key jobs. Keep the billing alert and zero-minimum-instance workload bounds; this circuit is not an absolute invoice cap.

Queued provider keys are encrypted, cryptographically expire after 15 minutes, and are cleared on terminal worker paths or stale reads. Never enable request-body logging. See [credential handling and limitations](THIRD_PARTY.md#use-your-own-gemini-api-key). Rotation of the encryption key invalidates pending personal-key jobs; allow them to drain first.
