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
from betty.attrs.owner import OwnerAttr
from betty.data import Data
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.bool import BoolDefinition
from betty.datas.str import StrDefinition
from betty.factory import DataManufacturable, Manufacturable
from betty.file import write
from betty.localizables.gettext import _
from betty.project import Project
from betty.project.generate import Generator
from betty.service_provider import ServiceProvider, ServiceProviderDefinition

from betty_nginx.asset_directories import nginx
from betty_nginx.jobs.jobs import GenerateArtifacts

if TYPE_CHECKING:
    from betty.job import Scheduler


@final
@ObjectDefinition(
    label=_("Nginx configuration"),
)
class NginxConfig(Data):
    """
    Provide configuration for the :py:class:`betty_nginx.Nginx` extension.
    """

    https = OwnerAttr(
        BoolDefinition(label="HTTPS"),
        omit_load=True,
        omit_dump=lambda data: data is None,
    ).optional
    """
    Whether the nginx server should use HTTPS.

    ``True`` to use HTTPS (and HTTP/2), ``False`` to use HTTP (and HTTP 1), ``None`` to let this behavior depend on 
    whether the project's URL uses HTTPS or not.
    """

    legacy_entity_redirects = OwnerAttr(
        BoolDefinition(label=_("Legacy entity redirects")),
        omit_load=True,
        omit_dump=lambda data: data is False,
    )
    """
    Whether to generate redirects from legacy (pre Betty 0.5) entity URLs.
    """

    www_directory = OwnerAttr(
        StrDefinition(label=_("WWW directory")),
        omit_load=True,
        omit_dump=lambda data: data is None,
    ).optional
    """
    The nginx server's public web root directory path.
    """

    def __init__(
        self,
        *,
        www_directory: str | None = None,
        https: bool | None = None,
        legacy_entity_redirects: bool = False,
    ):
        super().__init__()
        self.https = https
        self.www_directory = www_directory
        self.legacy_entity_redirects = legacy_entity_redirects


@final
@ServiceProviderDefinition(
    "nginx",
    label="Nginx",
    description=_(
        "Generate nginx configuration for your site, as well as a Dockerfile to build a Docker container around it."
    ),
    requires=[Project.asset_directories.require(nginx)],
)
class Nginx(
    Generator, ServiceProvider, DataManufacturable[NginxConfig], Manufacturable
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
    def new_data_cls(cls) -> type[NginxConfig]:
        return NginxConfig

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: NginxConfig | None = None, /) -> Self:
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
            nginx.assets / "nginx" / "Dockerfile",
            self._artifacts_directory / "Dockerfile",
        )

    async def _generate_content_negotiation(self) -> None:
        await makedirs(self._artifacts_directory, exist_ok=True)
        await asyncio.to_thread(
            copyfile,
            nginx.assets / "nginx" / "content_negotiation.lua",
            self._artifacts_directory / "content_negotiation.lua",
        )
