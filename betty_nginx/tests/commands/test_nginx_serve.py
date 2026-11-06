from json import dumps
from pathlib import Path

from betty.app import App
from betty.file import write
from betty.project import ProjectData
from betty.servers.no_op import NoOpServer
from betty.sys import ExitCode
from betty.test_utils.console import run
from pytest_mock import MockerFixture

from betty_nginx.service_providers.nginx import Nginx


class TestNginxServe:
    async def test(
        self, isolated_app: App, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty_nginx.commands.nginx_serve.NginxServe._wait_forever",
            side_effect=KeyboardInterrupt,
        )
        mocker.patch("betty_nginx.servers.dockerized.DockerizedServer", new=NoOpServer)
        configuration_file = tmp_path / "betty.json"
        configuration = ProjectData(
            service_providers=[Nginx], title="Betty", url="https://example.com"
        )
        await write(
            configuration_file,
            dumps(configuration.definition().porter.dump(configuration)),
        )
        (configuration_file.parent / "output" / "www").mkdir(parents=True)
        await run(
            isolated_app,
            "nginx-serve",
            "-p",
            str(configuration_file),
            expected_exit_code=ExitCode.USER_QUIT,
        )
