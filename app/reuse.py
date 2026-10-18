"""Explain cache eligibility without turning a lookup miss into a truth verdict."""
from datetime import datetime, timezone
from app.fingerprints import normalize_claim, EVIDENCE_POLICY
from app.context import publication_stamp


def reuse_blockers(submission, identity, report, current):
    reasons = []
    if normalize_claim(submission.claim) != report['claim']:
        reasons.append('caption_changed')
    if identity['sha256'] != report['media']['sha256']:
        reasons.append('similar_image_only')
    if publication_stamp(submission) != report.get('publication_context', {}).get('published_at'):
        reasons.append('publication_time_changed')
    if datetime.fromisoformat(report['expires_at']) <= current:
        reasons.append('report_expired')
    if datetime.fromisoformat(report['created_at']).astimezone(timezone.utc).date() != current.date():
        reasons.append('reference_date_changed')
    if report.get('evidence_policy') != EVIDENCE_POLICY and report.get('corpus') != 'demo':
        reasons.append('assessment_policy_changed')
    return reasons
