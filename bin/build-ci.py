#!/usr/bin/env python
"""
Build the CI environment.

This command is internal to betty-nginx's own CI setup.
"""

from subprocess import check_call

check_call(["pip", "install", ".[ci]"])
