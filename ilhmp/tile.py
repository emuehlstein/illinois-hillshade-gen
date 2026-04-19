"""
Tile generation for MBTiles and PMTiles output.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path


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
        
        # Generate tiles with gdal2tiles
        cmd = [
            "gdal2tiles.py",
            "-z", f"{min_zoom}-{max_zoom}",
            "-w", "none",  # No web viewer
            "--xyz",       # XYZ tile scheme (not TMS)
            str(input_raster),
            str(tiles_dir),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"gdal2tiles failed: {result.stderr}")
        
        # Pack to MBTiles using mb-util
        # Remove existing output
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
    
    return output_path


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


def generate_tiles_direct(
    input_raster: Path,
    output_dir: Path,
    min_zoom: int = 10,
    max_zoom: int = 16,
) -> Path:
    """
    Generate XYZ tile directory (for direct serving or debugging).
    """
    input_raster = Path(input_raster)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "gdal2tiles.py",
        "-z", f"{min_zoom}-{max_zoom}",
        "-w", "none",
        "--xyz",
        str(input_raster),
        str(output_dir),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdal2tiles failed: {result.stderr}")
    
    return output_dir
