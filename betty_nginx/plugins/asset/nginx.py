"""
Maps assets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from betty.asset import AssetDefinition

NGINX: Final[AssetDefinition] = AssetDefinition(
    "nginx", assets=Path(__file__).parent.parent.parent / "assets"
)
