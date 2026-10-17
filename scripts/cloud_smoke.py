"""Exercise private Cloud Run, durable queue, Firestore and exact reuse."""
import json
import os
import subprocess
import time
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parent.parent
URL='https://proofmesh-2god3tua3a-el.a.run.app'
os.environ['CLOUDSDK_CORE_DISABLE_FILE_LOGGING']='true'
identity=subprocess.run(['/opt/homebrew/bin/gcloud','auth','print-identity-token'],check=True,capture_output=True,text=True).stdout.strip()
headers={'Authorization':'Bearer '+(ROOT/'data/cloud-api-token').read_text().strip(), 'X-Serverless-Authorization':'Bearer '+identity}
session=requests.Session();session.headers.update(headers)
result={'url':URL,'unauthenticated_status':requests.get(URL+'/api/health',timeout=20).status_code}
health=session.get(URL+'/api/health',timeout=30);health.raise_for_status();result['health']=health.json(); print(json.dumps(result),flush=True)
body={'claim':"NASA's Perseverance rover landed on Mars on February 18, 2021.", 'corpus':'live'}
start=time.perf_counter(); response=session.post(URL+'/api/jobs?retry_failed=true',json=body,timeout=25);response.raise_for_status();job=response.json()
result['job_id']=job['id'];print('Job '+job['id']+' queued',flush=True)
for _ in range(120):
    response=session.get(URL+'/api/jobs/'+job['id'],timeout=20);response.raise_for_status();job=response.json()
    if job['status'] in {'succeeded','failed'}:break
    time.sleep(3)
result['job']=job;result['elapsed_seconds']=round(time.perf_counter()-start,3)
if job['status']=='succeeded':
    report=session.get(URL+'/api/investigations/'+job['report_id'],timeout=20);report.raise_for_status()
    result['findings']=[f['status'] for f in report.json()['assessment']['findings']]
    start=time.perf_counter(); match=session.post(URL+'/api/matches',json=body,timeout=20);match.raise_for_status();matched=match.json()
    result.update(match_status=matched['status'],match_model_calls=matched['model_calls'],match_seconds=round(time.perf_counter()-start,4))
    (ROOT/'data/cloud-smoke-report.json').write_text(json.dumps(report.json(),indent=2))
(ROOT/'data/cloud-smoke-result-final.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result),flush=True)
