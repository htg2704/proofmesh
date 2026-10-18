# ProofMesh

**Investigate once. Inform everywhere.**

ProofMesh is a prototype evidence rail: an API and shared registry for context-aware misinformation investigations. The web workspace and X extension are its first clients. A source-linked report belongs to a particular claim and media context. Recognizing an image must never transfer a verdict to a different caption.

**Status: deployed hackathon prototype.** Cloud Run, Firestore and queued investigations are implemented. The twelve-case development evaluation and public X extension checks are documented below. Fresh inference can fail with provider capacity errors; broader compatibility and production readiness are not established.

## Start here

- [Two-person task board](TASKS.md): responsibilities, acceptance criteria and October 14–17 schedule.
- [API contract](docs/API.md): shared backend/extension/portal interfaces.
- [Architecture and limitations](docs/ARCHITECTURE.md).
- [Google Cloud deployment guide](docs/DEPLOYMENT.md).
- [Verification record](docs/VERIFICATION.md).
- [Product QA record](docs/PRODUCT_QA.md): completed partner tasks, browser checks and remaining limits.

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

1. Click **Try an example** to prefill the workspace and inspect a labeled recorded investigation.
2. Check shared evidence to retrieve a fresh exact-context result without inference, or inspect related media without inheriting its verdict. Archived recorded reports remain readable but cannot silently satisfy fresh lookups.
3. Edit the caption: a familiar image remains a separate question.
4. Configure Vertex AI before requesting any new live investigation. Default demo mode makes no paid model calls.
5. Reports and credentials persist in the ignored local `data/` directory. The optional `/feed` route is a synthetic extension regression fixture, not the main user experience.

## Hosted demo

Deployment: https://proofmesh-2god3tua3a-el.a.run.app/. Enter a claim/image or prefill an example in the same workspace. No reviewer code or separate demo page is required. On first use, a visitor receives an isolated, rate-limited browser session automatically. `/developers` provides scoped keys for third-party integrations. The team uses separate trusted credentials; none are in GitHub.

## Chrome extension

1. Open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select this repository's `extension/` directory.
2. Open the extension popup and explicitly enable visible-post lookups.
3. Select **Local development** or **Google Cloud demo** in the popup. Local development needs the server at **127.0.0.1:8000**; hosted mode uses the fixed Cloud Run origin. Existing local tokens and hosted tokens are stored separately. Fixture lookups seed their own clearly labeled synthetic evidence.
4. Visit **http://127.0.0.1:8000/feed** for the two-post fixture.
5. Test public X posts separately. Local feed uses the demo collection; X uses the live collection.

The development extension sends visible post text and the first supported image to the local server when enabled. It does not read cookies, history or direct messages. It does not automatically launch model investigations. Clicking **Investigate with Google Cloud** sends that post to the live pipeline. Host permissions are limited to localhost, the fixed ProofMesh Cloud Run origin and X image assets. New investigations enqueue a job immediately and open a polling workspace. Reload the unpacked extension after updating to version 0.4.0; changing hosts requires an explicit popup selection.

The local fixture is a development aid. The installed extension also passed public X extraction checks on October 15. Quoted posts, galleries and video remain explicitly unverified. English relative-time captions require an unambiguous publication timestamp; without it they remain unverified. DOM regression tests cover SPA/private-route handling, recycled nodes and retry; logged-in X variants need further browser QA.

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

Run `.venv/bin/python scripts/smoke_vertex.py` only when live mode is configured and usage is authorized. It investigates one public NASA claim, records returned token/search-query counts in ignored `data/vertex-smoke-result.json`, and checks that the repeat uses zero model calls. The pipeline uses one SDK HTTP attempt per stage, with one explicit application retry of a failed stage only for provider 429 and output-token limits of 4,096/3,072/1,536 for research/assessment/critique. These controls bound this test; they are not a Google billing-account spend cap.

Live workflow: Cloud Vision image-match leads -> Google Search research -> bounded source-page retrieval -> structured assessment -> critique. Generated search summaries remain leads. A supported or contradicted finding must cite a fetched source passage. Unknown evidence references are rejected; findings without support remain unresolved. This is a second model review of the supplied evidence, not independent forensic verification. Reports retain Google Search attribution for isolated rendering in the portal.

If credentials, model access or evidence retrieval fail, the application returns an explicit failure or unresolved result. It never substitutes a synthetic report.

## Tests

```bash
.venv/bin/python -m pytest -q
npm ci --ignore-scripts
npm test
node --check web/app.js
node --check extension/content.js
```

Python tests cover context separation, cache reuse, persistence, expiration, invalid images, citation validation, auth and cloud-storage safeguards. JavaScript tests cover DOM extraction, recycled/stale posts, retry, private routes, extension messaging, token correction and upload state. Tests do not establish model accuracy or compatibility with every X layout. See the product QA record for actual browser coverage.

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
- Live evidence distinguishes fetched source passages from generated search summaries and image-match leads. Fetching a page and validating an ID do not prove factual entailment; the selected evaluation is in `docs/EVALUATION.md`.
- Cloud Vision Web Detection is integrated. C2PA inspection, SynthID verification, video investigation and universal AI-origin detection are not implemented. Media origin remains unknown.
- Local persistence uses SQLite; hosted reports and job state use Firestore. Exact reuse looks up the context document directly. Related-media scans are capped at 1,000 records and are not a production search index.
- Hosted jobs use transactional deduplication, a persisted daily cap and a single-dispatch Cloud Tasks queue. One explicit retry is allowed for a failed job; interrupted workers are not automatically reinvoked. New hosted live submissions stop after November 17 at 23:59:59 India time. Matching and public recorded demos remain available. Full multi-user identity and contribution moderation remain future work.
- The public repository includes code, synthetic fixtures and three deliberately published recorded evaluation reports. Private user submissions, credentials and the live application registry are excluded.

Do not describe this starter as a reliable real/fake classifier. Report observed evidence, limitations and evaluation results.

## References

- [Google Gen AI SDK](https://googleapis.github.io/python-genai/)
- [Chrome extension network requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests)
- [Chrome content scripts](https://developer.chrome.com/docs/extensions/develop/concepts/content-scripts)
- [Google Cloud Vision Web Detection](https://docs.cloud.google.com/vision/docs/detecting-web) — integrated retrieval source
- [C2PA explainer](https://spec.c2pa.org/specifications/specifications/2.4/explainer/Explainer.html) — possible future provenance integration

License selection remains with the authors; public visibility alone does not grant an open-source license.

## v0.4 evidence and reviewer release

Publication timestamps anchor relative dates and participate in cache identity. Conclusive findings require exact quotations from fetched passages; generated summaries alone cannot support a verdict. New reviewer access uses a separate shared collection and reserved allowance without exposing team credentials or reports. The private reviewer link is in ignored `data/reviewer-access.txt`.

The twelve-case prespecified development evaluation produced 11 expected outcomes, including nine conclusive findings and three abstentions. Three first-pass provider failures required explicit reruns. All twelve completed repeats used zero model calls. This is not representative accuracy. The latest hosted reviewer investigation also failed with provider 429 after its bounded retry; see the full [evaluation](docs/EVALUATION.md). All 74 regression checks pass.

## Evidence rail and future clients

The current REST API exposes lookup, queued investigation and report retrieval. The web workspace and Chrome extension consume that shared contract. [The rail roadmap](docs/RAIL.md) separates this working prototype from future SDK, MCP, platform and Android/Gemini integrations. No integration or partnership with those platforms is claimed.

## Third-party access and team testing (v0.5)

The normal hosted app works without a reviewer code: limited browser access is created automatically when needed. Examples prefill that same workspace. `/developers` provides scoped keys for REST integrations, with 120 requests/minute and ten new investigations/UTC day per credential. Keys and reports are isolated between clients; selected public examples can be reused when the exact context is fresh.

Harshwardhan, Chennika and authorized Codex tests have distinct trusted credentials. Their application rate limits are removed; the shared trial spending guard and provider limits still apply. Private credentials are in ignored `data/TEAM_ACCESS.md`, never this repository. Existing owner API credentials also receive the exemption.

See [third-party setup and limits](docs/THIRD_PARTY.md) and the new [editable architecture](docs/diagrams/proofmesh-architecture.drawio). All new inference uses durable jobs, including local deployments; the legacy synchronous endpoint directs fresh work to `/api/jobs`. Current checks: 61 Python + 28 JavaScript.
