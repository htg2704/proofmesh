"""A reviewer credential has no access to team reports, secrets or settings."""
import hashlib
import hmac
import secrets
import time

COOKIE = 'proofmesh_review'


def review_cookie(secret, now=None):
    expiry = int(time.time() if now is None else now) + 8 * 3600
    payload = f'{expiry}.{secrets.token_hex(12)}'
    signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f'{payload}.{signature}'


def valid_cookie(value, secret, now=None):
    if len(secret) < 32 or not value or len(value) > 180:
        return False
    try:
        expiry, nonce, signature = value.split('.')
        current = int(time.time() if now is None else now)
        if not current < int(expiry) <= current + 8 * 3600:
            return False
        expected = hmac.new(secret.encode(), f'{expiry}.{nonce}'.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected)
    except (ValueError, TypeError):
        return False
