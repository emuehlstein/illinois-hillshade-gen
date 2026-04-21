"""
Download ILHMP elevation data from ISGS clearinghouse.

Downloads full 1m resolution ZIP files - no shortcuts.
"""

import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from . import counties


def download_county(
    county: str,
    dem_type: str = "dtm",
    output_path: Path = None,
    bounds: Optional[Tuple[float, float, float, float]] = None,
) -> Path:
    """
    Download elevation data for a county.

    Always downloads the full 1m resolution ZIP from ISGS clearinghouse.

    Args:
        county: County name (e.g., 'putnam', 'cook')
        dem_type: 'dtm' (bare earth) or 'dsm' (with buildings/trees)
        output_path: Output GeoTIFF path
        bounds: Optional (minlon, minlat, maxlon, maxlat) to clip after download

    Returns:
        Path to the output GeoTIFF
    """
    county_info = counties.get_county(county)
    if not county_info:
        raise ValueError(f"Unknown county: {county}")

    output_path = output_path or Path(f"./{county.lower()}_{dem_type.lower()}.tif")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    return _download_zip(county_info, dem_type, output_path, bounds)


def extract_local_zip(
    zip_path: Path,
    output_path: Path,
    bounds: Optional[Tuple[float, float, float, float]] = None,
) -> Path:
    """
    Extract and convert a locally downloaded ZIP to GeoTIFF.

    Skips the network download step entirely; otherwise identical to the
    internal _download_zip pipeline (unpack → find raster → gdal_translate).

    Temp files are co-located with the output path so they stay on the same
    disk partition, avoiding accidental /tmp exhaustion for large ZIPs.

    Args:
        zip_path: Path to an existing ZIP file on disk
        output_path: Destination GeoTIFF path
        bounds: Optional (minlon, minlat, maxlon, maxlat) to clip after conversion

    Returns:
        Path to the output GeoTIFF
    """
    zip_path = Path(zip_path)
    output_path = Path(output_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP not found: {zip_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=output_path.parent) as tmp_dir:
        tmp_dir = Path(tmp_dir)
        extract_dir = tmp_dir / "extracted"

        print(f"Extracting {zip_path}...")
        shutil.unpack_archive(str(zip_path), extract_dir)

        raster_path = _find_raster(extract_dir)
        if not raster_path:
            raise ValueError(f"No raster data found in ZIP: {zip_path}")

        print(f"Found raster: {raster_path}")

        print("Converting to GeoTIFF...")
        if raster_path.suffix.lower() in [".tif", ".tiff"]:
            cmd = [
                "gdal_translate",
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                "-co", "BIGTIFF=IF_SAFER",
            ]
        else:
            cmd = [
                "gdal_translate",
                "-of", "GTiff",
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                "-co", "BIGTIFF=IF_SAFER",
            ]

        cmd.extend([str(raster_path), str(output_path)])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"gdal_translate failed: {result.stderr}")

        if bounds:
            print(f"Clipping to bounds: {bounds}")
            clipped = output_path.with_suffix(".clipped.tif")
            cmd = [
                "gdalwarp",
                "-te", str(bounds[0]), str(bounds[1]), str(bounds[2]), str(bounds[3]),
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                str(output_path),
                str(clipped),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"gdalwarp clip failed: {result.stderr}")
            clipped.replace(output_path)

    print(f"✓ Saved: {output_path}")
    return output_path


def _download_zip(
    county_info: dict,
    dem_type: str,
    output_path: Path,
    bounds: Optional[Tuple[float, float, float, float]] = None,
) -> Path:
    """Download and extract from clearinghouse ZIP.

    Temp files are co-located with the output path so they stay on the same
    disk partition, avoiding accidental /tmp exhaustion for large ZIPs.
    """
    zip_url = county_info.get(f"{dem_type.lower()}_url")
    if not zip_url:
        raise ValueError(f"No {dem_type.upper()} ZIP available for {county_info['name']}")

    with tempfile.TemporaryDirectory(dir=output_path.parent) as tmp_dir:
        tmp_dir = Path(tmp_dir)
        zip_path = tmp_dir / "data.zip"
        
        # Download ZIP
        print(f"Downloading {zip_url}...")
        print(f"  (This may take a while for large counties)")
        urllib.request.urlretrieve(zip_url, zip_path)
        print(f"  Downloaded: {zip_path.stat().st_size / 1e9:.2f} GB")
        
        # Extract
        print("Extracting...")
        extract_dir = tmp_dir / "extracted"
        shutil.unpack_archive(zip_path, extract_dir)
        
        # Find raster data (GeoTIFF, IMG, or ArcGrid)
        raster_path = _find_raster(extract_dir)
        if not raster_path:
            raise ValueError(f"No raster data found in ZIP")
        
        print(f"Found raster: {raster_path}")
        
        # Convert to GeoTIFF
        print("Converting to GeoTIFF...")
        if raster_path.suffix.lower() in [".tif", ".tiff"]:
            # Already GeoTIFF, just copy with compression
            cmd = [
                "gdal_translate",
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                "-co", "BIGTIFF=IF_SAFER",
            ]
        else:
            # ArcGrid or other format - convert
            cmd = [
                "gdal_translate",
                "-of", "GTiff",
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                "-co", "BIGTIFF=IF_SAFER",
            ]
        
        cmd.extend([str(raster_path), str(output_path)])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"gdal_translate failed: {result.stderr}")
        
        # Optionally clip to bounds
        if bounds:
            print(f"Clipping to bounds: {bounds}")
            clipped = output_path.with_suffix(".clipped.tif")
            cmd = [
                "gdalwarp",
                "-te", str(bounds[0]), str(bounds[1]), str(bounds[2]), str(bounds[3]),
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                str(output_path),
                str(clipped),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"gdalwarp clip failed: {result.stderr}")
            clipped.replace(output_path)
    
    print(f"✓ Saved: {output_path}")
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
