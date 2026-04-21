"""
Integrate the nginx extension with Betty's Serve API.
"""

import logging
from typing import final, override

import docker
from aiofiles.os import makedirs
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.server import Server, ServerNotStarted
from docker.errors import DockerException

from betty_nginx.docker import Container, Environment


@final
class DockerizedNginxServer(Server):
    """
    An nginx server that runs within a Docker container.
    """

    def __init__(
        self, project: Project, /, *, environment: Environment = Environment.LOCAL
    ) -> None:
        super().__init__(user=project.upstream.user)
        self._project = project
        self._environment = environment
        self._container: Container | None = None

    @override
    async def start(self) -> None:
        await self._user.message_debug(_("Starting a Dockerized nginx web server..."))

        await makedirs(self._project.www_directory, exist_ok=True)

        self._container = Container(
            self._project.output_directory, environment=self._environment
        )
        await self._container.start()

    @override
    async def stop(self) -> None:
        if self._container:
            await self._container.stop()

    @override
    @property
    def public_url(self) -> str:
        if self._container is not None:
            return f"http://{self._container.ip}"
        raise ServerNotStarted

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if Docker is available.
        """
        try:
            docker.from_env()
        except DockerException as e:
            logging.getLogger(__name__).warning(e)
            return False
        else:
            return True
