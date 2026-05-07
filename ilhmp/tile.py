"""
Tile generation for MBTiles and PMTiles output.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path


def generate_tiles_direct(
    input_raster: Path,
    output_dir: Path,
    min_zoom: int = 10,
    max_zoom: int = 16,
) -> Path:
    """
    Generate TMS tile directory from a hillshade raster.
    """
    input_raster = Path(input_raster)
    output_dir = Path(output_dir)
    
    # Remove existing
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "gdal2tiles.py",
        "-z", f"{min_zoom}-{max_zoom}",
        "-w", "none",
        "--tms",
        "--processes=4",
        str(input_raster),
        str(output_dir),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdal2tiles failed: {result.stderr}")
    
    return output_dir


def generate_mbtiles(
    input_raster: Path,
    output_path: Path,
    min_zoom: int = 10,
    max_zoom: int = 16,
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
        
        generate_tiles_direct(input_raster, tiles_dir, min_zoom, max_zoom)
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
    
    cmd = [
        "mb-util",
        str(tiles_dir),
        str(output_path),
        "--image_format=png",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"mb-util failed: {result.stderr}")
    
    # Ensure scheme metadata matches tile coordinate system
    # gdal2tiles --tms produces TMS coordinates; mb-util preserves them
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
    
    cmd = [
        "pmtiles", "convert",
        str(input_mbtiles),
        str(output_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"pmtiles convert failed: {result.stderr}")
    
    return output_path
