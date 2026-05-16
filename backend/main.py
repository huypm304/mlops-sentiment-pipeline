"""Legacy entrypoint — use `uvicorn backend.app.main:app` instead."""

from backend.app.main import app

__all__ = ["app"]
