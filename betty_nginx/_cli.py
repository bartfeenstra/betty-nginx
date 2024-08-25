"""
Provide Command Line Interface functionality.
"""

import asyncio

from betty.cli.commands import command, pass_project
from betty.project import Project
from betty.typing import internal

from betty_nginx import serve


@internal
@command(help="Serve a generated site with nginx in a Docker container.")
@pass_project
async def nginx_serve(project: Project) -> None:
    async with serve.DockerizedNginxServer(project) as server:
        await server.show()
        while True:
            await asyncio.sleep(999)
