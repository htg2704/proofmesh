"""Prespecified development evaluation. No label changes or automatic paid retries."""
import base64
import io
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from scripts.dev import load_settings
load_settings()
from PIL import Image
from app.demo import demo_image
from app.models import Submission
from app.investigator import GeminiInvestigator
from app.service import ProofMesh
from app.store import SQLiteStore
ROOT=Path(__file__).resolve().parent.parent
out=ROOT/'data/evaluation-v04';out.mkdir(exist_ok=True)
service=ProofMesh(SQLiteStore(str(out/'reports.sqlite3')),GeminiInvestigator())
cases=json.loads((ROOT/'evaluation/cases-v04.json').read_text())
# Twelve prespecified cases; --recheck-failures permits one explicit rerun per failed case. Failures
# conservatively reserve $0.15 in the working estimate; billing can differ.
spent=0; results=[]
for case in cases:
    path=out/(case['id']+'.json')
    prior=out/(case['id']+'-first-attempt.json')
    if prior.exists():
        spent+=json.loads(prior.read_text()).get('working_cost_usd',0.15)
    if path.exists():
        row=json.loads(path.read_text())
        if '--recheck-failures' not in sys.argv or 'error_type' not in row or prior.exists():
            results.append(row);spent+=row.get('working_cost_usd',0.15);continue
        path.rename(prior);spent+=row.get('working_cost_usd',0.15)
    if spent+0.15>1.8:
        print('Stopped at evaluation budget guard.',flush=True);break
    raw=None
    if case.get('image')=='synthetic-bridge':raw=demo_image()
    elif case.get('image'):
        raw=(ROOT/'web/earthrise.jpg').read_bytes()
        if case['image']=='earthrise-crop':
            im=Image.open(io.BytesIO(raw));w,h=im.size;im=im.crop((int(w*.1),int(h*.1),int(w*.9),int(h*.9)))
            b=io.BytesIO();im.save(b,format='JPEG',quality=70);raw=b.getvalue()
    sub=Submission(claim=case['claim'],image_base64=base64.b64encode(raw).decode() if raw else None,published_at=case.get('published_at'))
    start=time.perf_counter()
    try:
        response=service.investigate(sub);elapsed=time.perf_counter()-start;report=response['report']
        stamp=time.perf_counter();cached=service.investigate(sub);reuse=time.perf_counter()-stamp
        statuses=[x['status'] for x in report['assessment']['findings']]
        observed='contradicted' if 'contradicted' in statuses else 'unresolved' if 'unresolved' in statuses or not statuses else 'supported'
        usage=report.get('usage',[])
        model_cost=sum((u.get('prompt_tokens') or 0)*1.5/1e6+((u.get('output_tokens') or 0)+(u.get('thinking_tokens') or 0))*9/1e6 for u in usage)
        queries=sum(u.get('reported_search_queries',0) for u in usage)
        cost=model_cost+queries*.014+(.004 if raw else 0)
        row={**case,'observed':observed,'matches_expected':observed==case['expected'] if case['expected']!='not_supported' else observed!='supported',
             'seconds':round(elapsed,3),'reuse_seconds':round(reuse,4),'model_calls':response['model_calls'],'repeat_model_calls':cached['model_calls'],
             'report_id':report['id'],'fetched_sources':len([e for e in report['evidence'] if e['kind']=='source_page_excerpt']),
             'usage':usage,'model_token_estimate_usd':round(model_cost,6),'working_cost_usd':round(max(cost,0.015),6),
             'assessment':report['assessment'],'events':report['events']}
        (out/(case['id']+'-report.json')).write_text(json.dumps(report,indent=2))
    except Exception as exc:
        row={**case,'error_type':type(exc).__name__,'error_code':getattr(exc,'code',None),'seconds':round(time.perf_counter()-start,3),'working_cost_usd':0.15}
    path.write_text(json.dumps(row,indent=2));results.append(row);spent+=row['working_cost_usd']
    print(json.dumps({k:v for k,v in row.items() if k in {'id','observed','matches_expected','seconds','model_calls','repeat_model_calls','error_type','error_code'}}),flush=True)
(out/'results.json').write_text(json.dumps(results,indent=2))
print('Working evaluation usage estimate:',round(spent,4),'USD; not an invoice.',flush=True)
