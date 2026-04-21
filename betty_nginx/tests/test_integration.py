import sys
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import pytest
import requests
from betty.extension import ExtensionManufacturer
from betty.functools import Do
from betty.plugins.entity.place import Place
from betty.project import Project, ProjectEntityType, ProjectLocale, generate
from betty.server import Server
from betty.test_utils.conftest import IsolatedProjectFactory
from requests import Response

from betty_nginx.data import NginxConfiguration
from betty_nginx.plugins.extension.nginx import Nginx
from betty_nginx.serve import DockerizedNginxServer
from betty_nginx.tests.conftest import AssertBettyHtml, AssertBettyJson


@pytest.mark.skipif(
    sys.platform in {"darwin", "win32"},
    reason="macOS and Windows do not natively support Docker.",
)
class TestNginx:
    @asynccontextmanager
    async def server(self, project: Project) -> AsyncIterator[Server]:
        await generate.generate(project)
        async with DockerizedNginxServer(project) as server:
            yield server

    def _build_assert_status_code(
        self, expected_http_status_code: int
    ) -> Callable[[Response], None]:
        def _assert(response: Response) -> None:
            assert response.status_code == expected_http_status_code

        return _assert

    async def test_front_page(
        self,
        assert_betty_html: AssertBettyHtml,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ]
            ) as project,
            self.server(project) as server,
        ):
            await Do(requests.get, server.public_url).until(
                self._build_assert_status_code(200), assert_betty_html
            )

    async def test_default_html_404(
        self,
        assert_betty_html: AssertBettyHtml,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ]
            ) as project,
            self.server(project) as server,
        ):
            await Do(requests.get, f"{server.public_url}/non-existent-path/").until(
                self._build_assert_status_code(404), assert_betty_html
            )

    async def test_negotiated_json_404(
        self,
        assert_betty_json: AssertBettyJson,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                clean_urls=True,
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
            ) as project,
            self.server(project) as server,
        ):
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
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async def _assert_response(response: Response) -> None:
            assert response.status_code == 200
            assert response.headers["Content-Language"] == "en"
            assert response.url == f"{server.public_url}/en/"
            await assert_betty_html(response)

        async with (
            isolated_project_factory(
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
                locales=[
                    ProjectLocale("en-US", alias="en"),
                    ProjectLocale("nl-NL", alias="nl"),
                ],
            ) as project,
            self.server(project) as server,
        ):
            await Do(requests.get, server.public_url).until(_assert_response)

    async def test_explicitly_localized_404(
        self,
        assert_betty_html: AssertBettyHtml,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async def _assert_response(response: Response) -> None:
            assert response.status_code == 404
            assert response.headers["Content-Language"] == "nl"
            await assert_betty_html(response)

        async with (
            isolated_project_factory(
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
                locales=[
                    ProjectLocale("en-US", alias="en"),
                    ProjectLocale("nl-NL", alias="nl"),
                ],
            ) as project,
            self.server(project) as server,
        ):
            await Do(requests.get, f"{server.public_url}/nl/non-existent-path/").until(
                _assert_response
            )

    async def test_negotiated_localized_front_page(
        self,
        assert_betty_html: AssertBettyHtml,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async def _assert_response(response: Response) -> None:
            assert response.status_code == 200
            assert response.headers["Content-Language"] == "nl"
            assert response.url == f"{server.public_url}/nl/"
            await assert_betty_html(response)

        async with (
            isolated_project_factory(
                clean_urls=True,
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
                locales=[
                    ProjectLocale("en-US", alias="en"),
                    ProjectLocale("nl-NL", alias="nl"),
                ],
            ) as project,
            self.server(project) as server,
        ):
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
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                clean_urls=True,
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
                locales=[
                    ProjectLocale("en-US", alias="en"),
                    ProjectLocale("nl-NL", alias="nl"),
                ],
            ) as project,
            self.server(project) as server,
        ):
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
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                entity_types=[
                    ProjectEntityType(entity_type=Place, generate_html_list=True)
                ],
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
            ) as project,
            self.server(project) as server,
        ):
            await Do(requests.get, f"{server.public_url}/place/index.html").until(
                self._build_assert_status_code(200), assert_betty_html
            )

    async def test_negotiated_html_resource(
        self,
        assert_betty_html: AssertBettyHtml,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                entity_types=[
                    ProjectEntityType(entity_type=Place, generate_html_list=True)
                ],
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
                clean_urls=True,
            ) as project,
            self.server(project) as server,
        ):
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
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
                clean_urls=True,
            ) as project,
            self.server(project) as server,
        ):
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
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
                locales=[
                    ProjectLocale("en-US", alias="en"),
                    ProjectLocale("nl-NL", alias="nl"),
                ],
            ) as project,
            self.server(project) as server,
        ):
            await Do(requests.get, f"{server.public_url}/index.html").until(
                self._build_assert_status_code(200), assert_betty_html
            )

    async def test_negotiated_html_static_resource(
        self,
        assert_betty_html: AssertBettyHtml,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
                locales=[
                    ProjectLocale("en-US", alias="en"),
                    ProjectLocale("nl-NL", alias="nl"),
                ],
                clean_urls=True,
            ) as project,
            self.server(project) as server,
        ):
            await Do(
                requests.get,
                f"{server.public_url}/",
                headers={
                    "Accept": "text/html",
                },
            ).until(self._build_assert_status_code(200), assert_betty_html)

    async def test_negotiated_json_static_resource(
        self,
        assert_betty_json: AssertBettyJson,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with (
            isolated_project_factory(
                extensions=[
                    ExtensionManufacturer(
                        Nginx, NginxConfiguration(www_directory="/var/www/betty")
                    )
                ],
                locales=[
                    ProjectLocale("en-US", alias="en"),
                    ProjectLocale("nl-NL", alias="nl"),
                ],
                clean_urls=True,
            ) as project,
            self.server(project) as server,
        ):
            await Do(
                requests.get,
                f"{server.public_url}/non-existent-path/",
                headers={
                    "Accept": "application/json",
                },
            ).until(self._build_assert_status_code(404), assert_betty_json)

    async def test_legacy_entity_redirects(
        self,
        assert_betty_html: AssertBettyHtml,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with isolated_project_factory(
            extensions=[
                ExtensionManufacturer(
                    Nginx,
                    NginxConfiguration(
                        legacy_entity_redirects=True, www_directory="/var/www/betty"
                    ),
                )
            ]
        ) as project:
            entity = Place(id="my-first-place")
            project.ancestry.add(entity)
            async with self.server(project) as server:
                await Do(
                    requests.get,
                    f"{server.public_url}/{entity.plugin().id}/{entity.id}/index.html",
                ).until(self._build_assert_status_code(200), assert_betty_html)

    async def test_legacy_entity_redirects__multilingual(
        self,
        assert_betty_html: AssertBettyHtml,
        isolated_project_factory: IsolatedProjectFactory,
    ) -> None:
        async with isolated_project_factory(
            extensions=[
                ExtensionManufacturer(
                    Nginx,
                    NginxConfiguration(
                        legacy_entity_redirects=True, www_directory="/var/www/betty"
                    ),
                )
            ],
            locales=[
                ProjectLocale("en-US", alias="en"),
                ProjectLocale("nl-NL", alias="nl"),
            ],
        ) as project:
            entity = Place(id="my-first-place")
            project.ancestry.add(entity)
            async with self.server(project) as server:
                await Do(
                    requests.get,
                    f"{server.public_url}/en/{entity.plugin().id}/{entity.id}/index.html",
                ).until(self._build_assert_status_code(200), assert_betty_html)
