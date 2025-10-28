import sys
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
import requests
from betty.ancestry import Ancestry
from betty.ancestry.place import Place
from betty.app import App
from betty.functools import Do
from betty.plugin.config import PluginInstanceConfiguration
from betty.project import Project
from betty.project import generate
from betty.project.config import (
    LocaleConfiguration,
    ProjectConfiguration,
    EntityTypeConfiguration,
)
from betty.serve import Server
from requests import Response

from betty_nginx import Nginx
from betty_nginx.config import NginxConfiguration
from betty_nginx.serve import DockerizedNginxServer
from betty_nginx.tests.conftest import AssertBettyJson, AssertBettyHtml


@pytest.mark.skipif(
    sys.platform in {"darwin", "win32"},
    reason="macOS and Windows do not natively support Docker.",
)
class TestNginx:
    @asynccontextmanager
    async def server(
        self, configuration: ProjectConfiguration, *, ancestry: Ancestry | None = None
    ) -> AsyncIterator[Server]:
        async with (
            App.new_temporary() as app,
            app,
            Project.new_temporary(
                app, ancestry=ancestry, configuration=configuration
            ) as project,
            project,
        ):
            await generate.generate(project)
            async with DockerizedNginxServer(project) as server:
                yield server

    @pytest.fixture
    async def monolingual_configuration(self, tmp_path: Path) -> ProjectConfiguration:
        return await ProjectConfiguration.new(
            tmp_path / "betty.json",
            extensions=[
                PluginInstanceConfiguration(
                    Nginx,
                    configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
        )

    @pytest.fixture
    async def monolingual_clean_urls_configuration(
        self, tmp_path: Path
    ) -> ProjectConfiguration:
        return await ProjectConfiguration.new(
            tmp_path / "betty.json",
            extensions=[
                PluginInstanceConfiguration(
                    Nginx,
                    configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
            clean_urls=True,
        )

    @pytest.fixture
    async def multilingual_configuration(self, tmp_path: Path) -> ProjectConfiguration:
        return await ProjectConfiguration.new(
            tmp_path / "betty.json",
            extensions=[
                PluginInstanceConfiguration(
                    Nginx,
                    configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
            locales=[
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
            ],
        )

    @pytest.fixture
    async def multilingual_clean_urls_configuration(
        self, tmp_path: Path
    ) -> ProjectConfiguration:
        return await ProjectConfiguration.new(
            tmp_path / "betty.json",
            extensions=[
                PluginInstanceConfiguration(
                    Nginx,
                    configuration=NginxConfiguration(
                        www_directory_path="/var/www/betty/"
                    ),
                ),
            ],
            locales=[
                LocaleConfiguration(
                    "en-US",
                    alias="en",
                ),
                LocaleConfiguration(
                    "nl-NL",
                    alias="nl",
                ),
            ],
            clean_urls=True,
        )

    def _build_assert_status_code(
        self, expected_http_status_code: int
    ) -> Callable[[Response], None]:
        def _assert(response: Response) -> None:
            assert response.status_code == expected_http_status_code

        return _assert

    async def test_front_page(
        self,
        assert_betty_html: AssertBettyHtml,
        monolingual_clean_urls_configuration: ProjectConfiguration,
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
            await Do(requests.get, server.public_url).until(
                self._build_assert_status_code(200), assert_betty_html
            )

    async def test_default_html_404(
        self,
        assert_betty_html: AssertBettyHtml,
        monolingual_clean_urls_configuration: ProjectConfiguration,
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
            await Do(requests.get, f"{server.public_url}/non-existent-path/").until(
                self._build_assert_status_code(404), assert_betty_html
            )

    async def test_negotiated_json_404(
        self,
        assert_betty_json: AssertBettyJson,
        monolingual_clean_urls_configuration: ProjectConfiguration,
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                },
            ).until(self._build_assert_status_code(404), assert_betty_json)

    async def test_default_localized_front_page(
        self,
        assert_betty_html: AssertBettyHtml,
        multilingual_configuration: ProjectConfiguration,
    ):
        async def _assert_response(response: Response) -> None:
            assert response.status_code == 200
            assert response.headers["Content-Language"] == "en"
            assert f"{server.public_url}/en/" == response.url
            await assert_betty_html(response)

        async with self.server(multilingual_configuration) as server:
            await Do(requests.get, server.public_url).until(_assert_response)

    async def test_explicitly_localized_404(
        self,
        assert_betty_html: AssertBettyHtml,
        multilingual_configuration: ProjectConfiguration,
    ):
        async def _assert_response(response: Response) -> None:
            assert response.status_code == 404
            assert response.headers["Content-Language"] == "nl"
            await assert_betty_html(response)

        async with self.server(multilingual_configuration) as server:
            await Do(requests.get, f"{server.public_url}/nl/non-existent-path/").until(
                _assert_response
            )

    async def test_negotiated_localized_front_page(
        self,
        assert_betty_html: AssertBettyHtml,
        multilingual_clean_urls_configuration: ProjectConfiguration,
    ):
        async def _assert_response(response: Response) -> None:
            assert response.status_code == 200
            assert response.headers["Content-Language"] == "nl"
            assert f"{server.public_url}/nl/" == response.url
            await assert_betty_html(response)

        async with self.server(multilingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                server.public_url,
                headers={
                    "Accept-Language": "nl-NL",
                },
            ).until(_assert_response)

    async def test_negotiated_localized_negotiated_json_404(
        self,
        assert_betty_json: AssertBettyJson,
        multilingual_clean_urls_configuration: ProjectConfiguration,
    ):
        async with self.server(multilingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                    "Accept-Language": "nl-NL",
                },
            ).until(self._build_assert_status_code(404), assert_betty_json)

    async def test_default_html_resource(
        self,
        assert_betty_html: AssertBettyHtml,
        monolingual_clean_urls_configuration: ProjectConfiguration,
    ):
        monolingual_clean_urls_configuration.entity_types.append(
            EntityTypeConfiguration(Place, generate_html_list=True)
        )
        async with self.server(monolingual_clean_urls_configuration) as server:
            await Do(requests.get, f"{server.public_url}/place/").until(
                self._build_assert_status_code(200), assert_betty_html
            )

    async def test_negotiated_html_resource(
        self,
        assert_betty_html: AssertBettyHtml,
        monolingual_clean_urls_configuration: ProjectConfiguration,
    ):
        monolingual_clean_urls_configuration.entity_types.append(
            EntityTypeConfiguration(Place, generate_html_list=True)
        )
        async with self.server(monolingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/place/",
                headers={
                    "Accept": "text/html",
                },
            ).until(self._build_assert_status_code(200), assert_betty_html)

    async def test_negotiated_json_resource(
        self,
        assert_betty_json: AssertBettyJson,
        monolingual_clean_urls_configuration: ProjectConfiguration,
    ):
        async with self.server(monolingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/place/",
                headers={
                    "Accept": "application/json",
                },
            ).until(self._build_assert_status_code(200), assert_betty_json)

    async def test_default_html_static_resource(
        self,
        assert_betty_html: AssertBettyHtml,
        multilingual_clean_urls_configuration: ProjectConfiguration,
    ):
        async with self.server(multilingual_clean_urls_configuration) as server:
            await Do(requests.get, f"{server.public_url}/non-existent-path/").until(
                self._build_assert_status_code(404), assert_betty_html
            )

    async def test_negotiated_html_static_resource(
        self,
        assert_betty_html: AssertBettyHtml,
        multilingual_clean_urls_configuration: ProjectConfiguration,
        tmp_path: Path,
    ):
        async with self.server(multilingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "text/html",
                },
            ).until(self._build_assert_status_code(404), assert_betty_html)

    async def test_negotiated_json_static_resource(
        self,
        assert_betty_json: AssertBettyJson,
        multilingual_clean_urls_configuration: ProjectConfiguration,
    ):
        async with self.server(multilingual_clean_urls_configuration) as server:
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                },
            ).until(self._build_assert_status_code(404), assert_betty_json)

    async def test_legacy_entity_redirects__monolingual(
        self,
        assert_betty_html: AssertBettyHtml,
        monolingual_configuration: ProjectConfiguration,
    ):
        monolingual_configuration.extensions[Nginx].configuration[  # type: ignore[call-overload,index]
            "legacy_entity_redirects"
        ] = True
        ancestry = Ancestry()
        entity = Place(id="my-first-place")
        ancestry.add(entity)
        async with self.server(monolingual_configuration, ancestry=ancestry) as server:
            await Do(
                requests.get,
                f"{server.public_url}/{entity.plugin.id}/{entity.id}/index.html",
            ).until(self._build_assert_status_code(200), assert_betty_html)

    async def test_legacy_entity_redirects__multilingual(
        self,
        assert_betty_html: AssertBettyHtml,
        multilingual_configuration: ProjectConfiguration,
    ):
        multilingual_configuration.extensions[Nginx].configuration[  # type: ignore[call-overload,index]
            "legacy_entity_redirects"
        ] = True
        ancestry = Ancestry()
        entity = Place(id="my-first-place")
        ancestry.add(entity)
        async with self.server(multilingual_configuration, ancestry=ancestry) as server:
            await Do(
                requests.get,
                f"{server.public_url}/en/{entity.plugin.id}/{entity.id}/index.html",
            ).until(self._build_assert_status_code(200), assert_betty_html)
