import json
import sqlite3
from pathlib import Path


class SQLiteStore:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS investigations (id TEXT PRIMARY KEY, context_key TEXT UNIQUE, body TEXT NOT NULL)")

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def put(self, report: dict):
        with self.connect() as db:
            db.execute("INSERT INTO investigations VALUES (?, ?, ?) ON CONFLICT(context_key) DO UPDATE SET body=excluded.body",
                       (report["id"], report["context_key"], json.dumps(report)))

    def get(self, report_id: str):
        with self.connect() as db:
            row = db.execute("SELECT body FROM investigations WHERE id=?", (report_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def all(self, corpus: str):
        with self.connect() as db:
            rows = db.execute("SELECT body FROM investigations ORDER BY rowid DESC LIMIT 1000").fetchall()
        return [r for (body,) in rows if (r := json.loads(body))["corpus"] == corpus]


class FirestoreStore:
    def __init__(self, project: str, collection: str):
        from google.cloud import firestore
        self.collection = firestore.Client(project=project).collection(collection)

    def put(self, report: dict):
        self.collection.document(report["id"]).set(report)

    def get(self, report_id: str):
        doc = self.collection.document(report_id).get()
        return doc.to_dict() if doc.exists else None

    def all(self, corpus: str):
        from google.cloud.firestore_v1.base_query import FieldFilter
        return [doc.to_dict() for doc in self.collection.where(filter=FieldFilter("corpus", "==", corpus)).limit(1000).stream()]

