"""Short-lived encrypted provider credentials, never part of reports or public jobs."""
import hashlib
import hmac
import os
from cryptography.fernet import Fernet, InvalidToken

TTL_SECONDS = 900

def cipher():
    value = os.getenv('PROOFMESH_CREDENTIAL_ENCRYPTION_KEY', '')
    if not value:
        raise ValueError('Personal Gemini keys are not configured on this deployment')
    return Fernet(value.encode())

def seal(key):
    return cipher().encrypt(key.encode()).decode()

def open_key(value):
    if not value:
        return None
    try:
        return cipher().decrypt(value.encode(), ttl=TTL_SECONDS).decode()
    except InvalidToken:
        raise ValueError('Personal Gemini key expired before processing; start a new investigation') from None

def fingerprint(key):
    cipher()  # Fail closed before admitting a job if encryption is unavailable.
    return hmac.new(os.environ['PROOFMESH_CREDENTIAL_ENCRYPTION_KEY'].encode(), key.encode(), hashlib.sha256).hexdigest()
