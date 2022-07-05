from pathlib import Path

import pytest
from betty.app import App
from betty.config import ConfigurationError, DumpedConfiguration

from betty_nginx.config import NginxConfiguration


class TestNginxConfiguration:
    def test_load_without_directory_should_error(self) -> None:
        dumped_configuration = None
        sut = NginxConfiguration()
        with App():
            with pytest.raises(ConfigurationError):
                sut.load(dumped_configuration)

    def test_load_with_minimal_configuration(self) -> None:
        dumped_configuration: DumpedConfiguration = {}
        sut = NginxConfiguration()
        sut.load(dumped_configuration)

    def test_load_with_full_configuration(self) -> None:
        https = True
        www_directory_path = '/'
        dumped_configuration = {
            'https': https,
            'www_directory_path': www_directory_path,
        }
        sut = NginxConfiguration()
        sut.load(dumped_configuration)
        assert https == sut.https
        assert Path(www_directory_path) == sut.www_directory_path

    def test_load_with_https(self) -> None:
        https = True
        dumped_configuration = {
            'https': https,
        }
        sut = NginxConfiguration()
        sut.load(dumped_configuration)
        assert https == sut.https

    def test_load_with_https_invalid_should_error(self) -> None:
        dumped_configuration = {
            'https': 123,
        }
        sut = NginxConfiguration()
        with App():
            with pytest.raises(ConfigurationError):
                sut.load(dumped_configuration)

    def test_load_with_www_directory_path(self) -> None:
        www_directory_path = '/'
        dumped_configuration = {
            'www_directory_path': www_directory_path,
        }
        sut = NginxConfiguration()
        sut.load(dumped_configuration)
        assert Path(www_directory_path) == sut.www_directory_path

    def test_load_with_www_directory_path_invalid_should_error(self) -> None:
        dumped_configuration = {
            'www_directory_path': 123,
        }
        sut = NginxConfiguration()
        with App():
            with pytest.raises(ConfigurationError):
                sut.load(dumped_configuration)

    def test_dump_with_minimal_configuration(self) -> None:
        sut = NginxConfiguration()
        dumped_configuration = sut.dump()
        expected: DumpedConfiguration = {}
        assert expected == dumped_configuration

    def test_dump_with_full_configuration(self) -> None:
        sut = NginxConfiguration()
        https = True
        sut.https = https
        www_directory_path = '/'
        sut.www_directory_path = www_directory_path
        dumped_configuration = sut.dump()
        expected = {
            'https': https,
            'www_directory_path': www_directory_path,
        }
        assert expected == dumped_configuration

    def test_dump_with_https(self) -> None:
        sut = NginxConfiguration()
        https = True
        sut.https = https
        dumped_configuration = sut.dump()
        expected = {
            'https': https,
        }
        assert expected == dumped_configuration

    def test_dump_with_www_directory_path(self) -> None:
        sut = NginxConfiguration()
        www_directory_path = '/'
        sut.www_directory_path = www_directory_path
        dumped_configuration = sut.dump()
        expected = {
            'www_directory_path': www_directory_path,
        }
        assert expected == dumped_configuration

    def test_https(self) -> None:
        sut = NginxConfiguration()
        assert sut.https is None
        sut.https = True
        assert sut.https is True
        del sut.https
        assert sut.https is None

    def test_www_directory_path(self) -> None:
        sut = NginxConfiguration()
        assert sut.www_directory_path is None
        www_directory_path = '/'
        sut.www_directory_path = www_directory_path
        assert Path(www_directory_path) == sut.www_directory_path
        del sut.www_directory_path
        assert sut.www_directory_path is None
