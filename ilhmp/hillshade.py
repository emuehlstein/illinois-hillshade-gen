"""
Hillshade generation with color styling.

Styles:
- dark: Blue-gray on dark background (ATAK dark mode)
- light: Warm gray on light background (ATAK light mode)
- tactical: Olive drab on dark background
- terrain: Earth tones
- gray: Grayscale (no tint)
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict

import numpy as np

try:
    from osgeo import gdal
    gdal.UseExceptions()
    HAS_GDAL_PYTHON = True
except ImportError:
    HAS_GDAL_PYTHON = False

# Color presets: (tint RGB 0-255, background RGB 0-255)
STYLES: Dict[str, Dict] = {
    "dark": {
        "tint": (77, 102, 153),     # Blue-gray
        "bg": (18, 18, 18),          # Near-black
    },
    "light": {
        "tint": (217, 209, 199),    # Warm gray
        "bg": (250, 250, 250),       # Near-white
    },
    "tactical": {
        "tint": (85, 107, 47),      # Olive drab
        "bg": (24, 24, 20),          # Dark olive-black
    },
    "terrain": {
        "tint": (140, 120, 100),    # Earth brown
        "bg": (245, 240, 230),       # Cream
    },
    "gray": {
        "tint": (255, 255, 255),    # White
        "bg": (0, 0, 0),             # Black
    },
}


def generate(
    input_dem: Path,
    output_path: Path,
    style: str = "dark",
    exaggeration: float = 3.0,
    azimuth: float = 315.0,
    altitude: float = 45.0,
    custom_tint: Optional[Tuple[int, int, int]] = None,
    custom_bg: Optional[Tuple[int, int, int]] = None,
    cache_dir: Optional[Path] = None,
    force_recompute: bool = False,
) -> Path:
    """
    Generate a styled hillshade from a DEM.

    Args:
        input_dem: Input DEM GeoTIFF
        output_path: Output styled hillshade GeoTIFF (RGBA)
        style: Color style name or 'custom'
        exaggeration: Vertical exaggeration factor (z-factor)
        azimuth: Sun azimuth in degrees (0-360, 0=N, default 315=NW)
        altitude: Sun altitude in degrees (0-90, default 45)
        custom_tint: RGB tuple (0-255) for custom style peak color
        custom_bg: RGB tuple (0-255) for custom style background
        cache_dir: Directory to cache the intermediate grayscale hillshade TIF.
            If provided, the gray TIF is saved as
            ``{cache_dir}/{input_dem.stem}_gray.tif`` and reused on subsequent
            runs that share the same DEM / exaggeration / azimuth / altitude.
        force_recompute: Ignore any cached grayscale TIF and regenerate it.

    Returns:
        Path to the output file
    """
    input_dem = Path(input_dem)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Get style colors
    if style == "custom":
        if not custom_tint or not custom_bg:
            raise ValueError("custom_tint and custom_bg required for style='custom'")
        tint = custom_tint
        bg = custom_bg
    else:
        if style not in STYLES:
            raise ValueError(f"Unknown style: {style}. Available: {list(STYLES.keys())}")
        tint = STYLES[style]["tint"]
        bg = STYLES[style]["bg"]

    # Determine grayscale cache path
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        gray_cache = cache_dir / f"{input_dem.stem}_gray_z{exaggeration}.tif"
    else:
        gray_cache = None

    if gray_cache and gray_cache.exists() and not force_recompute:
        # Reuse cached grayscale — skip the expensive gdaldem step
        _apply_color_tint(gray_cache, output_path, tint, bg)
    else:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            gray_path = tmp_dir / "hillshade_gray.tif"

            # Step 1: Generate grayscale hillshade
            _generate_grayscale(input_dem, gray_path, exaggeration, azimuth, altitude)

            # Persist to cache if a cache_dir was requested
            if gray_cache is not None:
                import shutil
                shutil.copy2(gray_path, gray_cache)
                gray_path = gray_cache

            # Step 2: Apply color tint with proper alpha
            _apply_color_tint(gray_path, output_path, tint, bg)

    return output_path


def _generate_grayscale(
    input_dem: Path,
    output_path: Path,
    exaggeration: float,
    azimuth: float,
    altitude: float,
) -> None:
    """Generate grayscale hillshade using gdaldem."""
    cmd = [
        "gdaldem", "hillshade",
        str(input_dem),
        str(output_path),
        "-z", str(exaggeration),
        "-az", str(azimuth),
        "-alt", str(altitude),
        "-compute_edges",
        "-co", "COMPRESS=LZW",
        "-co", "TILED=YES",
        "-co", "BIGTIFF=YES",
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdaldem failed: {result.stderr}")


def _apply_color_tint(
    input_gray: Path,
    output_path: Path,
    tint: Tuple[int, int, int],
    bg: Tuple[int, int, int],
    chunk_size: int = 1000,
) -> None:
    """
    Apply color tint to grayscale hillshade, processing in row chunks.

    Processes chunk_size rows at a time to avoid OOM on large counties
    (e.g. Cook ~3.7B pixels, Bond ~1.7B pixels).

    tint/bg are RGB tuples (0-255 integers).
    Alpha: 255 where hillshade > 0, 0 for nodata.

    Uses GDAL Python bindings when available (faster, streaming).
    Falls back to a subprocess pipeline using gdal_calc.py + gdal_merge.py
    when bindings are not installed.
    """
    if HAS_GDAL_PYTHON:
        _apply_color_tint_gdal(input_gray, output_path, tint, bg, chunk_size)
    else:
        _apply_color_tint_subprocess(input_gray, output_path, tint, bg)


def _apply_color_tint_gdal(
    input_gray: Path,
    output_path: Path,
    tint: Tuple[int, int, int],
    bg: Tuple[int, int, int],
    chunk_size: int = 1000,
) -> None:
    """Apply color tint using GDAL Python bindings (streaming, memory-efficient)."""
    src = gdal.Open(str(input_gray))
    width = src.RasterXSize
    height = src.RasterYSize
    band = src.GetRasterBand(1)

    driver = gdal.GetDriverByName('GTiff')
    out = driver.Create(
        str(output_path),
        width,
        height,
        4,  # RGBA
        gdal.GDT_Byte,
        options=['COMPRESS=DEFLATE', 'TILED=YES', 'BIGTIFF=IF_SAFER']
    )
    out.SetGeoTransform(src.GetGeoTransform())
    out.SetProjection(src.GetProjection())

    bg_arr = np.array(bg, dtype=np.float32)
    tint_arr = np.array(tint, dtype=np.float32)

    for row_off in range(0, height, chunk_size):
        rows = min(chunk_size, height - row_off)
        hs = band.ReadAsArray(0, row_off, width, rows).astype(np.float32)
        hs_norm = hs / 255.0

        r = (bg_arr[0] + hs_norm * (tint_arr[0] - bg_arr[0])).astype(np.uint8)
        g = (bg_arr[1] + hs_norm * (tint_arr[1] - bg_arr[1])).astype(np.uint8)
        b = (bg_arr[2] + hs_norm * (tint_arr[2] - bg_arr[2])).astype(np.uint8)
        alpha = np.where(hs > 0, 255, 0).astype(np.uint8)

        out.GetRasterBand(1).WriteArray(r, 0, row_off)
        out.GetRasterBand(2).WriteArray(g, 0, row_off)
        out.GetRasterBand(3).WriteArray(b, 0, row_off)
        out.GetRasterBand(4).WriteArray(alpha, 0, row_off)

    out.FlushCache()
    out = None
    src = None


def _apply_color_tint_subprocess(
    input_gray: Path,
    output_path: Path,
    tint: Tuple[int, int, int],
    bg: Tuple[int, int, int],
) -> None:
    """
    Apply color tint using only GDAL CLI tools (no Python bindings required).

    Uses gdal_calc.py to compute each RGBA band as a linear blend:
        channel = bg + (A / 255.0) * (tint - bg)
        alpha   = where(A > 0, 255, 0)

    Then merges bands into a single RGBA GeoTIFF via gdal_merge.py.
    """
    tmp_dir = Path(tempfile.mkdtemp(prefix="ilhmp_tint_"))

    try:
        # Compute each band with gdal_calc.py
        band_files = []
        for i, (ch_name, t_val, b_val) in enumerate([
            ("R", tint[0], bg[0]),
            ("G", tint[1], bg[1]),
            ("B", tint[2], bg[2]),
        ]):
            out_band = tmp_dir / f"band_{ch_name}.tif"
            band_files.append(out_band)

            # Formula: bg + (A / 255.0) * (tint - bg), clamped to uint8
            calc_expr = f"{b_val} + (A / 255.0) * ({t_val} - {b_val})"
            cmd = [
                "gdal_calc.py",
                "-A", str(input_gray),
                f"--calc={calc_expr}",
                f"--outfile={out_band}",
                "--type=Byte",
                "--co=COMPRESS=DEFLATE",
                "--co=TILED=YES",
                "--co=BIGTIFF=IF_SAFER",
                "--quiet",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"gdal_calc.py ({ch_name}) failed: {result.stderr}")

        # Alpha band: 255 where input > 0, else 0
        alpha_band = tmp_dir / "band_A.tif"
        band_files.append(alpha_band)
        cmd = [
            "gdal_calc.py",
            "-A", str(input_gray),
            "--calc=(A > 0) * 255",
            f"--outfile={alpha_band}",
            "--type=Byte",
            "--co=COMPRESS=DEFLATE",
            "--co=TILED=YES",
            "--co=BIGTIFF=IF_SAFER",
            "--quiet",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"gdal_calc.py (alpha) failed: {result.stderr}")

        # Merge bands into RGBA using gdal_merge.py
        cmd = [
            "gdal_merge.py",
            "-o", str(output_path),
            "-separate",
            "-co", "COMPRESS=DEFLATE",
            "-co", "TILED=YES",
            "-co", "BIGTIFF=IF_SAFER",
            "-ot", "Byte",
        ] + [str(f) for f in band_files]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"gdal_merge.py failed: {result.stderr}")

    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


def get_styles() -> Dict[str, Dict]:
    """Return available color styles."""
    return STYLES.copy()
