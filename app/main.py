import hashlib
import hmac
import logging
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, Response, PlainTextResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.demo import seed, demo_image
from app.investigator import GeminiInvestigator
from app.models import Submission
from app.jobs import Jobs
from app.access import COOKIE, review_cookie, valid_cookie
from app.clients import ClientAccess, Principal, RateLimited, SpendingLimit, trusted_credentials, DEFAULT_CLIENT_RPM, DEFAULT_CLIENT_DAILY_JOBS, DEFAULT_REGISTRATIONS_PER_HOUR
from app.examples import match_examples
from starlette.concurrency import run_in_threadpool
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.service import ProofMesh
from app.store import SQLiteStore, FirestoreStore

ROOT = Path(__file__).resolve().parent.parent


def create_app(store=None, investigator=None):
    token = os.getenv("PROOFMESH_API_TOKEN", "")
    reviewer_token = os.getenv("PROOFMESH_REVIEW_TOKEN", "")
    judge_token = os.getenv('PROOFMESH_JUDGE_TOKEN', '')
    judge_until_text = os.getenv('PROOFMESH_JUDGE_UNTIL') or os.getenv('PROOFMESH_LIVE_UNTIL')
    judge_until = datetime.fromisoformat(judge_until_text) if judge_until_text else None
    if judge_until and not judge_until.tzinfo:
        raise RuntimeError('Judge expiry must include a timezone')
    if judge_token and len(judge_token) < 32:
        raise RuntimeError('Judge token must have at least 32 characters')
    trusted = trusted_credentials()
    live = os.getenv("PROOFMESH_ENABLE_LIVE", "false").lower() == "true"
    if live and len(token) < 24:
        raise RuntimeError("Live mode requires PROOFMESH_API_TOKEN with at least 24 characters")
    if os.getenv("K_SERVICE") and (os.getenv("PROOFMESH_STORE") != "firestore" or len(token) < 24):
        raise RuntimeError("Cloud Run requires Firestore and an API token; local SQLite is ephemeral there")
    if store is None:
        store = (FirestoreStore(os.environ["GOOGLE_CLOUD_PROJECT"], os.getenv("PROOFMESH_FIRESTORE_COLLECTION", "proofmesh_investigations"))
                 if os.getenv("PROOFMESH_STORE") == "firestore" else SQLiteStore(os.getenv("PROOFMESH_DB", str(ROOT / "data/proofmesh.sqlite3"))))
    service = ProofMesh(store, investigator or GeminiInvestigator())
    app = FastAPI(title="ProofMesh", version="0.7.0", docs_url=None, redoc_url=None)
    app.state.service = service
    jobs = Jobs(store, service)
    app.state.jobs = jobs
    clients = ClientAccess(store)
    app.state.clients = clients
    demo_service = ProofMesh(SQLiteStore(os.getenv("PROOFMESH_DEMO_DB", str(ROOT / "data/demo.sqlite3"))), service.investigator)

    @app.exception_handler(RequestValidationError)
    async def safe_validation(request, exc):
        # Pydantic's default error includes raw input, potentially a provider key.
        return JSONResponse({'detail': [{'loc': e['loc'], 'type': e['type'], 'msg': e['msg']} for e in exc.errors()]}, status_code=422)

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        header = request.headers.get("authorization", "")
        principal = Principal()
        if not token or hmac.compare_digest(header, f"Bearer {token}"):
            principal = Principal('team', 'owner')
        else:
            for name, credential in trusted.items():
                if hmac.compare_digest(header, f'Bearer {credential}'):
                    principal = Principal('team', name)
                    break
            if principal.role == 'none' and len(judge_token) >= 32 and (not judge_until or datetime.now(timezone.utc) < judge_until) and hmac.compare_digest(header, f'Bearer {judge_token}'):
                principal = Principal('judge', hashlib.sha256(judge_token.encode()).hexdigest()[:24])
            client_credential = header[7:] if header.startswith('Bearer pm_client_') else request.cookies.get('proofmesh_client', '') if not header else ''
            if principal.role == 'none' and client_credential:
                principal = await run_in_threadpool(clients.authenticate, client_credential) or principal
            if principal.role == 'none' and len(reviewer_token) >= 32 and (hmac.compare_digest(header, f"Bearer {reviewer_token}") or (not header and valid_cookie(request.cookies.get(COOKIE), reviewer_token))):
                principal = Principal('review', 'review')
        request.state.principal, request.state.role = principal, principal.role
        registry_read = request.method == 'GET' and (request.url.path in {'/api/registry', '/api/v1/registry'} or request.url.path.startswith(('/api/registry/', '/api/v1/registry/')))
        public = registry_read or request.url.path in {"/api/health", "/api/v1/health", "/api/access/guest", "/api/access/register", "/api/v1/access/register", "/api/access/reviewer", "/api/examples", "/api/demo", "/api/demo/matches"} or request.url.path.startswith("/api/demo/reports/")
        if request.url.path.startswith("/api/") and not public and request.state.role == "none":
            return JSONResponse({"detail": "A developer key, team credential or reviewer session is required"}, status_code=401, headers={'Cache-Control': 'no-store'})
        rate_headers = {}
        if request.url.path.startswith('/api/') and principal.role in {'client', 'review'}:
            try:
                rate_headers = await run_in_threadpool(clients.take, principal.role + ':' + principal.identifier, int(os.getenv('PROOFMESH_CLIENT_REQUESTS_PER_MINUTE', str(DEFAULT_CLIENT_RPM))))
            except RateLimited as exc:
                return JSONResponse({'detail': str(exc)}, status_code=429, headers={'Retry-After': str(exc.retry_after), 'Cache-Control': 'no-store'})
        if request.url.path.startswith("/api/"):
            if request.method == "POST":
                if request.headers.get("content-type", "").split(";")[0] != "application/json":
                    return JSONResponse({"detail": "Use application/json"}, status_code=415)
                total, chunks = 0, []
                async for chunk in request.stream():
                    total += len(chunk)
                    if total > 7_100_000:
                        return JSONResponse({"detail": "Request too large"}, status_code=413)
                    chunks.append(chunk)
                request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers.update(rate_headers)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    # Third-party web clients may use bearer keys. Cookies are never shared
    # cross-origin; the worker secret header is deliberately not allowed.
    app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False,
                       allow_methods=['GET', 'POST'], allow_headers=['Authorization', 'Content-Type'],
                       expose_headers=['Retry-After', 'X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset'])

    def scope(submission, request):
        if request.state.role in {'client', 'judge'} and submission.corpus != 'demo':
            return submission.for_client(request.state.principal.identifier)
        if request.state.role == "review" and submission.corpus != "demo":
            return submission.model_copy(update={"corpus": "review"})
        return submission

    def can_read(corpus, request):
        return corpus == 'public' or request.state.role == 'team' or corpus == request.state.principal.namespace

    def examples():
        import json
        path = ROOT / 'web/recorded-cases.json'
        return json.loads(path.read_text()) if path.exists() else []

    def published_report(identifier):
        return service.registry.get(identifier) or next((r for r in examples() if r.get('recorded_example') and r['id'] == identifier), None)

    class ClientLabel(BaseModel):
        label: str = Field(min_length=3, max_length=60, pattern=r'^[\w .-]+$')

    @app.post('/api/v1/access/register', status_code=201)
    @app.post('/api/access/register', status_code=201)
    def register_client(body: ClientLabel):
        if os.getenv('PROOFMESH_SELF_REGISTRATION', 'false').lower() != 'true':
            raise HTTPException(403, 'Self-registration is disabled. Ask the service owner for a developer key, or run your own deployment.')
        try:
            clients.take('public-registration', int(os.getenv('PROOFMESH_REGISTRATIONS_PER_HOUR', str(DEFAULT_REGISTRATIONS_PER_HOUR))), 3600)
        except RateLimited as exc:
            raise HTTPException(429, str(exc), headers={'Retry-After': str(exc.retry_after)}) from exc
        return clients.issue(body.label)

    @app.post('/api/access/guest')
    def guest_session(request: Request):
        if request.state.role in {'team', 'client', 'judge'}:
            return {'access': request.state.role}
        issued = register_client(ClientLabel(label='Browser workspace'))
        response = JSONResponse({'access': 'client', 'message': 'Your limited workspace is ready'})
        response.delete_cookie(COOKIE)
        response.set_cookie('proofmesh_client', issued['token'], httponly=True, secure=bool(os.getenv('K_SERVICE')), samesite='strict', max_age=30*86400)
        return response

    @app.post('/api/v1/clients', status_code=201)
    @app.post('/api/clients', status_code=201)
    def issue_client(body: ClientLabel, request: Request):
        if request.state.role != 'team':
            raise HTTPException(403, 'Only the service owner or trusted team may issue developer keys')
        return clients.issue(body.label)

    @app.get('/api/v1/clients')
    @app.get('/api/clients')
    def list_clients(request: Request):
        if request.state.role != 'team':
            raise HTTPException(403, 'Team access required')
        return {'clients': clients.all()}

    @app.post('/api/v1/clients/{client_id}/revoke')
    @app.post('/api/clients/{client_id}/revoke')
    def revoke_client(client_id: str, request: Request):
        if request.state.role != 'team':
            raise HTTPException(403, 'Team access required')
        if not clients.revoke(client_id):
            raise HTTPException(404, 'Client not found')
        return {'revoked': True}

    class ReviewerAccess(BaseModel):
        code: str = Field(min_length=24, max_length=128)

    @app.post("/api/access/reviewer")
    def review_access(body: ReviewerAccess):
        if len(reviewer_token) < 32 or not hmac.compare_digest(body.code, reviewer_token):
            raise HTTPException(401, "Invalid reviewer access link")
        response = JSONResponse({"access": "review", "message": "Review workspace connected"})
        response.set_cookie(COOKIE, review_cookie(reviewer_token), httponly=True, secure=bool(os.getenv("K_SERVICE")), samesite="strict", max_age=8*3600)
        return response

    @app.get("/api/v1/health")
    @app.get("/api/health")
    def health(request: Request):
        return {"status": "ok", "live_enabled": live, "authentication_required": bool(token), "access": request.state.role,
                "review_enabled": len(reviewer_token) >= 32, "judge_enabled": len(judge_token) >= 32 and (not judge_until or datetime.now(timezone.utc) < judge_until), "version": "0.7.0", "release": os.getenv("PROOFMESH_RELEASE", "local"),
                "self_registration": os.getenv('PROOFMESH_SELF_REGISTRATION', 'false').lower() == 'true',
                "rate_limits_exempt": request.state.principal.exempt,
                "client_requests_per_minute": int(os.getenv('PROOFMESH_CLIENT_REQUESTS_PER_MINUTE', str(DEFAULT_CLIENT_RPM))),
                "client_daily_jobs": int(os.getenv('PROOFMESH_CLIENT_DAILY_JOBS', str(DEFAULT_CLIENT_DAILY_JOBS))),
                "registrations_per_hour": int(os.getenv('PROOFMESH_REGISTRATIONS_PER_HOUR', str(DEFAULT_REGISTRATIONS_PER_HOUR))),
                "public_registry_cap": service.registry.capacity, "shared_investigation_cap": False,
                "personal_gemini_key_enabled": bool(os.getenv("PROOFMESH_CREDENTIAL_ENCRYPTION_KEY")),
                "personal_key_daily_cap": None}

    @app.get('/api/v1/registry')
    @app.get('/api/registry')
    def public_registry(limit: int = 20, offset: int = 0):
        if not 1 <= limit <= 50 or not 0 <= offset < 200:
            raise HTTPException(400, 'Use limit 1–50 and offset 0–199')
        reports = service.registry.all()
        fields = {'id', 'claim', 'created_at', 'expires_at', 'registry_published_at', 'corpus', 'public_registry', 'assessment_status'}
        return {'capacity': service.registry.capacity, 'size': len(reports), 'reports': [{k: v for k, v in r.items() if k in fields} for r in reports[offset:offset+limit]]}

    @app.get('/api/v1/registry/{report_id}')
    @app.get('/api/registry/{report_id}')
    def read_public_report(report_id: str):
        if not re.fullmatch(r'[a-f0-9]{64}', report_id):
            raise HTTPException(404, 'Public report not found')
        report = service.registry.get(report_id)
        if not report:
            raise HTTPException(404, 'Public report not found or replaced by the registry capacity policy')
        return report

    @app.post('/api/v1/investigations/{report_id}/publish')
    @app.post('/api/investigations/{report_id}/publish')
    def publish_report(report_id: str, request: Request):
        if not re.fullmatch(r'[a-f0-9]{64}', report_id):
            raise HTTPException(404, 'Investigation not found')
        report = store.get(report_id)
        if not report or not can_read(report.get('corpus'), request):
            raise HTTPException(404, 'Investigation not found')
        result = service.share(report)
        if result['status'] != 'published':
            raise HTTPException(409 if result['status'] == 'not_eligible' else 503, result['message'])
        return result

    @app.post('/api/v1/registry/{report_id}/withdraw')
    @app.post('/api/registry/{report_id}/withdraw')
    def withdraw_report(report_id: str, request: Request):
        if not re.fullmatch(r'[a-f0-9]{64}', report_id):
            raise HTTPException(404, 'Public report not found')
        record = service.registry.record(report_id)
        try:
            removed = service.registry.withdraw(report_id, request.state.principal.namespace, request.state.role == 'team')
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        if not removed:
            raise HTTPException(404, 'Public report not found')
        source = store.get(record['source_report_id']) if record else None
        if source:
            source['registry_publication'] = {'status': 'withdrawn'}
            store.put(source)
        return {'withdrawn': True}

    @app.get("/api/v1/investigations")
    @app.get("/api/investigations")
    def list_reports(request: Request, corpus: str = "live"):
        if request.state.role == "review":
            corpus = "review"
        if request.state.role in {'client', 'judge'}:
            return {'reports': service.store.all(request.state.principal.namespace)}
        if corpus not in {"live", "demo", "review"}:
            raise HTTPException(400, "Unknown corpus")
        return {"reports": service.store.all(corpus)}

    @app.get("/api/v1/investigations/{report_id}")
    @app.get("/api/investigations/{report_id}")
    def read_report(report_id: str, request: Request):
        if not re.fullmatch(r"[a-f0-9]{64}", report_id):
            raise HTTPException(404, "Investigation not found")
        report = published_report(report_id)
        if report:
            return report
        report = service.store.get(report_id)
        if not report or not can_read(report.get('corpus'), request):
            raise HTTPException(404, "Investigation not found")
        return report

    @app.post("/api/v1/matches")
    @app.post("/api/matches")
    def match(submission: Submission, request: Request):
        submission = scope(submission, request)
        try:
            if submission.corpus == "demo":
                seed(demo_service)
                return demo_service.match(submission)
            result = service.match(submission)
            if not result.get('needs_publication_time') and not result['report']:
                published, related = match_examples(submission, examples())
                if published:
                    result.update(status='exact_context', report=published)
                elif related:
                    result.update(status='related_media', related=(result['related'] + related)[:10])
            return result
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/investigations")
    def investigate(submission: Submission, request: Request):
        # Keep zero-call legacy reads; all fresh inference uses the same durable
        # admission path, including local deployments and trusted testers.
        submission = scope(submission, request)
        cached = match(submission, request)
        if cached['report']:
            return {'report': cached['report'], 'reused': True, 'model_calls': 0}
        if not live:
            raise HTTPException(503, 'Live investigation is disabled')
        raise HTTPException(409, 'Use POST /api/jobs and poll its status for new investigations')

    @app.post("/api/v1/jobs", status_code=202)
    @app.post("/api/jobs", status_code=202)
    def start_job(submission: Submission, background: BackgroundTasks, request: Request, retry_failed: bool = False):
        submission = scope(submission, request)
        if not live:
            raise HTTPException(503, "Live investigation is disabled")
        try:
            if submission.corpus != 'demo':
                cached = match(submission, request).get('report')
                if cached:
                    if submission.share_publicly and cached.get('corpus') not in {'demo', 'public'}:
                        service.share(cached)
                    return {'id': cached['id'], 'status': 'succeeded', 'report_id': cached['id'], 'reused': True, 'model_calls': 0}
            job, created = jobs.reserve(submission, retry_failed=retry_failed, bypass_rate_limits=request.state.principal.exempt, requested_by=request.state.principal.identifier)
            if created:
                try:
                    jobs.save_image(job['id'], submission.image_base64)
                    if jobs.cloud:
                        jobs.enqueue(job['id'])
                    else:
                        background.add_task(jobs.run, job['id'])
                except Exception:
                    jobs.update(job['id'], provider_key_ciphertext=None, status='failed', error='Could not enqueue investigation. No model was invoked.')
                    jobs.image(jobs.get(job['id'])['image_key'], delete=True)
                    raise HTTPException(503, "Could not enqueue investigation")
            return jobs.public(job)
        except RateLimited as exc:
            raise HTTPException(429, str(exc), headers={'Retry-After': str(exc.retry_after)}) from exc
        except SpendingLimit as exc:
            raise HTTPException(503, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/v1/jobs/{job_id}")
    @app.get("/api/jobs/{job_id}")
    def read_job(job_id: str, request: Request):
        if not re.fullmatch(r"[a-f0-9]{64}", job_id):
            raise HTTPException(404, "Job not found")
        job = jobs.get(job_id)
        if job and not can_read(job.get('corpus', 'live'), request):
            raise HTTPException(404, "Job not found")
        if not job:
            # Cached jobs can have no job document.
            published = published_report(job_id)
            report = published or store.get(job_id)
            if report and (published or can_read(report.get('corpus'), request)):
                return {"id": job_id, "status": "succeeded", "report_id": job_id, "reused": True, "model_calls": 0}
            raise HTTPException(404, "Job not found")
        return jobs.public(job)

    @app.post("/internal/jobs/{job_id}")
    def worker(job_id: str, request: Request):
        expected = os.getenv("PROOFMESH_WORKER_TOKEN", "")
        if len(expected) < 24 or not hmac.compare_digest(request.headers.get("x-proofmesh-worker-token", ""), expected):
            raise HTTPException(401, "Worker authentication required")
        if not re.fullmatch(r"[a-f0-9]{64}", job_id) or not jobs.get(job_id):
            raise HTTPException(404, "Job not found")
        jobs.run(job_id)
        return {"accepted": True}

    @app.post("/api/demo/matches")
    def demo_match(submission: Submission):
        if submission.corpus != "demo":
            raise HTTPException(400, "Demo collection required")
        seed(demo_service)
        try:
            return demo_service.match(submission)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/demo/reports/{report_id}")
    def demo_report(report_id: str):
        if not re.fullmatch(r"[a-f0-9]{64}", report_id):
            raise HTTPException(404, "Demo report not found")
        seed(demo_service)
        report = demo_service.store.get(report_id)
        if not report:
            raise HTTPException(404, "Demo report not found")
        return report

    @app.post("/api/demo")
    def demo():
        return seed(demo_service if os.getenv("K_SERVICE") or token else service)

    @app.get("/fixtures/bridge.png")
    def bridge():
        return Response(demo_image(), media_type="image/png")

    @app.get("/fixtures/bridge-archive.txt")
    def archive():
        return PlainTextResponse("PROOFMESH SYNTHETIC FIXTURE\nIllustration: Riverton bridge.\nFictional archive date: 2021-06-18.\nThis is not a photograph of a real event. No external facts are asserted.\n")

    @app.get("/fixtures/bridge-archive")
    def archive_page():
        return FileResponse(ROOT / "web/evidence.html")

    @app.get("/api/examples")
    def recorded_examples():
        return {"reports": examples()}

    @app.get("/")
    def index():
        return FileResponse(ROOT / "web/index.html")

    @app.get('/developers')
    def developers():
        return FileResponse(ROOT / 'web/developers.html')

    @app.get("/feed")
    def feed():
        return FileResponse(ROOT / "web/feed.html")

    app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")
    return app
