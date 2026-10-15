import hmac
import logging
import os
import re
import threading
from collections import deque
from pathlib import Path
from time import monotonic
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse, Response, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from app.demo import seed, demo_image
from app.investigator import GeminiInvestigator, InvestigationUnavailable
from app.models import Submission
from app.service import ProofMesh
from app.store import SQLiteStore, FirestoreStore

ROOT = Path(__file__).resolve().parent.parent


def create_app(store=None, investigator=None):
    token = os.getenv("PROOFMESH_API_TOKEN", "")
    live = os.getenv("PROOFMESH_ENABLE_LIVE", "false").lower() == "true"
    if live and len(token) < 24:
        raise RuntimeError("Live mode requires PROOFMESH_API_TOKEN with at least 24 characters")
    if os.getenv("K_SERVICE") and (os.getenv("PROOFMESH_STORE") != "firestore" or len(token) < 24):
        raise RuntimeError("Cloud Run requires Firestore and an API token; local SQLite is ephemeral there")
    if store is None:
        store = (FirestoreStore(os.environ["GOOGLE_CLOUD_PROJECT"], os.getenv("PROOFMESH_FIRESTORE_COLLECTION", "proofmesh_investigations"))
                 if os.getenv("PROOFMESH_STORE") == "firestore" else SQLiteStore(os.getenv("PROOFMESH_DB", str(ROOT / "data/proofmesh.sqlite3"))))
    service = ProofMesh(store, investigator or GeminiInvestigator())
    app = FastAPI(title="ProofMesh", version="0.1.0", docs_url=None, redoc_url=None)
    app.state.service = service
    lock, recent = threading.Lock(), deque()

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        if request.url.path.startswith("/api/") and request.url.path != "/api/health":
            if token and not hmac.compare_digest(request.headers.get("authorization", ""), f"Bearer {token}"):
                return JSONResponse({"detail": "API token required"}, status_code=401)
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
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    def health():
        return {"status": "ok", "live_enabled": live, "authentication_required": bool(token), "version": "0.1.0"}

    @app.get("/api/investigations")
    def list_reports(corpus: str = "live"):
        if corpus not in {"live", "demo"}:
            raise HTTPException(400, "Unknown corpus")
        return {"reports": service.store.all(corpus)}

    @app.get("/api/investigations/{report_id}")
    def read_report(report_id: str):
        if not re.fullmatch(r"[a-f0-9]{64}", report_id):
            raise HTTPException(404, "Investigation not found")
        report = service.store.get(report_id)
        if not report:
            raise HTTPException(404, "Investigation not found")
        return report

    @app.post("/api/matches")
    def match(submission: Submission):
        try:
            return service.match(submission)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @app.post("/api/investigations")
    def investigate(submission: Submission):
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

    @app.post("/api/demo")
    def demo():
        return seed(service)

    @app.get("/fixtures/bridge.png")
    def bridge():
        return Response(demo_image(), media_type="image/png")

    @app.get("/fixtures/bridge-archive.txt")
    def archive():
        return PlainTextResponse("PROOFMESH SYNTHETIC FIXTURE\nIllustration: Riverton bridge.\nFictional archive date: 2021-06-18.\nThis is not a photograph of a real event. No external facts are asserted.\n")

    @app.get("/fixtures/bridge-archive")
    def archive_page():
        return FileResponse(ROOT / "web/evidence.html")

    @app.get("/")
    def index():
        return FileResponse(ROOT / "web/index.html")

    @app.get("/feed")
    def feed():
        return FileResponse(ROOT / "web/feed.html")

    app.mount("/assets", StaticFiles(directory=ROOT / "web"), name="assets")
    return app
