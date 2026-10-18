import hashlib
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.service import now
from app.store import SQLiteStore
from tests.test_registry import Validated

OWNER='owner-abcdefghijklmnopqrstuvwxyz'
JUDGE='pm_judge_fixture_abcdefghijklmnopqrstuvwxyz0123456789'

@pytest.fixture
def api(tmp_path,monkeypatch):
    monkeypatch.setenv('PROOFMESH_API_TOKEN',OWNER)
    monkeypatch.setenv('PROOFMESH_JUDGE_TOKEN',JUDGE)
    monkeypatch.setenv('PROOFMESH_JUDGE_UNTIL',(now()+timedelta(days=1)).isoformat())
    monkeypatch.setenv('PROOFMESH_ENABLE_LIVE','true')
    monkeypatch.setenv('PROOFMESH_SELF_REGISTRATION','true')
    monkeypatch.setenv('PROOFMESH_CLIENT_REQUESTS_PER_MINUTE','1')
    monkeypatch.setenv('PROOFMESH_CLIENT_DAILY_JOBS','1')
    return TestClient(create_app(SQLiteStore(str(tmp_path/'judge.db')),Validated()))

def auth(token):return {'Authorization':'Bearer '+token}

def test_judge_exempt_but_isolated_from_team_and_has_no_administration(api):
    owner,judge=auth(OWNER),auth(JUDGE)
    r=api.post('/api/jobs',json={'claim':'A private team investigation'},headers=owner);assert r.status_code==202
    private=api.get('/api/jobs/'+r.json()['id'],headers=owner).json()['report_id']
    for _ in range(3):
        health=api.get('/api/health',headers=judge);assert health.status_code==200 and health.json()['access']=='judge' and health.json()['rate_limits_exempt']
        assert 'X-RateLimit-Limit' not in health.headers
    assert api.get('/api/investigations/'+private,headers=judge).status_code==404
    for i in range(3):assert api.post('/api/jobs',json={'claim':f'A separate judge test {i}'},headers=judge).status_code==202
    rows=api.get('/api/investigations',headers=judge).json()['reports']
    namespace='client:'+hashlib.sha256(JUDGE.encode()).hexdigest()[:24]
    assert len(rows)==3 and all(r['corpus']==namespace for r in rows)
    assert api.post('/api/access/guest',json={},headers=judge).json()['access']=='judge'
    assert api.get('/api/clients',headers=judge).status_code==403
    assert api.post('/api/clients',json={'label':'Escalation'},headers=judge).status_code==403
    assert api.post('/api/jobs',json={'claim':'Attempt a privileged flag','bypass_rate_limits':True},headers=judge).status_code==422


def test_judge_still_respects_project_funding_approval(api,monkeypatch):
    monkeypatch.setenv('PROOFMESH_PROJECT_BUDGET_USD','0.5')
    monkeypatch.setenv('PROOFMESH_JOB_RESERVE_USD','0.5')
    assert api.post('/api/jobs',json={'claim':'One funded judge job'},headers=auth(JUDGE)).status_code==202
    denied=api.post('/api/jobs',json={'claim':'A second funded judge job'},headers=auth(JUDGE))
    assert denied.status_code==503 and 'trial funds' in denied.json()['detail']


def test_expired_or_short_judge_token_never_grants_access(tmp_path,monkeypatch):
    monkeypatch.setenv('PROOFMESH_API_TOKEN',OWNER)
    monkeypatch.setenv('PROOFMESH_JUDGE_TOKEN',JUDGE)
    monkeypatch.setenv('PROOFMESH_JUDGE_UNTIL','2020-01-01T00:00:00+00:00')
    client=TestClient(create_app(SQLiteStore(str(tmp_path/'expired.db')),Validated()))
    assert client.get('/api/health',headers=auth(JUDGE)).json()['access']=='none'
    assert client.get('/api/investigations',headers=auth(JUDGE)).status_code==401
    monkeypatch.setenv('PROOFMESH_JUDGE_TOKEN','too-short')
    with pytest.raises(RuntimeError,match='at least 32'):create_app(SQLiteStore(str(tmp_path/'short.db')),Validated())
