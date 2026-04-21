"""
Nginx jobs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.job import Job

if TYPE_CHECKING:
    from betty.job.scheduler import Scheduler

    from betty_nginx.plugins.extension.nginx import Nginx


@final
class GenerateArtifacts(Job):
    """
    Generate the artifacts.
    """

    def __init__(self, nginx: Nginx, /):
        super().__init__(self.id_for(), priority=True)
        self._nginx = nginx

    @classmethod
    def id_for(cls) -> str:
        """
        Get the job ID.
        """
        return "betty-nginx-generate-artifacts"

    @override
    async def do(self, scheduler: Scheduler, /) -> None:
        await self._nginx.generate_artifacts()
