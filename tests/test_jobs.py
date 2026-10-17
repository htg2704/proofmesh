import json
from datetime import timedelta
from app.jobs import Jobs, utc
from app.models import Submission
from app.service import ProofMesh
from app.store import SQLiteStore
class FakeInvestigator:
    def __init__(self): self.calls = 0
    def investigate(self, submission, reference_date):
        self.calls += 1
        return {"assessment": {"summary": "Unresolved", "findings": [], "limitations": []}, "evidence": [], "events": [], "model_calls": 3}


def make(tmp_path):
    store = SQLiteStore(str(tmp_path / 'jobs.sqlite'))
    service = ProofMesh(store, FakeInvestigator())
    return Jobs(store, service), service


def test_jobs_survive_restart_and_duplicate_submission(tmp_path):
    jobs, service = make(tmp_path)
    sub = Submission(claim='A durable investigation claim')
    job, created = jobs.reserve(sub)
    assert created
    again, created = jobs.reserve(sub)
    assert again['id'] == job['id'] and not created
    restarted = Jobs(SQLiteStore(jobs.store.path), service)
    restarted.run(job['id'])
    assert restarted.get(job['id'])['status'] == 'succeeded'
    restarted.run(job['id'])
    assert service.investigator.calls == 1
    cached, created = restarted.reserve(sub)
    assert not created and cached['model_calls'] == 0


def test_interrupted_job_does_not_retry_model(tmp_path):
    jobs, service = make(tmp_path)
    job, _ = jobs.reserve(Submission(claim='A potentially interrupted claim'))
    jobs.update(job['id'], status='running', started_at=(utc()-timedelta(minutes=7)).isoformat())
    assert jobs.get(job['id'])['status'] == 'failed'
    jobs.run(job['id'])
    assert service.investigator.calls == 0


def test_durable_daily_quota(tmp_path, monkeypatch):
    monkeypatch.setenv('PROOFMESH_DAILY_JOBS', '1')
    jobs, _ = make(tmp_path)
    jobs.reserve(Submission(claim='The first distinct claim'))
    import pytest
    with pytest.raises(ValueError, match='cap reached'):
        jobs.reserve(Submission(claim='The second distinct claim'))


def test_api_jobs_auth_and_public_demo(tmp_path, monkeypatch):
    from app.main import create_app
    from fastapi.testclient import TestClient
    monkeypatch.setenv('PROOFMESH_API_TOKEN', 'a-long-test-token-0123456789')
    monkeypatch.setenv('PROOFMESH_ENABLE_LIVE', 'true')
    client = TestClient(create_app(SQLiteStore(str(tmp_path/'api.sqlite')), FakeInvestigator()))
    assert client.post('/api/jobs', json={'claim':'A new live claim'}).status_code == 401
    assert client.post('/internal/jobs/'+'a'*64).status_code == 401
    assert client.post('/api/demo',json={}).status_code == 200
    headers={'Authorization':'Bearer a-long-test-token-0123456789'}
    result=client.post('/api/jobs',json={'claim':'A new live claim'},headers=headers)
    assert result.status_code==202
    status=client.get('/api/jobs/'+result.json()['id'],headers=headers).json()
    assert status['status']=='succeeded'
    assert 'claim' not in status and 'image_key' not in status


def test_explicit_retry_is_bounded_and_counts_against_quota(tmp_path):
    jobs, _ = make(tmp_path)
    sub=Submission(claim='A failed job eligible for one manual retry')
    job,_=jobs.reserve(sub)
    jobs.update(job['id'],status='failed')
    assert jobs.reserve(sub)[1] is False
    retried,created=jobs.reserve(sub,retry_failed=True)
    assert created and retried['attempt']==2
    jobs.update(job['id'],status='failed')
    assert jobs.reserve(sub,retry_failed=True)[1] is False


def test_window_cap_covers_previous_days(tmp_path,monkeypatch):
    monkeypatch.setenv('PROOFMESH_TOTAL_JOBS','1')
    jobs,_=make(tmp_path)
    job,_=jobs.reserve(Submission(claim='A claim on an earlier day'))
    jobs.update(job['id'],created_at='2020-01-01T00:00:00+00:00')
    import pytest
    with pytest.raises(ValueError,match='Live-window'):
        jobs.reserve(Submission(claim='A distinct claim the next day'))


def test_capacity_failure_publishes_no_report_and_does_not_restart(tmp_path):
    jobs, service = make(tmp_path)
    class CapacityError(Exception):
        code = 429
    calls = []
    def unavailable(*args, **kwargs):
        calls.append(1)
        raise CapacityError()
    service.investigate = unavailable
    job, _ = jobs.reserve(Submission(claim='A capacity constrained claim'))
    jobs.run(job['id'])
    jobs.run(job['id'])
    failed = jobs.get(job['id'])
    assert failed['status'] == 'failed' and failed['error_code'] == 429
    assert 'capacity' in failed['error'] and failed['report_id'] is None
    assert len(calls) == 1
