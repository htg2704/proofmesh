"""Bounded public snapshots; private investigations and owner identities stay separate."""
import copy
import json
import os
from datetime import datetime, timezone
from app.fingerprints import context_key, EVIDENCE_POLICY

MAX_PUBLIC_REPORTS = 200
PUBLIC_FIELDS = {'claim', 'media', 'created_at', 'expires_at', 'assessment', 'origin', 'evidence',
                 'publication_context', 'evidence_policy', 'assessment_status', 'validation',
                 'model_calls', 'events', 'search_attribution_html', 'source_origin_validated'}


def stamp():
    return datetime.now(timezone.utc)


def snapshot(report):
    current = stamp()
    if (report.get('corpus') in {'demo', 'public'} or report.get('assessment_status') != 'complete'
        or report.get('evidence_policy') != EVIDENCE_POLICY
        or report.get('validation', {}).get('status') != 'passed'
        or datetime.fromisoformat(report['expires_at']) <= current
        or datetime.fromisoformat(report['created_at']).astimezone(timezone.utc).date() != current.date()
        or not any(e.get('kind') == 'source_page_excerpt' for e in report.get('evidence', []))):
        raise ValueError('Only fresh reports completed under the current citation policy can be published. Start a new investigation if needed.')
    result = {k: copy.deepcopy(v) for k, v in report.items() if k in PUBLIC_FIELDS}
    # Source URLs supplied by a user are private input, rather than fetched evidence.
    result.get('publication_context', {}).pop('source_url', None)
    key = context_key(report['claim'], report['media'], 'public', current.date().isoformat(), report.get('publication_context', {}).get('published_at'))
    result.update(id=key, context_key=key, corpus='public', public_registry=True, registry_published_at=current.isoformat())
    if len(json.dumps(result).encode()) > 500_000:
        raise ValueError('Report is too large for the MVP public registry')
    return result


class PublicRegistry:
    def __init__(self, store, capacity=None):
        self.store = store
        self.capacity = min(MAX_PUBLIC_REPORTS, max(1, int(capacity if capacity is not None else os.getenv('PROOFMESH_REGISTRY_CAP', '200'))))
        self.cloud = hasattr(store, 'client')
        if self.cloud:
            self.collection = store.client.collection(store.collection.id + '_registry')
            self.index = store.client.collection('proofmesh_registry_state').document(store.collection.id)
        else:
            with store.connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS public_registry (id TEXT PRIMARY KEY, body TEXT NOT NULL)')

    def record(self, identifier):
        if self.cloud:
            doc = self.collection.document(identifier).get()
            return doc.to_dict() if doc.exists else None
        with self.store.connect() as db:
            row = db.execute('SELECT body FROM public_registry WHERE id=?', (identifier,)).fetchone()
        return json.loads(row[0]) if row else None

    def get(self, identifier):
        record = self.record(identifier)
        return record['report'] if record else None

    def all(self):
        if self.cloud:
            meta = self.index.get()
            entries = meta.to_dict().get('entries', []) if meta.exists else []
            refs = [self.collection.document(e['id']) for e in entries[:MAX_PUBLIC_REPORTS]]
            records = [d.to_dict() for d in self.store.client.get_all(refs) if d.exists] if refs else []
        else:
            with self.store.connect() as db:
                rows = db.execute('SELECT body FROM public_registry ORDER BY rowid DESC LIMIT ?', (MAX_PUBLIC_REPORTS,)).fetchall()
            records = [json.loads(r[0]) for r in rows]
        return sorted((r['report'] for r in records), key=lambda r: r['registry_published_at'], reverse=True)

    def publish(self, source):
        public = snapshot(source)
        record = {'report': public, 'owner_namespace': source['corpus'], 'source_report_id': source['id']}
        item = {'id': public['id'], 'expires_at': public['expires_at'], 'registry_published_at': public['registry_published_at']}
        current = stamp().isoformat()
        def trim(entries):
            expired = [e for e in entries if e['expires_at'] <= current]
            active = sorted((e for e in entries if e['expires_at'] > current), key=lambda e: e['registry_published_at'])
            extra = max(0, len(active) - self.capacity + 1)
            return active[extra:] + [item], expired + active[:extra]
        if self.cloud:
            from google.cloud import firestore
            ref = self.collection.document(public['id'])
            @firestore.transactional
            def save(transaction):
                old = ref.get(transaction=transaction)
                meta = self.index.get(transaction=transaction)
                if old.exists:
                    return old.to_dict()['report']
                entries, removed = trim(meta.to_dict().get('entries', []) if meta.exists else [])
                for entry in removed:
                    transaction.delete(self.collection.document(entry['id']))
                transaction.set(ref, record)
                transaction.set(self.index, {'entries': entries, 'capacity': self.capacity})
                return public
            return save(self.store.client.transaction())
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT body FROM public_registry WHERE id=?', (public['id'],)).fetchone()
            if old:
                return json.loads(old[0])['report']
            records = [json.loads(r[0]) for r in db.execute('SELECT body FROM public_registry').fetchall()]
            entries, removed = trim([{'id': r['report']['id'], 'expires_at': r['report']['expires_at'], 'registry_published_at': r['report']['registry_published_at']} for r in records])
            for entry in removed:
                db.execute('DELETE FROM public_registry WHERE id=?', (entry['id'],))
            db.execute('INSERT INTO public_registry VALUES (?,?)', (public['id'], json.dumps(record)))
        return public

    def withdraw(self, identifier, namespace, team=False):
        def permitted(record):
            if record and not team and record['owner_namespace'] != namespace:
                raise PermissionError('Only the publisher or team can withdraw this public snapshot')
        if self.cloud:
            from google.cloud import firestore
            ref = self.collection.document(identifier)
            @firestore.transactional
            def remove(transaction):
                doc = ref.get(transaction=transaction)
                meta = self.index.get(transaction=transaction)
                record = doc.to_dict() if doc.exists else None
                permitted(record)
                if not record:
                    return False
                entries = [e for e in meta.to_dict().get('entries', []) if e['id'] != identifier] if meta.exists else []
                transaction.delete(ref)
                transaction.set(self.index, {'entries': entries, 'capacity': self.capacity})
                return True
            return remove(self.store.client.transaction())
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT body FROM public_registry WHERE id=?', (identifier,)).fetchone()
            record = json.loads(old[0]) if old else None
            permitted(record)
            if record:
                db.execute('DELETE FROM public_registry WHERE id=?', (identifier,))
            return bool(record)
