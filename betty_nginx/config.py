from pathlib import Path
from typing import Optional, TYPE_CHECKING

from betty.config import ConfigurationError, Configuration, DumpedConfiguration
from betty.error import ensure_context
from betty.os import PathLike
from reactives import reactive

if TYPE_CHECKING:
    from betty_nginx.builtins import _


class NginxConfiguration(Configuration):
    def __init__(self, www_directory_path: Optional[PathLike] = None, https: Optional[bool] = None):
        super().__init__()
        self._https = https
        self._www_directory_path = None if www_directory_path is None else Path(www_directory_path)

    def load(self, dumped_configuration: DumpedConfiguration) -> None:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError(_('Nginx configuration must be a mapping (dictionary).'))

        if 'www_directory_path' in dumped_configuration:
            with ensure_context('www_directory_path'):
                if not isinstance(dumped_configuration['www_directory_path'], str) and dumped_configuration['www_directory_path'] is not None:
                    raise ConfigurationError(_('The WWW directory must be a string or left empty.'))
                self.www_directory_path = dumped_configuration['www_directory_path']

        if 'https' in dumped_configuration:
            with ensure_context('https'):
                if not isinstance(dumped_configuration['https'], bool) and dumped_configuration['https'] is not None:
                    raise ConfigurationError(_('HTTPS must be a boolean or left empty.'))
                self.https = dumped_configuration['https']

    def dump(self) -> DumpedConfiguration:
        dumped_configuration = {}
        if self.www_directory_path is not None:
            dumped_configuration['www_directory_path'] = str(self.www_directory_path)
        if self.https is not None:
            dumped_configuration['https'] = self.https
        return dumped_configuration

    @reactive  # type: ignore
    @property
    def https(self) -> Optional[bool]:
        return self._https

    @https.setter
    def https(self, https: bool) -> None:
        self._https = https

    @https.deleter
    def https(self) -> None:
        self._https = None

    @reactive  # type: ignore
    @property
    def www_directory_path(self) -> Optional[Path]:
        return self._www_directory_path

    @www_directory_path.setter
    def www_directory_path(self, www_directory_path: PathLike) -> None:
        self._www_directory_path = Path(www_directory_path)

    @www_directory_path.deleter
    def www_directory_path(self) -> None:
        self._www_directory_path = None
