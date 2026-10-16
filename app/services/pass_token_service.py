import base64
import hashlib
import hmac

from app.core.config import settings


def create_pass_token(pass_id: str) -> str:
    signature = hmac.new(
        settings.pass_token_secret.encode(),
        pass_id.encode(),
        hashlib.sha256,
    ).digest()

    encoded_signature = (
        base64.urlsafe_b64encode(signature)
        .decode()
        .rstrip("=")
    )

    return f"{pass_id}.{encoded_signature}"


def verify_pass_token(token: str):
    try:
        pass_id, received_signature = token.rsplit(".", 1)
    except ValueError:
        return None

    expected_token = create_pass_token(pass_id)

    _, expected_signature = expected_token.rsplit(".", 1)

    if not hmac.compare_digest(
        received_signature,
        expected_signature,
    ):
        return None

    return pass_id