from hashlib import sha256

import docker
from betty.os import PathLike
from docker.models.containers import Container as DockerContainer

try:
    from typing import Self  # type: ignore
except ImportError:
    from typing_extensions import Self


class Container:
    def __init__(self, www_directory_path: PathLike, docker_directory_path: PathLike, nginx_configuration_file_path: PathLike):
        self._docker_directory_path = docker_directory_path
        self._nginx_configuration_file_path = nginx_configuration_file_path
        self._www_directory_path = www_directory_path
        self._client = docker.from_env()
        self._container: DockerContainer

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self) -> None:
        tag = 'betty_nginx-serve-' + sha256(str(self._docker_directory_path).encode('utf-8')).hexdigest()
        self._client.images.build(path=str(self._docker_directory_path), tag=tag)
        self._container = self._client.containers.create(tag, auto_remove=True, detach=True, volumes={
            self._nginx_configuration_file_path: {
                'bind': '/etc/nginx/conf.d/betty_nginx.conf',
                'mode': 'ro',
            },
            self._www_directory_path: {
                'bind': '/var/www/betty_nginx',
                'mode': 'ro',
            },
        })
        self._container.start()
        self._container.exec_run(['nginx', '-s', 'reload'])

    def stop(self) -> None:
        self._container.stop()

    @property
    def ip(self) -> str:
        return self._client.api.inspect_container(self._container.id)['NetworkSettings']['Networks']['bridge']['IPAddress']
