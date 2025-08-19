"""Integrate Betty with `nginx <https://nginx.org/>`_."""

from pathlib import Path
from typing import final

from betty.job import Job
from betty.job.scheduler import Scheduler
from betty.locale.localizable import _, Localizable, Plain
from betty.machine_name import MachineName
from betty.project import ProjectContext
from betty.project.extension import ConfigurableExtension
from betty.project.generate import Generator
from typing_extensions import override

from betty_nginx.artifact import generate_configuration_file, generate_dockerfile_file
from betty_nginx.config import NginxConfiguration


@final
class GenerateConfigurationFile(Job[ProjectContext]):
    """
    Generate nginx.conf.
    """

    def __init__(self):
        super().__init__(self.id_for(), priority=True)

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "betty-nginx-generate-configuration-file"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        await generate_configuration_file(scheduler.context.project)


@final
class GenerateDockerfile(Job[ProjectContext]):
    """
    Generate Dockerfile.
    """

    def __init__(self):
        super().__init__(self.id_for(), priority=True)

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "betty-nginx-generate-dockerfile"

    @override
    async def do(self, scheduler: Scheduler[ProjectContext], /) -> None:
        await generate_dockerfile_file(scheduler.context.project)


@final
class Nginx(Generator, ConfigurableExtension[NginxConfiguration]):
    """
    Integrate Betty with nginx (and Docker).
    """

    @override
    @classmethod
    def plugin_id(cls) -> MachineName:
        return "nginx"

    @override
    @classmethod
    def plugin_label(cls) -> Localizable:
        return Plain("Nginx")

    @override
    @classmethod
    def plugin_description(cls) -> Localizable:
        return _(
            "Generate nginx configuration for your site, as well as a Dockerfile to build a Docker container around it."
        )

    @override
    async def generate(self, scheduler: Scheduler[ProjectContext]) -> None:
        await scheduler.add(GenerateConfigurationFile(), GenerateDockerfile())

    @override
    @classmethod
    def new_default_configuration(cls) -> NginxConfiguration:
        return NginxConfiguration()

    @override
    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / "assets"

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
