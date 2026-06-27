"""Security utilities: JWT tokens, password hashing, encryption."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import base64
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- JWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token. Returns payload or None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# --- SMS Verification Code ---

def generate_sms_code() -> str:
    """Generate a 6-digit SMS verification code using cryptographically secure random."""
    import secrets
    return f"{secrets.randbelow(900000) + 100000}"


def get_sms_code_key(phone: str) -> str:
    """Get the Redis key for storing SMS verification code."""
    return f"sms:code:{phone}"


def get_sms_rate_limit_key(phone: str) -> str:
    """Get the Redis key for SMS rate limiting."""
    return f"sms:rate:{phone}"


# --- User API Key Encryption ---

def _get_fernet() -> Fernet:
    """Get a Fernet instance for encryption."""
    key = hashlib.sha256(settings.USER_KEY_ENCRYPTION_KEY.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    return Fernet(fernet_key)


def encrypt_api_key(api_key: str) -> str:
    """Encrypt a user's API key for storage."""
    f = _get_fernet()
    return f.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt a user's stored API key."""
    f = _get_fernet()
    return f.decrypt(encrypted_key.encode()).decode()
