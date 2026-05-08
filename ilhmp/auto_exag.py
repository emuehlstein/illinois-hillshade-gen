"""
Auto-exaggeration computation for hillshade generation.

Uses elevation standard deviation from DEM stats to compute a base exaggeration
that achieves ~40 gray levels of visual contrast.
"""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# Zoom-level scaling curve from design doc
_ZOOM_SCALES = [
    (0, 6, 0.4),
    (7, 9, 0.7),
    (10, 13, 1.0),
    (14, 16, 1.2),
    (17, 19, 0.6),
    (20, 99, 0.4),
]


@dataclass
class ExaggerationConfig:
    """Configuration for vertical exaggeration."""
    mode: str  # 'fixed' or 'auto'
    base_value: float
    zoom_curve: bool = True  # Whether to apply zoom-level scaling


def compute_auto_exaggeration(dem_path: Path, target_contrast: float = 40.0) -> float:
    """
    Compute automatic vertical exaggeration from DEM statistics.

    Reads elevation stddev via gdalinfo and scales to achieve approximately
    target_contrast gray levels of visual contrast.

    Args:
        dem_path: Path to input DEM GeoTIFF
        target_contrast: Target gray level contrast (default 40)

    Returns:
        Computed base exaggeration factor, clamped to [0.5, 10.0]
    """
    dem_path = Path(dem_path)

    cmd = ["gdalinfo", "-stats", "-json", str(dem_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return 3.0

    try:
        info = json.loads(result.stdout)
        bands = info.get("bands", [])
        if not bands:
            return 3.0

        stddev = bands[0].get("stdDev")
        if stddev is None or stddev <= 0:
            return 3.0

        # Higher stddev → terrain has lots of natural contrast → less exaggeration needed
        exaggeration = target_contrast / stddev
        return max(0.5, min(10.0, exaggeration))

    except (json.JSONDecodeError, KeyError, TypeError):
        return 3.0


def zoom_scale(zoom: int, base_exagg: float) -> float:
    """
    Apply zoom-level scaling curve to base exaggeration.

    Args:
        zoom: Map zoom level
        base_exagg: Base exaggeration factor

    Returns:
        Scaled exaggeration factor for this zoom level
    """
    for z_min, z_max, scale in _ZOOM_SCALES:
        if z_min <= zoom <= z_max:
            return base_exagg * scale
    return base_exagg * 0.4
