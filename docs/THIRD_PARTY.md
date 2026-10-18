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

| Policy | Trial-funded browser / developer | Personal Gemini key | Trusted team |
|---|---|---|---|
| API requests | 120 per fixed minute per credential | 120 per fixed minute per credential | Exempt |
| New investigations | 10 admissions per UTC day per credential | No daily ProofMesh check cap | Exempt |
| Shared investigation count cap | None | None | None |
| Provider quotas | Apply | Apply to your Google account | Apply |

Public credential issuance is limited to 30 registrations/hour across the deployment; owner-issued keys bypass this issuance limit. Reads and polling count toward API request limits. A failed trial attempt or explicit retry consumes a daily admission; a fresh cached repeat does not. Responses include rate headers and 429 includes `Retry-After`.

Project-funded checks use the approved US$10 trial budget and November 17 live window. A conservative monetary reservation circuit can pause trial funding with 503; it is not an investigation-count quota and does not apply to personal-key jobs. It reserves US$0.50 per project-funded attempt over an initial US$4 reserve for earlier usage. Reservations are not billing receipts or an absolute Google spending cap; infrastructure costs and provider billing remain external. Trusted rate exemptions do not remove financial approval limits.

## Use your own Gemini API key

In the main workspace open **Use your own Gemini API key**, paste a key from [Google AI Studio](https://aistudio.google.com/api-keys), then click **Use my Gemini key**. The key stays in page memory, never browser local/session storage; reloading clears it. **Switch to trial allowance** clears it immediately. ProofMesh access tokens under Advanced settings identify your private workspace; they are different credentials.

For integrations, include `provider_api_key` only in the JSON body of `POST /api/v1/jobs`. Continue using your ProofMesh developer token in the Authorization header. Do not put either credential in URLs or public frontend bundles. Pass JSON through a private file/stdin rather than command-line literals. Example body:

```json
{"claim":"Canberra is the national capital of Australia.","provider_api_key":"YOUR_GEMINI_API_KEY"}
```

Personal-key jobs use the Gemini Developer API and Google Search with your key, billed to your Google account according to its plan. They never fall back to ProofMesh's Vertex credentials on failure. Dedicated Cloud Vision image lookup is skipped; Gemini still receives the submitted image, but a missing independent image association remains explicit. Google quotas, safety rules, per-request workload bounds and the 120/minute ProofMesh API limit still apply. No daily ProofMesh investigation cap or trial-funds reservation applies to these jobs. This feature currently lives in the web app/REST API; the Chrome extension does not collect personal Gemini keys.

The server temporarily encrypts the key with Fernet for queued delivery, using an encryption key held in Secret Manager. Ciphertexts are excluded from job responses and reports. The worker decrypts only within 15 minutes of admission and clears the ciphertext on success/failure; reads clear stale ciphertext. An abandoned job can retain undecryptable ciphertext until accessed or administratively cleaned up. This is cryptographic expiry, not a promise of scheduled physical deletion. The server and Google process the plaintext key during the request; only use a trusted deployment. Raw request bodies and provider exception strings must not be logged.

Limits persist in Firestore on Cloud Run and SQLite locally. Admission and deduplication are committed together. Request counters use one document per credential/bucket rather than an ever-growing document per minute. Credential renewal or cookie clearing can create a new identity; this prototype does not claim Sybil resistance, production DDoS protection, individual account authentication or billing reconciliation.

## Owner operations

Use an owner/trusted bearer credential:

- `POST /api/v1/clients` with `{ "label": "Approved app" }` issues a limited key.
- `GET /api/v1/clients` lists metadata, never tokens or digests.
- `POST /api/v1/clients/{id}/revoke` with `{}` revokes that key immediately.

Set `PROOFMESH_SELF_REGISTRATION=false` to require owner-issued keys. This also disables automatic guest creation; existing valid credentials continue working. Never share a trusted testing key with an integration: it grants team access and bypasses application rate limits.

## Run your own instance

Follow the root README's Python or Docker setup. Demo mode needs no Google credentials and makes no new model calls. For live work, configure a strong team token and explicitly enable live mode. Use Vertex project/model/ADC for trial-funded work, or set a Fernet encryption key and `GEMINI_API_MODEL` for personal-key work (no Vertex ADC is required for that path). Use SQLite locally; use Firestore, Cloud Tasks, private image storage and attached service identities on Cloud Run. Review `.env.example`, configure your own limits and budget, and enable self-registration only when you intend to accept public users.
