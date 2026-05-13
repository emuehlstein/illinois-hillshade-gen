"""
Tile generation for MBTiles and PMTiles output.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path


def _find_tool(name: str) -> str:
    """Resolve a CLI tool by name, falling back to /opt/homebrew/bin for macOS."""
    found = shutil.which(name)
    if found:
        return found
    # Homebrew installs here but it may not be in PATH in all execution contexts
    homebrew_path = f"/opt/homebrew/bin/{name}"
    if os.path.isfile(homebrew_path):
        return homebrew_path
    return name  # last resort: let subprocess raise a clean error

from .zoom_utils import parse_zoom, zoom_segments, ZoomInput


def generate_tiles_direct(
    input_raster: Path,
    output_dir: Path,
    min_zoom: int = None,
    max_zoom: int = None,
    zooms: ZoomInput = None,
) -> Path:
    """
    Generate TMS tile directory from a hillshade raster.

    Accepts either:
      - zooms="10-13,15,18" / zooms=[10,11,12,13,15,18]
      - legacy min_zoom/max_zoom ints (contiguous, backward-compatible)
    """
    input_raster = Path(input_raster)
    output_dir = Path(output_dir)

    # Resolve zoom list
    if zooms is not None:
        zoom_list = parse_zoom(zooms)
    elif min_zoom is not None and max_zoom is not None:
        zoom_list = list(range(min_zoom, max_zoom + 1))
    else:
        zoom_list = parse_zoom(None)  # default 10-16

    # Remove existing and recreate
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gdal2tiles_bin = _find_tool("gdal2tiles.py")

    # gdal2tiles only supports contiguous ranges; run once per segment
    for seg_lo, seg_hi in zoom_segments(zoom_list):
        cmd = [
            gdal2tiles_bin,
            "-z", f"{seg_lo}-{seg_hi}",
            "-w", "none",
            "--tms",
            "--processes=4",
            str(input_raster),
            str(output_dir),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"gdal2tiles failed (z{seg_lo}-{seg_hi}): {result.stderr}")

    return output_dir


def generate_mbtiles(
    input_raster: Path,
    output_path: Path,
    min_zoom: int = None,
    max_zoom: int = None,
    zooms: ZoomInput = None,
) -> Path:
    """
    Generate MBTiles from a hillshade raster.

    Uses gdal2tiles.py for tile generation, then mb-util to pack.
    """
    input_raster = Path(input_raster)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        tiles_dir = tmp_dir / "tiles"

        generate_tiles_direct(
            input_raster, tiles_dir,
            min_zoom=min_zoom, max_zoom=max_zoom, zooms=zooms,
        )
        generate_mbtiles_from_dir(tiles_dir, output_path)

    return output_path


def generate_mbtiles_from_dir(
    tiles_dir: Path,
    output_path: Path,
) -> Path:
    """
    Pack a TMS tiles directory into MBTiles.
    """
    tiles_dir = Path(tiles_dir)
    output_path = Path(output_path)

    if output_path.exists():
        output_path.unlink()

    mb_util_bin = _find_tool("mb-util")
    cmd = [
        mb_util_bin,
        "--scheme=tms",
        str(tiles_dir),
        str(output_path),
        "--image_format=png",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"mb-util failed: {result.stderr}")

    # Ensure scheme metadata matches tile coordinate system
    _set_mbtiles_metadata(output_path, "scheme", "tms")

    return output_path


def _set_mbtiles_metadata(mbtiles_path: Path, key: str, value: str) -> None:
    """Set a metadata value in an MBTiles file."""
    import sqlite3 as sqlite3_mod
    conn = sqlite3_mod.connect(str(mbtiles_path))
    conn.execute(
        "INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)",
        (key, value)
    )
    conn.commit()
    conn.close()


def convert_to_pmtiles(
    input_mbtiles: Path,
    output_path: Path,
) -> Path:
    """
    Convert MBTiles to PMTiles format.

    Requires the `pmtiles` CLI tool.
    """
    input_mbtiles = Path(input_mbtiles)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        output_path.unlink()

    pmtiles_bin = _find_tool("pmtiles")
    cmd = [
        pmtiles_bin, "convert",
        str(input_mbtiles),
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pmtiles convert failed: {result.stderr}")

    return output_path
