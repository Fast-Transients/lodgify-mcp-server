from pytest import MonkeyPatch
from pytest_httpx import HTTPXMock

import entrypoint


def test_api_connection_unauthorized(
    httpx_mock: HTTPXMock, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setenv("LODGIFY_API_KEY", "dummy")
    httpx_mock.add_response(
        url="https://api.lodgify.com/v2/properties?limit=1",
        status_code=401,
    )
    assert entrypoint.test_api_connection() is False
