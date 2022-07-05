
# Nginx for Betty 👵

![Test status](https://github.com/bartfeenstra/betty-nginx/workflows/Test/badge.svg) [![Code coverage](https://codecov.io/gh/bartfeenstra/betty-nginx/branch/master/graph/badge.svg)](https://codecov.io/gh/bartfeenstra/betty-nginx) [![PyPI releases](https://badge.fury.io/py/betty-nginx.svg)](https://pypi.org/project/betty-nginx/) [![Supported Python versions](https://img.shields.io/pypi/pyversions/betty-nginx.svg?logo=python&logoColor=FBE072)](https://pypi.org/project/betty-nginx/) [![Recent downloads](https://img.shields.io/pypi/dm/betty-nginx.svg)](https://pypi.org/project/betty-nginx/) [![Follow Betty on Twitter](https://img.shields.io/twitter/follow/Betty_Project.svg?label=Betty_Project&style=flat&logo=twitter&logoColor=4FADFF)](https://twitter.com/Betty_Project) 

[Betty](https://pypi.org/project/betty/) is a static site generator for your [Gramps](https://gramps-project.org/) and
[GEDCOM](https://en.wikipedia.org/wiki/GEDCOM) family trees.

*Nginx for Betty* is a Betty extension that generates configuration files for the
[nginx](https://pypi.org/project/betty/) web server to run your own Betty site, as well as a
[`Dockerfile`](https://docs.docker.com/engine/reference/builder/) to run your site in a
[Docker](https://www.docker.com/) container using nginx and the generated configuration. 

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Development](#development)
- [Contributions](#contributions)
- [License](#license)

## Installation

### Requirements
- **Python 3.7+**
- Linux, Mac OS, or Windows
- [Docker](https://www.docker.com/) (optional)

### Instructions
Run `pip install betty-nginx` to install the latest stable release.

To install the latest development version, run `pip install git+https://github.com/bartfeenstra/betty-nginx.git`. If you
want the latest source code, read the [development](#development) documentation.

## Usage
This extension can be enabled through Betty's Graphical User Interface (GUI), or by adding the following to your Betty
configuration file:
```yaml
extensions:
    betty_nginx.nginx.Nginx:
        configuration:
            www_directory_path: /var/www/betty
            https: true
```
Configuration:
- `www_directory_path` (optional): The public www directory where Betty will be deployed. Defaults to `www`
    inside the output directory.
- `https` (optional): Whether or not nginx will be serving Betty over HTTPS. Most upstream nginx servers will
    want to have this disabled, so the downstream server can terminate SSL and communicate over HTTP 2 instead.
    Defaults to `true` if the base URL specifies HTTPS, or `false` otherwise.

If Betty's `content_negotiation` is enabled. You must make sure the nginx
[Lua module](https://github.com/openresty/lua-nginx-module#readme) is enabled, and
[CONE](https://github.com/bartfeenstra/cone)'s
[cone.lua](https://raw.githubusercontent.com/bartfeenstra/cone/master/cone.lua) can be found by putting it in nginx's
[lua_package_path](https://github.com/openresty/lua-nginx-module#lua_package_path). This is done automatically when
using the `Dockerfile`.

### Docker
The `./nginx/Dockerfile` generated inside your Betty site's output directory includes all dependencies needed to serve
your Betty site over HTTP (port 80).

To run Betty using this Docker image, configure the extension as follows:
```yaml
# ...
extensions:
    betty_nginx.nginx.Nginx:
        configuration:
            www_directory_path: /var/www/betty/
            https: false
``` 
Then generate your site, and when starting the container based on the generated image, mount `./nginx/nginx.conf` and
`./www` from the output directory to `/etc/nginx/conf.d/betty.conf` and `/var/www/betty` respectively.

You can choose to map the container's port 80 to a port on your host machine, or set up a load balancer to proxy
traffic to the container.

#### HTTPS/SSL
The Docker image does not currently support secure connections
([read more](https://github.com/bartfeenstra/betty-nginx/issues/3)). For HTTPS support, you will have to set up a
separate web server to terminate SSL, and forward all traffic to the container over HTTP.  

## Development
First, [fork and clone](https://guides.github.com/activities/forking/) the repository, and navigate to its root directory.

### Requirements
- The installation requirements documented earlier.
- [Docker](https://www.docker.com/)
- Bash (you're all good if `which bash` outputs a path in your terminal)

### Installation
In any existing Python environment, run `./bin/build-dev`.

### Working on translations
To add a new translation, run `./bin/init-translation $locale` where `$locale` is a
[IETF BCP 47](https://tools.ietf.org/html/bcp47), but using underscores instead of dashes (`nl_NL` instead of `nl-NL`).

After making changes to the translatable strings in the source code, run `./bin/extract-translatables`.

### Testing
In any existing Python environment, run `./bin/test`.

### Fixing problems automatically
In any existing Python environment, run `./bin/fix`.

## Contributions 🥳
Nginx for Betty is Free and Open Source Software. As such you are welcome to
[report bugs](https://github.com/bartfeenstra/betty-nginx/issues) or
[submit improvements](https://github.com/bartfeenstra/betty-nginx/pulls).

## Copyright & license
Nginx for Betty is copyright [Bart Feenstra](https://twitter.com/BartFeenstra/) and contributors, and released under the
[GNU General Public License, Version 3](./LICENSE.txt). In short, that means **you are free to use Nginx for Betty**,
but **if you distribute Nginx for Betty yourself, you must do so under the exact same license**, provide that license, 
and make your source code available.

Nginx for Betty is not affiliated with nginx.
