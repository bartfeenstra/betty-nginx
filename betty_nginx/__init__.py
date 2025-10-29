"""Integrate Betty with `nginx <https://nginx.org/>`_."""

import asyncio
from asyncio import gather
from pathlib import Path
from shutil import copyfile
from typing import final
from urllib.parse import urlparse

import aiofiles
from aiofiles.os import makedirs
from betty.job import Job
from betty.job.scheduler import Scheduler
from betty.locale.localizable import _, Plain
from betty.project import ProjectContext
from betty.project.extension import ConfigurableExtension, ExtensionDefinition
from betty.project.generate import Generator
from jinja2 import FileSystemLoader
from typing_extensions import override

from betty_nginx.config import NginxConfiguration


def _rootname(source_path: Path) -> Path:
    root = source_path
    while True:
        possible_root = root.parent
        if possible_root == root:
            return root
        root = possible_root


@final
class GenerateArtifacts(Job[ProjectContext]):
    """
    Generate the artifacts.
    """

    def __init__(self):
        super().__init__(self.id_for(), priority=True)

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "betty-nginx-generate-artifacts"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        extensions = await scheduler.context.project.extensions
        await extensions[Nginx].generate_artifacts()


@final
@ExtensionDefinition(
    id="nginx",
    label=Plain("Nginx"),
    description=_(
        "Generate nginx configuration for your site, as well as a Dockerfile to build a Docker container around it."
    ),
    assets_directory_path=Path(__file__).parent / "assets",
)
class Nginx(Generator, ConfigurableExtension[NginxConfiguration]):
    """
    Integrate Betty with nginx (and Docker).
    """

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(GenerateArtifacts())

    @override
    @classmethod
    def new_default_configuration(cls) -> NginxConfiguration:
        return NginxConfiguration()

    @property
    def https(self) -> bool:
        """
        Whether the nginx server should use HTTPS.
        """
        if self._configuration.https is None:
            return self._project.configuration.base_url.startswith("https")
        return self._configuration.https

    @property
    def www_directory_path(self) -> str:
        """
        The nginx server's public web root directory path.
        """
        return self._configuration.www_directory_path or str(
            self._project.configuration.www_directory_path
        )

    @property
    def artifacts_directory_path(self) -> Path:
        """
        The directory into which to generate the artifacts.
        """
        return self.project.configuration.output_directory_path / "nginx"

    async def generate_artifacts(self) -> None:
        """
        Generate all artifacts.
        """
        await gather(
            self._generate_nginx_configuration("nginx.conf", self.https),
            self._generate_nginx_configuration(".nginx-local.conf", False),
            self._generate_content_negotiation(),
            self._generate_dockerfile(),
        )

    async def _generate_nginx_configuration(
        self, file_name: str, https: bool | None
    ) -> None:
        data = {
            "server_name": urlparse(self.project.configuration.base_url).netloc,
            "www_directory_path": self.www_directory_path,
            "https": https,
        }
        root_path = _rootname(Path(__file__))
        configuration_file_template_name = "/".join(
            (Path(__file__).parent / "assets" / "nginx.conf.j2")
            .relative_to(root_path)
            .parts
        )
        jinja2_environment = await self.project.jinja2_environment
        template = FileSystemLoader(root_path).load(
            jinja2_environment,
            configuration_file_template_name,
            jinja2_environment.globals,
        )
        configuration_file_contents = await template.render_async(data)
        await makedirs(self.artifacts_directory_path, exist_ok=True)
        async with aiofiles.open(
            self.artifacts_directory_path / file_name, "w", encoding="utf-8"
        ) as f:
            await f.write(configuration_file_contents)

    async def _generate_dockerfile(self) -> None:
        await makedirs(self.artifacts_directory_path, exist_ok=True)
        await asyncio.to_thread(
            copyfile,
            Path(__file__).parent / "assets" / "Dockerfile",
            self.artifacts_directory_path / "Dockerfile",
        )

    async def _generate_content_negotiation(self) -> None:
        await makedirs(self.artifacts_directory_path, exist_ok=True)
        await asyncio.to_thread(
            copyfile,
            Path(__file__).parent / "assets" / "content_negotiation.lua",
            self.artifacts_directory_path / "content_negotiation.lua",
        )
