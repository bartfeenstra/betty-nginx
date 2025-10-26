"""
Integrate Betty with Docker.
"""

import asyncio
from pathlib import Path
from types import TracebackType
from typing import cast

import docker
from docker.models.containers import Container as DockerContainer


class Container:
    """
    A Docker container with nginx, configured to serve a Betty site.
    """

    _IMAGE_TAG = "betty-nginx"

    def __init__(self, artifacts_directory_path: Path, output_directory_path: Path, /):
        self._artifacts_directory_path = artifacts_directory_path
        self._www_directory_path = output_directory_path / "www"
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
        self._client.images.build(
            path=str(self._artifacts_directory_path / "docker"), tag=self._IMAGE_TAG
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

    @property
    def _container(self) -> DockerContainer:
        if self._docker_container is None:
            nginx_configuration_path = self._artifacts_directory_path / "conf.d"
            nginx_configuration_path.mkdir(exist_ok=True, parents=True)
            self._www_directory_path.mkdir(exist_ok=True, parents=True)

            self._docker_container = self._client.containers.create(
                self._IMAGE_TAG,
                auto_remove=True,
                detach=True,
                volumes={
                    **{
                        nginx_configuration_file_path: {
                            "bind": f"/etc/nginx/conf.d/{Path(nginx_configuration_file_path).name}",
                            "mode": "ro",
                        }
                        for nginx_configuration_file_path in nginx_configuration_path.iterdir()
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
