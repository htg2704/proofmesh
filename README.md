# ProofMesh

**Investigate once. Inform everywhere.**

ProofMesh is a hackathon prototype for context-aware misinformation investigations. A source-linked report belongs to a particular claim and media context. Recognizing an image must never transfer a verdict to a different caption.

**Status: first development slice, not a finished fact-checking service.** Local registry, synthetic demonstration, portal and tests are runnable. One live Gemini on Vertex AI investigation and zero-call repeat reuse are verified. The Chrome extension starter, real X behavior and Google Cloud deployment still require integration validation.

## Start here

- [Two-person task board](TASKS.md): responsibilities, acceptance criteria and October 14–17 schedule.
- [API contract](docs/API.md): shared backend/extension/portal interfaces.
- [Architecture and limitations](docs/ARCHITECTURE.md).
- [Google Cloud deployment guide](docs/DEPLOYMENT.md).
- [Verification record](docs/VERIFICATION.md).

## Run locally

Requires Python 3.12+; Node 22+ is used only for JavaScript tests. No frontend build step is needed.

```bash
git clone https://github.com/htg2704/proofmesh.git
cd proofmesh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. The default mode makes no Google model calls and requires no cloud credentials.

1. Click **Load synthetic example**.
2. Click **Check shared evidence**: the same image and claim retrieve an existing report with zero model calls.
3. Click **Try the alternate caption**: the same image produces a related-media match, with no inherited verdict.
4. Open the source fixture and download the report.
5. Restart the server: reports persist in `data/proofmesh.sqlite3` (ignored by Git).

The bridge image is a generated geometric illustration and all associated events are fictional. No demo result is represented as a real fact-check. The live and demo collections cannot match one another.

## Chrome extension

1. Open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select this repository's `extension/` directory.
2. Open the extension popup and explicitly enable visible-post lookups.
3. Keep the backend running at **127.0.0.1:8000**. Load the synthetic example in the portal first.
4. Visit **http://127.0.0.1:8000/feed** for the two-post fixture.
5. Test public X posts separately. Local feed uses the demo collection; X uses the live collection.

The development extension sends visible post text and the first supported image to the local server when enabled. It does not read cookies, history or direct messages. It does not automatically launch model investigations. Clicking **Investigate with Google Cloud** sends that post to the live pipeline. The endpoint and host permissions are deliberately limited to localhost; configure a deployed origin before distribution.

The local fixture is a development aid, not proof of compatibility with X. Real X selectors, quoted posts, galleries, SPA navigation and retry behavior remain integration work.

## Enable live investigations

Use a Google Cloud project with Vertex AI enabled, billing/quotas reviewed and application-default credentials configured. Never paste credentials into source files.

```bash
export GOOGLE_CLOUD_PROJECT='your-project-id'
export GOOGLE_CLOUD_LOCATION='global'
export GEMINI_MODEL='your-available-vertex-model-id'
export PROOFMESH_ENABLE_LIVE=true
# Generate this locally; keep it out of version control.
export PROOFMESH_API_TOKEN="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(32))')"
.venv/bin/python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Enter the token through **Connection settings** in the portal, and the extension popup if needed. `.env.example` documents settings. Alternatively, put settings in a Git-ignored repository `.env` and run `.venv/bin/python scripts/dev.py`; this launcher loads plain key/value settings without shell evaluation. Direct uvicorn invocation uses exported environment variables only.

Run `.venv/bin/python scripts/smoke_vertex.py` only when live mode is configured and usage is authorized. It investigates one public NASA claim, records returned token/search-query counts in ignored `data/vertex-smoke-result.json`, and checks that the repeat uses zero model calls. The pipeline uses one HTTP attempt per stage and output-token limits of 4,096/3,072/1,536 for research/assessment/critique. These controls bound this test; they are not a Google billing-account spend cap.

Live workflow: Google Search-grounded research -> structured assessment -> critique. Only source-linked grounding segments can become evidence. Unknown evidence references are rejected; findings without support remain unresolved. This is a second model review of the supplied evidence, not independent forensic verification. Reports retain Google Search attribution for isolated rendering in the portal.

If credentials, model access or evidence retrieval fail, the application returns an explicit failure or unresolved result. It never substitutes a synthetic report.

## Tests

```bash
.venv/bin/python -m pytest -q
node --test tests/test_extension.mjs
node --check web/app.js
node --check extension/content.js
```

Python tests cover context separation, cache reuse, persistence, expiration, invalid images, citation validation, auth and cloud-storage safeguards. JavaScript tests cover permitted origins, restricted image fetching and extension permissions. They do not establish model accuracy or extension compatibility with live X.

## Repository map

```text
app/          API, registry, fingerprints, Gemini pipeline and synthetic fixture
web/          Buildless portal and controlled feed fixture
extension/    Manifest V3 extension, worker, content script and popup
tests/        Deterministic regression and boundary tests
docs/         API, architecture, deployment and verification notes
TASKS.md      Work split for two engineers
Dockerfile    Cloud Run container starter
```

## Scope and known gaps

- Exact normalized claim + decoded image identity + UTC reference date supports reuse. A 24-hour expiry bounds reuse. Semantic claim matching is not implemented.
- dHash retrieves candidate related media only; crops, overlays and visually similar unrelated images can miss or collide.
- Source evidence in live mode consists of **search-grounded model excerpts**, not independently fetched, verbatim article text. Check their supporting pages before a public demonstration.
- No reverse-image web search, C2PA inspection, SynthID verification, video investigation or universal AI detector is implemented. Media origin remains unknown.
- Local persistence uses SQLite. Firestore is implemented as a deployment adapter but requires a real project and validation. Registry scans are capped at 1,000 records and are not a production search index.
- Synchronous investigations are serialized per process and limited to 10 attempts/hour per process. Distributed quotas, durable jobs, identity, abuse controls, retention/deletion and public contribution moderation are future work.
- The public GitHub repository contains only code and synthetic fixtures. The application registry is not published by Git.

Do not describe this starter as a reliable real/fake classifier. Report observed evidence, limitations and evaluation results.

## References

- [Google Gen AI SDK](https://googleapis.github.io/python-genai/)
- [Chrome extension network requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests)
- [Chrome content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts)
- [Google Cloud Vision Web Detection](https://docs.cloud.google.com/vision/docs/detecting-web) — planned retrieval integration
- [C2PA explainer](https://spec.c2pa.org/specifications/specifications/2.4/explainer/Explainer.html) — possible future provenance integration

License selection remains with the authors; public visibility alone does not grant an open-source license.
