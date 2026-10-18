> Current consumer access: v0.5. Normal browser use needs no access code. Start with [THIRD_PARTY.md](THIRD_PARTY.md) for scoped keys, limits and versioned routes; earlier reviewer-only examples below describe optional compatibility behavior that is disabled on the hosted service.

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

- `provider_api_key`: optional Gemini Developer API key, new jobs only. No daily ProofMesh check cap; Google bills the key owner. Encrypted temporarily, never included in responses/reports. Distinct from the ProofMesh bearer token. See [personal-key handling](THIRD_PARTY.md#use-your-own-gemini-api-key).
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
- `evidence[].kind`: `demo_fixture`, `source_page_excerpt`, `search_grounded_excerpt` or `image_match_lead`. Never label the latter as a verbatim source quote.
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

## v0.4 publication and reviewer access

Submissions accept `published_at` as an ISO 8601 timestamp with an explicit timezone, plus optional public HTTPS `source_url`. English relative-time claims require the publication timestamp for a fresh live/review investigation. This is supplied context, not verified capture time. Reports include `publication_context`, `assessment.context_checks`, exact `evidence_quotes`, and `provider_attempts`. A conclusive finding requires verified passage quotations; otherwise it becomes unresolved.

`POST /api/access/reviewer` accepts `{ "code": "<private reviewer code>" }`, sets an eight-hour signed HttpOnly cookie and returns the review role. The role forces all non-demo submissions/queries to the shared `review` corpus and rejects access to team report/job IDs. Reviewers cannot use the synchronous investigation route. The team bearer token remains separate. The reviewer fragment is exchanged and removed by the portal. No Google credentials are shared.

Only provider 429 triggers one application retry of the failed stage after five seconds; SDK retries are disabled. A failed job returns its numeric `error_code` and a safe message. A new job clears the old on-screen report. Manual whole-job retry remains bounded and consumes another admission.

## v0.5 consumer contract

The `/api/v1` aliases provide health, matches, jobs, reports, developer registration and owner key administration. See [the integration guide](THIRD_PARTY.md) for examples and response policy. Browser visitors use an on-demand HttpOnly guest cookie; developer clients use scoped bearer credentials. Submitted namespace or bypass fields are forbidden. API read/job IDs are checked against the authenticated namespace; only the deliberately published example library crosses those boundaries.

Default limits are 120 requests/fixed minute and ten new jobs/UTC day per client. 429 includes Retry-After; successful limited requests include X-RateLimit headers. Trusted team credentials bypass those application limits. Shared spending guards return 503 and still apply to trusted callers. The old synchronous POST now serves cached results only and directs all fresh work to the durable job path.

## v0.6 evidence conclusions and origin attribution

The pipeline now returns `assessment_status` (`complete`, `partial`, `validation_failed`, `review_rejected`, or `no_evidence`), `validation` diagnostics and an explicit `evidence_policy`. Policy 0.6 changes cache identity, so an earlier citation-failure report cannot silently satisfy a new investigation. Earlier reports remain readable and are labeled as older policy outputs.

The assessor may cite a stable `passage_id` from a server-built catalogue. The server fills the exact fetched quotation; generated quotation text is never substituted for missing evidence. Typographic normalization is limited to Unicode, quotes/dashes and whitespace, not fuzzy word/number/negation changes. One bounded `citation_repair` call may correct citations using the same sources. A failure after that is a processing failure, with affected findings marked `assessment_issue=citation_validation_failed`; valid findings are retained. Critique can reject indexed findings or context checks without erasing unrelated valid conclusions. Normal pipelines use three logical calls; repaired-and-reviewed pipelines use up to four, with provider attempts tracked separately.

`assessment.media_origin` describes published source reporting, with supporting fetched quotations. `image_match_evidence_ids` can reference actual full/partial image-match leads for association, but those leads cannot substantiate the origin claim by themselves. `origin` distinguishes source reporting, image association and `independent_verification=not_performed`. Where image association is not established, the status is `unconfirmed_media_match`, not a verified AI-origin verdict for the upload. ProofMesh does not run a watermark or provenance detector.

Current third-party defaults: **120 API requests/minute, 10 new investigations per UTC day per credential, 30 new credentials/hour across the service**. Trusted testers are exempt from application rate limits. There is no shared investigation-count cap.
