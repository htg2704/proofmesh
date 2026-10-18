import json
from datetime import timedelta
import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from app.models import Submission
from app.jobs import Jobs, utc
from app.service import ProofMesh
from app.store import SQLiteStore
from app.main import create_app
from tests.test_jobs import FakeInvestigator

KEY='AIza-personal-test-key-never-a-real-key'

@pytest.fixture
def jobs(tmp_path,monkeypatch):
    monkeypatch.setenv('PROOFMESH_CREDENTIAL_ENCRYPTION_KEY',Fernet.generate_key().decode())
    monkeypatch.setenv('PROOFMESH_CLIENT_DAILY_JOBS','1')
    monkeypatch.setenv('PROOFMESH_PROJECT_BUDGET_USD','0.5')
    monkeypatch.setenv('PROOFMESH_JOB_RESERVE_USD','0.5')
    store=SQLiteStore(str(tmp_path/'byok.db'))
    return Jobs(store,ProofMesh(store,FakeInvestigator()))

def sub(claim,key=None):
    return Submission(claim=claim,provider_api_key=key).for_client('a'*24)

def test_personal_key_bypasses_daily_and_trial_funds_but_not_isolation(jobs):
    jobs.reserve(sub('Trial funded first check'))
    for i in range(3):
        job,created=jobs.reserve(sub(f'Personal key distinct check {i}',KEY))
        assert created and job['corpus']=='client:'+'a'*24
    with pytest.raises(ValueError,match='trial funds'):jobs.reserve(sub('More project funded work'))
    with jobs.store.connect() as db:
        assert db.execute('SELECT reserved_microusd FROM project_funds').fetchone()[0]==500_000

def test_personal_key_encrypted_removed_and_never_published(jobs):
    submission=sub('Encrypted credentials lifecycle',KEY)
    assert KEY not in repr(submission) and 'provider_api_key' not in submission.model_dump()
    seen=[]
    original=jobs.service.investigator.investigate
    def inspect(s,date):
        seen.append(s.provider_api_key)
        return original(s,date)
    jobs.service.investigator.investigate=inspect
    job,_=jobs.reserve(submission)
    assert job['provider_key_ciphertext'] and KEY not in json.dumps(job)
    assert 'provider_key_ciphertext' not in jobs.public(job)
    jobs.run(job['id'])
    completed=jobs.get(job['id']);assert completed['status']=='succeeded' and completed['provider_key_ciphertext'] is None
    assert seen==[KEY]
    report=jobs.store.get(completed['report_id']);assert KEY not in json.dumps(report) and 'provider_api_key' not in json.dumps(report)
    cached,_=jobs.reserve(submission);assert cached['report_id']==completed['report_id']

def test_expired_key_never_falls_back_to_project_credentials(jobs):
    job,_=jobs.reserve(sub('Expired queued credential',KEY))
    jobs.update(job['id'],created_at=(utc()-timedelta(minutes=16)).isoformat())
    jobs.run(job['id'])
    assert jobs.get(job['id'])['status']=='failed'
    assert jobs.get(job['id'])['provider_key_ciphertext'] is None
    assert jobs.service.investigator.calls==0

def test_rotation_changes_job_identity_failure_clears_key(jobs):
    first,_=jobs.reserve(sub('Failed credential then rotated',KEY))
    def fail(*a):raise RuntimeError('provider error with secret '+KEY)
    jobs.service.investigator.investigate=fail
    jobs.run(first['id'])
    failed=jobs.get(first['id']);assert failed['provider_key_ciphertext'] is None and KEY not in json.dumps(jobs.public(failed))
    second,created=jobs.reserve(sub('Failed credential then rotated',KEY+'different'))
    assert created and second['id']!=first['id']

def test_no_encryption_fails_before_admission(jobs,monkeypatch):
    monkeypatch.delenv('PROOFMESH_CREDENTIAL_ENCRYPTION_KEY')
    with pytest.raises(ValueError,match='not configured'):jobs.reserve(sub('Cannot store unencrypted credential',KEY))
    with jobs.store.connect() as db:assert db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]==0

def test_api_invalid_key_does_not_echo_sensitive_input(jobs,monkeypatch):
    monkeypatch.setenv('PROOFMESH_API_TOKEN','owner-abcdefghijklmnopqrstuvwxyz')
    client=TestClient(create_app(jobs.store,FakeInvestigator()))
    result=client.post('/api/jobs',headers={'Authorization':'Bearer owner-abcdefghijklmnopqrstuvwxyz'},json={'claim':'A complete claim','provider_api_key':'secret-too-short'})
    assert result.status_code==422 and 'secret-too-short' not in result.text

def test_sdk_personal_key_route_never_loads_adc_or_cloud_vision(monkeypatch):
    from google import genai
    import google.auth
    from app.investigator import GeminiInvestigator
    monkeypatch.setenv('PROOFMESH_ENABLE_LIVE','true')
    monkeypatch.delenv('GOOGLE_CLOUD_PROJECT',raising=False)
    calls=[]
    class Stop(Exception):pass
    def client(**kwargs):calls.append(kwargs);raise Stop()
    monkeypatch.setattr(genai,'Client',client)
    def forbidden(*a,**kw):raise AssertionError('Project funded service invoked')
    monkeypatch.setattr(google.auth,'default',forbidden)
    with pytest.raises(Stop):GeminiInvestigator(media_retriever=forbidden).investigate(Submission(claim='Personal Gemini routing',provider_api_key=KEY),'2026-10-18')
    assert calls[0]['vertexai'] is False and calls[0]['api_key']==KEY
    assert 'project' not in calls[0] and 'credentials' not in calls[0]
