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

## Not yet verified

- Broad evaluation of live grounding quality, billed cost reconciliation, search attribution styling, and contradicted/unresolved cases. One successful live request is documented above.
- Firestore against a Google Cloud project and Cloud Run container execution/deployment.
- Installed unpacked extension on real X or the fixture page. The extension's boundary functions are tested, but browser installation was not performed.
- Responsive mobile layout, screen reader behavior, galleries/quoted posts in actual X DOM, long-running worker behavior and network recovery.
- CI for the starter commit is verified above; subsequent commits have their own workflow results.

## What this establishes

The deterministic first slice demonstrates separate image and caption identity, exact-context reuse, explicit unknowns and a readable evidence report. It does **not** establish misinformation detection accuracy, trustworthy AI-origin detection or production readiness.
