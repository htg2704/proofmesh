# Verification record — October 14, 2026

## Resumed verification — October 15

- Re-ran all 17 Python tests, all 3 JavaScript tests, and both JavaScript syntax checks successfully.
- Verified GitHub reports `htg2704/proofmesh` as public, with `main` as the default branch.
- Verified local `main` and fetched `origin/main` both pointed to starter commit `67161aa77c918295d5448f04c315e5b4f3aed8f2` before this documentation update.
- Verified [GitHub Actions run 38604551946](https://github.com/htg2704/proofmesh/actions/runs/38604551946) completed successfully for that starter commit.
- The installed-extension and Cloud Run limitations below remain outstanding. The live Gemini configuration is now verified by the additional smoke test below.

## Vertex AI setup and smoke test — October 15

- The active `proofmesh` gcloud profile uses the user-approved account and the trial-credit project. App credentials are stored in Git-ignored `data/gcloud-trial/`; `.env` selects that credential file and project explicitly. The prior global ADC file was not replaced.
- Verified trial billing linkage and that `aiplatform.googleapis.com` is enabled.
- Configured `gemini-3.5-flash` on the global endpoint. Existing SDK default automatic retries are disabled; each stage has an explicit output-token limit.
- Live claim: NASA's Perseverance rover landed on Mars on February 18, 2021.
- Result: supported, with three evidence segments from two distinct source URLs. The sources were Wikipedia and Royal Museums Greenwich, so this does not establish a primary-source-only retrieval policy.
- Three model invocations completed in **22.76 seconds**. A repeat retrieved the persisted report with **zero model calls**.
- Provider-reported totals: **2,006 prompt tokens**, **264 candidate-output tokens**, **1,304 thinking tokens**, and **one reported search query**.
- At the published Gemini 3.5 Flash global rates checked October 15, indicative model token cost is **US$0.017121**, before search charges, credits, taxes and final billing adjustments. One search query would add US$0.014 if outside the account's free allowance. This estimate is not a billing receipt or a hard account spend cap.
- An earlier attempt on the initial project returned HTTP 504 and published no report. The working setup uses the new trial-credit project; the unused initial project's billing linkage was not changed.
- Added three mocked provider tests covering quota attribution, no retries, token limits, abstention without grounding and critique rejection. **20 Python tests and 3 JavaScript tests pass** after these changes. Mock tests do not make paid calls.

## Passed locally

- Python: **17 tests passed** using Python 3.12 and the frozen dependencies in `requirements.txt`.
- JavaScript: **3 tests passed** using Node's built-in test runner.
- Syntax checks: `web/app.js`, `extension/content.js`.
- Installed Google Gen AI SDK accepts the structured Assessment schema and Google Search tool configuration. This is a local compatibility check, not a live model call.
- Portal loaded in a real browser at `http://127.0.0.1:8000`.
- **Load synthetic example** created a persistent report and displayed its source fixture and limitations.
- **Check shared evidence** returned an exact context match and displayed zero model calls.
- **Try the alternate caption** returned related media, displayed unverified status and did not transfer the stored verdict.
- Full-page desktop visual inspection found no clipping in the tested flow.
- Restart persistence is covered by a new SQLite connection in the automated tests.

One dependency emits a Starlette warning about future test-client migration from httpx to httpx2. The tests pass; no runtime failure was observed.

## Product follow-up — October 15

Partner tasks F1–F4 are completed within the documented browser coverage. See [the product QA record](PRODUCT_QA.md) for the installed extension, public X extraction, upload limits, token handling, mobile layout and exports. Current suite: **20 Python + 21 JavaScript tests**.

## Not yet verified

- Broad evaluation of live grounding quality, billed cost reconciliation, search attribution styling, and contradicted/unresolved cases. One successful live request is documented above.
- Firestore against a Google Cloud project and Cloud Run container execution/deployment.
- Logged-in X variants, screen reader behavior, galleries/quoted posts in actual logged-in X DOM, long-running worker behavior and broader network recovery. Public X, fixture Chrome integration and 390-pixel mobile layout are verified in the product record.
- CI for the starter commit is verified above; subsequent commits have their own workflow results.

## What this establishes

The deterministic first slice demonstrates separate image and caption identity, exact-context reuse, explicit unknowns and a readable evidence report. It does **not** establish misinformation detection accuracy, trustworthy AI-origin detection or production readiness.

## Release verification — October 17

Current suite: 36 Python + 23 JavaScript tests. Public hosted portal, private live API boundary, durable text/image jobs, Cloud Storage cleanup and Firestore persistence after revision restart are verified in `DEPLOYMENT.md`. The installed hosted extension was checked on the synthetic feed and actual public X in Chrome 155.0.8059.80. Selected model outcomes, initial provider failures and an incidental temporal wording error are documented in `EVALUATION.md`; no accuracy percentage is claimed.

The official submission template was downloaded from the organizer's linked Google Slides, adapted locally, rendered and exported to a PDF under 5 MB. The captioned video is 3:20. The organizer's form was read only; no form fields, uploads or Submit action were performed.

## v0.4 gap-fix verification — October 17

47 Python and 27 JavaScript tests pass. Prespecified evaluation, publication context, exact quotation checks and first-pass failures are recorded in `EVALUATION.md`. Reviewer login and team/report collection isolation passed against Cloud Run. Fresh reviewer inference failed with provider 429 on both bounded research attempts; no report was published. The previous report being left on screen was fixed and regression-tested. The user reloaded extension 0.4.0; hosted exact/changed-caption behavior and its corrected public report link were verified directly. The public frozen samples were refreshed from v0.4 runs and keep explicit recorded-example labels.

## v0.5 normal app and third-party access — October 17

61 Python and 28 JavaScript checks pass. Hosted Firestore-backed verification confirmed a limited client receives 429 with Retry-After, another client stays unaffected, private team reports return 404, revocation returns 401, and cross-origin bearer preflight succeeds without cross-origin cookie credentials. All three trusted testing credentials returned rate-exempt team access. Disposable QA keys were revoked.

The ordinary browser flow opened an isolated workspace without a code, reused a selected public example, then completed a fresh Canberra investigation with three model calls and one provider attempt per stage. Its repeat used zero model calls. The report stayed in a client namespace. This is an integration check, not another independent accuracy benchmark. Hosted legacy reviewer credentials and reserved quotas are retired. The shared guard has five of twelve admissions consumed.

The editable draw.io file was opened in the native viewer; embedded logos, grouped components and corrected datastore cylinders were visually checked. SVG/PNG previews derive from the same layout. Application image 3d62817; diagram correction 66e7b74. CI: https://github.com/htg2704/proofmesh/actions/runs/39047021769. No demo/voiceover work or hackathon submission was performed in this phase.

## v0.6 personal-key and evidence verification — October 18

Deployed application image `4498c8a` as Cloud Run revision `proofmesh-00012-cw5`. GitHub Actions passed for that source and the diagram follow-up `058260f`. Local suite: **79 Python + 31 JavaScript tests**. Hosted health confirms 120 requests/minute, 10 trial-funded checks/client/UTC day, personal-key support enabled, and no shared investigation-count cap. The main page visibly displays these limits and the personal-key panel. The updated editable diagram includes Vertex and Gemini Developer API branches.

Rechecked the user's private BRICS image with the original short caption “BRICS 2026 selfie”. The hosted job succeeded with three model calls, one provider attempt per stage, no citation repair needed and no validation diagnostics. The factual finding was contradicted; the origin field was `reported_ai_generated` with a **partial** image-match association. The independent provenance/watermark state remains `not_performed`. This is one successful regression case, not an accuracy benchmark. The image and complete report remain in ignored local data/private team storage; they were not added to public examples.

Used a disposable developer identity with its real Firestore trial counter set to 10. A new project-funded job returned 429. A personal-key job was admitted (202), then a deliberately invalid test key returned provider 400. The encrypted credential was cleared, the daily trial counter remained 10, and the project-funds ledger was unchanged. The disposable developer credential was revoked. This verifies the deployed admission, queue, negative provider route and cleanup; At this point successful inference using a real personal Gemini key had not been exercised; see the follow-up below. Unit tests verify SDK routing without ADC/Vision, successful secret delivery to the mocked model pipeline, encryption, rotation, expiry and removal from reports/responses. Browser tests verify the key never enters local/session storage or lookup/poll URLs and can be cleared.

Project-funded admissions use the approved US$10 monetary reservation circuit, not the removed shared count quota. Personal-key jobs bypass that circuit; Google and API request quotas remain. No hackathon submission or demo/voiceover change was made.

### Supplied personal Gemini key follow-up — October 18

The user supplied a real key for testing. One hosted investigation was admitted for a disposable client already at its daily trial allowance, but failed with provider 429 after the bounded retry. The encrypted credential was cleared, project model-funds reservations and the client trial counter were unchanged, and the temporary ProofMesh credential was revoked.

A single small direct `gemini-3.6-flash` request succeeded. A separate bounded request with Google Search grounding returned `429 RESOURCE_EXHAUSTED`, with Google's message to check current quota, plan and billing. This isolates a provider quota blocker for grounded requests; it does not establish that a specific billing change is required or that the key's whole project has no quota. A complete successful personal-key investigation remains unverified. No further automatic retries were made. The supplied key was read through a hidden terminal prompt and was not put in source, shell arguments, reports or committed documentation.

## v0.7 shared registry, primary action and judge access — October 18

Deployed source `5eebaf2` as Cloud Run revision `proofmesh-00013-bkk`; GitHub Actions passed. **92 Python and 34 JavaScript tests pass (126 total)**. Coverage includes concurrent publication beyond 200 entries, exact cross-client reuse, privacy allowlists, private-by-default REST behavior, failed publication preserving paid results, stale/policy/context blockers, ownership/withdrawal, judge expiry/isolation/admin denial and application-limit exemptions. Browser tests verify the primary form submission starts investigations, lookup-only results have a direct investigation CTA, public report links work without creating a guest workspace, and info controls display the ordinary trial numbers and judge/tester exemptions.

An isolated Firestore QA collection verified transactional capacity three, oldest-public-snapshot replacement, retained private copies, persistence through a new store instance, and withdrawal. Its test-only collections/index were cleaned up. The production cap is 200; no production retention entries were replaced during this check.

Hosted judge authentication and exemption were verified using the separate Secret Manager credential after explicit user approval for its runtime secret-only IAM grant. The judge could not read a private team BRICS report or list/administer client credentials. One new factual investigation of the Perseverance landing completed with four logical model calls (including citation repair), a supported finding, complete assessment status and a published public snapshot. Two separately issued consumer credentials matched and reused that snapshot with zero model calls and no added project-funds reservations. Neither could read the private original; their own private histories stayed empty. A changed Mars/Venus caption did not inherit the verdict. The publisher withdrew and republished the public copy without rerunning inference. Temporary consumer credentials were revoked.

The hosted main UI was inspected in Chrome: **Start a new investigation** is the first filled primary action, **Find an existing report** is secondary, sharing is a visible choice, the info popover states 10 trial checks/client/UTC day and 120 API requests/minute, and the public registry displays its occupancy/capacity separately from private history. The lookup miss label is **Not assessed for this context** with explicit reuse blockers, rather than a truth verdict of “Unverified.”

The actual judge token/instructions are in ignored `data/JUDGE_ACCESS.md` (mode 0600), not GitHub, browser assets or this document. It remains valid through November 17, 2026, 23:59:59 IST. Provider quotas and the approved project-funded spending limit still apply. Existing private tester/BRICS reports were not migrated into public storage; the new public factual smoke case is separate. The demo/video remains frozen and no hackathon submission was made.
