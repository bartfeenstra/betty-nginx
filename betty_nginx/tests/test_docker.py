import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile

import requests
from betty.asyncio import sync

from betty_nginx.docker import Container


class TestContainer:
    _DOCKERFILE = '''
FROM openresty/openresty:alpine
    '''

    _NGINX_CONFIGURATION = '''
server {
    listen 80;
    root /var/www/betty_nginx;
    error_log /nginx.log debug;
    location / {
        try_files $uri =404;
    }
}
    '''

    @sync
    async def test(self) -> None:
        content = 'Hello, and welcome to my site!'
        with TemporaryDirectory() as www_directory_path:
            os.chmod(www_directory_path, 0o755)
            content_file_path = Path(www_directory_path) / 'index.txt'
            with open(content_file_path, mode='w') as f:
                f.write(content)
            with TemporaryDirectory() as docker_directory_path:
                with open(Path(docker_directory_path) / 'Dockerfile', mode='w') as f:
                    f.write(self._DOCKERFILE)
                with NamedTemporaryFile() as nginx_configuration_file:
                    with open(nginx_configuration_file.name, mode='w') as f:
                        f.write(self._NGINX_CONFIGURATION)
                    with Container(www_directory_path, docker_directory_path, nginx_configuration_file.name) as container:
                        assert re.match(r'^\d{1,3}\.\d{1,3}.\d{1,3}.\d{1,3}$', container.ip)
                        response = requests.get(f'http://{container.ip}/index.txt')
                        assert 200 == response.status_code
                        assert content == response.content.decode('utf-8')
