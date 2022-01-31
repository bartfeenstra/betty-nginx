import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import html5lib
import jsonschema
import requests
from betty import generate
from betty.app import App
from betty.asyncio import sync
from betty.fs import ROOT_DIRECTORY_PATH
from betty.model.ancestry import File
from betty.project import ProjectExtensionConfiguration
from betty.serve import Server
from requests import Response

from betty_nginx.config import NginxConfiguration
from betty_nginx.nginx import Nginx
from betty_nginx.serve import DockerizedNginxServer


class TestNginx:
    class NginxTestServer(Server):
        def __init__(self, app: App):
            self._app = app
            self._server: Server

        @classmethod
        @asynccontextmanager
        async def for_configuration_file(cls, app: App, configuration_template_file_name: str) -> AsyncIterator[Server]:
            configuration_file_path = Path(__file__).parent / 'test_integration_assets' / configuration_template_file_name
            app.project.configuration.read(configuration_file_path)
            del app.project.configuration.configuration_file_path
            async with cls(app) as server:
                yield server

        async def start(self) -> None:
            await generate.generate(self._app)
            self._server = DockerizedNginxServer(self._app)
            await self._server.start()

        async def stop(self) -> None:
            await self._server.stop()

        @property
        def public_url(self) -> str:
            return self._server.public_url

    def assert_betty_html(self, response: Response) -> None:
        assert 'text/html' == response.headers['Content-Type']
        parser = html5lib.HTMLParser()
        parser.parse(response.text)
        assert 'Betty' in response.text

    def assert_betty_json(self, response: Response) -> None:
        assert 'application/json' == response.headers['Content-Type']
        data = response.json()
        with open(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'public' / 'static' / 'schema.json') as f:
            jsonschema.validate(data, json.load(f))

    @sync
    async def test_front_page(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-monolingual.json') as server:
                response = requests.get(server.public_url)
                assert 200 == response.status_code
                self.assert_betty_html(response)

    @sync
    async def test_default_html_404(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-monolingual.json') as server:
                response = requests.get(f'{server.public_url}/non-existent')
                assert 404 == response.status_code
                self.assert_betty_html(response)

    @sync
    async def test_negotiated_json_404(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-monolingual-content-negotiation.json') as server:
                response = requests.get(f'{server.public_url}/non-existent', headers={
                    'Accept': 'application/json',
                })
                assert 404 == response.status_code
                self.assert_betty_json(response)

    @sync
    async def test_default_localized_front_page(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-multilingual.json') as server:
                response = requests.get(server.public_url)
                assert 200 == response.status_code
                assert 'en' == response.headers['Content-Language']
                assert f'{server.public_url}/en/' == response.url
                self.assert_betty_html(response)

    @sync
    async def test_explicitly_localized_404(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-multilingual.json') as server:
                response = requests.get(f'{server.public_url}/nl/non-existent')
                assert 404 == response.status_code
                assert 'nl' == response.headers['Content-Language']
                self.assert_betty_html(response)

    @sync
    async def test_negotiated_localized_front_page(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-multilingual-content-negotiation.json') as server:
                response = requests.get(server.public_url, headers={
                    'Accept-Language': 'nl-NL',
                })
                assert 200 == response.status_code
                assert 'nl' == response.headers['Content-Language']
                assert f'{server.public_url}/nl/' == response.url
                self.assert_betty_html(response)

    @sync
    async def test_negotiated_localized_default_html_404(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-multilingual-content-negotiation.json') as server:
                response = requests.get(f'{server.public_url}/non-existent', headers={
                    'Accept-Language': 'nl-NL',
                })
                assert 404 == response.status_code
                assert 'nl' == response.headers['Content-Language']
                self.assert_betty_html(response)

    @sync
    async def test_negotiated_localized_negotiated_json_404(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-multilingual-content-negotiation.json') as server:
                response = requests.get(f'{server.public_url}/non-existent', headers={
                    'Accept': 'application/json',
                    'Accept-Language': 'nl-NL',
                })
                assert 404 == response.status_code
                self.assert_betty_json(response)

    @sync
    async def test_default_html_resource(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-monolingual-content-negotiation.json') as server:
                response = requests.get(f'{server.public_url}/place/')
            assert 200 == response.status_code
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_html_resource(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-monolingual-content-negotiation.json') as server:
                response = requests.get(f'{server.public_url}/place/', headers={
                    'Accept': 'text/html',
                })
            assert 200 == response.status_code
            self.assert_betty_html(response)

    @sync
    async def test_negotiated_json_resource(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-monolingual-content-negotiation.json') as server:
                response = requests.get(f'{server.public_url}/place/', headers={
                    'Accept': 'application/json',
                })
                assert 200 == response.status_code
                self.assert_betty_json(response)

    @sync
    async def test_default_html_static_resource(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-multilingual-content-negotiation.json') as server:
                response = requests.get(f'{server.public_url}/non-existent-path/')
                self.assert_betty_html(response)

    @sync
    async def test_negotiated_html_static_resource(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-multilingual-content-negotiation.json') as server:
                response = requests.get(f'{server.public_url}/non-existent-path/', headers={
                    'Accept': 'text/html',
                })
                self.assert_betty_html(response)

    @sync
    async def test_negotiated_json_static_resource(self) -> None:
        with App() as app:
            async with self.NginxTestServer.for_configuration_file(app, 'betty-multilingual-content-negotiation.json') as server:
                response = requests.get(f'{server.public_url}/non-existent-path/', headers={
                    'Accept': 'application/json',
                })
                self.assert_betty_json(response)

    @sync
    async def test_betty_0_3_file_path(self) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(
                Nginx,
                extension_configuration=NginxConfiguration('/var/www/betty_nginx'),
            ))
            file_id = 'FILE1'
            app.project.ancestry.entities.append(File(file_id, __file__))
            async with self.NginxTestServer(app) as server:
                response = requests.get(f'{server.public_url}/file/{file_id}.py', headers={
                    'Accept': 'application/json',
                })
                assert 200 == response.status_code
                assert f'{server.public_url}/file/{file_id}/file/{Path(__file__).name}' == response.url
