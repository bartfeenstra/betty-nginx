from __future__ import annotations


from betty.locale.translation import update_extension_translations
from betty.test_utils.locale import PotFileTestBase
from typing_extensions import override

from betty_nginx import Nginx
from pathlib import Path


class TestPotFile(PotFileTestBase):
    @override
    def assets_directory_path(self) -> Path:
        return Path(__file__).parent.parent / "assets"

    @override
    def command(self) -> str:
        return "betty extension-update-translations betty-nginx ./betty_nginx"  # pragma: no cover

    @override
    async def update_translations(
        self, output_assets_directory_path_override: Path
    ) -> None:
        await update_extension_translations(
            Nginx,
            Path(__file__).parent.parent,
            _output_assets_directory_path_override=output_assets_directory_path_override,
        )
