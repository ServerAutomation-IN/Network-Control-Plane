# ADR-001: Selection of Python & FastAPI for Control Plane Backend

## Context
The Network Control Plane requires a performant, asynchronous API server with native schema validation, OpenAPI generation, and strong Docker/container ecosystem libraries.

## Decision
Adopt **Python 3.12+** with **FastAPI**, **Pydantic v2**, and **Uvicorn/Gunicorn**.

## Rationale
FastAPI provides high-performance native async IO, built-in Pydantic schema validation, automatic OpenAPI generation, and access to rich networking and container libraries.
