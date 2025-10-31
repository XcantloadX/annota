"""
## annota.file

This module contains codes to read/write annota project files.
"""

from .asset import ImageAsset

FORMAT_VERSION: int = 1
"""The version of the annota file format."""

__all__ = [
    'ImageAsset',
    'FORMAT_VERSION',
]