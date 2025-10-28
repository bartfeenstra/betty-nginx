from aiofiles.os import makedirs
from betty.app import App
from betty.config.file import write_configuration_file
from betty.console import SystemExitCode
from betty.project import Project
from betty.test_utils.console import run
from betty.test_utils.serve import NoOpServer
from pytest_mock import MockerFixture

from betty_nginx import Nginx


class TestServe:
    async def test(self, mocker: MockerFixture, temporary_app: App) -> None:
        mocker.patch("asyncio.sleep", side_effect=KeyboardInterrupt)
        mocker.patch("betty_nginx.serve.DockerizedNginxServer", new=NoOpServer)
        async with Project.new_temporary(temporary_app) as project:
            project.configuration.extensions.enable(Nginx)
            await write_configuration_file(
                project.configuration, project.configuration.configuration_file_path
            )
            await makedirs(project.configuration.www_directory_path)
            async with project:
                await run(
                    temporary_app,
                    "nginx-serve",
                    "-p",
                    str(project.configuration.configuration_file_path),
                    expected_exit_code=SystemExitCode.USER_QUIT,
                )
