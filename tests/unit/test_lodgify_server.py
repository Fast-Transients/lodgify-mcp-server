import httpx
import pytest
from pytest import MonkeyPatch
from pytest_httpx import HTTPXMock

import lodgify_server


@pytest.mark.asyncio
async def test_handle_api_error_json() -> None:
    response = httpx.Response(
        401,
        json={"message": "Invalid API key", "code": 401},
        request=httpx.Request("GET", "https://api.lodgify.com/v2/properties"),
    )
    msg = await lodgify_server.handle_api_error(response)
    assert msg == "Lodgify API Error 401: Invalid API key"


def test_get_client_not_initialized(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(lodgify_server, "_client", None)
    with pytest.raises(RuntimeError):
        lodgify_server.get_client()


@pytest.mark.asyncio
async def test_get_properties_success(
    httpx_mock: HTTPXMock, monkeypatch: MonkeyPatch
) -> None:
    client = httpx.AsyncClient(base_url="https://api.lodgify.com/v2")
    monkeypatch.setattr(lodgify_server, "_client", client)
    httpx_mock.add_response(
        url="https://api.lodgify.com/v2/properties?limit=1&offset=0",
        json={"items": [{"id": 1, "name": "Test Property"}]},
    )

    result = await lodgify_server.get_properties(ctx=None, limit=1, offset=0)

    assert result["success"] is True
    assert len(result["data"]["items"]) == 1

    await client.aclose()
    monkeypatch.setattr(lodgify_server, "_client", None)
