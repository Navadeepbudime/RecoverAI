import hmac
from hashlib import sha256


def verify_webhook_signature(body_bytes, signature, secret):
    if not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), body_bytes, sha256).hexdigest()
    return hmac.compare_digest(digest, signature or "")
