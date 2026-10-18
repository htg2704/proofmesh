# MVP public evidence registry

The registry holds at most **200 public report snapshots** per deployment, separate from private investigations, clients and jobs. It works in Firestore on Cloud Run and SQLite locally. `PROOFMESH_REGISTRY_CAP` can lower capacity; code clamps values to 1–200. The cap is storage retention, not a shared investigation quota.

## Publication and privacy

The browser shows a checked sharing choice immediately before starting an investigation, explaining that claim/report text and evidence links become public. Uncheck it to keep new work private. REST requests default to `share_publicly=false`; callers must explicitly opt in. Existing private investigations and selected frozen examples are not automatically migrated.

Only fresh reports created today under the current evidence policy, with `assessment_status=complete`, passed citation validation and fetched source evidence, are eligible. Failed, stale, demo, incomplete and older-policy reports are rejected. An owner can explicitly publish an eligible private report from its report view or API without invoking the model again. Publication failure preserves the private report and does not mark its paid investigation failed or repeat inference. These are automated checks, not human moderation or a guarantee of truth.

Snapshots use a new global context ID, not the owner's report ID. The allowlist includes assessment, evidence, media fingerprints, timestamps and Google Search attribution, while excluding client/owner identities, private report IDs, credentials, ciphertext, upload bytes and user-supplied source URL input. Fetched public evidence links remain. Private server-side ownership metadata supports withdrawal and is never returned from public endpoints. Public report links remain available only while the snapshot is retained.

## Capacity and consistency

Publication and the bounded index update occur in one Firestore transaction or SQLite `BEGIN IMMEDIATE` transaction. Duplicate publication of the same global context keeps the first snapshot and does not consume an extra slot or overwrite another publisher's report. A new publication removes expired snapshots first, then the oldest published entries as necessary to admit the new snapshot. Only the public copies are replaced; private reports remain. This is a lightweight retention policy, not a long-term public archive or a limit on private history.

Firestore uses `<private_report_collection>_registry` for snapshot documents and `proofmesh_registry_state/<private_report_collection>` for the bounded index. Each snapshot record contains a public `report` plus internal ownership metadata. The index contains at most 200 IDs, expiration timestamps and publication timestamps. Local storage uses a separate `public_registry` SQLite table. Registry scans are bounded at 200 reports; this deliberately favors a small MVP over a search index. Publication is serialized by the index transaction; a higher-throughput public service needs a different index design.

## Reuse and lookup

The same API used by the web workspace and extension checks private exact matches and the shared registry. Public reuse requires exact normalized caption, identical image fingerprint, supplied publication timestamp, current UTC reference date, unexpired evidence and matching evidence policy. Related images expose links and reuse blockers only. There is no semantic paraphrase-based verdict transfer. A lookup miss is labeled **Not assessed for this context**, rather than “Unverified.” New investigations first attempt this exact reuse automatically.

## REST API

| Operation | Route | Access |
|---|---|---|
| List summaries | `GET /api/v1/registry?limit=20&offset=0` | Public |
| Read snapshot | `GET /api/v1/registry/{id}` | Public |
| Publish private report | `POST /api/v1/investigations/{private_id}/publish` with `{}` | Private report owner or team |
| Withdraw snapshot | `POST /api/v1/registry/{public_id}/withdraw` with `{}` | Original publisher or team |
| Publish after investigation | `POST /api/v1/jobs` with `share_publicly=true` | Normal job admission |

Unversioned aliases remain available. List limit is 1–50; offset is 0–199. Responses include `capacity`, `size`, and public report summaries. New model work still requires a client/team credential and the existing per-client or personal-key policy. Public read endpoints require no credential; authenticated client requests retain their ordinary request quota. Public reads do not invoke inference. Expired reports can be inspected but never reused as fresh results. Withdrawal/eviction returns 404 for later public reads; existing downloaded copies cannot be recalled.

No existing private BRICS/tester report is published as part of deploying this feature. A new public factual smoke check can verify cross-client reuse separately.
