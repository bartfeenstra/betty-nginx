"""Integrates Nginx for Betty with Python's setuptools."""

from glob import glob
from pathlib import Path
from setuptools import setup, find_packages

from betty_nginx import ROOT_DIRECTORY_PATH

with open(ROOT_DIRECTORY_PATH / 'VERSION', encoding='utf-8') as f:
    VERSION = f.read()

with open(ROOT_DIRECTORY_PATH / 'README.md', encoding='utf-8') as f:
    long_description = f.read()

SETUP = {
    'name': 'betty-nginx',
    'description': 'Nginx for Betty lets you run your Betty sites using nginx and Docker.',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'version': VERSION,
    'license': 'GPLv3',
    'author': 'Bart Feenstra & contributors',
    'author_email': 'bart@mynameisbart.com',
    'url': 'https://github.com/bartfeenstra/betty-nginx',
    'classifiers': [
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: POSIX :: Linux',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'Topic :: Sociology :: Genealogy',
        'Topic :: Software Development :: Code Generators',
    ],
    'python_requires': '~= 3.8',
    'install_requires': [
        'betty ~= 0.3.0',
        'docker ~= 5.0.3',
        'PyQt6 ~= 6.3.0',
        'reactives ~= 0.4.2',
        'typing_extensions ~= 4.2.0; python_version < "3.10"',
    ],
    'extras_require': {
        'development': [
            'autopep8 ~= 1.6.0',
            'codecov ~= 2.1.12',
            'coverage ~= 6.3',
            'flake8 ~= 4.0.1',
            'html5lib ~= 1.1',
            'jsonschema ~= 4.4.0',
            'mypy ~= 0.950',
            'pytest ~= 7.1.1',
            'pytest-cov ~= 3.0.0',
            'pytest-mock ~= 3.7.0',
            'pytest-qt ~= 4.0.2',
            'pytest-xvfb ~= 2.0.0',
        ],
    },
    'entry_points': {
        'betty.extensions': [
            'betty_nginx.nginx.Nginx=betty_nginx.nginx.Nginx',
        ],
    },
    'packages': find_packages(),
    'data_files': [
        ('', [
            'LICENSE.txt',
            'README.md',
            'VERSION',
        ])
    ],
    'include_package_data': True,
    'package_data': {
        'betty_nginx': [
            *list(map(str, [
                data_path
                for data_path
                in [
                    ROOT_DIRECTORY_PATH / 'VERSION',
                    *map(Path, glob(str(ROOT_DIRECTORY_PATH / 'betty_nginx' / 'assets' / '**'), recursive=True)),
                ]
                if data_path.is_file()
            ])),
            str(ROOT_DIRECTORY_PATH / 'betty' / 'py.typed'),
        ],
    },
}

if __name__ == '__main__':
    setup(**SETUP)
