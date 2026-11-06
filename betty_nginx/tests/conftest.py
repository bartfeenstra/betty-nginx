"""
Pytest configuration.
"""

from collections.abc import Awaitable, Callable

import pytest
from betty.test_utils.conftest import *  # noqa F403
from lxml.etree import ParserError
from lxml.html import document_fromstring
from requests import Response

type AssertBettyHtml = Callable[[Response], Awaitable[None]]
type AssertBettyJson = Callable[[Response], Awaitable[None]]


@pytest.fixture
async def assert_betty_html() -> AssertBettyHtml:
    async def _assert_betty_html(response: Response) -> None:
        assert response.headers["Content-Type"] == "text/html"
        try:
            document_fromstring(response.text)
        except ParserError as e:
            raise ValueError(
                f'HTML parse error "{e}" in:\n{response.text}'
            ) from None  # pragma: no cover
        assert "Betty" in response.text

    return _assert_betty_html
