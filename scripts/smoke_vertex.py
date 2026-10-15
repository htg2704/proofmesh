"""Run exactly one live pipeline; no automatic retries. May incur Google charges."""
import json
from pathlib import Path
import sys
from time import monotonic

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.dev import ROOT, load_settings
from app.investigator import GeminiInvestigator
from app.models import Submission
from app.service import ProofMesh
from app.store import SQLiteStore


def main():
    load_settings()
    service = ProofMesh(SQLiteStore(str(ROOT / "data/proofmesh.sqlite3")), GeminiInvestigator())
    submission = Submission(claim="NASA's Mars rover Perseverance landed on Mars on 18 February 2021.")
    started = monotonic()
    result = service.investigate(submission)
    report = result["report"]
    summary = {"report_id": report["id"], "reused": result["reused"], "model_calls": result["model_calls"],
               "elapsed_seconds": round(monotonic() - started, 2), "summary": report["assessment"]["summary"],
               "findings": report["assessment"]["findings"], "source_count": len({e["url"] for e in report["evidence"]}),
               "evidence_segments": len(report["evidence"]),
               "sources": [{"title": e["title"], "url": e["url"]} for e in report["evidence"]],
               "usage": report.get("usage", [])}
    (ROOT / "data/vertex-smoke-result.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    cached = service.investigate(submission)
    if not cached["reused"] or cached["model_calls"] != 0:
        raise RuntimeError("Repeated context did not reuse the stored report")
    print("Repeat lookup: reused report with zero model calls.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # SDK errors can contain private request metadata; never dump them.
        code = getattr(exc, "code", None)
        print(json.dumps({"status": "failed", "type": type(exc).__name__, "code": code}))
        raise SystemExit(1)
