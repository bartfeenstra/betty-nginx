"""
The nginx-serve command.
"""

import argparse
import asyncio
from typing import Self, final, override

from betty.app import App
from betty.commands.project import add_project_argument
from betty.console import Command, CommandDefinition, CommandFunction
from betty.factory import Manufacturable
from betty.localizables.gettext import _
from betty.project import Project

from betty_nginx.docker import Environment
from betty_nginx.servers import dockerized


@final
@CommandDefinition(
    "nginx-serve", label=_("Serve a generated site with nginx in a Docker container.")
)
class NginxServe(Manufacturable, Command):
    """
    A command to serve a generated site with nginx in a Docker container.
    """

    def __init__(self, app: App, /):
        self._app = app

    @override
    @App.require
    @classmethod
    async def new(cls, app: App, /) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        command_function = await add_project_argument(
            parser, self._command_function, self._app
        )
        environment_group = parser.add_mutually_exclusive_group()
        environment_group.add_argument(
            "--local",
            dest="environment",
            action="store_const",
            const=Environment.LOCAL,
            help=self._app.ui.localizer.translate._(
                "Generate configuration for a local environment. This disables HTTPS, for example."
            ),
        )
        environment_group.add_argument(
            "--public",
            dest="environment",
            action="store_const",
            const=Environment.PUBLIC,
            help=self._app.ui.localizer.translate._(
                "Generate configuration for a public hosting environment."
            ),
        )
        return command_function

    async def _command_function(
        self, environment: Environment, project: Project
    ) -> None:
        async with (
            project,
            dockerized.DockerizedServer(project, environment=environment) as server,
        ):
            await server.show()
            await self._wait_forever()

    async def _wait_forever(self) -> None:
        while True:
            await asyncio.sleep(999)
