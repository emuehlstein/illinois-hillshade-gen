"""
Auxiliary terrain layers generated from a DEM using gdaldem.

Provides aspect, slope, roughness, and TRI (Terrain Ruggedness Index).
"""

import subprocess
from pathlib import Path
from typing import Optional

_GDAL_CO = [
    "-co", "COMPRESS=DEFLATE",
    "-co", "TILED=YES",
    "-co", "BIGTIFF=YES",
]


def _run_gdaldem(mode: str, dem_path: Path, output_path: Path, extra_args: list = None) -> Path:
    cmd = [
        "gdaldem", mode,
        str(dem_path),
        str(output_path),
        "-compute_edges",
    ] + (extra_args or []) + _GDAL_CO
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdaldem {mode} failed: {result.stderr}")
    return output_path


def generate_aspect(
    dem_path: Path,
    output_path: Path,
    cache_dir: Optional[Path] = None,
) -> Path:
    """
    Generate aspect layer (slope direction 0-360°) from a DEM.

    Args:
        dem_path: Input DEM GeoTIFF
        output_path: Output aspect GeoTIFF
        cache_dir: If provided, cache intermediate result here

    Returns:
        Path to output file
    """
    dem_path = Path(dem_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_dir is not None:
        cached = Path(cache_dir) / f"{dem_path.stem}_aspect.tif"
        if cached.exists():
            return cached
        result = _run_gdaldem("aspect", dem_path, cached)
        return result

    return _run_gdaldem("aspect", dem_path, output_path)


def generate_slope(
    dem_path: Path,
    output_path: Path,
    cache_dir: Optional[Path] = None,
) -> Path:
    """
    Generate slope layer (steepness in degrees) from a DEM.

    Args:
        dem_path: Input DEM GeoTIFF
        output_path: Output slope GeoTIFF
        cache_dir: If provided, cache intermediate result here

    Returns:
        Path to output file
    """
    dem_path = Path(dem_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_dir is not None:
        cached = Path(cache_dir) / f"{dem_path.stem}_slope.tif"
        if cached.exists():
            return cached
        return _run_gdaldem("slope", dem_path, cached)

    return _run_gdaldem("slope", dem_path, output_path)


def generate_roughness(
    dem_path: Path,
    output_path: Path,
    cache_dir: Optional[Path] = None,
) -> Path:
    """
    Generate terrain roughness layer from a DEM.

    Args:
        dem_path: Input DEM GeoTIFF
        output_path: Output roughness GeoTIFF
        cache_dir: If provided, cache intermediate result here

    Returns:
        Path to output file
    """
    dem_path = Path(dem_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_dir is not None:
        cached = Path(cache_dir) / f"{dem_path.stem}_roughness.tif"
        if cached.exists():
            return cached
        return _run_gdaldem("roughness", dem_path, cached)

    return _run_gdaldem("roughness", dem_path, output_path)


def generate_tri(
    dem_path: Path,
    output_path: Path,
    cache_dir: Optional[Path] = None,
) -> Path:
    """
    Generate TRI (Terrain Ruggedness Index) layer from a DEM.

    Args:
        dem_path: Input DEM GeoTIFF
        output_path: Output TRI GeoTIFF
        cache_dir: If provided, cache intermediate result here

    Returns:
        Path to output file
    """
    dem_path = Path(dem_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if cache_dir is not None:
        cached = Path(cache_dir) / f"{dem_path.stem}_TRI.tif"
        if cached.exists():
            return cached
        return _run_gdaldem("TRI", dem_path, cached)

    return _run_gdaldem("TRI", dem_path, output_path)
