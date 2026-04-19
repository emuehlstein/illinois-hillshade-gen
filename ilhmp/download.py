"""
Download ILHMP elevation data from ISGS clearinghouse or ImageServer.

Primary method: ZIP download from clearinghouse (full resolution)
Fallback: ImageServer export (for quick previews or partial areas)
"""

import os
import json
import shutil
import subprocess
import tempfile
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple

from . import counties


def download_county(
    county: str,
    dem_type: str = "dtm",
    output_path: Path = None,
    method: str = "auto",
    bounds: Optional[Tuple[float, float, float, float]] = None,
) -> Path:
    """
    Download elevation data for a county.
    
    Args:
        county: County name (e.g., 'putnam', 'cook')
        dem_type: 'dtm' or 'dsm'
        output_path: Output GeoTIFF path
        method: 'zip' (clearinghouse), 'imageserver', or 'auto'
        bounds: Optional (minlon, minlat, maxlon, maxlat) to clip
    
    Returns:
        Path to the output GeoTIFF
    """
    county_info = counties.get_county(county)
    if not county_info:
        raise ValueError(f"Unknown county: {county}")
    
    output_path = output_path or Path(f"./{county.lower()}_{dem_type.lower()}.tif")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Auto-select method
    if method == "auto":
        zip_url = county_info.get(f"{dem_type.lower()}_url")
        if zip_url and not bounds:
            method = "zip"
        else:
            method = "imageserver"
    
    if method == "zip":
        return _download_zip(county_info, dem_type, output_path)
    else:
        return _download_imageserver(county_info, dem_type, output_path, bounds)


def _download_zip(county_info: dict, dem_type: str, output_path: Path) -> Path:
    """Download and extract from clearinghouse ZIP."""
    zip_url = county_info.get(f"{dem_type.lower()}_url")
    if not zip_url:
        raise ValueError(f"No {dem_type.upper()} ZIP available for {county_info['name']}")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        zip_path = tmp_dir / "data.zip"
        
        # Download ZIP
        print(f"Downloading {zip_url}...")
        urllib.request.urlretrieve(zip_url, zip_path)
        
        # Extract
        extract_dir = tmp_dir / "extracted"
        shutil.unpack_archive(zip_path, extract_dir)
        
        # Find raster data (GeoTIFF, IMG, or ArcGrid)
        raster_path = _find_raster(extract_dir)
        if not raster_path:
            raise ValueError(f"No raster data found in ZIP")
        
        # Convert to GeoTIFF if needed
        if raster_path.suffix.lower() in [".tif", ".tiff"]:
            # Already GeoTIFF, just copy with compression
            subprocess.run([
                "gdal_translate",
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                "-co", "BIGTIFF=IF_SAFER",
                str(raster_path),
                str(output_path)
            ], check=True, capture_output=True)
        else:
            # ArcGrid or other format - convert
            subprocess.run([
                "gdal_translate",
                "-of", "GTiff",
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                "-co", "BIGTIFF=IF_SAFER",
                str(raster_path),
                str(output_path)
            ], check=True, capture_output=True)
    
    return output_path


def _find_raster(directory: Path) -> Optional[Path]:
    """Find the main raster file in an extracted directory."""
    # Look for GeoTIFF
    for ext in [".tif", ".tiff", ".img"]:
        files = list(directory.rglob(f"*{ext}"))
        if files:
            # Return the largest one (main data, not overviews)
            return max(files, key=lambda f: f.stat().st_size)
    
    # Look for ArcGrid (folder with hdr.adf)
    for adf in directory.rglob("hdr.adf"):
        return adf.parent
    
    return None


def _download_imageserver(
    county_info: dict,
    dem_type: str,
    output_path: Path,
    bounds: Optional[Tuple[float, float, float, float]] = None,
) -> Path:
    """Download via ArcGIS ImageServer export."""
    server_url = county_info.get(f"{dem_type.lower()}_imageserver_url")
    if not server_url:
        raise ValueError(f"No ImageServer available for {county_info['name']} {dem_type.upper()}")
    
    # Get bounds from county info if not specified
    if not bounds:
        bounds = county_info.get("bounds")
        if not bounds:
            # Query server for extent
            bounds = _get_server_extent(server_url)
    
    minlon, minlat, maxlon, maxlat = bounds
    
    # Calculate appropriate size (max ~4096x4096 per request)
    # For simplicity, request at reasonable resolution
    width = 4000
    height = int(width * (maxlat - minlat) / (maxlon - minlon))
    
    # Build export URL
    params = {
        "bbox": f"{minlon},{minlat},{maxlon},{maxlat}",
        "bboxSR": 4326,
        "imageSR": 4326,
        "size": f"{width},{height}",
        "format": "tiff",
        "f": "pjson",
    }
    query = urllib.parse.urlencode(params)
    url = f"{server_url}/exportImage?{query}"
    
    # Request export
    req = urllib.request.Request(url, headers={"User-Agent": "ilhmp/0.1"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = json.loads(response.read())
    
    if "href" not in data:
        raise ValueError(f"ImageServer export failed: {data}")
    
    # Download the actual TIFF
    tiff_url = data["href"]
    urllib.request.urlretrieve(tiff_url, output_path)
    
    return output_path


def _get_server_extent(server_url: str) -> Tuple[float, float, float, float]:
    """Query ImageServer for its extent in WGS84."""
    url = f"{server_url}?f=json"
    req = urllib.request.Request(url, headers={"User-Agent": "ilhmp/0.1"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = json.loads(response.read())
    
    ext = data.get("extent", {})
    # Note: extent is in native SRS, need to transform
    # For now, require bounds to be specified or use county defaults
    raise ValueError("Bounds not specified and auto-detection not implemented for this county")
