"""
Integrate the nginx extension with Betty's Serve API.
"""

import logging
from contextlib import AsyncExitStack
from pathlib import Path
from typing import final, Self

import docker
from aiofiles.os import makedirs
from aiofiles.tempfile import TemporaryDirectory
from betty.project import Project
from betty.project.factory import ProjectDependentFactory
from betty.serve import NoPublicUrlBecauseServerNotStartedError, Server
from docker.errors import DockerException
from typing_extensions import override

from betty_nginx.artifact import generate_nginx_configuration, generate_dockerfile
from betty_nginx.docker import Container


@final
class DockerizedNginxServer(ProjectDependentFactory, Server):
    """
    An nginx server that runs within a Docker container.
    """

    def __init__(self, project: Project) -> None:
        super().__init__(user=project.app.user)
        self._project = project
        self._exit_stack = AsyncExitStack()
        self._container: Container | None = None

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
        return cls(project)

    @override
    async def start(self) -> None:
        logging.getLogger(__name__).info("Starting a Dockerized nginx web server...")

        await makedirs(self._project.configuration.www_directory_path, exist_ok=True)

        isolated_artifacts_directory_path = Path(
            await self._exit_stack.enter_async_context(TemporaryDirectory())
        )

        await generate_nginx_configuration(
            self._project,
            artifacts_directory_path=isolated_artifacts_directory_path,
            https=False,
            www_directory_path="/var/www/betty",
        )
        await generate_dockerfile(
            self._project,
            artifacts_directory_path=isolated_artifacts_directory_path,
        )

        self._container = Container(
            isolated_artifacts_directory_path,
            self._project.configuration.output_directory_path,
        )
        await self._exit_stack.enter_async_context(self._container)

    @override
    async def stop(self) -> None:
        await self._exit_stack.aclose()

    @override
    @property
    def public_url(self) -> str:
        if self._container is not None:
            return f"http://{self._container.ip}"
        raise NoPublicUrlBecauseServerNotStartedError()

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if Docker is available.
        """
        try:
            docker.from_env()
            return True
        except DockerException as e:
            logging.getLogger(__name__).warning(e)
            return False
