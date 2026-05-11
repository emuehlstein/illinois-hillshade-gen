"""
Zoom level utilities for ilhmp.

Handles both contiguous ranges ("10-16") and discontinuous selections
("10-13,15,18") and normalizes them to a sorted list of ints.
"""

from __future__ import annotations
from typing import Union


ZoomInput = Union[str, list, None]


def parse_zoom(zoom: ZoomInput, default: str = "10-16") -> list[int]:
    """
    Parse any zoom input into a sorted list of unique ints.

    Accepts:
      - "10-16"          → [10, 11, 12, 13, 14, 15, 16]
      - "10-13,15,18"    → [10, 11, 12, 13, 15, 18]
      - [10, 11, 13, 15] → [10, 11, 13, 15]  (pass-through, deduped/sorted)
      - None             → parse_zoom(default)
    """
    if zoom is None:
        zoom = default

    if isinstance(zoom, (list, tuple)):
        return sorted(set(int(z) for z in zoom))

    zooms: set[int] = set()
    for part in str(zoom).split(","):
        part = part.strip()
        if "-" in part:
            lo, hi = part.split("-", 1)
            zooms.update(range(int(lo), int(hi) + 1))
        elif part:
            zooms.add(int(part))
    return sorted(zooms)


def zoom_segments(zooms: list[int]) -> list[tuple[int, int]]:
    """
    Break a zoom list into contiguous (min, max) segments for gdal2tiles.

    [10, 11, 12, 13, 15, 18] → [(10, 13), (15, 15), (18, 18)]
    """
    if not zooms:
        return []
    segments = []
    start = prev = zooms[0]
    for z in zooms[1:]:
        if z == prev + 1:
            prev = z
        else:
            segments.append((start, prev))
            start = prev = z
    segments.append((start, prev))
    return segments


def zoom_str(zooms: list[int]) -> str:
    """
    Serialize a zoom list to the compact string form.

    [10, 11, 12, 13, 15, 18] → "10-13,15,18"
    [10, 11, 12, 13, 14, 15, 16] → "10-16"
    """
    parts = []
    for lo, hi in zoom_segments(zooms):
        parts.append(f"{lo}-{hi}" if lo != hi else str(lo))
    return ",".join(parts)


def zoom_max(zooms: list[int]) -> int:
    """Return the highest zoom level."""
    return max(zooms)


def zoom_min(zooms: list[int]) -> int:
    """Return the lowest zoom level."""
    return min(zooms)
