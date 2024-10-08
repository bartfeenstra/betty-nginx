"""
Provide Command Line Interface functionality.
"""

import asyncio
from typing import final, Self

import asyncclick as click
from betty.app import App
from betty.app.factory import AppDependentFactory
from betty.cli.commands import command, project_option, Command
from betty.locale.localizable import _
from betty.locale.localizer import Localizer
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

    def __init__(self, localizer: Localizer):
        self._localizer = localizer

    @override
    @classmethod
    async def new_for_app(cls, app: App) -> Self:
        return cls(await app.localizer)

    @override
    async def click_command(self) -> click.Command:
        description = self.plugin_description()

        @command(
            self.plugin_id(),
            short_help=self.plugin_label().localize(self._localizer),
            help=description.localize(self._localizer)
            if description
            else self.plugin_label().localize(self._localizer),
        )
        @project_option
        async def nginx_serve(project: Project) -> None:
            async with await serve.DockerizedNginxServer.new_for_project(
                project
            ) as server:
                await server.show()
                while True:
                    await asyncio.sleep(999)

        return nginx_serve
