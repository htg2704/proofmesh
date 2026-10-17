import base64
from datetime import timedelta
from types import SimpleNamespace as NS
import pytest
from fastapi.testclient import TestClient
from app.demo import demo_image, seed, DEMO_CLAIM, ALTERNATE_CLAIM
from app.fingerprints import image_identity, context_key, normalize_claim
from app.investigator import validate_assessment, grounded_evidence
from app.main import create_app
from app.models import Submission, Assessment
from app.service import ProofMesh, now
from app.store import SQLiteStore


class FakeInvestigator:
    calls = 0
    def investigate(self, submission, reference_date):
        self.calls += 1
        return {"assessment": {"summary": "Unknown", "findings": [], "limitations": []}, "evidence": [], "events": [], "model_calls": 3}


@pytest.fixture
def service(tmp_path):
    return ProofMesh(SQLiteStore(str(tmp_path / "test.sqlite")), FakeInvestigator())


def submission(claim=DEMO_CLAIM, corpus="demo"):
    return Submission(claim=claim, image_base64=base64.b64encode(demo_image()).decode(), corpus=corpus, published_at="2026-10-14T12:00:00Z" if corpus == "live" else None)


def test_exact_context_reuses_without_inference(service):
    seed(service)
    result = service.investigate(submission())
    assert result["reused"] and result["model_calls"] == 0
    assert service.investigator.calls == 0


def test_same_image_different_caption_never_inherits_verdict(service):
    seed(service)
    match = service.match(submission(ALTERNATE_CLAIM))
    assert match["status"] == "related_media"
    assert match["report"] is None
    assert len(match["related"]) == 1
    assert "assessment" not in match["related"][0]


def test_live_and_demo_are_isolated(service):
    seed(service)
    assert service.match(submission(corpus="live"))["status"] == "unknown"


def test_first_live_then_cached_is_one_pipeline(service):
    first = service.investigate(submission(corpus="live"))
    second = service.investigate(submission(corpus="live"))
    assert first["model_calls"] == 3 and second["model_calls"] == 0
    assert service.investigator.calls == 1


def test_persistence_across_restart(service):
    seed(service)
    reopened = ProofMesh(SQLiteStore(service.store.path), FakeInvestigator())
    assert reopened.match(submission())["status"] == "exact_context"


def test_expired_report_does_not_reuse(service):
    report = seed(service)["report"]
    report["expires_at"] = (now() - timedelta(seconds=1)).isoformat()
    service.store.put(report)
    assert service.match(submission())["report"] is None


def test_reference_date_changes_identity():
    identity = image_identity(None)
    assert context_key("It happened today", identity, "live", "2026-10-14") != context_key("It happened today", identity, "live", "2026-10-15")


def test_normalization_preserves_negation_numbers_case():
    assert normalize_claim("  US   is 12 ") == "US is 12"
    assert normalize_claim("It happened") != normalize_claim("It did not happen")


@pytest.mark.parametrize("bad", ["not base64!", base64.b64encode(b"not an image").decode()])
def test_bad_image_rejected(bad):
    with pytest.raises(ValueError):
        image_identity(bad)


@pytest.mark.parametrize("ids", [[], ["invented"]])
def test_unsupported_conclusion_rejected(ids):
    assessment = Assessment(summary="Example", findings=[{"claim": "A claim", "status": "supported", "explanation": "Because", "evidence_ids": ids}], limitations=[])
    with pytest.raises(ValueError):
        validate_assessment(assessment, [{"id": "E1"}])


def test_grounding_drops_missing_and_unsafe_sources():
    meta = NS(grounding_chunks=[NS(web=NS(uri="javascript:alert(1)", title="bad")), NS(web=NS(uri="https://example.org", title="good"))],
              grounding_supports=[NS(segment=NS(text="Source-linked segment"), grounding_chunk_indices=[0, 1, 99])])
    evidence = grounded_evidence(NS(candidates=[NS(grounding_metadata=meta)]))
    assert len(evidence) == 1 and evidence[0]["url"] == "https://example.org"


def test_api_demo_matching_and_disabled_live(tmp_path, monkeypatch):
    monkeypatch.delenv("PROOFMESH_API_TOKEN", raising=False)
    monkeypatch.setenv("PROOFMESH_ENABLE_LIVE", "false")
    client = TestClient(create_app(SQLiteStore(str(tmp_path / "api.sqlite"))))
    demo = client.post("/api/demo", json={}).json()
    source = client.get(demo["report"]["evidence"][0]["url"])
    assert source.status_code == 200 and "text/html" in source.headers["content-type"]
    assert "Not real-world evidence" in source.text
    match = client.post("/api/matches", json={"claim": demo["claim"], "image_base64": demo["image_base64"], "corpus": "demo"})
    assert match.status_code == 200 and match.json()["status"] == "exact_context"
    response = client.post("/api/investigations", json={"claim": "A brand new factual claim"})
    assert response.status_code == 503
    assert client.get("/api/investigations?corpus=live").json()["reports"] == []


def test_auth_enforced(tmp_path, monkeypatch):
    monkeypatch.setenv("PROOFMESH_API_TOKEN", "a-long-test-token-0123456789")
    client = TestClient(create_app(SQLiteStore(str(tmp_path / "auth.sqlite")), FakeInvestigator()))
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/investigations").status_code == 401
    assert client.get("/api/investigations", headers={"Authorization": "Bearer a-long-test-token-0123456789"}).status_code == 200


def test_live_mode_requires_auth(tmp_path, monkeypatch):
    monkeypatch.setenv("PROOFMESH_ENABLE_LIVE", "true")
    monkeypatch.delenv("PROOFMESH_API_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        create_app(SQLiteStore(str(tmp_path / "auth.sqlite")))


def test_cloud_refuses_ephemeral_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("K_SERVICE", "proofmesh")
    monkeypatch.setenv("PROOFMESH_STORE", "sqlite")
    with pytest.raises(RuntimeError):
        create_app(SQLiteStore(str(tmp_path / "cloud.sqlite")))
