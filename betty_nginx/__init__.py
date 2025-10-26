"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from asyncio import gather
from pathlib import Path
from typing import final

from betty.job import Job
from betty.job.scheduler import Scheduler
from betty.locale.localizable import _, Plain
from betty.project import ProjectContext
from betty.project.extension import ConfigurableExtension, ExtensionDefinition
from betty.project.generate import Generator
from typing_extensions import override

from betty_nginx.artifact import generate_nginx_configuration, generate_dockerfile
from betty_nginx.config import NginxConfiguration


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
        await gather(
            generate_nginx_configuration(scheduler.context.project),
            generate_dockerfile(scheduler.context.project),
        )


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
