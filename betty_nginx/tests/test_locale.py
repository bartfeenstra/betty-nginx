import difflib
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from betty_nginx import ROOT_DIRECTORY_PATH


class TestPotFile:
    def _readlines(self, directory_path: Path) -> Iterator[str]:
        with open(directory_path / 'betty_nginx' / 'assets' / 'betty_nginx.pot') as f:
            return filter(
                lambda line: not line.startswith((
                    '"POT-Creation-Date: ',
                    '"PO-Revision-Date: ',
                )),
                f.readlines(),
            )

    def test(self) -> None:
        with TemporaryDirectory() as working_directory_path:
            shutil.copytree(ROOT_DIRECTORY_PATH, working_directory_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns(
                '*.git',
                '.*_cache',
                '.tox',
                'build',
                'dist',
            ))
            subprocess.check_call(
                (
                    'bash',
                    Path() / 'bin' / 'extract-translatables',
                ),
                cwd=working_directory_path,
                stderr=subprocess.DEVNULL,
            )
            actual_pot_contents = self._readlines(ROOT_DIRECTORY_PATH)
            expected_pot_contents = self._readlines(Path(working_directory_path))
            diff = difflib.unified_diff(
                list(actual_pot_contents),
                list(expected_pot_contents),
            )
            assert 0 == len(list(diff)), f'The gettext *.po files are not up to date. Did you run {Path() / "bin" / "extract-translatables"}?'
