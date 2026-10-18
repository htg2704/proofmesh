import copy
from datetime import datetime, timezone, timedelta
from app.context import publication_stamp, context_record, require_publication_context, RELATIVE_TIME
from app.fingerprints import image_identity, context_key, normalize_claim, similar
from app.fingerprints import EVIDENCE_POLICY
from app.origin import origin_from_result
from app.registry import PublicRegistry
from app.reuse import reuse_blockers


def now():
    return datetime.now(timezone.utc)


class ProofMesh:
    def __init__(self, store, investigator):
        self.store, self.investigator = store, investigator
        self.registry = PublicRegistry(store)

    def match(self, submission):
        identity = image_identity(submission.image_base64)
        if submission.corpus != "demo" and RELATIVE_TIME.search(submission.claim) and not submission.published_at:
            return {"status": "unknown", "report": None, "related": [], "model_calls": 0, "needs_publication_time": True, "message": "Publication time is required to interpret this caption."}
        key = context_key(submission.claim, identity, submission.namespace, now().date().isoformat(), publication_stamp(submission))
        records = self.store.all(submission.namespace)
        exact = self.store.get(key)
        if exact and datetime.fromisoformat(exact["expires_at"]) <= now():
            exact = None
        if submission.corpus != 'demo':
            public = self.registry.all()
            public_key = context_key(submission.claim, identity, 'public', now().date().isoformat(), publication_stamp(submission))
            if not exact:
                exact = next((r for r in public if r['id'] == public_key and not reuse_blockers(submission, identity, r, now())), None)
            public_ids = {r['id'] for r in public}
            records = [r for r in records if r.get('registry_publication', {}).get('id') not in public_ids] + public
        related = [{"reuse_blockers": reuse_blockers(submission, identity, r, now()), "public_registry": r.get('public_registry', False), "id": r["id"], "claim": r["claim"], "match": "same_media" if identity["sha256"] == r["media"]["sha256"] else "similar_media"}
                   for r in records if identity["sha256"] and similar(identity, r["media"]) and (not exact or r["id"] != exact["id"])]
        return {"status": "exact_context" if exact else "related_media" if related else "unknown", "report": exact,
                "related": related[:10], "model_calls": 0,
                "message": "Related images never transfer a verdict to a different caption."}

    def investigate(self, submission):
        cached = self.match(submission)
        if cached["report"]:
            if submission.share_publicly and cached["report"].get("corpus") not in {"demo", "public"}:
                self.share(cached["report"])
            return {"report": cached["report"], "reused": True, "model_calls": 0}
        if submission.corpus not in {"live", "review"}:
            raise ValueError("Demo investigations are fixed fixtures. Use the live corpus for new investigations.")
        require_publication_context(submission)
        identity = image_identity(submission.image_base64)
        stamp = now()
        key = context_key(submission.claim, identity, submission.namespace, stamp.date().isoformat(), publication_stamp(submission))
        result = self.investigator.investigate(submission, stamp.date().isoformat())
        report = self.make_report(submission.claim, identity, key, submission.namespace, result, stamp)
        report["publication_context"] = context_record(submission, stamp.date().isoformat())
        self.store.put(report)
        if submission.share_publicly:
            self.share(report)
        return {"report": report, "reused": False, "model_calls": result["model_calls"]}

    def share(self, report):
        try:
            public = self.registry.publish(report)
            report['registry_publication'] = {'status': 'published', 'id': public['id']}
        except ValueError:
            report['registry_publication'] = {'status': 'not_eligible', 'message': 'Only fresh, complete assessments with validated source citations can be published.'}
        except Exception as exc:
            import logging
            logging.getLogger('proofmesh').error('Registry publication failed: %s', type(exc).__name__)
            report['registry_publication'] = {'status': 'unavailable', 'message': 'Report saved privately. Public registry publication is temporarily unavailable.'}
        self.store.put(report)
        return report['registry_publication']

    @staticmethod
    def make_report(claim, identity, key, corpus, result, stamp):
        return {"id": key, "context_key": key, "claim": normalize_claim(claim), "media": identity, "corpus": corpus,
                "created_at": stamp.isoformat(), "expires_at": (stamp + timedelta(hours=24)).isoformat(),
                "origin": origin_from_result(result), "evidence_policy": EVIDENCE_POLICY, **copy.deepcopy(result)}
