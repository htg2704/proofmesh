"""Scoped developer credentials and persistent fixed-window request limits."""
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from dataclasses import dataclass

DEFAULT_CLIENT_RPM = 120
DEFAULT_CLIENT_DAILY_JOBS = 10
DEFAULT_REGISTRATIONS_PER_HOUR = 30


def client_limits_enabled():
    """Operator opt-in only. Public MVP access has no application usage caps."""
    return os.getenv('PROOFMESH_CLIENT_LIMITS_ENABLED', 'false').lower() == 'true'



class RateLimited(ValueError):
    def __init__(self, message, retry_after=60):
        super().__init__(message)
        self.retry_after = max(1, int(retry_after))


class SpendingLimit(ValueError):
    """A shared financial admission guard, separate from client rate limits."""


@dataclass(frozen=True)
class Principal:
    role: str = 'none'
    identifier: str = 'anonymous'

    @property
    def exempt(self):
        return self.role in {'team', 'judge'}

    @property
    def namespace(self):
        return 'client:' + self.identifier if self.role in {'client', 'judge'} else 'review' if self.role == 'review' else 'live'


def trusted_credentials():
    raw = json.loads(os.getenv('PROOFMESH_TRUSTED_TOKENS', '{}'))
    if not isinstance(raw, dict) or any(not re.fullmatch(r'[a-z][a-z0-9_-]{0,39}', name) or not isinstance(token, str) or len(token) < 32 for name, token in raw.items()):
        raise RuntimeError('Trusted credentials must map short labels to strong tokens')
    if len(set(raw.values())) != len(raw):
        raise RuntimeError('Each trusted tester needs a distinct credential')
    return raw


class ClientAccess:
    def __init__(self, store, clock=time.time):
        self.store, self.clock = store, clock
        self.cloud = hasattr(store, 'client')
        if self.cloud:
            self.clients = store.client.collection('proofmesh_clients')
            self.rates = store.client.collection('proofmesh_request_limits')
        else:
            with store.connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS clients (id TEXT PRIMARY KEY, body TEXT NOT NULL)')
                db.execute('CREATE TABLE IF NOT EXISTS request_limits (id TEXT PRIMARY KEY, window INTEGER NOT NULL, count INTEGER NOT NULL)')

    def issue(self, label):
        identifier = secrets.token_hex(12)
        token = 'pm_client_' + identifier + '.' + secrets.token_urlsafe(32)
        body = {'id': identifier, 'label': label, 'created_at': int(self.clock()),
                'expires_at': int(self.clock()) + 30 * 86400, 'revoked': False,
                'token_hash': hashlib.sha256(token.encode()).hexdigest()}
        if self.cloud:
            self.clients.document(identifier).create(body)
        else:
            with self.store.connect() as db:
                db.execute('INSERT INTO clients VALUES (?, ?)', (identifier, json.dumps(body)))
        return {**self.public(body), 'token': token}

    def get(self, identifier):
        if not re.fullmatch(r'[0-9a-f]{24}', identifier):
            return None
        if self.cloud:
            doc = self.clients.document(identifier).get()
            return doc.to_dict() if doc.exists else None
        with self.store.connect() as db:
            row = db.execute('SELECT body FROM clients WHERE id=?', (identifier,)).fetchone()
        return json.loads(row[0]) if row else None

    def authenticate(self, token):
        match = re.fullmatch(r'pm_client_([0-9a-f]{24})\.[A-Za-z0-9_-]{43}', token)
        if not match:
            return None
        body = self.get(match[1])
        if not body or body['revoked'] or body['expires_at'] <= self.clock():
            return None
        if not hmac.compare_digest(body['token_hash'], hashlib.sha256(token.encode()).hexdigest()):
            return None
        return Principal('client', body['id'])

    def revoke(self, identifier):
        body = self.get(identifier)
        if not body:
            return False
        body['revoked'] = True
        if self.cloud:
            self.clients.document(identifier).update({'revoked': True})
        else:
            with self.store.connect() as db:
                db.execute('UPDATE clients SET body=? WHERE id=?', (json.dumps(body), identifier))
        return True

    def all(self):
        if self.cloud:
            return [self.public(doc.to_dict()) for doc in self.clients.limit(1000).stream()]
        with self.store.connect() as db:
            return [self.public(json.loads(body)) for (body,) in db.execute('SELECT body FROM clients ORDER BY rowid DESC LIMIT 1000')]

    @staticmethod
    def public(body):
        return {k: v for k, v in body.items() if k != 'token_hash'}

    def take(self, key, maximum, seconds=60):
        """One document per principal/bucket; counters survive restarts and races."""
        stamp = int(self.clock())
        window, reset = stamp // seconds, (stamp // seconds + 1) * seconds
        identifier = hashlib.sha256(key.encode()).hexdigest()
        if self.cloud:
            from google.cloud import firestore
            ref = self.rates.document(identifier)
            @firestore.transactional
            def reserve(transaction):
                snap = ref.get(transaction=transaction)
                body = snap.to_dict() if snap.exists else {}
                count = body.get('count', 0) if body.get('window') == window else 0
                if count >= maximum:
                    raise RateLimited('Request limit reached; retry after the indicated reset.', reset - stamp)
                transaction.set(ref, {'window': window, 'count': count + 1})
                return count + 1
            count = reserve(self.store.client.transaction())
        else:
            with self.store.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                row = db.execute('SELECT window, count FROM request_limits WHERE id=?', (identifier,)).fetchone()
                count = row[1] if row and row[0] == window else 0
                if count >= maximum:
                    raise RateLimited('Request limit reached; retry after the indicated reset.', reset - stamp)
                count += 1
                db.execute('INSERT OR REPLACE INTO request_limits VALUES (?, ?, ?)', (identifier, window, count))
        return {'X-RateLimit-Limit': str(maximum), 'X-RateLimit-Remaining': str(maximum - count), 'X-RateLimit-Reset': str(reset)}
