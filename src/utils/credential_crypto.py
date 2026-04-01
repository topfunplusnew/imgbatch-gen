from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from loguru import logger

from ..config.settings import settings


def _normalize_fernet_key(raw_key: str) -> bytes:
    candidate = (raw_key or "").strip().encode("utf-8")
    try:
        decoded = base64.urlsafe_b64decode(candidate)
        if len(decoded) == 32:
            return candidate
    except Exception:
        pass
    digest = hashlib.sha256(candidate).digest()
    return base64.urlsafe_b64encode(digest)


@lru_cache(maxsize=1)
def _get_cipher() -> Fernet:
    raw_key = settings.credential_encryption_key
    if not raw_key:
        logger.warning(
            "CREDENTIAL_ENCRYPTION_KEY is not configured; using an ephemeral in-process key. "
            "Stored credentials will become unreadable after restart."
        )
        raw_key = Fernet.generate_key().decode("utf-8")
    return Fernet(_normalize_fernet_key(raw_key))


def encrypt_api_key(api_key: str) -> str:
    return _get_cipher().encrypt(api_key.encode("utf-8")).decode("utf-8")


def decrypt_api_key(token: str) -> str:
    try:
        return _get_cipher().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Stored API credential cannot be decrypted with the current encryption key.") from exc


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}...{api_key[-4:]}"
