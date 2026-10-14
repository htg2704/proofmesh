# Google Cloud deployment — prepared, not executed

The hackathon build targets Gemini on Vertex AI, Firestore and Cloud Run. No cloud resources or billing changes were created by the starter.

## Prerequisites

1. Choose a Google Cloud project and region, review cost/quotas, and enable Cloud Run, build/artifact services, Firestore and Vertex AI as required.
2. Create a Firestore Native database appropriate to the project/region.
3. Create a runtime service account with narrowly scoped Vertex AI access and Firestore data access. Store the application API token in Secret Manager; grant access only to that secret. Do not ship a service-account key.
4. Choose a currently available Gemini model that supports the configured Google Search tool and structured output. Set `GEMINI_MODEL` explicitly.
5. Validate one real investigation and the resulting search attribution using application-default credentials locally.

## Container

```bash
docker build -t proofmesh .
docker run --rm -p 8000:8080 -e PORT=8080 proofmesh
```

This local command demonstrates demo mode only. Container-local SQLite is temporary; use a mounted volume for local persistence or Firestore for cloud deployment.

## Cloud Run configuration

Use the checked-in Dockerfile via a source or container build. Configure:

```text
PROOFMESH_STORE=firestore
PROOFMESH_ENABLE_LIVE=true
GOOGLE_CLOUD_PROJECT=<project>
GOOGLE_CLOUD_LOCATION=<supported-location>
GEMINI_MODEL=<available-model>
PROOFMESH_FIRESTORE_COLLECTION=proofmesh_investigations
PROOFMESH_API_TOKEN=<Secret Manager reference, not a source literal>
```

Start with one instance, concurrency 1, a 240-second request timeout and a measured memory limit (1 GiB is an initial configuration to test, not a benchmark). Local hourly limits are process-local and reset on restart; add distributed quota accounting before public access.

Keep Cloud Run IAM authentication enabled for initial testing. Use the gcloud authenticated proxy or an authenticated client to validate it. The public hackathon demo access design remains a separate step: do not expose unrestricted paid model calls. The portal accepts an application token, but that is not a substitute for multi-user authentication or abuse prevention.

For a hosted extension, change the API constant in `extension/background.js`, portal links in `content.js`/`popup.html`, and the manifest's narrowly scoped host permissions. Keep only the intended host. Verify the consent copy accurately describes where visible post information is sent.

## Deployment acceptance

- Reports survive instance restart.
- Unauthorized API requests fail; a fresh claim without a token cannot invoke the model.
- Gemini returns actual grounding metadata and report links open correctly.
- Empty grounding and provider failures do not publish fabricated assessments.
- Exact repeat lookups make zero additional model calls.
- Same image with a new caption remains separately assessed.
- Budget alerts and quotas are reviewed; note that alerts alone do not impose a hard spend cap.
- Browser integration works against the real deployment.

