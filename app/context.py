"""Publication metadata is an interpretation anchor, never proof of media origin."""
import re
from datetime import timezone

RELATIVE_TIME = re.compile(r'\b(today|yesterday|tomorrow|tonight|right now|this (morning|evening|week|month|year))\b', re.I)


def publication_stamp(submission):
    value = submission.published_at
    return value.astimezone(timezone.utc).isoformat() if value else None


def require_publication_context(submission):
    if RELATIVE_TIME.search(submission.claim) and not submission.published_at:
        raise ValueError('Add the post publication time before investigating a relative-time caption. The current date is not a substitute for the post date.')


def context_record(submission, reference_date):
    stamp = publication_stamp(submission)
    return {'published_at': stamp, 'source_url': submission.source_url, 'retrieval_date': reference_date,
            'date_basis': 'UTC', 'limitation': 'Publication time is supplied context, not verified capture time. The author\'s local timezone may differ; abstain on ambiguous day boundaries.'}
