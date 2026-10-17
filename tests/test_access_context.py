from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.access import COOKIE, review_cookie, valid_cookie
from app.main import create_app
from app.models import Submission, Assessment
from app.service import ProofMesh
from app.store import SQLiteStore
from app.investigator import validate_assessment
from app.jobs import Jobs

TOKEN='team-token-abcdefghijklmnopqrstuvwxyz'
REVIEW='review-token-abcdefghijklmnopqrstuvwxyz'

class Fake:
    calls=0
    def investigate(self,submission,reference_date):
        self.calls+=1
        return {'assessment':{'summary':'Unresolved','findings':[],'limitations':[]},'evidence':[],'events':[],'model_calls':3}

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('PROOFMESH_API_TOKEN',TOKEN)
    monkeypatch.setenv('PROOFMESH_REVIEW_TOKEN',REVIEW)
    monkeypatch.setenv('PROOFMESH_ENABLE_LIVE','true')
    monkeypatch.setenv('PROOFMESH_DAILY_JOBS','20')
    return TestClient(create_app(SQLiteStore(str(tmp_path/'test.db')),Fake()))

def test_reviewer_cookie_expiry_and_tampering():
    cookie=review_cookie(REVIEW,now=100)
    assert valid_cookie(cookie,REVIEW,now=101)
    assert not valid_cookie(cookie,REVIEW,now=100+8*3600)
    assert not valid_cookie(cookie+'a',REVIEW,now=101)
    assert not valid_cookie(cookie,TOKEN,now=101)

def test_review_workspace_cannot_read_team_reports_or_jobs(client):
    team={'Authorization':'Bearer '+TOKEN}
    body={'claim':'An absolute historical claim','corpus':'live'}
    first=client.post('/api/jobs',json=body,headers=team);assert first.status_code==202
    team_id=first.json()['id']
    access=client.post('/api/access/reviewer',json={'code':REVIEW})
    assert access.status_code==200 and 'HttpOnly' in access.headers['set-cookie'] and 'SameSite=strict' in access.headers['set-cookie']
    assert client.get('/api/health').json()['access']=='review'
    assert client.get('/api/jobs/'+team_id).status_code==404
    assert client.get('/api/investigations/'+team_id).status_code==404
    assert client.get('/api/investigations?corpus=live').json()['reports']==[]
    second=client.post('/api/jobs',json=body);assert second.status_code==202
    assert second.json()['id']!=team_id
    job=client.get('/api/jobs/'+second.json()['id']).json()
    assert job['status']=='succeeded'
    reports=client.get('/api/investigations?corpus=live').json()['reports']
    assert len(reports)==1 and reports[0]['corpus']=='review'
    assert client.post('/api/investigations',json=body).status_code==409
    assert client.post('/internal/jobs/'+team_id).status_code==401

def test_bad_reviewer_code_does_not_grant_access(client):
    assert client.post('/api/access/reviewer',json={'code':'x'*32}).status_code==401
    assert client.get('/api/investigations').status_code==401

def test_staff_cannot_spend_reserved_review_budget(tmp_path,monkeypatch):
    monkeypatch.setenv('PROOFMESH_REVIEW_TOKEN',REVIEW)
    monkeypatch.setenv('PROOFMESH_TOTAL_JOBS','3')
    monkeypatch.setenv('PROOFMESH_REVIEW_JOBS','2')
    monkeypatch.setenv('PROOFMESH_DAILY_JOBS','20')
    store=SQLiteStore(str(tmp_path/'quota.db'));jobs=Jobs(store,ProofMesh(store,Fake()))
    jobs.reserve(Submission(claim='First team investigation'))
    with pytest.raises(ValueError,match='reserved'):
        jobs.reserve(Submission(claim='Second team investigation'))
    jobs.reserve(Submission(claim='First reviewer investigation',corpus='review'))
    jobs.reserve(Submission(claim='Second reviewer investigation',corpus='review'))
    with pytest.raises(ValueError,match='Reviewer'):
        jobs.reserve(Submission(claim='Third reviewer investigation',corpus='review'))

def test_publication_time_changes_context_and_timezone_normalizes(tmp_path):
    fake=Fake(); service=ProofMesh(SQLiteStore(str(tmp_path/'context.db')),fake)
    sub=Submission(claim='This event happened today.',published_at='2026-10-17T00:00:00Z')
    report=service.investigate(sub)['report']
    offset=sub.model_copy(update={'published_at':datetime.fromisoformat('2026-10-17T05:30:00+05:30')})
    assert service.match(offset)['report']['id']==report['id']
    later=sub.model_copy(update={'published_at':datetime(2026,10,18,tzinfo=timezone.utc)})
    assert service.match(later)['report'] is None
    assert report['publication_context']['published_at']=='2026-10-17T00:00:00+00:00'

def test_relative_caption_without_time_cannot_inherit_or_run(tmp_path):
    fake=Fake();service=ProofMesh(SQLiteStore(str(tmp_path/'context.db')),fake)
    sub=Submission(claim='This event happened today.')
    assert service.match(sub)['needs_publication_time']
    with pytest.raises(ValueError,match='publication time'):service.investigate(sub)
    assert fake.calls==0

def test_publication_time_requires_explicit_timezone():
    with pytest.raises(ValueError):Submission(claim='A date claim',published_at='2026-10-17T10:00:00')

def test_fabricated_quote_cannot_validate_even_with_real_source_id():
    sources=[{'id':'E1','kind':'source_page_excerpt','excerpt':'The event occurred on 24 December 1968.'}]
    assessment=Assessment(summary='Claim',findings=[{'claim':'A claim','status':'supported','explanation':'Because','evidence_ids':['E1'],'evidence_quotes':[{'evidence_id':'E1','quote':'The event occurred in 2026.'}]}],limitations=[])
    with pytest.raises(ValueError,match='quotation'):validate_assessment(assessment,sources)
    assessment.findings[0].evidence_quotes[0].quote='The event occurred on 24 December 1968.'
    assert validate_assessment(assessment,sources).findings[0].status=='supported'
