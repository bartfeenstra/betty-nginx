#!/usr/bin/env python
"""
Run Busted.
"""

import sys
from subprocess import check_call

print("Running Busted...")  # noqa T201

check_call(["busted", *sys.argv[2:]])
