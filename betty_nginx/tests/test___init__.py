from betty.app import App
from betty.project import Project
from betty.project.extension import Extension
from betty.project.generate import generate
from betty.test_utils.project.extension import (
    ExtensionTestBase,
    ExtensionDefinitionTestBase,
)
from typing_extensions import override

from betty_nginx import Nginx
import pytest
from betty.plugin import PluginDefinition


class TestNginxDefinition(ExtensionDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Nginx.plugin


class TestNginx(ExtensionTestBase):
    @override
    @pytest.fixture
    async def sut(self, new_temporary_app: App) -> Extension:
        async with Project.new_temporary(new_temporary_app) as project, project:
            return await Nginx.new_for_project(project)

    async def test_generate(self, new_temporary_app: App):
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.url = "http://example.com"
            project.configuration.extensions.enable(Nginx)
            async with project:
                await generate(project)
                assert (
                    project.configuration.output_directory_path / "nginx" / "nginx.conf"
                ).exists()
                assert (
                    project.configuration.output_directory_path
                    / "nginx"
                    / "content_negotiation.lua"
                ).exists()
                assert (
                    project.configuration.output_directory_path / "nginx" / "Dockerfile"
                ).exists()
