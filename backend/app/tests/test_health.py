"""Health endpoint contract tests."""

import asyncio

import httpx

from app.core.config import AppEnvironment, Settings
from app.main import create_app


def test_health_endpoint_returns_ok() -> None:
    """The liveness endpoint remains dependency-independent and stable."""
    settings = Settings(_env_file=None, app_env=AppEnvironment.TESTING)

    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(app=create_app(settings))
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get("/health")

    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-request-id"]
