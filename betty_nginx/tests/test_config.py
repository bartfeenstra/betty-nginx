from pathlib import Path
from typing import Any, TYPE_CHECKING

import pytest
from betty.assertion.error import AssertionFailed
from betty.test_utils.assertion.error import raises_error

from betty_nginx.config import NginxConfiguration

if TYPE_CHECKING:
    from collections.abc import Mapping
    from betty.serde.dump import Dump


class TestNginxConfiguration:
    async def test_load_with_minimal_configuration(self) -> None:
        dump: Mapping[str, Any] = {}
        NginxConfiguration().load(dump)

    async def test_load_without_dict_should_error(self) -> None:
        dump = None
        with raises_error(error_type=AssertionFailed):
            NginxConfiguration().load(dump)

    @pytest.mark.parametrize(
        "https",
        [
            None,
            True,
            False,
        ],
    )
    async def test_load_with_https(self, https: bool | None) -> None:
        dump: Dump = {
            "https": https,
        }
        sut = NginxConfiguration()
        sut.load(dump)
        assert sut.https == https

    @pytest.mark.parametrize(
        "www_directory",
        [
            None,
            "/var/www",
        ],
    )
    async def test_load_with_www_directory(self, www_directory: str | None) -> None:
        dump: Dump = {
            "www_directory": www_directory,
        }
        sut = NginxConfiguration()
        sut.load(dump)
        assert sut.www_directory_path == www_directory

    async def test_dump_with_minimal_configuration(self) -> None:
        sut = NginxConfiguration()
        expected = {
            "https": None,
            "www_directory": None,
        }
        assert sut.dump() == expected

    async def test_dump_with_www_directory_path(self, tmp_path: Path) -> None:
        www_directory_path = str(tmp_path)
        sut = NginxConfiguration()
        sut.www_directory_path = www_directory_path
        expected = {
            "https": None,
            "www_directory": www_directory_path,
        }
        assert sut.dump() == expected
