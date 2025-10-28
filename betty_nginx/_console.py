"""
Provide console functionality.
"""

import argparse
import asyncio
from typing import final, Self

from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.console.command import Command, CommandFunction, CommandDefinition
from betty.console.project import add_project_argument
from betty.locale.localizable import _
from betty.project import Project
from typing_extensions import override

from betty_nginx import serve, Nginx
from betty_nginx.docker import Environment


@final
@CommandDefinition(
    id="nginx-generate",
    label=_("Generate nginx configuration"),
)
class NginxGenerate(AppDependentFactory, Command):
    """
    Generate nginx configuration.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        return await add_project_argument(parser, self._command_function, self._app)

    async def _command_function(self, project: Project) -> None:
        async with project:
            extensions = await project.extensions
            await extensions[Nginx].generate_artifacts()


@final
@CommandDefinition(
    id="nginx-serve",
    label=_("Serve a generated site with nginx in a Docker container."),
)
class NginxServe(AppDependentFactory, Command):
    """
    A command to serve a generated site with nginx in a Docker container.
    """

    def __init__(self, app: App):
        self._app = app

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(app)

    @override
    async def configure(self, parser: argparse.ArgumentParser) -> CommandFunction:
        localizer = await self._app.localizer
        command_function = await add_project_argument(
            parser, self._command_function, self._app
        )
        environment_group = parser.add_mutually_exclusive_group()
        environment_group.add_argument(
            "--local",
            dest="environment",
            action="store_const",
            const=Environment.LOCAL,
            help=localizer._(
                "Whether to generate configuration for a local environment. This disables HTTPS, for example."
            ),
        )
        environment_group.add_argument(
            "--public",
            dest="_verbosity",
            action="store_const",
            const=Environment.PUBLIC,
            help=localizer._(
                "Whether to generate configuration for a public hosting environment."
            ),
        )
        return command_function

    async def _command_function(
        self, environment: Environment, project: Project
    ) -> None:
        async with (
            project,
            serve.DockerizedNginxServer(project, environment=environment) as server,
        ):
            await server.show()
            while True:
                await asyncio.sleep(999)
