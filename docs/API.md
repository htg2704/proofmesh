# API contract v0.2

Development origin: `http://127.0.0.1:8000`. Machine-readable schema: `/openapi.json`. No third-party documentation scripts are loaded.

## Shared submission

```json
{
  "claim": "The exact post caption, including dates and places",
  "image_base64": null,
  "corpus": "live"
}
```

- `claim`: 5–3,000 characters. Preserve wording; do not paraphrase it before matching.
- `image_base64`: optional plain base64, without a data-URL prefix. PNG/JPEG/WebP, maximum 5 MB decoded and 16 megapixels. The API computes canonical pixel SHA-256 and 64-bit dHash.
- `corpus`: `live` or `demo`. Default `live`. Clients must not mix the collections.
- API requests are JSON. If configured, send `Authorization: Bearer <PROOFMESH_API_TOKEN>`. Tokens never go in URLs.

## Endpoints

| Method/path | Purpose |
|---|---|
| `GET /api/health` | Public readiness/configuration flags; no secrets. |
| `POST /api/matches` | Read-only registry lookup; **zero model calls**. |
| `POST /api/jobs` | Create or reuse a persistent live investigation job; returns 202. |
| `GET /api/jobs/{id}` | Poll queued, running, succeeded or failed status. |
| `POST /api/investigations` | Local synchronous compatibility route; hosted service returns 409. |
| `POST /api/demo/matches` | Public synthetic lookup, zero model calls. |
| `GET /api/demo/reports/{id}` | Public synthetic report only. |
| `GET /api/investigations?corpus=live` | List up to 1,000 records in the selected collection. |
| `GET /api/investigations/{id}` | Read a source-linked report. |
| `POST /api/demo` with `{}` | Idempotently load the synthetic demonstration for the current UTC date. |

### Matching result

```json
{
  "status": "related_media",
  "report": null,
  "related": [{"id": "64-character-report-id", "claim": "Another caption", "match": "same_media"}],
  "model_calls": 0,
  "message": "Related images never transfer a verdict to a different caption."
}
```

- `exact_context`: a fresh report exists for the exact normalized claim, exact canonical image, corpus and reference date. Show the report and its investigation date.
- `related_media`: same or similar image found; **show no verdict for the submitted claim**. Related reports are evidence-navigation candidates.
- `unknown`: no usable match. **Unknown does not mean trustworthy or false.**

### Investigation result

`{ "report": { ... }, "reused": false, "model_calls": 3 }`

`model_calls` counts logical SDK model invocations in this request. Cached reuse reports zero. It is not a billing invoice or token estimate. The research pass can return unresolved after one invocation if no usable grounding exists.

A report contains `id`, `context_key`, `claim`, `media`, `corpus`, `created_at`, `expires_at`, `origin`, `assessment`, `evidence`, `events`, `model_calls`, optional `usage`, and optional `search_attribution_html`.

`usage` records provider-returned prompt, candidate-output, thinking and total token counts per stage, plus the number of reported web search queries. Missing values remain null. These are observability data, not an invoice or guaranteed billing total. The SDK is configured for one HTTP attempt per stage, with no automatic retries.

- `origin.status` is currently always `unknown`; no detector ran.
- `assessment.findings[].status`: `supported`, `contradicted`, or `unresolved`.
- Non-unresolved findings require valid evidence IDs. Valid IDs establish structural linkage, not factual correctness; the evaluation must test entailment.
- `evidence[].kind`: `demo_fixture` or `search_grounded_excerpt`. Never label the latter as a verbatim source quote.
- `events` are completed pipeline steps, not a streamed progress feed.
- `search_attribution_html` must be shown in a sandboxed frame without script privileges, not injected into the main page DOM.

### Failure semantics

- `400`: invalid image, demo-only request used as a fresh investigation, or invalid assessment output.
- `401`: missing/wrong access token.
- `413`: request too large.
- `415`: request is not JSON.
- `422`: submission schema validation failed.
- `429`: another pipeline is running or local hourly cap reached.
- `502`: provider/pipeline failure; no successful report published.
- `503`: live pipeline is not configured.

## Persistent jobs

POST the shared live submission to `/api/jobs`; persist its `id` and poll `GET /api/jobs/{id}` every three seconds. A succeeded job returns `report_id`, `reused` and `model_calls`; fetch the protected report separately. Failed jobs return a generic error without provider details. Submission and worker claims are transactional, so duplicates do not repeat the pipeline. A killed running worker becomes failed after six minutes and is not automatically reinvoked because it may already have incurred usage.

Cloud Tasks delivers queued jobs to an authenticated worker. Uploaded image bytes live in a private temporary bucket, are deleted after execution, and have a one-day lifecycle cleanup backstop. Local SQLite jobs survive process restarts before execution; run pending jobs explicitly when restarting local development. Cloud Tasks handles hosted delivery independently of browser lifetime.

The hosted configuration limits new attempts to four per UTC day and twelve across the live window and disables new live submissions after November 17, 2026 at 23:59:59 India time. These are workload controls, not an absolute billing cap. Keep the team API token private. Public demo routes cannot invoke inference or read live reports.

`source_page_excerpt` means an independently fetched passage. `image_match_lead` and `search_grounded_excerpt` remain leads. Non-unresolved findings must cite at least one fetched passage; schema checks still do not guarantee entailment. Source publication dates are not image capture dates.
