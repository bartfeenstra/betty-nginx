"""
Integrate the nginx extension with Betty's Serve API.
"""

import logging
from collections.abc import Mapping
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

from betty_nginx import Nginx
from betty_nginx.artifact import generate_dockerfile_file, generate_configuration_file
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

        output_directory_path_str: str = await self._exit_stack.enter_async_context(
            TemporaryDirectory()
        )

        isolated_project: Project = await self._exit_stack.enter_async_context(
            Project.new_temporary(self._project.app, ancestry=self._project.ancestry)
        )
        isolated_project.configuration.configuration_file_path = (
            self._project.configuration.configuration_file_path
        )
        isolated_project.configuration.load(self._project.configuration.dump())
        isolated_project.configuration.debug = True

        # Work around https://github.com/bartfeenstra/betty-nginx/issues/3.
        nginx_configuration = isolated_project.configuration.extensions[
            Nginx
        ].configuration
        assert isinstance(nginx_configuration, Mapping)
        nginx_configuration["https"] = False

        await self._exit_stack.enter_async_context(isolated_project)

        nginx_configuration_file_path = Path(output_directory_path_str) / "nginx.conf"
        docker_directory_path = Path(output_directory_path_str)
        dockerfile_file_path = docker_directory_path / "Dockerfile"

        await generate_configuration_file(
            isolated_project,
            destination_file_path=nginx_configuration_file_path,
            https=False,
            www_directory_path="/var/www/betty",
        )
        await generate_dockerfile_file(
            isolated_project,
            destination_file_path=dockerfile_file_path,
        )
        self._container = Container(
            isolated_project.configuration.www_directory_path,
            docker_directory_path,
            nginx_configuration_file_path,
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
