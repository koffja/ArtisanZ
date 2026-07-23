"""Canonical curve colors shared by renderer adapters and style controls."""
from __future__ import annotations

from typing import Final


CANONICAL_CURVE_COLORS: Final[dict[str, str]] = {
    'et': '#C0504D',
    'bt': '#3A7CA5',
    'deltaet': '#D4943A',
    'deltabt': '#5B9BD5',
}


__all__ = ['CANONICAL_CURVE_COLORS']
