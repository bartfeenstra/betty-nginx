"""
Pytest configuration.
"""

from collections.abc import Callable, Awaitable
from typing import TypeAlias

import html5lib
import pytest
from betty.app import App
from betty.project import Project, ProjectSchema
from betty.test_utils.conftest import *  # noqa F403
from requests import Response

AssertBettyHtml: TypeAlias = Callable[[Response], Awaitable[None]]
AssertBettyJson: TypeAlias = Callable[[Response], Awaitable[None]]


@pytest.fixture
async def assert_betty_html() -> AssertBettyHtml:
    async def _assert_betty_html(response: Response) -> None:
        assert response.headers["Content-Type"] == "text/html"
        parser = html5lib.HTMLParser()
        parser.parse(response.text)
        assert "Betty" in response.text

    return _assert_betty_html


@pytest.fixture
async def assert_betty_json(temporary_app: App) -> AssertBettyJson:
    async def _assert_betty_json(response: Response) -> None:
        assert response.headers["Content-Type"] == "application/json"
        data = response.json()
        async with Project.new_temporary(temporary_app) as project, project:
            schema = await ProjectSchema.new_for_project(project)
            schema.validate(data)

    return _assert_betty_json
