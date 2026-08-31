import json
import redis
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.config import settings

_serializer = URLSafeTimedSerializer(settings.state_signing_secret)
_redis_client = redis.from_url(settings.redis_url)

STATE_TTL_SECONDS = 600


def sign_state(user_id: int) -> str:
    return _serializer.dumps({"user_id": user_id})


def store_state(state: str, user_id: int, code_verifier: str):
    payload = json.dumps({"user_id": user_id, "code_verifier": code_verifier})
    _redis_client.setex(f"oauth_state:{state}", STATE_TTL_SECONDS, payload)


def verify_and_consume_state(state: str) -> dict:
    try:
        _serializer.loads(state, max_age=STATE_TTL_SECONDS)
    except SignatureExpired:
        raise ValueError("OAuth state expired. Please try connecting again.")
    except BadSignature:
        raise ValueError("Invalid OAuth state.")

    redis_key = f"oauth_state:{state}"
    pipe = _redis_client.pipeline()
    pipe.get(redis_key)
    pipe.delete(redis_key)
    value, deleted = pipe.execute()

    if not value or deleted == 0:
        raise ValueError("OAuth state already used or invalid.")

    return json.loads(value)