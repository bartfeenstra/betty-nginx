from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog
from betty.app import App
from betty.project import ProjectExtensionConfiguration

from betty_nginx.gui import _NginxGuiWidget
from betty_nginx.nginx import Nginx


class Test_NginxGuiWidget:
    def test_https_base_url(self, qtbot) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            sut = _NginxGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._nginx_https_base_url.setChecked(True)

            assert app.extensions[Nginx].configuration.https is None

    def test_https_https(self, qtbot) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            sut = _NginxGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._nginx_https_https.setChecked(True)
            assert app.extensions[Nginx].configuration.https is True

    def test_https_http(self, qtbot) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            sut = _NginxGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._nginx_https_http.setChecked(True)

            assert app.extensions[Nginx].configuration.https is False

    def test_www_directory_path_enter_path(self, qtbot) -> None:
        www_directory_path = '/'
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            sut = _NginxGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            sut._nginx_www_directory_path.setText(www_directory_path)

            assert app.extensions[Nginx].configuration.www_directory_path == Path(www_directory_path)

    def test_www_directory_path_find_path(self, qtbot, mocker) -> None:
        www_directory_path = '/'
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            sut = _NginxGuiWidget(app)
            qtbot.addWidget(sut)
            sut.show()

            mocker.patch.object(QFileDialog, 'getExistingDirectory', mocker.MagicMock(return_value=www_directory_path))
            qtbot.mouseClick(sut._nginx_www_directory_path_find, Qt.MouseButton.LeftButton)

            assert app.extensions[Nginx].configuration.www_directory_path == Path(www_directory_path)
