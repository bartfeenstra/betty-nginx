#!/usr/bin/env python
"""
Build the development environment.
"""

from subprocess import check_call

# Install Python dependencies.
check_call(["pip", "install", "-e", ".[development]"])
