"""Persistent, deduplicated jobs. Never automatically repeat an uncertain model run."""
import hashlib
import base64
import json
import os
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from app.fingerprints import context_key, image_identity
from app.models import Submission
from app.credentials import seal, open_key, fingerprint, TTL_SECONDS
from app.context import publication_stamp, require_publication_context
from app.clients import RateLimited, SpendingLimit, DEFAULT_CLIENT_DAILY_JOBS


def utc():
    return datetime.now(timezone.utc)


class Jobs:
    def __init__(self, store, service):
        self.store, self.service = store, service
        self.cloud = hasattr(store, 'client')
        if self.cloud:
            self.collection = store.client.collection('proofmesh_jobs')
        else:
            with store.connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, body TEXT NOT NULL)')

    def get(self, key):
        if self.cloud:
            doc = self.collection.document(key).get()
            job = doc.to_dict() if doc.exists else None
        else:
            with self.store.connect() as db:
                row = db.execute('SELECT body FROM jobs WHERE id=?', (key,)).fetchone()
            job = json.loads(row[0]) if row else None
        if job and job.get('provider_key_ciphertext') and utc() > datetime.fromisoformat(job['created_at']) + timedelta(seconds=TTL_SECONDS):
            self.update(key, provider_key_ciphertext=None, status='failed', error='Personal Gemini key expired before completion; start a new investigation.')
            return self.get(key)
        if job and job['status'] == 'running' and utc() > datetime.fromisoformat(job['started_at']) + timedelta(minutes=6):
            # A killed worker may have consumed tokens; do not automatically reinvoke it.
            self.update(key, provider_key_ciphertext=None, status='failed', error='Worker interrupted. No automatic paid retry was attempted.')
            return self.get(key)
        return job

    def update(self, key, **changes):
        if self.cloud:
            self.collection.document(key).update(changes)
        else:
            with self.store.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute('SELECT body FROM jobs WHERE id=?', (key,)).fetchone()
                body = json.loads(row[0]); body.update(changes)
                db.execute('UPDATE jobs SET body=? WHERE id=?', (json.dumps(body), key))

    def reserve(self, submission, retry_failed=False, *, bypass_rate_limits=False, requested_by=None):
        if submission.corpus not in {'live', 'review'}:
            raise ValueError('New jobs require the live corpus')
        require_publication_context(submission)
        identity = image_identity(submission.image_base64)
        key = context_key(submission.claim, identity, submission.namespace, utc().date().isoformat(), publication_stamp(submission))
        byok = bool(submission.provider_api_key)
        if byok:
            key = hashlib.sha256((key + fingerprint(submission.provider_api_key)).encode()).hexdigest()
        cached = self.service.match(submission)['report']
        if cached:
            return {'id': key, 'status': 'succeeded', 'report_id': cached['id'], 'reused': True, 'model_calls': 0}, False
        cutoff = os.getenv('PROOFMESH_LIVE_UNTIL')
        if not byok and cutoff and utc() > datetime.fromisoformat(cutoff):
            raise SpendingLimit('Live demo window ended; matching existing evidence remains available.')
        client_id = submission._client_id
        day = utc().date().isoformat()
        reset = int((utc().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1) - utc()).total_seconds())
        job = {'id': key, 'status': 'queued', 'created_at': utc().isoformat(), 'claim': submission.claim, 'corpus': submission.namespace, 'published_at': publication_stamp(submission), 'source_url': submission.source_url, 'share_publicly': submission.share_publicly,
               'requested_by': requested_by, 'client_id': client_id,
               'funding': 'personal_gemini_key' if byok else 'project_trial',
               'provider_key_ciphertext': seal(submission.provider_api_key) if byok else None,
               'attempt': 1, 'image_key': None, 'report_id': None, 'reused': False, 'model_calls': None, 'error': None}
        reserve_usd = float(os.getenv('PROOFMESH_JOB_RESERVE_USD', '0.50'))
        budget_usd = float(os.getenv('PROOFMESH_PROJECT_BUDGET_USD', '0'))
        baseline_usd = float(os.getenv('PROOFMESH_BUDGET_BASELINE_USD', '0'))
        reserve_units = round(reserve_usd * 1_000_000) if not byok and budget_usd else 0
        budget_units = round(budget_usd * 1_000_000)
        baseline_units = round(baseline_usd * 1_000_000)
        def check_funds(used):
            if reserve_units and used + reserve_units > budget_units:
                raise SpendingLimit('Project trial funds are reserved. Use your own Gemini API key to continue; cached reports remain available.')
        # The quota and deduplication claim are committed together, across instances.
        if self.cloud:
            from google.cloud import firestore
            ref = self.collection.document(key)
            budget = self.store.client.collection('proofmesh_limits').document(utc().date().isoformat())
            total_ref = self.store.client.collection('proofmesh_limits').document('window_total')
            funds_ref = self.store.client.collection('proofmesh_limits').document('project_funds')
            client_ref = self.store.client.collection('proofmesh_client_daily').document(client_id) if client_id else None
            @firestore.transactional
            def take(transaction):
                old = ref.get(transaction=transaction)
                limit = budget.get(transaction=transaction)
                total_doc = total_ref.get(transaction=transaction)
                funds_doc = funds_ref.get(transaction=transaction)
                client_doc = client_ref.get(transaction=transaction) if client_ref else None
                if old.exists:
                    previous = old.to_dict()
                    if not retry_failed or previous['status'] != 'failed' or previous.get('attempt', 1) >= 2:
                        return previous, False
                    job['attempt'] = previous.get('attempt', 1) + 1
                count = limit.to_dict().get('count', 0) if limit.exists else 0
                total_count = total_doc.to_dict().get('count', 0) if total_doc.exists else count
                funds_used = funds_doc.to_dict().get('reserved_microusd', baseline_units) if funds_doc.exists else baseline_units
                check_funds(funds_used)
                client_body = client_doc.to_dict() if client_doc and client_doc.exists else {}
                client_count = client_body.get('count', 0) if client_body.get('day') == day else 0
                if not bypass_rate_limits and not byok:
                    if client_id and client_count >= int(os.getenv('PROOFMESH_CLIENT_DAILY_JOBS', str(DEFAULT_CLIENT_DAILY_JOBS))):
                        raise RateLimited('Client daily investigation limit reached. Cached evidence remains available.', reset)
                transaction.set(budget, {'count': count + 1})
                transaction.set(total_ref, {'count': total_count + 1})
                if reserve_units:
                    transaction.set(funds_ref, {'reserved_microusd': funds_used + reserve_units})
                if client_ref and not byok:
                    transaction.set(client_ref, {'day': day, 'count': client_count + 1})
                transaction.set(ref, job)
                return job, True
            return take(self.store.client.transaction())
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT body FROM jobs WHERE id=?', (key,)).fetchone()
            if old:
                previous = json.loads(old[0])
                if not retry_failed or previous['status'] != 'failed' or previous.get('attempt', 1) >= 2:
                    return previous, False
                job['attempt'] = previous.get('attempt', 1) + 1
            count = db.execute('SELECT COALESCE(SUM(COALESCE(json_extract(body, "$.attempt"), 1)),0) FROM jobs WHERE json_extract(body, "$.created_at") LIKE ?', (utc().date().isoformat() + '%',)).fetchone()[0]
            db.execute('CREATE TABLE IF NOT EXISTS project_funds (id INTEGER PRIMARY KEY, reserved_microusd INTEGER NOT NULL)')
            funds_row = db.execute('SELECT reserved_microusd FROM project_funds WHERE id=1').fetchone()
            funds_used = funds_row[0] if funds_row else baseline_units
            check_funds(funds_used)
            if not bypass_rate_limits and not byok:
                if client_id:
                    client_count = db.execute('SELECT COALESCE(SUM(COALESCE(json_extract(body, "$.attempt"),1)),0) FROM jobs WHERE json_extract(body, "$.client_id")=? AND COALESCE(json_extract(body, "$.funding"), "project_trial")="project_trial" AND json_extract(body, "$.created_at") LIKE ?', (client_id, day + '%')).fetchone()[0]
                    if client_count >= int(os.getenv('PROOFMESH_CLIENT_DAILY_JOBS', str(DEFAULT_CLIENT_DAILY_JOBS))):
                        raise RateLimited('Client daily investigation limit reached. Cached evidence remains available.', reset)
            if reserve_units:
                db.execute('INSERT OR REPLACE INTO project_funds VALUES (1,?)', (funds_used + reserve_units,))
            db.execute('INSERT OR REPLACE INTO jobs VALUES (?,?)', (key, json.dumps(job)))
        return job, True

    def save_image(self, key, encoded):
        if not encoded:
            return
        data = base64.b64decode(encoded)
        name = f'jobs/{key}-{secrets.token_hex(8)}'
        if self.cloud:
            from google.cloud import storage
            storage.Client(project=os.environ['GOOGLE_CLOUD_PROJECT']).bucket(os.environ['PROOFMESH_IMAGE_BUCKET']).blob(name).upload_from_string(data, content_type='application/octet-stream', timeout=20)
        else:
            path = Path(self.store.path).parent / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data); path.chmod(0o600)
        self.update(key, image_key=name)

    def image(self, name, delete=False):
        if not name:
            return None
        if self.cloud:
            from google.cloud import storage
            blob = storage.Client(project=os.environ['GOOGLE_CLOUD_PROJECT']).bucket(os.environ['PROOFMESH_IMAGE_BUCKET']).blob(name)
            if delete:
                blob.delete(timeout=20); return None
            return base64.b64encode(blob.download_as_bytes(timeout=20)).decode()
        path = Path(self.store.path).parent / name
        if delete:
            path.unlink(missing_ok=True); return None
        return base64.b64encode(path.read_bytes()).decode()

    def claim(self, key):
        if self.cloud:
            from google.cloud import firestore
            ref = self.collection.document(key)
            @firestore.transactional
            def take(transaction):
                snap = ref.get(transaction=transaction)
                if not snap.exists or snap.to_dict()['status'] != 'queued':
                    return False
                transaction.update(ref, {'status': 'running', 'started_at': utc().isoformat()})
                return True
            return take(self.store.client.transaction())
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT body FROM jobs WHERE id=?', (key,)).fetchone()
            if not row or json.loads(row[0])['status'] != 'queued':
                return False
            job = json.loads(row[0]); job.update(status='running', started_at=utc().isoformat())
            db.execute('UPDATE jobs SET body=? WHERE id=?', (json.dumps(job), key))
        return True

    def run(self, key):
        if not self.claim(key):
            return
        job = self.get(key)
        try:
            if job.get('funding') == 'personal_gemini_key' and not job.get('provider_key_ciphertext'):
                raise ValueError('Personal Gemini key expired')
            submission = Submission(claim=job['claim'], image_base64=self.image(job['image_key']), corpus='live' if job.get('client_id') else job.get('corpus', 'live'), published_at=job.get('published_at'), source_url=job.get('source_url'), provider_api_key=open_key(job.get('provider_key_ciphertext')), share_publicly=job.get('share_publicly', False))
            if job.get('client_id'):
                submission = submission.for_client(job['client_id'])
            result = self.service.investigate(submission)
            self.update(key, status='succeeded', report_id=result['report']['id'], model_calls=result['model_calls'], reused=result['reused'], completed_at=utc().isoformat())
        except Exception as exc:
            import logging
            logging.getLogger('proofmesh').error('Job failed: %s code=%s', type(exc).__name__, getattr(exc, 'code', None))
            code = getattr(exc, 'code', None)
            message = ('Gemini key rejected or not authorized. Check your key and its Gemini API access. ' if job.get('funding') == 'personal_gemini_key' and code in {400, 401, 403} else 'Google model capacity is temporarily unavailable (429). The bounded stage retry was exhausted. ' if code == 429 else 'Investigation failed. ')
            self.update(key, status='failed', error=message + 'No successful report was published; no automatic whole-investigation retry.', error_code=code, completed_at=utc().isoformat())
        finally:
            self.update(key, provider_key_ciphertext=None)
            try:
                self.image(job['image_key'], delete=True)
                self.update(key, image_key=None)
            except Exception:
                pass  # Private bucket lifecycle is the cleanup backstop.

    def enqueue(self, key):
        from google.cloud import tasks_v2
        from google.protobuf.duration_pb2 import Duration
        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(os.environ['GOOGLE_CLOUD_PROJECT'], os.environ['PROOFMESH_REGION'], os.environ['PROOFMESH_QUEUE'])
        root = os.environ['PROOFMESH_WORKER_URL'].rstrip('/')
        client.create_task(parent=parent, task={'name': parent + '/tasks/job-' + key + '-a' + str(self.get(key).get('attempt', 1)),
            'http_request': {'http_method': tasks_v2.HttpMethod.POST, 'url': root + '/internal/jobs/' + key,
                             'headers': {'X-ProofMesh-Worker-Token': os.environ['PROOFMESH_WORKER_TOKEN']},
                             'oidc_token': {'service_account_email': os.environ['PROOFMESH_TASK_IDENTITY'], 'audience': root}},
            'dispatch_deadline': Duration(seconds=300)}, retry=None, timeout=15)

    @staticmethod
    def public(job):
        return {k: v for k, v in job.items() if k not in {'claim', 'image_key', 'provider_key_ciphertext'}}
