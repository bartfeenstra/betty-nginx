from typing import Any, TYPE_CHECKING

import pytest
from betty.exception import UserFacingException
from betty.test_utils.exception import raises_error

from betty_nginx.config import NginxConfiguration

if TYPE_CHECKING:
    from collections.abc import Mapping
    from betty.serde.dump import Dump


class TestNginxConfiguration:
    async def test_load__minimal(self) -> None:
        dump: Mapping[str, Any] = {}
        NginxConfiguration().load(dump)

    async def test_load__without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=UserFacingException):
            NginxConfiguration().load(dump)

    @pytest.mark.parametrize(
        "https",
        [
            None,
            True,
            False,
        ],
    )
    async def test_load__with_https(self, https: bool | None) -> None:
        dump: Dump = {
            "https": https,
        }
        sut = NginxConfiguration()
        sut.load(dump)
        assert sut.https == https

    async def test_load__with_legacy_entity_redirects(self) -> None:
        dump: Dump = {
            "legacy_entity_redirects": True,
        }
        sut = NginxConfiguration()
        sut.load(dump)
        assert sut.legacy_entity_redirects

    async def test_load__with_www_directory(self) -> None:
        www_directory = "/var/www"
        dump: Dump = {
            "www_directory": www_directory,
        }
        sut = NginxConfiguration()
        sut.load(dump)
        assert sut.www_directory_path == www_directory

    async def test_dump__minimal(self) -> None:
        sut = NginxConfiguration()
        expected = {
            "https": None,
        }
        assert sut.dump() == expected

    async def test_dump__with_legacy_entity_redirects(self) -> None:
        sut = NginxConfiguration()
        sut.legacy_entity_redirects = True
        expected = {
            "https": None,
            "legacy_entity_redirects": True,
        }
        assert sut.dump() == expected

    async def test_dump__with_www_directory(self) -> None:
        www_directory_path = "/var/www"
        sut = NginxConfiguration()
        sut.www_directory_path = www_directory_path
        expected = {
            "https": None,
            "www_directory": www_directory_path,
        }
        assert sut.dump() == expected
