"""
Illinois county boundary data from ISGS.

Source: https://clearinghouse.isgs.illinois.edu/data/reference/illinois-county-boundaries-polygons-and-lines
"""

import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional

# ISGS county boundaries
BOUNDARIES_SOURCE = "https://clearinghouse.isgs.illinois.edu/data/reference/illinois-county-boundaries-polygons-and-lines"

# Known local paths (check these before downloading)
LOCAL_PATHS = [
    Path("/Volumes/MAPSTORE/US/IL/IL_BNDY_County.zip"),
    Path.home() / "US" / "IL" / "IL_BNDY_County.zip",
]

# Cache location
CACHE_DIR = Path.home() / ".cache" / "ilhmp"


def get_cache_dir() -> Path:
    """Get or create the cache directory."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def find_boundaries_zip() -> Optional[Path]:
    """Find the boundaries ZIP in known local locations."""
    for path in LOCAL_PATHS:
        if path.exists():
            return path
    return None


def download_boundaries(force: bool = False) -> Path:
    """
    Get Illinois county boundaries shapefile.
    
    Checks local paths first, then cache, then downloads.
    Returns path to the extracted directory.
    """
    cache_dir = get_cache_dir()
    boundaries_dir = cache_dir / "IL_BNDY_County"
    shapefile = boundaries_dir / "IL_BNDY_County_Py.shp"
    
    if shapefile.exists() and not force:
        return boundaries_dir
    
    # Check local paths
    local_zip = find_boundaries_zip()
    
    if local_zip:
        print(f"Using local boundaries: {local_zip}")
        boundaries_dir.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(local_zip, boundaries_dir)
        print(f"✓ Extracted to {boundaries_dir}")
        return boundaries_dir
    
    # No local file - provide instructions
    raise FileNotFoundError(
        f"County boundaries not found.\n\n"
        f"Download IL_BNDY_County.zip from:\n"
        f"  {BOUNDARIES_SOURCE}\n\n"
        f"Then place it in one of:\n" +
        "\n".join(f"  - {p}" for p in LOCAL_PATHS)
    )


def get_county_geojson(county_name: str, output_path: Optional[Path] = None) -> Path:
    """
    Extract a single county boundary as GeoJSON.
    
    Args:
        county_name: County name (case-insensitive)
        output_path: Optional output path. If None, saves to cache.
    
    Returns:
        Path to the GeoJSON file.
    """
    boundaries_dir = download_boundaries()
    shapefile = boundaries_dir / "IL_BNDY_County_Py.shp"
    
    if not shapefile.exists():
        raise FileNotFoundError(f"Shapefile not found: {shapefile}")
    
    # Normalize county name
    county_upper = county_name.upper().replace(" COUNTY", "").strip()
    
    # Output path
    if output_path is None:
        output_path = get_cache_dir() / "counties" / f"{county_name.lower()}.geojson"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract with ogr2ogr
    cmd = [
        "ogr2ogr",
        "-f", "GeoJSON",
        str(output_path),
        str(shapefile),
        "-where", f"COUNTY_NAM = '{county_upper}'"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ogr2ogr failed: {result.stderr}")
    
    # Verify it worked
    with open(output_path) as f:
        data = json.load(f)
        if not data.get("features"):
            raise ValueError(f"No county found matching '{county_name}'")
    
    return output_path


def get_all_counties_geojson(output_path: Optional[Path] = None) -> Path:
    """
    Get all Illinois county boundaries as a single GeoJSON file.
    """
    boundaries_dir = download_boundaries()
    shapefile = boundaries_dir / "IL_BNDY_County_Py.shp"
    
    if output_path is None:
        output_path = get_cache_dir() / "il_counties.geojson"
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cmd = ["ogr2ogr", "-f", "GeoJSON", str(output_path), str(shapefile)]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ogr2ogr failed: {result.stderr}")
    
    return output_path


def list_counties() -> list[str]:
    """List all county names in the boundaries file."""
    boundaries_dir = download_boundaries()
    shapefile = boundaries_dir / "IL_BNDY_County_Py.shp"
    
    cmd = ["ogrinfo", "-al", "-geom=NO", str(shapefile)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    counties = []
    for line in result.stdout.splitlines():
        if "COUNTY_NAM" in line and "=" in line:
            name = line.split("=")[1].strip()
            if name:
                counties.append(name.title())
    
    return sorted(set(counties))
