"""
The Nginx extension.
"""

from __future__ import annotations

import asyncio
from asyncio import gather
from shutil import copyfile
from typing import TYPE_CHECKING, Self, final, override
from urllib.parse import urlparse

from aiofiles.os import makedirs
from betty.extension import Extension, ExtensionDefinition
from betty.factory import DataManufacturable, Manufacturable
from betty.file import write
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.project.generate import Generator

from betty_nginx.data import NginxConfiguration
from betty_nginx.jobs import GenerateArtifacts
from betty_nginx.plugins.asset_directory.nginx import NGINX

if TYPE_CHECKING:
    from betty.job import Scheduler


@final
@ExtensionDefinition(
    "nginx",
    label="Nginx",
    description=_(
        "Generate nginx configuration for your site, as well as a Dockerfile to build a Docker container around it."
    ),
    requires=[Project.asset_directories.require(NGINX)],
)
class Nginx(
    Generator, Extension, DataManufacturable[NginxConfiguration], Manufacturable
):
    """
    Integrate Betty with nginx (and Docker).
    """

    def __init__(
        self,
        *,
        project: Project,
        https: bool | None = None,
        legacy_entity_redirects: bool = False,
        www_directory: str | None = None,
    ):
        super().__init__()
        self._artifacts_directory = project.output_directory / "nginx"
        self._https = project.base_url.startswith("https") if https is None else https
        self._legacy_entity_redirects = legacy_entity_redirects
        self._project = project
        self._www_directory = www_directory or str(project.www_directory)

    @override
    @classmethod
    def new_data_cls(cls) -> type[NginxConfiguration]:
        return NginxConfiguration

    @override
    @Project.require
    @classmethod
    async def new(
        cls, project: Project, data: NginxConfiguration | None = None, /
    ) -> Self:
        return cls(
            https=data.https if data else None,
            legacy_entity_redirects=data.legacy_entity_redirects if data else False,
            project=project,
            www_directory=data.www_directory if data else None,
        )

    @override
    async def generate(self, scheduler: Scheduler) -> None:
        await scheduler.add(GenerateArtifacts(self))

    async def generate_artifacts(self) -> None:
        """
        Generate all artifacts.
        """
        await gather(
            self._generate_nginx_configuration("nginx.conf", self._https),
            self._generate_nginx_configuration(".nginx-local.conf", False),
            self._generate_content_negotiation(),
            self._generate_dockerfile(),
        )

    async def _generate_nginx_configuration(
        self, file_name: str, https: bool | None
    ) -> None:
        data = {
            "https": https,
            "legacy_entity_redirects": self._legacy_entity_redirects,
            "server_name": urlparse(self._project.base_url).netloc,
            "www_directory": self._www_directory,
        }
        configuration_file_contents = (
            await (await self._project.jinja)
            .get_template("nginx/nginx.conf.j2")
            .render_async(**data)
        )
        await makedirs(self._artifacts_directory, exist_ok=True)
        await write(self._artifacts_directory / file_name, configuration_file_contents)

    async def _generate_dockerfile(self) -> None:
        await makedirs(self._artifacts_directory, exist_ok=True)
        await asyncio.to_thread(
            copyfile,
            NGINX.assets / "nginx" / "Dockerfile",
            self._artifacts_directory / "Dockerfile",
        )

    async def _generate_content_negotiation(self) -> None:
        await makedirs(self._artifacts_directory, exist_ok=True)
        await asyncio.to_thread(
            copyfile,
            NGINX.assets / "nginx" / "content_negotiation.lua",
            self._artifacts_directory / "content_negotiation.lua",
        )
