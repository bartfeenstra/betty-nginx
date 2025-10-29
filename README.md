# Nginx for Betty 👵

[![Test](https://github.com/bartfeenstra/betty-nginx/actions/workflows/test.yml/badge.svg?branch=0.1.x)](https://github.com/bartfeenstra/betty-nginx/actions/workflows/test.yml) [![Code coverage](https://codecov.io/gh/bartfeenstra/betty-nginx/branch/0.1.x/graph/badge.svg)](https://codecov.io/gh/bartfeenstra/betty-nginx) [![PyPI releases](https://badge.fury.io/py/betty-nginx.svg)](https://pypi.org/project/betty-nginx/) [![Supported Python versions](https://img.shields.io/pypi/pyversions/betty-nginx.svg?logo=python&logoColor=FBE072)](https://pypi.org/project/betty-nginx/) [![Recent downloads](https://img.shields.io/pypi/dm/betty-nginx.svg)](https://pypi.org/project/betty-nginx/) [![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)  [![Follow Betty on Twitter](https://img.shields.io/twitter/follow/Betty_Project.svg?label=Betty_Project&style=flat&logo=twitter&logoColor=4FADFF)](https://twitter.com/Betty_Project)

Generate nginx and Docker artifacts for your [Betty](https://betty.readthedocs.io/) site.

# Configuration
```yaml
# Add to your project's configuration file:
extensions:
    nginx:
        configuration:
          https: False
          legacy_entity_redirects: True
          www_directory: /var/www
```

## ``https``
(*optional*, **boolean**)

Whether to support HTTPS in the public nginx configuration. Requires you to set up SSL certificates yourself.

Defaults to whether or not your project's URL uses HTTPS.

## ``legacy_entity_redirects``
(*optional*, **boolean**)

Whether to generate redirects from legacy (pre Betty 0.5) entity URLs.

## ``www_directory``
(*optional*, **string**)

The www directory to serve.

Defaults to your project's www directory.

## Usage
Add the extension to your project configuration. Whenever you generate your site, nginx artifacts will be created.

Additionally, use `betty nginx-generate` to create these same artifacts without also generating your site.

Launch a Docker container to serve your site locally with `betty nginx-serve`, or `betty nginx-serve --public` to launch
a container to serve your site publicly, over the internet.

### Docker & known limitations
The Docker images [do not yet support HTTPS connections](https://github.com/bartfeenstra/betty-nginx/issues/3). When
hosting your site over HTTPS, you must use a proxy to terminate HTTPS connections and forward HTTP traffic to the
container.

# Artifacts
The Nginx extension generates the following artifacts relative to your project's output directory:

## `./nginx/content_negotiation.lua`
The Lua code the nginx configuration uses for [content negotiation](https://en.wikipedia.org/wiki/Content_negotiation). It must be placed in your nginx's
`lua_package_path`.

## `./nginx/Dockerfle`
A Docker image build manifest. You may use this to run your own containers. Nginx configuration MUST be placed in 
`/etc/nginx/conf.d`, and the WWW directory MUST exist at `/var/www/betty`.

## `./nginx/nginx.conf`
Your site's public nginx configuration file. You may deploy this anywhere. You MUST configure `lua_package_path`. If you
are using HTTPS, you MUST configure SSL certificates.
