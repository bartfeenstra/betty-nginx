from json import dumps
from pathlib import Path

from betty.app import App
from betty.console import SystemExitCode
from betty.file import write
from betty.project.data import ProjectConfiguration
from betty.test_utils.console import run
from betty.test_utils.server import NoOpServer
from pytest_mock import MockerFixture

from betty_nginx.plugins.extension.nginx import Nginx


class TestNginxServe:
    async def test(
        self, isolated_app: App, mocker: MockerFixture, tmp_path: Path
    ) -> None:
        mocker.patch(
            "betty_nginx.plugins.command.nginx_serve.NginxServe._wait_forever",
            side_effect=KeyboardInterrupt,
        )
        mocker.patch("betty_nginx.serve.DockerizedNginxServer", new=NoOpServer)
        configuration_file = tmp_path / "betty.json"
        configuration = ProjectConfiguration(
            extensions=[Nginx], title="Betty", url="https://example.com"
        )
        await write(
            configuration_file, dumps(configuration.data().porter.dump(configuration))
        )
        (configuration_file.parent / "output" / "www").mkdir(parents=True)
        await run(
            isolated_app,
            "nginx-serve",
            "-p",
            str(configuration_file),
            expected_exit_code=SystemExitCode.USER_QUIT,
        )
