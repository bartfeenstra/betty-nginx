import re

from betty.extension import ExtensionManufacturer
from betty.project import Project, ProjectLocale
from betty.project.generate import generate
from betty.test_utils.conftest import IsolatedProjectFactory

from betty_nginx.data import NginxConfiguration
from betty_nginx.plugins.extension.nginx import Nginx


class TestNginx:
    async def test_generate(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(extensions=[Nginx]) as project:
            await generate(project)
            assert (project.output_directory / "nginx").exists()

    _LEADING_WHITESPACE_PATTERN = re.compile(r"^\s*(.*?)$")

    def _normalize_configuration(self, configuration: str) -> str:
        return "\n".join(
            filter(
                None,
                map(self._normalize_configuration_line, configuration.splitlines()),
            )
        )

    def _normalize_configuration_line(self, line: str) -> str | None:
        match = self._LEADING_WHITESPACE_PATTERN.fullmatch(line)
        if match is None:
            return None
        return match.group(1)

    async def _assert_configuration_equals(
        self, expected: str, project: Project
    ) -> None:
        await (await project.extensions[Nginx]).generate_artifacts()
        with open(
            project.output_directory / "nginx" / "nginx.conf", encoding="utf-8"
        ) as f:
            actual = f.read()
        assert self._normalize_configuration(expected) == self._normalize_configuration(
            actual
        )

    async def test_generate_artifacts__nginx_configuration(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            extensions=[Nginx],
            url="http://example.com",
        ) as project:
            expected = rf"""
server {{
    add_header Vary Accept-Language;
    add_header Cache-Control "max-age=86400";
    listen 80;
    server_name example.com;
    root {project.www_directory};
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set $media_type_extension html;
    index index.$media_type_extension;

    location / {{
        # Handle HTTP error responses.
        error_page 401 /.error/401.$media_type_extension;
        error_page 403 /.error/403.$media_type_extension;
        error_page 404 /.error/404.$media_type_extension;
        location /.error {{
            internal;
        }}

        try_files $uri $uri/ =404;
    }}
}}
"""
            await self._assert_configuration_equals(expected, project)

    async def test_generate_artifacts__nginx_configuration_multilingual(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            extensions=[Nginx],
            locales=[
                ProjectLocale(
                    "en-US",
                    alias="en",
                ),
                ProjectLocale(
                    "nl-NL",
                    alias="nl",
                ),
            ],
            url="http://example.com",
        ) as project:
            expected = rf"""
server {{
    add_header Vary Accept-Language;
    add_header Cache-Control "max-age=86400";
    listen 80;
    server_name example.com;
    root {project.www_directory};
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set $media_type_extension html;
    index index.$media_type_extension;

    location @localized_redirect {{
        set $locale_alias en;
        return 301 /$locale_alias$uri;
    }}


    # The front page.
    location = / {{
        # nginx does not support redirecting to named locations, so we use try_files with an empty first
        # argument and assume that never matches a real file.
        try_files '' @localized_redirect;
    }}

    # Localized resources.
    location ~* ^/(en|nl)(/|$) {{
        set $locale $1;
        add_header Vary Accept-Language;
        add_header Cache-Control "max-age=86400";
        add_header Content-Language "$locale" always;

        # Handle HTTP error responses.
        error_page 401 /$locale/.error/401.$media_type_extension;
        error_page 403 /$locale/.error/403.$media_type_extension;
        error_page 404 /$locale/.error/404.$media_type_extension;
        location ~ ^/$locale/\.error {{
            internal;
        }}

        try_files $uri $uri/ =404;
    }}

    # Static resources.
    location / {{
        # Handle HTTP error responses.
        error_page 401 /en/.error/401.$media_type_extension;
        error_page 403 /en/.error/403.$media_type_extension;
        error_page 404 /en/.error/404.$media_type_extension;
        location ~ ^/en/\.error {{
            internal;
        }}
        try_files $uri $uri/ =404;
    }}
}}
"""
            await self._assert_configuration_equals(expected, project)

    async def test_generate_artifacts__nginx_configuration_multilingual_with_clean_urls(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            clean_urls=True,
            extensions=[Nginx],
            locales=[
                ProjectLocale(
                    "en-US",
                    alias="en",
                ),
                ProjectLocale(
                    "nl-NL",
                    alias="nl",
                ),
            ],
            url="http://example.com",
        ) as project:
            expected = rf"""
server {{
    add_header Vary Accept-Language;
    add_header Cache-Control "max-age=86400";
    listen 80;
    server_name example.com;
    root {project.www_directory};
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set_by_lua_block $media_type_extension {{
        local available_media_types = {{'text/html', 'application/json'}}
        local media_type_extensions = {{}}
        media_type_extensions['text/html'] = 'html'
        media_type_extensions['application/json'] = 'json'
        local media_type = require('content_negotiation').negotiate(ngx.req.get_headers()['Accept'], available_media_types)
        return media_type_extensions[media_type]
    }}
    index index.$media_type_extension;
    location @localized_redirect {{
        set_by_lua_block $locale_alias {{
            local available_locales = {{'en-US', 'nl-NL'}}
            local locale_aliases = {{}}
            locale_aliases['en-US'] = 'en'
            locale_aliases['nl-NL'] = 'nl'
            local locale = require('content_negotiation').negotiate(ngx.req.get_headers()['Accept-Language'], available_locales)
            return locale_aliases[locale]
        }}
        add_header Vary Accept-Language;
        add_header Cache-Control "max-age=86400";
        add_header Content-Language "$locale_alias" always;

        return 307 /$locale_alias$uri;
    }}

    # The front page.
    location = / {{
        # nginx does not support redirecting to named locations, so we use try_files with an empty first
        # argument and assume that never matches a real file.
        try_files '' @localized_redirect;
    }}

    # Localized resources.
    location ~* ^/(en|nl)(/|$) {{
        set $locale $1;
        add_header Vary Accept-Language;
        add_header Cache-Control "max-age=86400";
        add_header Content-Language "$locale" always;

        # Handle HTTP error responses.
        error_page 401 /$locale/.error/401.$media_type_extension;
        error_page 403 /$locale/.error/403.$media_type_extension;
        error_page 404 /$locale/.error/404.$media_type_extension;
        location ~ ^/$locale/\.error {{
            internal;
        }}

        try_files $uri $uri/ =404;
    }}

    # Static resources.
    location / {{
        # Handle HTTP error responses.
        error_page 401 /en/.error/401.$media_type_extension;
        error_page 403 /en/.error/403.$media_type_extension;
        error_page 404 /en/.error/404.$media_type_extension;
        location ~ ^/en/\.error {{
            internal;
        }}
        try_files $uri $uri/ =404;
    }}
}}
"""
            await self._assert_configuration_equals(expected, project)

    async def test_generate_artifacts__nginx_configuration_with_clean_urls(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            clean_urls=True,
            extensions=[Nginx],
            url="http://example.com",
        ) as project:
            expected = rf"""
server {{
    add_header Vary Accept-Language;
    add_header Cache-Control "max-age=86400";
    listen 80;
    server_name example.com;
    root {project.www_directory};
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set_by_lua_block $media_type_extension {{
        local available_media_types = {{'text/html', 'application/json'}}
        local media_type_extensions = {{}}
        media_type_extensions['text/html'] = 'html'
        media_type_extensions['application/json'] = 'json'
        local media_type = require('content_negotiation').negotiate(ngx.req.get_headers()['Accept'], available_media_types)
        return media_type_extensions[media_type]
    }}
    index index.$media_type_extension;

    location / {{
        # Handle HTTP error responses.
        error_page 401 /.error/401.$media_type_extension;
        error_page 403 /.error/403.$media_type_extension;
        error_page 404 /.error/404.$media_type_extension;
        location /.error {{
            internal;
        }}

        try_files $uri $uri/ =404;
    }}
}}"""
            await self._assert_configuration_equals(expected, project)

    async def test_generate_artifacts__nginx_configuration_with_https(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            extensions=[Nginx],
            url="https://example.com",
        ) as project:
            expected = rf"""
server {{
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}}
server {{
    add_header Vary Accept-Language;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Cache-Control "max-age=86400";
    listen 443 ssl http2;
    server_name example.com;
    root {project.www_directory};
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_types text/css application/javascript application/json application/xml;

    set $media_type_extension html;
    index index.$media_type_extension;

    location / {{
        # Handle HTTP error responses.
        error_page 401 /.error/401.$media_type_extension;
        error_page 403 /.error/403.$media_type_extension;
        error_page 404 /.error/404.$media_type_extension;
        location /.error {{
            internal;
    }}

    try_files $uri $uri/ =404;
    }}
}}
"""
            await self._assert_configuration_equals(expected, project)

    async def test_generate_artifacts__nginx_configuration_with_overridden_www_directory(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(
            extensions=[
                ExtensionManufacturer(
                    Nginx,
                    NginxConfiguration(
                        www_directory="/tmp/overridden-www",
                    ),
                )
            ],
            url="https://example.com",
        ) as project:
            expected = """
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}
server {
    add_header Vary Accept-Language;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Cache-Control "max-age=86400";
    listen 443 ssl http2;
    server_name example.com;
    root /tmp/overridden-www;
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
"""
            await self._assert_configuration_equals(expected, project)

    async def test_generate_artifacts__dockerfile(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(extensions=[Nginx]) as project:
            await (await project.extensions[Nginx]).generate_artifacts()
            assert (
                project.output_directory / "nginx" / "content_negotiation.lua"
            ).exists()

    async def test_generate_artifacts__content_negotiation(
        self, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(extensions=[Nginx]) as project:
            await (await project.extensions[Nginx]).generate_artifacts()
            assert (project.output_directory / "nginx" / "Dockerfile").exists()
