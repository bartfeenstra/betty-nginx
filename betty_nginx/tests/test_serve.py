import sys

import pytest
import requests
from betty.app import App
from betty.functools import Do
from betty.plugin.config import PluginInstanceConfiguration
from betty.project import Project
from betty.project.generate import generate
from betty.serve import NoPublicUrlBecauseServerNotStartedError
from docker.errors import DockerException
from pytest_mock import MockerFixture

from betty_nginx import Nginx
from betty_nginx.config import NginxConfiguration
from betty_nginx.serve import DockerizedNginxServer
from betty_nginx.tests.conftest import AssertBettyHtml


class TestDockerizedNginxServer:
    @pytest.mark.skipif(
        sys.platform in {"darwin", "win32"},
        reason="macOS and Windows do not natively support Docker.",
    )
    async def test_context_manager(
        self, assert_betty_html: AssertBettyHtml, temporary_app: App
    ):
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.append(
                PluginInstanceConfiguration(
                    Nginx,
                    NginxConfiguration(www_directory_path="/var/www/betty"),
                )
            )
            async with project:
                await generate(project)
                async with DockerizedNginxServer(project) as server:
                    await Do(requests.get, server.public_url).until(assert_betty_html)

    async def test_public_url__unstarted(self, temporary_app: App) -> None:
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Nginx)
            async with project:
                sut = DockerizedNginxServer(project)
                with pytest.raises(NoPublicUrlBecauseServerNotStartedError):
                    sut.public_url  # noqa B018

    async def test_is_available__is_available(
        self, mocker: MockerFixture, temporary_app: App
    ) -> None:
        m_from_env = mocker.patch("docker.from_env")
        m_from_env.return_value = mocker.Mock("docker.client.DockerClient")
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Nginx)
            async with project:
                sut = DockerizedNginxServer(project)
                assert sut.is_available()

    async def test_is_available__is_unavailable(
        self, mocker: MockerFixture, temporary_app: App
    ) -> None:
        m_from_env = mocker.patch("docker.from_env")
        m_from_env.side_effect = DockerException()
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Nginx)
            async with project:
                sut = DockerizedNginxServer(project)

                assert not sut.is_available()
