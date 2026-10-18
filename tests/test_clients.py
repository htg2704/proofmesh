import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from app.clients import ClientAccess, RateLimited, trusted_credentials
from app.main import create_app
from app.models import Submission
from app.store import SQLiteStore

TEAM='owner-token-abcdefghijklmnopqrstuvwxyz'
TRUSTED={name:name+'-testing-token-abcdefghijklmnopqrstuvwxyz' for name in ['harshwardhan','chennika','codex-testing']}

class Fake:
    def investigate(self,submission,reference_date):
        return {'assessment':{'summary':'Test fixture, not a model result','findings':[],'limitations':[]},'evidence':[],'events':[],'model_calls':0}

@pytest.fixture
def api(tmp_path,monkeypatch):
    monkeypatch.setenv('PROOFMESH_CLIENT_LIMITS_ENABLED','true')
    monkeypatch.setenv('PROOFMESH_API_TOKEN',TEAM)
    monkeypatch.setenv('PROOFMESH_TRUSTED_TOKENS',json.dumps(TRUSTED))
    monkeypatch.setenv('PROOFMESH_ENABLE_LIVE','true')
    monkeypatch.setenv('PROOFMESH_SELF_REGISTRATION','true')
    monkeypatch.setenv('PROOFMESH_CLIENT_REQUESTS_PER_MINUTE','100')
    monkeypatch.setenv('PROOFMESH_TOTAL_JOBS','20')
    monkeypatch.setenv('PROOFMESH_DAILY_JOBS','1')
    monkeypatch.setenv('PROOFMESH_CLIENT_DAILY_JOBS','1')
    monkeypatch.delenv('PROOFMESH_REVIEW_TOKEN',raising=False)
    return TestClient(create_app(SQLiteStore(str(tmp_path/'api.sqlite')),Fake()))

def headers(token):return {'Authorization':'Bearer '+token}
def enroll(api,label='Example app'):return api.post('/api/v1/access/register',json={'label':label}).json()

def test_client_credentials_persist_hash_only_expire_and_revoke(tmp_path):
    path=str(tmp_path/'keys.sqlite');clock=[100]
    access=ClientAccess(SQLiteStore(path),clock=lambda:clock[0]);key=access.issue('Example app')
    stored=access.get(key['id']);assert key['token'] not in json.dumps(stored)
    assert stored['token_hash']==hashlib.sha256(key['token'].encode()).hexdigest()
    reopened=ClientAccess(SQLiteStore(path),clock=lambda:clock[0])
    assert reopened.authenticate(key['token']).identifier==key['id']
    assert not reopened.authenticate(key['token']+'x')
    clock[0]=key['expires_at'];assert not reopened.authenticate(key['token'])
    clock[0]=101;assert reopened.revoke(key['id'])
    assert not access.authenticate(key['token'])
    assert 'token_hash' not in json.dumps(access.all())

def test_request_counter_is_atomic_persistent_and_resets(tmp_path):
    path=str(tmp_path/'rates.sqlite');clock=[120]
    def take(_):
        access=ClientAccess(SQLiteStore(path),clock=lambda:clock[0])
        try:access.take('client-a',5);return True
        except RateLimited:return False
    with ThreadPoolExecutor(max_workers=8) as pool:assert sum(pool.map(take,range(16)))==5
    access=ClientAccess(SQLiteStore(path),clock=lambda:clock[0])
    with pytest.raises(RateLimited) as e:access.take('client-a',5)
    assert e.value.retry_after==60
    assert access.take('client-b',5)['X-RateLimit-Remaining']=='4'
    clock[0]=180;assert access.take('client-a',5)['X-RateLimit-Remaining']=='4'

def test_client_isolation_jobs_reports_lookup_and_admin(api):
    a,b=enroll(api,'Client A'),enroll(api,'Client B');ha,hb=headers(a['token']),headers(b['token'])
    body={'claim':'A fixed isolated test claim','corpus':'review'}
    first=api.post('/api/v1/jobs',json=body,headers=ha);assert first.status_code==202
    rid=first.json()['id'];assert api.get('/api/v1/jobs/'+rid,headers=ha).json()['status']=='succeeded'
    report=api.get('/api/v1/investigations/'+rid,headers=ha);assert report.status_code==200
    assert report.json()['corpus']=='client:'+a['id']
    assert api.get('/api/jobs/'+rid,headers=hb).status_code==404
    assert api.get('/api/investigations/'+rid,headers=headers(TEAM)).status_code==200
    assert api.get('/api/investigations/'+rid,headers=hb).status_code==404
    assert api.get('/api/investigations?corpus=review',headers=hb).json()['reports']==[]
    assert api.post('/api/matches',json=body,headers=hb).json()['report'] is None
    assert api.post('/api/investigations',json=body,headers=ha).json()['model_calls']==0
    assert api.post('/api/investigations',json={'claim':'An uncached fresh claim'},headers=ha).status_code==409
    assert api.post('/api/clients',json={'label':'Escalation'},headers=ha).status_code==403
    assert api.get('/api/clients',headers=ha).status_code==403
    assert api.post('/api/clients/'+b['id']+'/revoke',json={},headers=ha).status_code==403
    assert api.post('/api/jobs',json={**body,'bypass_rate_limits':True},headers=ha).status_code==422
    assert api.post('/api/jobs',json={**body,'_client_id':b['id']},headers=ha).status_code==422

def test_client_job_limit_returns_429_but_reuse_is_free(api):
    a=enroll(api);h=headers(a['token']);body={'claim':'First bounded client claim'}
    assert api.post('/api/jobs',json=body,headers=h).status_code==202
    repeat=api.post('/api/jobs',json=body,headers=h);assert repeat.status_code==202 and repeat.json()['model_calls']==0
    denied=api.post('/api/jobs',json={'claim':'Second distinct client claim'},headers=h)
    assert denied.status_code==429 and int(denied.headers['Retry-After'])>0

@pytest.mark.parametrize('name',TRUSTED)
def test_trusted_testers_bypass_rate_and_daily_caps_but_not_spending_guard(api,monkeypatch,name):
    monkeypatch.setenv('PROOFMESH_CLIENT_REQUESTS_PER_MINUTE','1')
    monkeypatch.setenv('PROOFMESH_PROJECT_BUDGET_USD','1')
    monkeypatch.setenv('PROOFMESH_JOB_RESERVE_USD','0.5')
    h=headers(TRUSTED[name])
    for _ in range(4):
        health=api.get('/api/health',headers=h);assert health.status_code==200 and health.json()['rate_limits_exempt']
        assert 'X-RateLimit-Limit' not in health.headers
    for i in range(2):assert api.post('/api/jobs',json={'claim':f'Trusted test {i}'},headers=h).status_code==202
    denied=api.post('/api/jobs',json={'claim':'Third trusted test'},headers=h)
    assert denied.status_code==503 and 'trial funds' in denied.json()['detail']

def test_request_throttle_and_revocation_are_enforced(api,monkeypatch):
    key=enroll(api);h=headers(key['token']);monkeypatch.setenv('PROOFMESH_CLIENT_REQUESTS_PER_MINUTE','1')
    one=api.get('/api/health',headers=h);assert one.status_code==200 and one.headers['X-RateLimit-Remaining']=='0'
    two=api.get('/api/health',headers=h);assert two.status_code==429 and 'Retry-After' in two.headers
    assert api.post('/api/clients/'+key['id']+'/revoke',json={},headers=headers(TEAM)).status_code==200
    assert api.get('/api/investigations',headers=h).status_code==401

def test_registration_can_be_disabled_and_owner_still_issues_keys(api,monkeypatch):
    monkeypatch.setenv('PROOFMESH_SELF_REGISTRATION','false')
    assert api.post('/api/access/register',json={'label':'Example app'}).status_code==403
    key=api.post('/api/clients',json={'label':'Approved app'},headers=headers(TEAM));assert key.status_code==201
    rows=api.get('/api/clients',headers=headers(TEAM)).json()['clients']
    assert len(rows)==1 and 'token' not in rows[0] and 'token_hash' not in rows[0]

def test_registration_has_its_own_persistent_global_limit(api,monkeypatch):
    monkeypatch.setenv('PROOFMESH_REGISTRATIONS_PER_HOUR','1')
    assert api.post('/api/access/register',json={'label':'First app'}).status_code==201
    denied=api.post('/api/access/register',json={'label':'Second app'})
    assert denied.status_code==429 and 'Retry-After' in denied.headers

def test_invalid_or_duplicate_trusted_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv('PROOFMESH_TRUSTED_TOKENS',json.dumps({'a':'x'*32,'b':'x'*32}))
    with pytest.raises(RuntimeError):trusted_credentials()

def test_browser_works_without_codes_and_keeps_guest_key_httponly(api):
    guest=api.post('/api/access/guest',json={})
    assert guest.status_code==200 and guest.json()['access']=='client' and 'token' not in guest.json()
    assert 'HttpOnly' in guest.headers['set-cookie'] and 'SameSite=strict' in guest.headers['set-cookie']
    assert api.get('/api/health').json()['access']=='client'
    assert api.post('/api/jobs',json={'claim':'A guest browser investigation'}).status_code==202
    assert api.post('/api/access/guest',json={}).json()['access']=='client'
    rows=api.get('/api/clients',headers=headers(TEAM)).json()['clients'];assert len(rows)==1

def test_published_examples_reuse_only_exact_fresh_context():
    import base64
    from datetime import datetime,timezone,timedelta
    from app.demo import demo_image
    from app.fingerprints import image_identity
    from app.examples import match_examples
    raw=base64.b64encode(demo_image()).decode();stamp=datetime(2026,10,17,12,tzinfo=timezone.utc)
    sub=Submission(claim='A deliberately published fixture',image_base64=raw)
    report={'id':'a'*64,'claim':sub.claim,'recorded_example':True,'evidence_policy':'0.6','media':image_identity(raw),'created_at':stamp.isoformat(),'expires_at':(stamp+timedelta(hours=1)).isoformat()}
    assert match_examples(sub,[report],stamp)[0]==report
    changed=sub.model_copy(update={'claim':'A different claim on the same image'})
    exact,related=match_examples(changed,[report],stamp);assert exact is None and related[0]['public_example']
    assert match_examples(sub,[report],stamp+timedelta(hours=2))[0] is None
    assert match_examples(sub,[{**report,'recorded_example':False}],stamp)==(None,[])

def test_browser_integrations_allow_bearer_preflight_without_cross_origin_cookies(api):
    response=api.options('/api/v1/matches',headers={'Origin':'https://third-party.example','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'authorization,content-type'})
    assert response.status_code==200 and response.headers['access-control-allow-origin']=='*'
    assert 'access-control-allow-credentials' not in response.headers
    blocked=api.options('/internal/jobs/'+'a'*64,headers={'Origin':'https://third-party.example','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'x-proofmesh-worker-token'})
    assert blocked.status_code==400

def test_public_mvp_has_no_client_request_daily_or_registration_caps(tmp_path,monkeypatch):
    monkeypatch.delenv('PROOFMESH_CLIENT_LIMITS_ENABLED',raising=False)
    monkeypatch.setenv('PROOFMESH_API_TOKEN',TEAM)
    monkeypatch.setenv('PROOFMESH_ENABLE_LIVE','true')
    monkeypatch.setenv('PROOFMESH_SELF_REGISTRATION','true')
    for variable in ['PROOFMESH_CLIENT_REQUESTS_PER_MINUTE','PROOFMESH_CLIENT_DAILY_JOBS','PROOFMESH_REGISTRATIONS_PER_HOUR']:monkeypatch.setenv(variable,'1')
    client=TestClient(create_app(SQLiteStore(str(tmp_path/'uncapped.sqlite')),Fake()))
    keys=[client.post('/api/access/register',json={'label':f'Client {i}'}) for i in range(3)]
    assert all(r.status_code==201 for r in keys)
    h=headers(keys[0].json()['token'])
    for _ in range(3):
        response=client.get('/api/health',headers=h);assert response.status_code==200
        body=response.json();assert not body['client_limits_enabled'] and body['rate_limits_exempt']
        assert body['client_daily_jobs'] is None and body['client_requests_per_minute'] is None and body['registrations_per_hour'] is None
        assert 'X-RateLimit-Limit' not in response.headers
    for i in range(3):assert client.post('/api/jobs',json={'claim':f'A separate uncapped client check {i}'},headers=h).status_code==202
    assert client.get('/api/clients',headers=h).status_code==403
    assert client.post('/api/jobs',json={'claim':'Cannot change server policy','client_limits_enabled':False},headers=h).status_code==422


def test_disabling_client_caps_ignores_existing_counters_but_preserves_funding_guard(api,monkeypatch):
    key=enroll(api);h=headers(key['token'])
    assert api.post('/api/jobs',json={'claim':'One bounded old-policy check'},headers=h).status_code==202
    assert api.post('/api/jobs',json={'claim':'Blocked old-policy check'},headers=h).status_code==429
    monkeypatch.setenv('PROOFMESH_CLIENT_LIMITS_ENABLED','false')
    assert api.post('/api/jobs',json={'claim':'Allowed after policy removal'},headers=h).status_code==202
    monkeypatch.setenv('PROOFMESH_PROJECT_BUDGET_USD','0.5')
    monkeypatch.setenv('PROOFMESH_JOB_RESERVE_USD','0.5')
    assert api.post('/api/jobs',json={'claim':'One project funded new check'},headers=h).status_code==202
    denied=api.post('/api/jobs',json={'claim':'Funding approval still applies'},headers=h)
    assert denied.status_code==503 and 'trial funds' in denied.json()['detail']
