from json import dumps
from pathlib import Path

from betty.app import App
from betty.file import write
from betty.project import ProjectData
from betty.test_utils.console import run

from betty_nginx.service_providers.nginx import Nginx


class TestNginxGenerate:
    async def test(self, isolated_app: App, tmp_path: Path) -> None:
        configuration_file = tmp_path / "betty.json"
        configuration = ProjectData(
            service_providers=[Nginx], title="Betty", url="https://example.com"
        )
        await write(
            configuration_file,
            dumps(configuration.definition().porter.dump(configuration)),
        )
        await run(
            isolated_app,
            "nginx-generate",
            "-p",
            str(configuration_file),
        )
        assert (configuration_file.parent / "output" / "nginx").exists()
