from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget, QFormLayout, QButtonGroup, QRadioButton, QFileDialog, QPushButton, QHBoxLayout, \
    QLineEdit
from betty.app import App
from betty.gui.error import catch_exceptions

from betty_nginx.nginx import Nginx

if TYPE_CHECKING:
    pass


class _NginxGuiWidget(QWidget):
    def __init__(self, app: App, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app = app
        self._configuration = self._app.extensions[Nginx].configuration
        layout = QFormLayout()

        self.setLayout(layout)

        https_button_group = QButtonGroup()

        def _update_configuration_https_base_url(checked: bool) -> None:
            if checked:
                self._configuration.https = None
        self._nginx_https_base_url = QRadioButton("Use HTTPS and HTTP/2 if the site's URL starts with https://")
        self._nginx_https_base_url.setChecked(self._configuration.https is None)
        self._nginx_https_base_url.toggled.connect(_update_configuration_https_base_url)  # type: ignore
        layout.addRow(self._nginx_https_base_url)
        https_button_group.addButton(self._nginx_https_base_url)

        def _update_configuration_https_https(checked: bool) -> None:
            if checked:
                self._configuration.https = True
        self._nginx_https_https = QRadioButton('Use HTTPS and HTTP/2')
        self._nginx_https_https.setChecked(self._configuration.https is True)
        self._nginx_https_https.toggled.connect(_update_configuration_https_https)  # type: ignore
        layout.addRow(self._nginx_https_https)
        https_button_group.addButton(self._nginx_https_https)

        def _update_configuration_https_http(checked: bool) -> None:
            if checked:
                self._configuration.https = False
        self._nginx_https_http = QRadioButton('Use HTTP')
        self._nginx_https_http.setChecked(self._configuration.https is False)
        self._nginx_https_http.toggled.connect(_update_configuration_https_http)  # type: ignore
        layout.addRow(self._nginx_https_http)
        https_button_group.addButton(self._nginx_https_http)

        def _update_configuration_www_directory_path(www_directory_path: str) -> None:
            self._configuration.www_directory_path = None if www_directory_path == '' or www_directory_path == self._app.project.configuration.www_directory_path else www_directory_path
        self._nginx_www_directory_path = QLineEdit()
        self._nginx_www_directory_path.setText(str(self._configuration.www_directory_path) if self._configuration.www_directory_path is not None else str(self._app.project.configuration.www_directory_path))
        self._nginx_www_directory_path.textChanged.connect(_update_configuration_www_directory_path)  # type: ignore
        www_directory_path_layout = QHBoxLayout()
        www_directory_path_layout.addWidget(self._nginx_www_directory_path)

        @catch_exceptions
        def find_www_directory_path() -> None:
            found_www_directory_path = QFileDialog.getExistingDirectory(self, 'Serve your site from...', directory=self._nginx_www_directory_path.text())
            if '' != found_www_directory_path:
                self._nginx_www_directory_path.setText(found_www_directory_path)
        self._nginx_www_directory_path_find = QPushButton('...')
        self._nginx_www_directory_path_find.released.connect(find_www_directory_path)  # type: ignore
        www_directory_path_layout.addWidget(self._nginx_www_directory_path_find)
        layout.addRow('WWW directory', www_directory_path_layout)