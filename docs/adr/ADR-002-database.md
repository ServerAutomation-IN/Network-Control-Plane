# ADR-002: Selection of PostgreSQL and SQLAlchemy 2.0 Async for Persistence

## Context
The control plane requires relational consistency, transactional audit records, complex graph query support, and async database access.

## Decision
Adopt **PostgreSQL 16** with **SQLAlchemy 2.0 (Async)** and **Alembic** schema migrations.

## Rationale
PostgreSQL offers robust relational transactions, JSONB querying capabilities for metadata/labels, and seamless integration with SQLAlchemy 2.0 async ORM.
