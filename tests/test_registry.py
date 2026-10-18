import copy
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import base64
import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.models import Submission
from app.service import ProofMesh, now
from app.store import SQLiteStore
from app.registry import PublicRegistry, snapshot
from app.demo import demo_image

class Validated:
    def __init__(self):self.calls=0
    def investigate(self, submission, reference_date):
        self.calls+=1
        return {'assessment':{'summary':'A mocked source-backed assessment','findings':[{'claim':submission.claim,'status':'supported','explanation':'Mock evidence','evidence_ids':['E1'],'evidence_quotes':[{'evidence_id':'E1','quote':'A verified source passage'}]}],'limitations':['Test fixture only']},'origin':{'status':'unknown'},'evidence':[{'id':'E1','title':'Mock source','url':'https://example.org/source','excerpt':'A verified source passage','kind':'source_page_excerpt'}],'events':[],'model_calls':3,'assessment_status':'complete','validation':{'status':'passed','diagnostics':[]}}

@pytest.fixture
def service(tmp_path):return ProofMesh(SQLiteStore(str(tmp_path/'registry.sqlite')),Validated())

def sub(claim='A stable source-backed claim',owner='a',shared=False,image=False):
    return Submission(claim=claim,share_publicly=shared,image_base64=base64.b64encode(demo_image()).decode() if image else None).for_client(owner*24)

def record(service,claim,owner='a'):
    return service.investigate(sub(claim,owner))['report']

def test_cross_client_reuse_uses_public_snapshot_not_private_id(service):
    a=service.investigate(sub(shared=True))['report'];pub=service.registry.all()[0]
    assert pub['id']!=a['id'] and pub['corpus']=='public'
    b=service.investigate(sub(owner='b'))
    assert b['reused'] and b['model_calls']==0 and b['report']['id']==pub['id']
    assert service.investigator.calls==1 and service.store.all('client:'+'b'*24)==[]

def test_private_reports_are_never_implicitly_migrated(service):
    a=record(service,'A private historical investigation')
    assert not service.registry.all()
    assert not service.match(sub(a['claim'],owner='b'))['report']
    assert service.investigator.calls==1

def test_public_snapshot_whitelist_excludes_identity_inputs_and_credentials(service):
    a=record(service,'A deliberately published investigation')
    a.update(client_id='private-client-marker',provider_api_key='secret-marker',provider_key_ciphertext='ciphertext-marker',image_base64='private-image-marker',arbitrary_field='private-unknown-marker')
    a['publication_context']['source_url']='https://example.org/?private-marker=secret'
    pub=service.registry.publish(a);encoded=json.dumps(pub)
    for marker in ['private-client-marker','secret-marker','ciphertext-marker','private-image-marker','private-unknown-marker','private-marker',a['id']]:assert marker not in encoded
    assert pub['assessment']==a['assessment'] and pub['media']==a['media']

def test_capacity_200_is_hard_bounded_and_concurrent_publication_is_atomic(service):
    first=record(service,'Capacity fixture first report')
    reg=PublicRegistry(service.store,capacity=9999);assert reg.capacity==200
    def publish(i):
        r=copy.deepcopy(first);r['id']=f'{i:064x}';r['claim']=f'A unique capacity claim {i}'
        return reg.publish(r)
    with ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(publish,range(215)))
    assert len(reg.all())==200
    assert len(PublicRegistry(SQLiteStore(service.store.path)).all())==200
    assert service.store.get(first['id']) is not None

def test_expired_entries_are_removed_before_oldest_and_duplicates_do_not_expand(service):
    reg=PublicRegistry(service.store,capacity=2)
    a,b,c=[record(service,f'An admission fixture {i}') for i in range(3)]
    pa=reg.publish(a);reg.publish(b)
    assert reg.publish(a)['id']==pa['id'] and len(reg.all())==2
    reg.publish(c)
    assert reg.get(pa['id']) is None and service.store.get(a['id'])
    # Force the newer snapshot to expire while keeping the older valid snapshot.
    entries=reg.all();expired=entries[0]
    with service.store.connect() as db:
        body=json.loads(db.execute('SELECT body FROM public_registry WHERE id=?',(expired['id'],)).fetchone()[0]);body['report']['expires_at']=(now()-timedelta(seconds=1)).isoformat();db.execute('UPDATE public_registry SET body=? WHERE id=?',(json.dumps(body),expired['id']))
    reg.publish(record(service,'Another capacity fixture'))
    assert reg.get(expired['id']) is None and len(reg.all())==2

def test_expiry_policy_caption_and_publication_time_block_verdict_reuse(service):
    a=service.investigate(sub(shared=True,image=True))['report'];pub=service.registry.all()[0]
    changed=sub('A changed caption on the same image',owner='b',image=True)
    result=service.match(changed)
    assert result['report'] is None and result['related'][0]['reuse_blockers']==['caption_changed']
    timed=sub(owner='b',image=True).model_copy(update={'published_at':now()})
    assert 'publication_time_changed' in service.match(timed)['related'][0]['reuse_blockers']
    pub['evidence_policy']='earlier'
    with service.store.connect() as db:
        row=json.loads(db.execute('SELECT body FROM public_registry WHERE id=?',(pub['id'],)).fetchone()[0]);row['report']=pub;db.execute('UPDATE public_registry SET body=? WHERE id=?',(json.dumps(row),pub['id']))
    assert service.match(sub(owner='b',image=True))['report'] is None
    assert 'assessment_policy_changed' in service.match(sub(owner='b',image=True))['related'][0]['reuse_blockers']

def test_failed_or_stale_assessments_cannot_be_published(service):
    original=record(service,'A freshness and validation fixture')
    for change in [{'assessment_status':'validation_failed'},{'validation':{'status':'partial'}},{'evidence_policy':'old'},{'corpus':'demo'},{'expires_at':(now()-timedelta(seconds=1)).isoformat()},{'evidence':[]}]:
        with pytest.raises(ValueError):snapshot({**original,**change})

def test_registry_publish_failure_preserves_private_report_and_does_not_repeat_inference(service,monkeypatch):
    def fail(*a):raise RuntimeError('Registry unavailable')
    monkeypatch.setattr(service.registry,'publish',fail)
    result=service.investigate(sub(shared=True))
    assert result['report']['registry_publication']['status']=='unavailable'
    assert service.store.get(result['report']['id'])
    assert service.investigate(sub(shared=True))['model_calls']==0 and service.investigator.calls==1

def test_api_public_read_publication_authority_withdrawal_and_private_copy(tmp_path,monkeypatch):
    monkeypatch.setenv('PROOFMESH_API_TOKEN','owner-abcdefghijklmnopqrstuvwxyz')
    monkeypatch.setenv('PROOFMESH_ENABLE_LIVE','true')
    monkeypatch.setenv('PROOFMESH_SELF_REGISTRATION','true')
    model=Validated();app=create_app(SQLiteStore(str(tmp_path/'api.db')),model);api=TestClient(app)
    def enroll(name):
        key=api.post('/api/access/register',json={'label':name}).json();return {'Authorization':'Bearer '+key['token']}
    a,b=enroll('Publisher A'),enroll('Consumer B')
    private=api.post('/api/jobs',json={'claim':'A public API test claim'},headers=a).json();private_id=api.get('/api/jobs/'+private['id'],headers=a).json()['report_id']
    assert api.get('/api/registry').json()['size']==0
    assert api.post('/api/investigations/'+private_id+'/publish',json={},headers=b).status_code==404
    publication=api.post('/api/investigations/'+private_id+'/publish',json={},headers=a);assert publication.status_code==200
    public_id=publication.json()['id']
    assert api.get('/api/registry').json()['size']==1
    public=api.get('/api/registry/'+public_id);assert public.status_code==200 and public.json()['public_registry']
    assert private_id not in public.text
    assert api.get('/api/registry/'+private_id).status_code==404
    assert api.get('/api/investigations/'+private_id,headers=b).status_code==404
    match=api.post('/api/matches',json={'claim':'A public API test claim'},headers=b).json();assert match['report']['id']==public_id
    reused=api.post('/api/jobs',json={'claim':'A public API test claim'},headers=b).json();assert reused['model_calls']==0 and model.calls==1
    assert api.post('/api/registry/'+public_id+'/withdraw',json={}).status_code==401
    assert api.post('/api/registry/'+public_id+'/withdraw',json={},headers=b).status_code==403
    assert api.post('/api/registry/'+public_id+'/withdraw',json={},headers=a).status_code==200
    assert api.get('/api/registry/'+public_id).status_code==404
    assert api.get('/api/investigations/'+private_id,headers=a).json()['registry_publication']['status']=='withdrawn'
    assert api.get('/api/registry?limit=201').status_code==400


def test_legacy_same_caption_explains_policy_blocker_without_assessing_truth(service):
    r=service.investigate(sub(image=True))['report']
    legacy=copy.deepcopy(r);legacy['id']='c'*64;legacy['context_key']='c'*64;legacy.pop('evidence_policy');service.store.put(legacy)
    # Remove the new-policy exact row to simulate a pre-upgrade report only.
    with service.store.connect() as db:db.execute('DELETE FROM investigations WHERE id=?',(r['id'],))
    result=service.match(sub(image=True))
    assert result['status']=='related_media' and not result['report']
    assert result['related'][0]['reuse_blockers']==['assessment_policy_changed']
