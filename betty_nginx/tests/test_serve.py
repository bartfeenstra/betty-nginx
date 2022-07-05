import re
from unittest.mock import patch, Mock

import pytest
import requests
from betty.app import App
from betty.asyncio import sync
from betty.project import ProjectExtensionConfiguration
from betty.serve import NoPublicUrlBecauseServerNotStartedError
from docker.errors import DockerException

from betty_nginx.config import NginxConfiguration
from betty_nginx.nginx import Nginx
from betty_nginx.serve import DockerizedNginxServer


class TestDockerizedNginxServer:
    @sync
    async def test_container_integration(self) -> None:
        content = 'Hello, and welcome to my site!'
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(
                Nginx,
                extension_configuration=NginxConfiguration('/var/www/betty_nginx'),
            ))
            app.project.configuration.www_directory_path.mkdir(parents=True)
            with open(app.project.configuration.www_directory_path / 'index.txt', mode='w') as f:
                f.write(content)
            async with DockerizedNginxServer(app) as server:
                response = requests.get(server.public_url + '/index.txt')
                assert 200 == response.status_code
                assert content == response.content.decode('utf-8')
                assert 'no-cache' == response.headers['Cache-Control']

    @sync
    async def test_public_url(self) -> None:
        with App() as app:
            app.project.configuration.www_directory_path.mkdir(parents=True)
            async with DockerizedNginxServer(app) as server:
                assert re.match(r'^http://\d{1,3}\.\d{1,3}.\d{1,3}.\d{1,3}$', server.public_url)

    @sync
    async def test_public_url_with_stopped_server_should_error(self) -> None:
        with App() as app:
            server = DockerizedNginxServer(app)
            with pytest.raises(NoPublicUrlBecauseServerNotStartedError):
                server.public_url

    @sync
    async def test_is_available_with_docker(self) -> None:
        assert DockerizedNginxServer.is_available() is True

    @patch('docker.from_env')
    @sync
    async def test_is_available_without_docker(self, m_from_env) -> None:
        m_client = Mock()
        m_client.info.side_effect = DockerException
        m_from_env.return_value = m_client
        assert DockerizedNginxServer.is_available() is False
