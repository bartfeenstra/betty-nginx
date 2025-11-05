#!/usr/bin/env python
"""
Automatically fix as many problems as possible.
"""

from subprocess import check_call

# Fix Python code style violations.
check_call(["ruff", "check", "--fix", "."])
check_call(["ruff", "format", "."])
