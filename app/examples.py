"""Only deliberately published examples may cross client namespaces."""
from datetime import datetime, timezone
from app.context import publication_stamp
from app.fingerprints import image_identity, normalize_claim, similar


def match_examples(submission, reports, stamp=None):
    stamp = stamp or datetime.now(timezone.utc)
    identity = image_identity(submission.image_base64)
    exact, related = None, []
    for report in reports:
        if not report.get('recorded_example'):
            continue
        same_media = identity['sha256'] == report['media']['sha256']
        same_context = (same_media and normalize_claim(submission.claim) == report['claim']
                        and publication_stamp(submission) == report.get('publication_context', {}).get('published_at'))
        fresh = (datetime.fromisoformat(report['expires_at']) > stamp
                 and datetime.fromisoformat(report['created_at']).astimezone(timezone.utc).date() == stamp.date())
        if same_context and fresh:
            exact = report
        elif identity['sha256'] and similar(identity, report['media']):
            related.append({'id': report['id'], 'claim': report['claim'], 'match': 'same_media' if same_media else 'similar_media', 'public_example': True})
    return exact, related
