# ProofMesh as an evidence rail

ProofMesh provides a shared place to investigate a claim and retrieve the resulting evidence in another interface. The web workspace is the reference application; the X extension is a second client. Neither client owns the investigation logic.

## Available in the prototype

- Look up an exact claim, image and publication context through `POST /api/matches`.
- Create durable work through `POST /api/jobs` and inspect state through `GET /api/jobs/{id}`.
- Retrieve source-linked findings, quotations, date/location/media checks, limitations and explicit unknown origin through `GET /api/investigations/{id}`.
- Reuse fresh matching reports without another model invocation. Related images expose leads without transferring verdicts.
- Keep client and team reports separate; the hosted reviewer-code flow is retired. Worker secrets and Google service identities remain private.

The current clients use the same REST endpoints and report schema. This establishes an initial reusable service boundary. It does not establish a production multi-tenant infrastructure product.

## Next demonstrable slice

A small SDK could wrap lookup, submission and polling. An MCP adapter could expose the same operations to agents with scoped access. Read-only lookup should be the default; paid new work should be an explicit tool with the same budgets and authorization. Both adapters need contract tests against the actual API, including changed-caption behavior and failed jobs. They are not implemented in this release.

## Pilot requirements

A pilot needs tenant isolation, scoped and revocable credentials, API versioning, per-consumer limits, contribution review, report revisions and expiry, audit records, source/content rights policies, deletion rules, monitoring and capacity planning. Scoped developer credentials, personal Gemini keys and per-client trial quotas are prototype controls. Exact quotation checks and same-model critique do not establish independent factual verification.

## Possible future applications

Social apps could show evidence inline before sharing. Android or Gemini experiences could retrieve context through an authorized integration. AI agents and model applications could query the rail through REST or an MCP adapter and cite the report with its limitations. These are proposed interfaces, not partnerships, deployed integrations, model-training feeds or claims that any platform currently uses ProofMesh.

The rail carries context-bound evidence, not a universal real/fake label. A report must retain its exact claim, media identity, publication context, source passages, timestamps, policy version and limitations wherever it appears.

The MVP now implements a genuinely cross-client public registry capped at 200 snapshots, alongside private workspaces. Eligible reports shared by one client can be reused by another for exact fresh context. This implements a small shared evidence layer; human moderation, semantic claim matching, platform integrations and production abuse resistance remain future work. See REGISTRY.md.
