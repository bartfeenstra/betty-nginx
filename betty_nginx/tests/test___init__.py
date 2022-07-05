import re
import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication, QWidget
from betty.app import App
from betty.asyncio import sync
from betty.generate import generate
from betty.project import LocaleConfiguration, ProjectExtensionConfiguration

from betty_nginx.config import NginxConfiguration
from betty_nginx.nginx import Nginx
from betty_nginx.serve import DockerizedNginxServer


class TestNginx:
    _LEADING_WHITESPACE_PATTERN = re.compile(r'^\s*(.*?)$')

    def test_servers_with_docker(self) -> None:
        with App() as app:
            sut = Nginx(app)
            servers = list(sut.servers)
            assert 1 == len(servers)
            assert isinstance(servers[0], DockerizedNginxServer)

    def test_servers_without_docker(self) -> None:
        original_is_available = DockerizedNginxServer.is_available
        DockerizedNginxServer.is_available = lambda: False  # type: ignore
        try:
            with App() as app:
                sut = Nginx(app)
                assert [] == sut.servers
        finally:
            DockerizedNginxServer.is_available = original_is_available  # type: ignore

    def _normalize_nginx_configuration(self, configuration: str) -> str:
        return '\n'.join(filter(None, map(self._normalize_nginx_configuration_line, configuration.splitlines())))

    def _normalize_nginx_configuration_line(self, line: str) -> Optional[str]:
        match = self._LEADING_WHITESPACE_PATTERN.fullmatch(line)
        if match is None:
            return None
        return match.group(1)

    @sync
    async def test_generate_config(self) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            await generate(app)
            with open(app.project.configuration.output_directory_path / 'nginx' / 'nginx.conf') as f:
                actual = f.read()
            expected = r'''
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;
    server_name example.com;
    root %s;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set $media_type_extension html;
    index index.$media_type_extension;

    location / {
        # Handle HTTP error responses.
        error_page 401 /.error/401.$media_type_extension;
        error_page 403 /.error/403.$media_type_extension;
        error_page 404 /.error/404.$media_type_extension;
        location /.error {
            internal;
        }

        try_files $uri $uri/ =404;
    }
}
''' % app.project.configuration.www_directory_path
        assert self._normalize_nginx_configuration(expected) == self._normalize_nginx_configuration(actual)

    @sync
    async def test_generate_config_with_clean_urls(self) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            app.project.configuration.clean_urls = True
            await generate(app)
            with open(app.project.configuration.output_directory_path / 'nginx' / 'nginx.conf') as f:
                actual = f.read()
            expected = r'''
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;
    server_name example.com;
    root %s;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set $media_type_extension html;
    index index.$media_type_extension;

    location / {
        # Handle HTTP error responses.
        error_page 401 /.error/401.$media_type_extension;
        error_page 403 /.error/403.$media_type_extension;
        error_page 404 /.error/404.$media_type_extension;
        location /.error {
            internal;
        }

        try_files $uri $uri/ =404;
    }
}
''' % app.project.configuration.www_directory_path
        assert self._normalize_nginx_configuration(expected) == self._normalize_nginx_configuration(actual)

    @sync
    async def test_generate_config_multilingual(self) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            app.project.configuration.locales.replace([
                LocaleConfiguration('en-US', 'en'),
                LocaleConfiguration('nl-NL', 'nl'),
            ])
            await generate(app)
            with open(app.project.configuration.output_directory_path / 'nginx' / 'nginx.conf') as f:
                actual = f.read()
            expected = r'''
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;
    server_name example.com;
    root %s;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set $media_type_extension html;
    index index.$media_type_extension;

    location ~ ^/(en|nl)(/|$) {
        set $locale $1;

        add_header Content-Language "$locale" always;

        # Handle HTTP error responses.
        error_page 401 /$locale/.error/401.$media_type_extension;
        error_page 403 /$locale/.error/403.$media_type_extension;
        error_page 404 /$locale/.error/404.$media_type_extension;
        location ~ ^/$locale/\.error {
            internal;
        }

        try_files $uri $uri/ =404;
    }
    location @localized_redirect {
        set $locale_alias en;
        return 301 /$locale_alias$uri;
    }
    location / {
        try_files $uri @localized_redirect;
    }
}
''' % app.project.configuration.www_directory_path
        assert self._normalize_nginx_configuration(expected) == self._normalize_nginx_configuration(actual)

    @sync
    async def test_generate_config_multilingual_with_content_negotiation(self) -> None:
        with App() as app:
            app.project.configuration.content_negotiation = True
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            app.project.configuration.locales.replace([
                LocaleConfiguration('en-US', 'en'),
                LocaleConfiguration('nl-NL', 'nl'),
            ])
            await generate(app)
            with open(app.project.configuration.output_directory_path / 'nginx' / 'nginx.conf') as f:
                actual = f.read()
            expected = r'''
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;
    server_name example.com;
    root %s;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set_by_lua_block $media_type_extension {
        local available_media_types = {'text/html', 'application/json'}
        local media_type_extensions = {}
        media_type_extensions['text/html'] = 'html'
        media_type_extensions['application/json'] = 'json'
        local media_type = require('cone').negotiate(ngx.req.get_headers()['Accept'], available_media_types)
        return media_type_extensions[media_type]
    }
    index index.$media_type_extension;

    location ~ ^/(en|nl)(/|$) {
        set $locale $1;

        add_header Content-Language "$locale" always;

        # Handle HTTP error responses.
        error_page 401 /$locale/.error/401.$media_type_extension;
        error_page 403 /$locale/.error/403.$media_type_extension;
        error_page 404 /$locale/.error/404.$media_type_extension;
        location ~ ^/$locale/\.error {
            internal;
        }

        try_files $uri $uri/ =404;
    }
    location @localized_redirect {
        set_by_lua_block $locale_alias {
            local available_locales = {'en-US', 'nl-NL'}
            local locale_aliases = {}
            locale_aliases['en-US'] = 'en'
            locale_aliases['nl-NL'] = 'nl'
            local locale = require('cone').negotiate(ngx.req.get_headers()['Accept-Language'], available_locales)
            return locale_aliases[locale]
        }
        return 301 /$locale_alias$uri;
    }
    location / {
        try_files $uri @localized_redirect;
    }
}
''' % app.project.configuration.www_directory_path
        assert self._normalize_nginx_configuration(expected) == self._normalize_nginx_configuration(actual)

    @sync
    async def test_generate_config_with_content_negotiation(self) -> None:
        with App() as app:
            app.project.configuration.content_negotiation = True
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            await generate(app)
            with open(app.project.configuration.output_directory_path / 'nginx' / 'nginx.conf') as f:
                actual = f.read()
            expected = r'''
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;
    server_name example.com;
    root %s;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set_by_lua_block $media_type_extension {
        local available_media_types = {'text/html', 'application/json'}
        local media_type_extensions = {}
        media_type_extensions['text/html'] = 'html'
        media_type_extensions['application/json'] = 'json'
        local media_type = require('cone').negotiate(ngx.req.get_headers()['Accept'], available_media_types)
        return media_type_extensions[media_type]
    }
    index index.$media_type_extension;

    location / {
        # Handle HTTP error responses.
        error_page 401 /.error/401.$media_type_extension;
        error_page 403 /.error/403.$media_type_extension;
        error_page 404 /.error/404.$media_type_extension;
        location /.error {
            internal;
        }

        try_files $uri $uri/ =404;
    }
}''' % app.project.configuration.www_directory_path
        assert self._normalize_nginx_configuration(expected) == self._normalize_nginx_configuration(actual)

    @sync
    async def test_generate_config_with_https(self) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(
                Nginx,
                extension_configuration=NginxConfiguration(https=True),
            ))
            await generate(app)
            with open(app.project.configuration.output_directory_path / 'nginx' / 'nginx.conf') as f:
                actual = f.read()
            expected = r'''
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;
    server_name example.com;
    root %s;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set $media_type_extension html;
    index index.$media_type_extension;

    location / {
        # Handle HTTP error responses.
        error_page 401 /.error/401.$media_type_extension;
        error_page 403 /.error/403.$media_type_extension;
        error_page 404 /.error/404.$media_type_extension;
        location /.error {
            internal;
    }

    try_files $uri $uri/ =404;
    }
}
''' % app.project.configuration.www_directory_path
        assert self._normalize_nginx_configuration(expected) == self._normalize_nginx_configuration(actual)

    @sync
    async def test_generate_config_without_https(self) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(
                Nginx,
                extension_configuration=NginxConfiguration(https=False),
            ))
            await generate(app)
            with open(app.project.configuration.output_directory_path / 'nginx' / 'nginx.conf') as f:
                actual = f.read()
            expected = r'''
server {
    listen 80;
    server_name example.com;
    root %s;
    add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set $media_type_extension html;
    index index.$media_type_extension;

    location / {
        # Handle HTTP error responses.
        error_page 401 /.error/401.$media_type_extension;
        error_page 403 /.error/403.$media_type_extension;
        error_page 404 /.error/404.$media_type_extension;
        location /.error {
            internal;
    }

    try_files $uri $uri/ =404;
    }
}
''' % app.project.configuration.www_directory_path
        assert self._normalize_nginx_configuration(expected) == self._normalize_nginx_configuration(actual)

    @sync
    async def test_generate_config_with_overridden_www_directory_path(self) -> None:
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx, True, NginxConfiguration(
                www_directory_path='/tmp/overridden-www',
            )))
            await generate(app)
            with open(app.project.configuration.output_directory_path / 'nginx' / 'nginx.conf') as f:
                actual = f.read()
            expected_root_path = '\\tmp\\overridden-www' if sys.platform == 'win32' else '/tmp/overridden-www'
            expected = r'''
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;
    server_name example.com;
    root %s;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Cache-Control "max-age=86400";
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set $media_type_extension html;
    index index.$media_type_extension;

    location / {
        # Handle HTTP error responses.
        error_page 401 /.error/401.$media_type_extension;
        error_page 403 /.error/403.$media_type_extension;
        error_page 404 /.error/404.$media_type_extension;
        location /.error {
            internal;
    }

    try_files $uri $uri/ =404;
    }
}
    ''' % expected_root_path
        assert self._normalize_nginx_configuration(expected) == self._normalize_nginx_configuration(actual)

    def test_label(self) -> None:
        assert 0 != len(Nginx.label())

    def test_gui_description(self) -> None:
        with App():
            assert 0 != len(Nginx.gui_description())

    def test_gui_build(self) -> None:
        __ = QApplication([])  # noqa: F841
        with App() as app:
            app.project.configuration.extensions.add(ProjectExtensionConfiguration(Nginx))
            sut = Nginx(app)
            assert isinstance(sut.gui_build(), QWidget)
