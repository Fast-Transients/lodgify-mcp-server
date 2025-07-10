import httpx
import pytest
from pytest import MonkeyPatch
from pytest_httpx import HTTPXMock

from typing import Any

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
async def test_get_properties_success(httpx_mock: HTTPXMock, monkeypatch: MonkeyPatch) -> None:
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


@pytest.mark.asyncio
async def test_get_occupancy_summary_invalid_date_format(monkeypatch: MonkeyPatch) -> None:
    # Mock get_calendar to prevent actual API calls
    

    # Mock get_calendar to return a successful response with valid data
    async def mock_get_calendar(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "success": True,
            "data": [
                {"date": "2023-01-01", "status": "Available", "price": 100.0},
                {"date": "2023-01-02", "status": "Booked", "price": 120.0},
            ],
        }

    monkeypatch.setattr(lodgify_server, "get_calendar", mock_get_calendar)

    # Test with invalid start_date format
    result = await lodgify_server.get_occupancy_summary(
        ctx=None, property_id=1, start_date="2023/01/01", end_date="2023-01-31"
    )
    assert result["success"] is False
    assert "Invalid date format" in result["error"]

    # Test with invalid end_date format
    result = await lodgify_server.get_occupancy_summary(
        ctx=None, property_id=1, start_date="2023-01-01", end_date="01-31-2023"
    )
    assert result["success"] is False
    assert "Invalid date format" in result["error"]

    # Test with invalid date format in calendar data
    async def mock_get_calendar_invalid_data(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {
            "success": True,
            "data": [
                {"date": "2023-01-01", "status": "Available", "price": 100.0},
                {"date": "invalid-date", "status": "Booked", "price": 120.0},
            ],
        }

    monkeypatch.setattr(lodgify_server, "get_calendar", mock_get_calendar_invalid_data)
    result = await lodgify_server.get_occupancy_summary(
        ctx=None, property_id=1, start_date="2023-01-01", end_date="2023-01-31"
    )
    assert result["success"] is False
    assert "Invalid date format in calendar data" in result["error"]
