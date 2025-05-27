"""
Provide console functionality.
"""

import argparse
import asyncio
from typing import final, Self

from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.console.command import Command, CommandFunction
from betty.console.project import add_project_argument
from betty.locale.localizable import _
from betty.plugin import ShorthandPluginBase
from betty.project import Project
from typing_extensions import override

from betty_nginx import serve


@final
class NginxServe(ShorthandPluginBase, AppDependentFactory, Command):
    """
    A command to serve a generated site with nginx in a Docker container.
    """

    _plugin_id = "nginx-serve"
    _plugin_label = _("Serve a generated site with nginx in a Docker container.")

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
        async with await serve.DockerizedNginxServer.new_for_project(project) as server:
            await server.show()
            while True:
                await asyncio.sleep(999)
