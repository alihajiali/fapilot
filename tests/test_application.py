import pytest
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient

from fapilot.apps import AppConfig
from fapilot.conf import FapilotSettings
from fapilot.core.application import Fapilot

router = APIRouter()


@router.get("/")
async def list_items() -> dict[str, bool]:
    return {"ok": True}


class ApiConfig(AppConfig):
    def __init__(self) -> None:
        super().__init__(name="tests.test_application", label="api", router=router)


@pytest.mark.anyio
async def test_create_fastapi_includes_app_routers() -> None:
    settings = FapilotSettings(DEBUG=False, INSTALLED_APPS=["tests.test_application.ApiConfig"])

    app = Fapilot(settings=settings).create_fastapi()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/api/")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
