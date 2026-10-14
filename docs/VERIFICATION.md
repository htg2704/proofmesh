# Verification record — October 14, 2026

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

- Actual Gemini on Vertex AI request, grounding quality, model availability, usage/cost and search attribution styling.
- Firestore against a Google Cloud project and Cloud Run container execution/deployment.
- Installed unpacked extension on real X or the fixture page. The extension's boundary functions are tested, but browser installation was not performed.
- Responsive mobile layout, screen reader behavior, galleries/quoted posts in actual X DOM, long-running worker behavior and network recovery.
- GitHub Actions will run after the repository push; local test results do not imply CI passed.

## What this establishes

The deterministic first slice demonstrates separate image and caption identity, exact-context reuse, explicit unknowns and a readable evidence report. It does **not** establish misinformation detection accuracy, trustworthy AI-origin detection or production readiness.
