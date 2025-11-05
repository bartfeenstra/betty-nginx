"""
Integrate Betty with Docker.
"""

import asyncio
from enum import IntEnum
from pathlib import Path
from types import TracebackType
from typing import cast, final

import docker
from betty.exception import HumanFacingException
from betty.locale.localizable import _
from docker.models.containers import Container as DockerContainer


@final
class Environment(IntEnum):
    """
    The kind of environment to create a container for.
    """

    LOCAL = 0
    PUBLIC = 1


class Container:
    """
    A Docker container with nginx, configured to serve a Betty site.
    """

    _IMAGE_TAG = "betty-nginx"

    def __init__(
        self,
        output_directory_path: Path,
        /,
        environment: Environment = Environment.LOCAL,
    ):
        self._artifacts_directory_path = output_directory_path / "nginx"
        self._www_directory_path = output_directory_path / "www"
        self._environment = environment
        self._client = docker.from_env()
        self._docker_container: DockerContainer | None = None

    async def __aenter__(self) -> None:
        await self.start()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.stop()

    async def start(self) -> None:
        """
        Start the container.
        """
        await asyncio.to_thread(self._start)

    def _start(self) -> None:
        self._assert_artifacts_directory()
        self._client.images.build(
            path=str(self._artifacts_directory_path),
            tag=self._IMAGE_TAG,
        )
        self._container.start()
        self._container.exec_run(["nginx", "-s", "reload"])

    async def stop(self) -> None:
        """
        Stop the container.
        """
        await asyncio.to_thread(self._stop)

    def _stop(self) -> None:
        if self._container is not None:
            self._container.stop()

    def _assert_artifacts_directory(self) -> None:
        if not self._artifacts_directory_path.is_dir():
            raise HumanFacingException(
                _(
                    "The nginx configuration has not been generated yet. Generate your site, and try again."
                )
            )

    @property
    def _container(self) -> DockerContainer:
        if self._docker_container is None:
            self._assert_artifacts_directory()
            nginx_configuration_file_path = self._artifacts_directory_path / (
                ".nginx-local.conf"
                if self._environment is Environment.LOCAL
                else "nginx.conf"
            )

            self._docker_container = self._client.containers.create(
                self._IMAGE_TAG,
                auto_remove=True,
                detach=True,
                volumes={
                    nginx_configuration_file_path: {
                        "bind": "/etc/nginx/conf.d/nginx.conf",
                        "mode": "ro",
                    },
                    self._www_directory_path: {
                        "bind": "/var/www/betty",
                        "mode": "ro",
                    },
                },
            )
        return self._docker_container

    @property
    def ip(self) -> str:
        """
        The container's public IP address.
        """
        return cast(
            "str",
            self._client.api.inspect_container(self._container.id)["NetworkSettings"][
                "Networks"
            ]["bridge"]["IPAddress"],
        )
