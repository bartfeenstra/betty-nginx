"""
The nginx-generate command.
"""

import argparse
from typing import Self, final, override

from betty.app import App
from betty.console import CommandDefinition, CommandFunction
from betty.console.command import Command
from betty.console.project import add_project_argument
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.project import Project

from betty_nginx.plugins.extension.nginx import Nginx


@final
@CommandDefinition("nginx-generate", label=_("Generate nginx configuration"))
class NginxGenerate(Manufacturable, Command):
    """
    Generate nginx configuration.
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
        return await add_project_argument(parser, self._command_function, self._app)

    async def _command_function(self, project: Project) -> None:
        async with project:
            await (await project.extensions[Nginx]).generate_artifacts()
