import logging
from pathlib import Path
from tempfile import TemporaryDirectory

import docker
from betty.app import App
from betty.serve import Server, NoPublicUrlBecauseServerNotStartedError
from betty_nginx.artifact import generate_dockerfile_file, generate_configuration_file
from betty_nginx.docker import Container
from docker.errors import DockerException


class DockerizedNginxServer(Server):
    def __init__(self, app: App):
        self._app = app
        self._container: Container = None  # type: ignore
        self._output_directory: TemporaryDirectory

    async def start(self) -> None:
        logging.getLogger().info('Starting a Dockerized nginx web server...')
        self._original_debug = self._app.project.configuration.debug
        # While the generated Docker configuration is suitable for production use, this server is not.
        self._app.project.configuration.debug = True
        self._output_directory = TemporaryDirectory()
        nginx_configuration_file_path = Path(self._output_directory.name) / 'nginx.conf'
        docker_directory_path = Path(self._output_directory.name) / 'docker'
        dockerfile_file_path = docker_directory_path / 'Dockerfile'
        await generate_configuration_file(
            self._app,
            destination_file_path=nginx_configuration_file_path,
            https=False,
            www_directory_path='/var/www/betty_nginx',
        )
        await generate_dockerfile_file(self._app, destination_file_path=dockerfile_file_path)
        self._container = Container(
            self._app.project.configuration.www_directory_path,
            docker_directory_path,
            nginx_configuration_file_path,
        )
        self._container.start()

    async def stop(self) -> None:
        self._app.project.configuration.debug = self._original_debug
        self._container.stop()
        self._output_directory.cleanup()

    @property
    def public_url(self) -> str:
        if self._container is not None:
            return f'http://{self._container.ip}'
        raise NoPublicUrlBecauseServerNotStartedError()

    @classmethod
    def is_available(cls) -> bool:
        try:
            docker.from_env().info()
            return True
        except DockerException as e:
            logging.getLogger().debug(e)
            return False
