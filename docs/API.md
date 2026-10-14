# API contract v0.1

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
| `POST /api/investigations` | Exact reuse or a new bounded live pipeline. |
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

A report contains `id`, `context_key`, `claim`, `media`, `corpus`, `created_at`, `expires_at`, `origin`, `assessment`, `evidence`, `events`, `model_calls`, and optional `search_attribution_html`.

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

The first slice is synchronous. If job polling is added, version the contract and agree on it before changing extension behavior.
