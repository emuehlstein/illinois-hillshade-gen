"""
Download ILHMP elevation data from ISGS clearinghouse.

Two download methods:
  zip          — Full county ZIP from clearinghouse (default). Slow but complete.
  imageserver  — ArcGIS ImageServer exportImage. Pulls only the requested bbox,
                 much faster for sub-county areas. Tiles requests to fit server
                 limits, then merges with gdal_merge.
"""

import json
import math
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple, Union

from . import counties
from .cache import Cache


# ISGS ImageServer limits (from service metadata)
_IMAGESERVER_MAX_WIDTH = 15000
_IMAGESERVER_MAX_HEIGHT = 4100


def download_county(
    county: str,
    dem_type: str = "dtm",
    output_path: Path = None,
    bounds: Optional[Tuple[float, float, float, float]] = None,
    cache_dir: Optional[Union[str, Path]] = None,
    method: str = "zip",
) -> Path:
    """
    Download elevation data for a county.

    Args:
        county:     County name (e.g., 'putnam', 'cook')
        dem_type:   'dtm' (bare earth) or 'dsm' (with buildings/trees)
        output_path: Output GeoTIFF path
        bounds:     Optional (minlon, minlat, maxlon, maxlat) to clip after download.
                    Required when method='imageserver'.
        cache_dir:  Local path or s3:// URI for caching DEMs
        method:     'zip'         — full county ZIP from clearinghouse (default)
                    'imageserver' — ArcGIS exportImage, pulls only the bbox
                                    (much faster for sub-county areas)

    Returns:
        Path to the output GeoTIFF
    """
    county_info = counties.get_county(county)
    if not county_info:
        raise ValueError(f"Unknown county: {county}")

    output_path = output_path or Path(f"./{county.lower()}_{dem_type.lower()}.tif")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cache = Cache(cache_dir)
    cache_key = f"dem/{county.lower()}/{county.lower()}_{dem_type.lower()}.tif"

    # Check cache first
    if cache.pull(cache_key, output_path):
        return output_path

    if method == "imageserver":
        if not bounds:
            raise ValueError(
                "bounds=(minlon, minlat, maxlon, maxlat) is required for method='imageserver'"
            )
        result = download_imageserver(
            county=county,
            dem_type=dem_type,
            bounds=bounds,
            output_path=output_path,
        )
    else:
        result = _download_zip(county_info, dem_type, output_path, bounds)

    # Persist to cache
    cache.push(output_path, cache_key)

    return result


def download_imageserver(
    county: str,
    dem_type: str = "dtm",
    bounds: Tuple[float, float, float, float] = None,
    output_path: Path = None,
    year: Optional[str] = None,
    pixel_size: Optional[float] = None,
) -> Path:
    """
    Download a DEM from the ISGS ArcGIS ImageServer using exportImage.

    Much faster than downloading the full county ZIP when you only need
    a sub-county area. The service streams only the requested bbox at
    native 1ft (0.3m) resolution.

    Tiles the request to respect server limits (15000 × 4100 px per call),
    downloads tiles in parallel, then merges with gdal_merge.py.

    Args:
        county:      County name (e.g., 'cook', 'mchenry')
        dem_type:    'dtm' or 'dsm'
        bounds:      (minlon, minlat, maxlon, maxlat) in WGS84 (EPSG:4326).
                     If None, uses the full county extent.
        output_path: Destination GeoTIFF. Defaults to ./{county}_{dem_type}.tif
        year:        Collection year to use. Defaults to latest available.
        pixel_size:  Output pixel size in degrees. Defaults to ~1ft at mid-latitude
                     (~0.000003°). Increase for faster downloads of large areas.

    Returns:
        Path to the merged output GeoTIFF (NAD83 / IL East ft, EPSG:3435 equivalent)
    """
    county_info = counties.get_county(county)
    if not county_info:
        raise ValueError(f"Unknown county: {county}")

    # Resolve collection year
    collection = _resolve_collection(county_info, year)
    svc_name = collection.get(f"{dem_type.lower()}_imageserver")
    if not svc_name:
        raise ValueError(
            f"No ImageServer for {county} {dem_type.upper()} "
            f"(year={collection['year']}). Try --method zip."
        )

    base_url = f"{counties.IMAGESERVER_BASE}/{svc_name}/ImageServer"

    # Resolve bounds (default = full county bbox from service)
    if bounds is None:
        bounds = _get_service_bounds_wgs84(base_url)
        print(f"  Using full county extent: {bounds}")

    minlon, minlat, maxlon, maxlat = bounds

    # Estimate pixel size in degrees (~1ft at the latitude midpoint)
    if pixel_size is None:
        mid_lat = (minlat + maxlat) / 2
        # 1 ft ≈ 0.3048 m; 1° lat ≈ 111_320 m
        pixel_size = 0.3048 / (111_320 * math.cos(math.radians(mid_lat)))

    output_path = output_path or Path(f"./{county.lower()}_{dem_type.lower()}.tif")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"ImageServer: {svc_name} ({collection['year']})")
    print(f"  Bounds: {minlon:.5f},{minlat:.5f} → {maxlon:.5f},{maxlat:.5f}")
    print(f"  Pixel size: {pixel_size:.8f}°  (~{pixel_size * 111320:.2f}m)")

    # Compute tile grid
    lon_range = maxlon - minlon
    lat_range = maxlat - minlat
    total_width = int(math.ceil(lon_range / pixel_size))
    total_height = int(math.ceil(lat_range / pixel_size))
    cols = math.ceil(total_width / _IMAGESERVER_MAX_WIDTH)
    rows = math.ceil(total_height / _IMAGESERVER_MAX_HEIGHT)
    print(f"  Raster size: {total_width}×{total_height}px → {cols}×{rows} tile grid")

    tile_paths = _download_imageserver_tiles(
        base_url=base_url,
        minlon=minlon, minlat=minlat, maxlon=maxlon, maxlat=maxlat,
        cols=cols, rows=rows,
        pixel_size=pixel_size,
        work_dir=output_path.parent,
    )

    if len(tile_paths) == 1:
        tile_paths[0].replace(output_path)
    else:
        print(f"Merging {len(tile_paths)} tiles...")
        _merge_tiles(tile_paths, output_path)
        for p in tile_paths:
            p.unlink(missing_ok=True)

    print(f"✓ Saved: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# ImageServer helpers
# ---------------------------------------------------------------------------

def _resolve_collection(county_info: dict, year: Optional[str]) -> dict:
    """Return the matching collection dict, defaulting to the newest."""
    colls = county_info.get("collections", [])
    if not colls:
        raise ValueError(f"No collections for {county_info['name']}")
    if year is None:
        return colls[0]  # newest-first
    for c in colls:
        if c["year"] == year:
            return c
    raise ValueError(
        f"Year {year!r} not found for {county_info['name']}. "
        f"Available: {[c['year'] for c in colls]}"
    )


def _get_service_bounds_wgs84(
    base_url: str,
) -> Tuple[float, float, float, float]:
    """Query the ImageServer info endpoint and return (minlon, minlat, maxlon, maxlat)."""
    url = f"{base_url}?f=json"
    with urllib.request.urlopen(url, timeout=30) as resp:
        info = json.load(resp)

    ext = info.get("extent", {})
    sr_wkt = (ext.get("spatialReference") or {}).get("wkt", "")

    # Project native extent to WGS84 using gdaltransform
    # Write a small VRT with the native CRS, run gdalinfo to get WGS84 bounds
    xmin = ext["xmin"]
    ymin = ext["ymin"]
    xmax = ext["xmax"]
    ymax = ext["ymax"]

    # Use gdaltransform to convert corners from native SRS to WGS84
    corners = [
        (xmin, ymin), (xmin, ymax),
        (xmax, ymin), (xmax, ymax),
    ]
    input_text = "\n".join(f"{x} {y}" for x, y in corners)
    cmd = ["gdaltransform", "-s_srs", sr_wkt, "-t_srs", "EPSG:4326"]
    result = subprocess.run(
        cmd,
        input=input_text,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gdaltransform failed: {result.stderr}")

    lons, lats = [], []
    for line in result.stdout.strip().splitlines():
        parts = line.split()
        lons.append(float(parts[0]))
        lats.append(float(parts[1]))

    return (min(lons), min(lats), max(lons), max(lats))


def _imageserver_export_url(
    base_url: str,
    minlon: float, minlat: float,
    maxlon: float, maxlat: float,
    width: int, height: int,
) -> str:
    """Build an ArcGIS ImageServer exportImage URL for a WGS84 bbox."""
    bbox = f"{minlon},{minlat},{maxlon},{maxlat}"
    bbox_sr = json.dumps({"wkid": 4326})
    params = urllib.parse.urlencode({
        "bbox": bbox,
        "bboxSR": bbox_sr,
        "size": f"{width},{height}",
        "imageSR": json.dumps({"wkid": 4326}),
        "format": "tiff",
        "pixelType": "F32",
        "noDataInterpretation": "esriNoDataMatchAny",
        "interpolation": "RSP_BilinearInterpolation",
        "f": "image",
    })
    return f"{base_url}/exportImage?{params}"


def _download_imageserver_tiles(
    base_url: str,
    minlon: float, minlat: float,
    maxlon: float, maxlat: float,
    cols: int, rows: int,
    pixel_size: float,
    work_dir: Path,
) -> List[Path]:
    """Download all tiles and return list of Paths."""
    tile_paths: List[Path] = []
    total = cols * rows
    n = 0

    lon_step = (maxlon - minlon) / cols
    lat_step = (maxlat - minlat) / rows

    for row in range(rows):
        for col in range(cols):
            t_minlon = minlon + col * lon_step
            t_maxlon = min(minlon + (col + 1) * lon_step, maxlon)
            # Rows go north-down: row 0 = northernmost
            t_maxlat = maxlat - row * lat_step
            t_minlat = max(maxlat - (row + 1) * lat_step, minlat)

            t_width = min(
                int(math.ceil((t_maxlon - t_minlon) / pixel_size)),
                _IMAGESERVER_MAX_WIDTH,
            )
            t_height = min(
                int(math.ceil((t_maxlat - t_minlat) / pixel_size)),
                _IMAGESERVER_MAX_HEIGHT,
            )

            n += 1
            tile_path = work_dir / f"_isgs_tile_{row}_{col}.tif"
            url = _imageserver_export_url(
                base_url,
                t_minlon, t_minlat, t_maxlon, t_maxlat,
                t_width, t_height,
            )

            print(f"  [{n}/{total}] Downloading tile ({col},{row}) "
                  f"{t_width}×{t_height}px ...")

            try:
                urllib.request.urlretrieve(url, tile_path)
            except urllib.error.URLError as exc:
                raise RuntimeError(
                    f"ImageServer tile ({col},{row}) failed: {exc}"
                ) from exc

            tile_paths.append(tile_path)

    return tile_paths


def _merge_tiles(tile_paths: List[Path], output_path: Path) -> None:
    """Merge downloaded tiles into a single GeoTIFF using gdal_merge.py."""
    cmd = [
        "gdal_merge.py",
        "-o", str(output_path),
        "-of", "GTiff",
        "-co", "COMPRESS=DEFLATE",
        "-co", "TILED=YES",
        "-co", "BIGTIFF=IF_SAFER",
        "-n", "3.4e+38",   # nodata value from ISGS service
        "-a_nodata", "nan",
    ] + [str(p) for p in tile_paths]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdal_merge.py failed: {result.stderr}")


# ---------------------------------------------------------------------------
# Local ZIP extraction
# ---------------------------------------------------------------------------

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
    """Find the main raster file in an extracted directory.

    ISGS ZIPs contain both elevation data (_dtm_/_dsm_) and pre-rendered
    hillshade visualizations (_dth_/_dsh_).  The visualizations are Byte
    (0-255) and useless for analysis, so we skip them.

    Priority order:
      1. ArcGrid (hdr.adf) — older ISGS data uses this for the real DEM
      2. GeoTIFF/IMG — but only if not in a hillshade viz folder
    """
    # Skip hillshade visualization folders (dth = DTM hillshade, dsh = DSM hillshade)
    viz_markers = ("_dth_", "_dsh_", "_dth/", "_dsh/")

    def _is_viz(path: Path) -> bool:
        s = str(path).lower()
        return any(m in s for m in viz_markers)

    # Prefer ArcGrid (older ISGS data) — these are always real elevation
    for adf in directory.rglob("hdr.adf"):
        if not _is_viz(adf):
            return adf.parent

    # Fall back to GeoTIFF / IMG, skipping viz folders
    for ext in [".tif", ".tiff", ".img"]:
        files = [f for f in directory.rglob(f"*{ext}") if not _is_viz(f)]
        if files:
            # Return the largest one (main data, not overviews)
            return max(files, key=lambda f: f.stat().st_size)

    # Last resort: anything at all
    for ext in [".tif", ".tiff", ".img"]:
        files = list(directory.rglob(f"*{ext}"))
        if files:
            return max(files, key=lambda f: f.stat().st_size)

    for adf in directory.rglob("hdr.adf"):
        return adf.parent

    return None
