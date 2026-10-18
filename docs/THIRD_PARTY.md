# Build on ProofMesh

The browser workspace and X extension use the same evidence API. Third parties can call the versioned REST contract or run their own deployment. No SDK, MCP server or platform partnership is claimed.

## Use the hosted app

Open https://proofmesh-2god3tua3a-el.a.run.app/. Enter a claim and optional image; check existing evidence or start an investigation. No reviewer code, sign-in or developer key is needed in the normal browser flow. On first use the server creates a scoped browser credential in a 30-day HttpOnly, Secure, SameSite=Strict cookie. It is not exposed to JavaScript. Prefilled examples live in the same workspace and clearly identify recorded results.

New reports are isolated by client. Deliberately published examples can be reused only for exact fresh context; related images never transfer a verdict. Clearing cookies loses access to that browser workspace. This is credential-based isolation, not verified human identity or full account recovery.

## Integrate a third-party application

Visit `/developers` to create and download a developer key. Alternatively:

```sh
curl -sS https://proofmesh-2god3tua3a-el.a.run.app/api/v1/access/register \
  -H 'Content-Type: application/json' \
  -d '{"label":"My research application"}'
```

Save the returned `token` privately; it is shown once. The server stores its SHA-256 digest. Keys expire after 30 days and can be revoked. Set `PROOFMESH_CLIENT_KEY` locally; never put keys in URLs, source control or public examples.

```sh
curl -sS https://proofmesh-2god3tua3a-el.a.run.app/api/v1/matches \
  -H "Authorization: Bearer $PROOFMESH_CLIENT_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"claim":"Canberra is the national capital of Australia."}'
```

- `POST /api/v1/matches`: existing evidence; no model calls.
- `POST /api/v1/jobs`: start or deduplicate a durable investigation.
- `GET /api/v1/jobs/{id}`: poll no faster than every three seconds.
- `GET /api/v1/investigations/{id}`: retrieve a report.
- `GET /api/v1/investigations`: list only this client's reports.
- `/openapi.json`: request schemas and the complete endpoint list.

Requests accept `claim`, optional `image_base64`, `published_at` with an explicit timezone, and optional public HTTPS `source_url`. The server assigns the private namespace; clients cannot select another client's collection. English relative-time claims require publication context. Images are limited to 5 MB and 16 megapixels. Redirects, credentials embedded in source URLs and private-network source retrieval are not allowed.

The existing unversioned routes remain aliases. The old synchronous POST `/api/investigations` serves existing matches only; fresh work returns 409 directing clients to jobs. This keeps all new inference behind the same admission checks on local and hosted deployments.

## Limits and errors

| Policy | Ordinary browser / developer | Trusted team testing |
|---|---|---|
| API requests | 120 per fixed minute, per credential | Exempt |
| New investigations | 10 admissions per UTC day, per credential | Exempt |
| Public credential issuance | 30 per fixed hour across the deployment | Owner-issued keys bypass public issuance |
| Shared trial spending guard | Applies | Applies |
| Live-window expiry / provider capacity | Applies | Applies |

A new job retry consumes another admission; an exact cached repeat does not. Reads and polling still count toward request limits. 429 responses include `Retry-After`; successful limited responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining` and `X-RateLimit-Reset` (Unix seconds). A shared spending guard or closed live window returns 503. These financial guards are distinct from rate limits.

The hosted trial keeps the existing twelve-admission total and November 17 live-window expiry under the approved US$5 budget. Model retries and inference have bounded workload controls; this is not an absolute Google billing cap. Keys do not entitle callers to unlimited paid computation. Provider 429 can still exhaust the bounded retry and fail a job safely. No synthetic result replaces failed inference.

Limits persist in Firestore on Cloud Run and SQLite locally. Admission and deduplication are committed together. Request counters use one document per credential/bucket rather than an ever-growing document per minute. Credential renewal or cookie clearing can create a new identity; this prototype does not claim Sybil resistance, production DDoS protection, individual account authentication or billing reconciliation.

## Owner operations

Use an owner/trusted bearer credential:

- `POST /api/v1/clients` with `{ "label": "Approved app" }` issues a limited key.
- `GET /api/v1/clients` lists metadata, never tokens or digests.
- `POST /api/v1/clients/{id}/revoke` with `{}` revokes that key immediately.

Set `PROOFMESH_SELF_REGISTRATION=false` to require owner-issued keys. This also disables automatic guest creation; existing valid credentials continue working. Never share a trusted testing key with an integration: it grants team access and bypasses application rate limits.

## Run your own instance

Follow the root README's Python or Docker setup. Demo mode needs no Google credentials and makes no new model calls. For live work, configure your own Vertex project/model/ADC and a strong team token, then explicitly enable live mode. Use SQLite locally; use Firestore, Cloud Tasks, private image storage and attached service identities on Cloud Run. Review `.env.example`, configure your own limits and budget, and enable self-registration only when you intend to accept public users.
