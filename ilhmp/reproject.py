"""
Reproject DEM to EPSG:4326 for web mapping.

Supports local cache directories. Atomic writes via temp file + rename
to prevent partial/corrupt outputs on interruption.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def reproject_to_4326(
    input_path: Path,
    output_path: Path,
    cache_dir: Optional[Path] = None,
    force: bool = False,
) -> Path:
    """
    Reproject a DEM to EPSG:4326 (WGS84).

    Uses bilinear resampling and DEFLATE compression. Writes atomically
    via a temporary file so that partial results never appear at output_path.

    Args:
        input_path: Source DEM GeoTIFF (any CRS)
        output_path: Destination reprojected GeoTIFF
        cache_dir: Optional directory to check/store cached reprojected DEMs.
                   Cache key is the input filename stem + "_4326.tif".
        force: Reproject even if cached version exists

    Returns:
        Path to the reprojected file
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    # Check output exists (simple resume)
    if output_path.exists() and not force:
        print(f"\u23e9 Using existing: {output_path}")
        return output_path

    # Check cache
    cached = None
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cached = cache_dir / f"{input_path.stem}_4326.tif"
        if cached.exists() and not force:
            if cached != output_path:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cached, output_path)
            print(f"\u23e9 Using cached reprojection: {cached}")
            return output_path

    # Reproject atomically: write to temp, then rename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".tif",
        dir=output_path.parent,
        prefix=f".{output_path.stem}_tmp_",
    )
    # Close the fd immediately — gdalwarp writes to the path
    import os
    os.close(tmp_fd)
    tmp_path = Path(tmp_path)

    try:
        cmd = [
            "gdalwarp",
            "-t_srs", "EPSG:4326",
            "-r", "bilinear",
            "-co", "COMPRESS=DEFLATE",
            "-co", "TILED=YES",
            "-co", "BIGTIFF=IF_SAFER",
            str(input_path),
            str(tmp_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"gdalwarp failed: {result.stderr}")

        # Atomic rename
        tmp_path.replace(output_path)
        print(f"\u2713 Reprojected: {output_path}")

        # Persist to cache
        if cached is not None and cached != output_path:
            cached.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output_path, cached)
            print(f"\U0001f4be Cached reprojection: {cached}")

        return output_path

    except Exception:
        # Clean up temp file on failure
        tmp_path.unlink(missing_ok=True)
        raise
