import sys

import pytest
import requests
from betty.extension import ExtensionManufacturer
from betty.functools import Do
from betty.project.generate import generate
from betty.server import ServerNotStarted
from betty.test_utils.conftest import IsolatedProjectFactory
from docker.errors import DockerException
from pytest_mock import MockerFixture

from betty_nginx.data import NginxConfiguration
from betty_nginx.plugins.extension.nginx import Nginx
from betty_nginx.serve import DockerizedNginxServer
from betty_nginx.tests.conftest import AssertBettyHtml


class TestDockerizedNginxServer:
    @pytest.mark.skipif(
        sys.platform in {"darwin", "win32"},
        reason="macOS and Windows do not natively support Docker.",
    )
    async def test_context_manager(
        self,
        assert_betty_html: AssertBettyHtml,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with isolated_project_factory(
            extensions=[
                ExtensionManufacturer(
                    Nginx,
                    NginxConfiguration(www_directory="/var/www/betty"),
                )
            ]
        ) as project:
            await generate(project)
            async with DockerizedNginxServer(project) as server:
                await Do(requests.get, server.public_url).until(assert_betty_html)

    async def test_public_url__unstarted(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(extensions=[Nginx]) as project:
            sut = DockerizedNginxServer(project)
            with pytest.raises(ServerNotStarted):
                sut.public_url  # noqa B018

    async def test_is_available__is_available(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        m_from_env = mocker.patch("docker.from_env")
        m_from_env.return_value = mocker.Mock("docker.client.DockerClient")
        async with isolated_project_factory(extensions=[Nginx]) as project:
            sut = DockerizedNginxServer(project)
            assert sut.is_available()

    async def test_is_available__is_unavailable(
        self, mocker: MockerFixture, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        m_from_env = mocker.patch("docker.from_env")
        m_from_env.side_effect = DockerException()
        async with isolated_project_factory(extensions=[Nginx]) as project:
            sut = DockerizedNginxServer(project)
            assert not sut.is_available()
