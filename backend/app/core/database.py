"""Database Connection & Session Management — Network Control Plane

SQLAlchemy 2.0 Async engine, sessionmaker, Base ORM class, and Fernet secret encryption helper.
"""

from typing import AsyncGenerator
from cryptography.fernet import Fernet
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Create Async Engine for PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base ORM model class for all database entities."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class SecretEncryptor:
    """Helper for Fernet field-level symmetric secret encryption at rest."""

    def __init__(self, key: str | None = None):
        fernet_key = key or getattr(settings, "SECRET_KEY", None)
        if not fernet_key:
            fernet_key = Fernet.generate_key().decode()
        elif isinstance(fernet_key, str):
            try:
                Fernet(fernet_key.encode())
            except Exception:
                import base64
                import hashlib
                fernet_key = base64.urlsafe_b64encode(hashlib.sha256(fernet_key.encode()).digest()).decode()

        self.key = fernet_key
        self.fernet = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)

    def encrypt(self, plain_text: str) -> str:
        """Encrypt plain text string into Fernet token string."""
        if not plain_text:
            return ""
        return self.fernet.encrypt(plain_text.encode()).decode()

    def decrypt(self, token: str) -> str:
        """Decrypt Fernet token string back into plain text."""
        if not token:
            return ""
        return self.fernet.decrypt(token.encode()).decode()


secret_encryptor = SecretEncryptor()
