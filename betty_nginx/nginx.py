from pathlib import Path
from typing import Optional, Iterable, TYPE_CHECKING

from PyQt6.QtWidgets import QWidget
from betty.app import ConfigurableExtension
from betty.generate import Generator
from betty.gui import GuiBuilder
from betty.serve import ServerProvider, Server
from betty_nginx.config import NginxConfiguration

if TYPE_CHECKING:
    from betty_nginx.builtins import _


class Nginx(ConfigurableExtension[NginxConfiguration], Generator, ServerProvider, GuiBuilder):
    @classmethod
    def default_configuration(cls) -> NginxConfiguration:
        return NginxConfiguration()

    @property
    def servers(self) -> Iterable[Server]:
        from betty_nginx.serve import DockerizedNginxServer

        if DockerizedNginxServer.is_available():
            return [DockerizedNginxServer(self._app)]
        return []

    async def generate(self) -> None:
        from betty_nginx.artifact import generate_configuration_file, generate_dockerfile_file

        await generate_configuration_file(self._app)
        await generate_dockerfile_file(self._app)

    @classmethod
    def assets_directory_path(cls) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

    @property
    def https(self) -> bool:
        if self.configuration.https is None:
            return self._app.project.configuration.base_url.startswith('https')
        return self.configuration.https

    @property
    def www_directory_path(self) -> Path:
        if self.configuration.www_directory_path is None:
            return self._app.project.configuration.www_directory_path
        return self.configuration.www_directory_path

    @classmethod
    def label(cls) -> str:
        return 'Nginx'

    @classmethod
    def gui_description(cls) -> str:
        return _('Generate <a href="https://nginx.org/">nginx</a> configuration for your site, as well as a <code>Dockerfile</code> to build a <a href="https://www.docker.com/">Docker</a> container around it.')

    def gui_build(self) -> Optional[QWidget]:
        from betty_nginx.gui import _NginxGuiWidget

        return _NginxGuiWidget(self._app)
