import hmac
import logging
import os
import re
import threading
from collections import deque
from pathlib import Path
from time import monotonic
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, Response, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from app.demo import seed, demo_image
from app.investigator import GeminiInvestigator, InvestigationUnavailable
from app.models import Submission
from app.jobs import Jobs
from app.access import COOKIE, review_cookie, valid_cookie
from pydantic import BaseModel, Field
from app.service import ProofMesh
from app.store import SQLiteStore, FirestoreStore

ROOT = Path(__file__).resolve().parent.parent


def create_app(store=None, investigator=None):
    token = os.getenv("PROOFMESH_API_TOKEN", "")
    reviewer_token = os.getenv("PROOFMESH_REVIEW_TOKEN", "")
    live = os.getenv("PROOFMESH_ENABLE_LIVE", "false").lower() == "true"
    if live and len(token) < 24:
        raise RuntimeError("Live mode requires PROOFMESH_API_TOKEN with at least 24 characters")
    if os.getenv("K_SERVICE") and (os.getenv("PROOFMESH_STORE") != "firestore" or len(token) < 24):
        raise RuntimeError("Cloud Run requires Firestore and an API token; local SQLite is ephemeral there")
    if store is None:
        store = (FirestoreStore(os.environ["GOOGLE_CLOUD_PROJECT"], os.getenv("PROOFMESH_FIRESTORE_COLLECTION", "proofmesh_investigations"))
                 if os.getenv("PROOFMESH_STORE") == "firestore" else SQLiteStore(os.getenv("PROOFMESH_DB", str(ROOT / "data/proofmesh.sqlite3"))))
    service = ProofMesh(store, investigator or GeminiInvestigator())
    app = FastAPI(title="ProofMesh", version="0.4.0", docs_url=None, redoc_url=None)
    app.state.service = service
    jobs = Jobs(store, service)
    app.state.jobs = jobs
    demo_service = ProofMesh(SQLiteStore(os.getenv("PROOFMESH_DEMO_DB", str(ROOT / "data/demo.sqlite3"))), service.investigator)
    lock, recent = threading.Lock(), deque()

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        header = request.headers.get("authorization", "")
        request.state.role = "none"
        if not token or hmac.compare_digest(header, f"Bearer {token}"):
            request.state.role = "team"
        elif len(reviewer_token) >= 32 and (hmac.compare_digest(header, f"Bearer {reviewer_token}") or valid_cookie(request.cookies.get(COOKIE), reviewer_token)):
            request.state.role = "review"
        public = request.url.path in {"/api/health", "/api/access/reviewer", "/api/examples", "/api/demo", "/api/demo/matches"} or request.url.path.startswith("/api/demo/reports/")
        if request.url.path.startswith("/api/") and not public and request.state.role == "none":
            return JSONResponse({"detail": "Team or reviewer access required"}, status_code=401)
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
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def scope(submission, request):
        if request.state.role == "review" and submission.corpus != "demo":
            return submission.model_copy(update={"corpus": "review"})
        return submission

    class ReviewerAccess(BaseModel):
        code: str = Field(min_length=24, max_length=128)

    @app.post("/api/access/reviewer")
    def review_access(body: ReviewerAccess):
        if len(reviewer_token) < 32 or not hmac.compare_digest(body.code, reviewer_token):
            raise HTTPException(401, "Invalid reviewer access link")
        response = JSONResponse({"access": "review", "message": "Review workspace connected"})
        response.set_cookie(COOKIE, review_cookie(reviewer_token), httponly=True, secure=bool(os.getenv("K_SERVICE")), samesite="strict", max_age=8*3600)
        return response

    @app.get("/api/health")
    def health(request: Request):
        return {"status": "ok", "live_enabled": live, "authentication_required": bool(token), "access": request.state.role,
                "review_enabled": len(reviewer_token) >= 32, "version": "0.4.0"}

    @app.get("/api/investigations")
    def list_reports(request: Request, corpus: str = "live"):
        if request.state.role == "review":
            corpus = "review"
        if corpus not in {"live", "demo", "review"}:
            raise HTTPException(400, "Unknown corpus")
        return {"reports": service.store.all(corpus)}

    @app.get("/api/investigations/{report_id}")
    def read_report(report_id: str, request: Request):
        if not re.fullmatch(r"[a-f0-9]{64}", report_id):
            raise HTTPException(404, "Investigation not found")
        report = service.store.get(report_id)
        if not report or (request.state.role == "review" and report.get("corpus") != "review"):
            raise HTTPException(404, "Investigation not found")
        return report

    @app.post("/api/matches")
    def match(submission: Submission, request: Request):
        submission = scope(submission, request)
        try:
            if submission.corpus == "demo":
                seed(demo_service)
                return demo_service.match(submission)
            return service.match(submission)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/investigations")
    def investigate(submission: Submission, request: Request):
        if os.getenv("K_SERVICE") or request.state.role == "review":
            raise HTTPException(409, "Use POST /api/jobs and poll its status on the hosted service")
        if not lock.acquire(blocking=False):
            raise HTTPException(429, "An investigation is already running; try again shortly")
        try:
            cached = service.match(submission)
            if cached["report"]:
                return {"report": cached["report"], "reused": True, "model_calls": 0}
            stamp = monotonic()
            while recent and stamp - recent[0] > 3600:
                recent.popleft()
            if len(recent) >= 10:
                raise HTTPException(429, "Local investigation limit reached: 10 per hour")
            recent.append(stamp)
            return service.investigate(submission)
        except InvestigationUnavailable as exc:
            raise HTTPException(503, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            # Never disclose credentials, raw provider errors, or submitted content.
            logging.getLogger("proofmesh").error("Investigation failed: %s", type(exc).__name__)
            raise HTTPException(502, "Investigation failed. No report was published; check server configuration and retry.") from exc
        finally:
            lock.release()

    @app.post("/api/jobs", status_code=202)
    def start_job(submission: Submission, background: BackgroundTasks, request: Request, retry_failed: bool = False):
        submission = scope(submission, request)
        if not live:
            raise HTTPException(503, "Live investigation is disabled")
        try:
            job, created = jobs.reserve(submission, retry_failed=retry_failed)
            if created:
                try:
                    jobs.save_image(job['id'], submission.image_base64)
                    if jobs.cloud:
                        jobs.enqueue(job['id'])
                    else:
                        background.add_task(jobs.run, job['id'])
                except Exception:
                    jobs.update(job['id'], status='failed', error='Could not enqueue investigation. No model was invoked.')
                    jobs.image(jobs.get(job['id'])['image_key'], delete=True)
                    raise HTTPException(503, "Could not enqueue investigation")
            return jobs.public(job)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.get("/api/jobs/{job_id}")
    def read_job(job_id: str, request: Request):
        if not re.fullmatch(r"[a-f0-9]{64}", job_id):
            raise HTTPException(404, "Job not found")
        job = jobs.get(job_id)
        if job and request.state.role == "review" and job.get("corpus", "live") != "review":
            raise HTTPException(404, "Job not found")
        if not job:
            # Cached jobs can have no job document.
            report = store.get(job_id)
            if report and (request.state.role != "review" or report.get("corpus") == "review"):
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
        import json
        path = ROOT / "web/recorded-cases.json"
        return {"reports": json.loads(path.read_text()) if path.exists() else []}

    @app.get("/")
    def index():
        return FileResponse(ROOT / "web/index.html")

    @app.get("/feed")
    def feed():
        return FileResponse(ROOT / "web/feed.html")

    app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")
    return app
