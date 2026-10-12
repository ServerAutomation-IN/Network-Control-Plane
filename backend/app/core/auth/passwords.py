"""Password Hashing Utilities — Network Control Plane

PBKDF2-HMAC-SHA256 password hashing with cryptographically secure random salt.
"""

import hashlib
import hmac
import os
from typing import Tuple, Optional


def hash_password(plain_password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Generate SHA256 PBKDF2 password hash with 100,000 iterations.
    
    Returns:
        Tuple of (hex_hashed_password, hex_salt)
    """
    if not salt:
        salt = os.urandom(16).hex()
    
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    ).hex()
    return hashed, salt


def verify_password(plain_password: str, hashed_password: str, salt: str) -> bool:
    """Verify plain password matches the hashed password using constant-time comparison."""
    new_hash, _ = hash_password(plain_password, salt=salt)
    return hmac.compare_digest(new_hash, hashed_password)
