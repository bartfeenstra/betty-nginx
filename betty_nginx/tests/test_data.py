import pytest
from betty.exception import HumanFacingException

from betty_nginx.data import NginxConfiguration


class TestNginxConfiguration:
    async def test_load__minimal(self) -> None:
        NginxConfiguration.data().porter.load({})

    async def test_load__without_dict_should_error(self) -> None:
        with pytest.raises(HumanFacingException):
            NginxConfiguration.data().porter.load(None)

    @pytest.mark.parametrize(
        "https",
        [
            None,
            True,
            False,
        ],
    )
    async def test_load__with_https(self, https: bool | None) -> None:
        sut = NginxConfiguration.data().porter.load({
            "https": https,
        })
        assert sut.https == https

    async def test_load__with_legacy_entity_redirects(self) -> None:
        sut = NginxConfiguration.data().porter.load({
            "legacy_entity_redirects": True,
        })
        assert sut.legacy_entity_redirects

    async def test_load__with_www_directory(self) -> None:
        www_directory = "/var/www"
        sut = NginxConfiguration.data().porter.load({
            "www_directory": www_directory,
        })
        assert sut.www_directory == www_directory

    async def test_dump__minimal(self) -> None:
        sut = NginxConfiguration()
        assert sut.data().porter.dump(sut) == {}

    async def test_dump__with_https(self) -> None:
        sut = NginxConfiguration(https=True)
        assert sut.data().porter.dump(sut) == {
            "https": True,
        }

    async def test_dump__with_legacy_entity_redirects(self) -> None:
        sut = NginxConfiguration(legacy_entity_redirects=True)
        assert sut.data().porter.dump(sut) == {
            "legacy_entity_redirects": True,
        }

    async def test_dump__with_www_directory(self) -> None:
        www_directory = "/var/www"
        sut = NginxConfiguration(www_directory=www_directory)
        assert sut.data().porter.dump(sut) == {
            "www_directory": www_directory,
        }
