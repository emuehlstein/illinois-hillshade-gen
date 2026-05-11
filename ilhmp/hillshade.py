"""
Hillshade generation with color styling.

Styles:
- dark: Blue-gray on dark background (ATAK dark mode)
- light: Warm gray on light background (ATAK light mode)
- tactical: Olive drab on dark background
- terrain: Earth tones
- gray: Grayscale (no tint)
"""

import shutil
import subprocess
import tempfile
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple, Dict, List

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
        "tint": (105, 130, 180),    # Blue (v2e)
        "bg": (18, 25, 45),          # Dark navy
    },
    "light": {
        "tint": (250, 246, 240),    # Warm white (v2c)
        "bg": (85, 72, 52),          # Warm sepia shadow
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

# Directory containing bundled ramp files
_RAMPS_DIR = Path(__file__).parent / "ramps"


class ShadingMode(str, Enum):
    STANDARD = "standard"
    MULTIDIRECTIONAL = "multidirectional"
    COMBINED = "combined"
    IGOR = "igor"
    COMPOSITE = "composite"


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
    shading_mode: ShadingMode = ShadingMode.MULTIDIRECTIONAL,
    color_mode: str = "ramp",
    composite_weights: Optional[Tuple[float, float, float]] = None,
    ramp_file: Optional[Path] = None,
    legacy: bool = False,
    aspect_blend: float = 0.0,
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
        cache_dir: Directory to cache intermediate grayscale hillshade TIFs.
        force_recompute: Ignore any cached grayscale TIF and regenerate it.
        shading_mode: Shading algorithm (default MULTIDIRECTIONAL).
        color_mode: 'ramp' (default, uses gdaldem color-relief on hillshade),
            'tint' (legacy blend), or 'elevation' (color-relief on DEM,
            modulated by hillshade for 3D effect).
        composite_weights: (multi, igor, combined) weights for COMPOSITE mode.
            Defaults to (0.6, 0.3, 0.1).
        ramp_file: Path to a custom GDAL color-relief ramp file. Defaults to
            bundled ramp matching ``style``.
        legacy: Restore v1 behavior (STANDARD shading, tint color_mode).

    Returns:
        Path to the output file
    """
    input_dem = Path(input_dem)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if legacy:
        shading_mode = ShadingMode.STANDARD
        color_mode = "tint"

    # Resolve tint/bg colors (needed for tint color_mode)
    if color_mode == "tint":
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
    else:
        tint = bg = None

    # Resolve ramp file (needed for ramp and elevation color_mode)
    if color_mode in ("ramp", "elevation") and ramp_file is None:
        candidate = _RAMPS_DIR / f"{style}.txt"
        if candidate.exists():
            ramp_file = candidate
        elif style not in STYLES:
            raise ValueError(f"Unknown style: {style}. Available: {list(STYLES.keys())}")
        else:
            # Fall back to tint if no ramp for custom style
            color_mode = "tint"
            tint = custom_tint or STYLES[style]["tint"]
            bg = custom_bg or STYLES[style]["bg"]

    # Determine grayscale cache path
    if cache_dir is not None:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        mode_tag = shading_mode.value if isinstance(shading_mode, ShadingMode) else shading_mode
        gray_cache = cache_dir / f"{input_dem.stem}_gray_z{exaggeration}_{mode_tag}.tif"
    else:
        gray_cache = None

    with tempfile.TemporaryDirectory() as _tmp:
        tmp_dir = Path(_tmp)

        if shading_mode == ShadingMode.COMPOSITE:
            gray_path = _generate_composite(
                input_dem, tmp_dir, exaggeration, azimuth, altitude,
                composite_weights, cache_dir, force_recompute,
                aspect_blend=aspect_blend,
            )
        else:
            gray_path = tmp_dir / "hillshade_gray.tif"

            if gray_cache and gray_cache.exists() and not force_recompute:
                gray_path = gray_cache
            else:
                _generate_grayscale(
                    input_dem, gray_path, exaggeration, azimuth, altitude,
                    shading_mode=shading_mode,
                )
                if gray_cache is not None:
                    shutil.copy2(gray_path, gray_cache)
                    gray_path = gray_cache

        if color_mode == "elevation":
            _apply_elevation_color(
                input_dem, gray_path, output_path, ramp_file,
                aspect_blend=aspect_blend,
            )
        elif color_mode == "ramp":
            generate_color_relief(gray_path, output_path, ramp_file)
        else:
            _apply_color_tint(gray_path, output_path, tint, bg)

    return output_path


def _generate_grayscale(
    input_dem: Path,
    output_path: Path,
    exaggeration: float,
    azimuth: float,
    altitude: float,
    shading_mode: ShadingMode = ShadingMode.MULTIDIRECTIONAL,
) -> None:
    """Generate grayscale hillshade using gdaldem."""
    cmd = [
        "gdaldem", "hillshade",
        str(input_dem),
        str(output_path),
        "-z", str(exaggeration),
        "-compute_edges",
        "-co", "COMPRESS=LZW",
        "-co", "TILED=YES",
        "-co", "BIGTIFF=YES",
    ]

    if shading_mode == ShadingMode.MULTIDIRECTIONAL:
        cmd.append("-multidirectional")
    elif shading_mode == ShadingMode.COMBINED:
        cmd.append("-combined")
    elif shading_mode == ShadingMode.IGOR:
        cmd.append("-igor")
    else:
        # STANDARD: use azimuth and altitude
        cmd += ["-az", str(azimuth), "-alt", str(altitude)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdaldem failed: {result.stderr}")


def _generate_composite(
    input_dem: Path,
    tmp_dir: Path,
    exaggeration: float,
    azimuth: float,
    altitude: float,
    weights: Optional[Tuple[float, float, float]],
    cache_dir: Optional[Path],
    force_recompute: bool,
    aspect_blend: float = 0.1,
) -> Path:
    """
    Generate composite hillshade by blending multidirectional, igor, and combined,
    with an optional aspect overlay for depth cues (Simmon technique).

    The aspect layer encodes slope direction (0-360°) which is rescaled to a
    0-255 grayscale and subtly blended into the composite.  This adds depth
    perception — northeast-facing slopes darken, southwest-facing slopes brighten
    — mimicking the Simmon multi-layer approach.

    Returns path to blended grayscale TIF.
    """
    w_multi, w_igor, w_combined = weights if weights else (0.6, 0.3, 0.1)

    layers: List[Tuple[ShadingMode, float]] = [
        (ShadingMode.MULTIDIRECTIONAL, w_multi),
        (ShadingMode.IGOR, w_igor),
        (ShadingMode.COMBINED, w_combined),
    ]

    layer_paths: List[Path] = []
    for mode, _ in layers:
        mode_tag = mode.value
        if cache_dir is not None:
            cached = cache_dir / f"{input_dem.stem}_gray_z{exaggeration}_{mode_tag}.tif"
        else:
            cached = None

        layer_path = tmp_dir / f"gray_{mode_tag}.tif"
        if cached and cached.exists() and not force_recompute:
            layer_path = cached
        else:
            _generate_grayscale(
                input_dem, layer_path, exaggeration, azimuth, altitude,
                shading_mode=mode,
            )
            if cached is not None:
                shutil.copy2(layer_path, cached)
                layer_path = cached
        layer_paths.append(layer_path)

    # Generate aspect layer for depth cues
    aspect_path = None
    if aspect_blend > 0:
        if cache_dir is not None:
            aspect_cached = cache_dir / f"{input_dem.stem}_aspect.tif"
        else:
            aspect_cached = None

        aspect_raw = tmp_dir / "aspect_raw.tif"
        if aspect_cached and aspect_cached.exists() and not force_recompute:
            aspect_raw = aspect_cached
        else:
            # gdaldem aspect produces 0-360 float values
            cmd = [
                "gdaldem", "aspect",
                str(input_dem), str(aspect_raw),
                "-compute_edges",
                "-co", "COMPRESS=LZW",
                "-co", "TILED=YES",
                "-co", "BIGTIFF=YES",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"gdaldem aspect failed: {result.stderr}")
            if aspect_cached is not None:
                shutil.copy2(aspect_raw, aspect_cached)
                aspect_raw = aspect_cached
        aspect_path = aspect_raw

    # Blend hillshade layers + optional aspect
    composite_path = tmp_dir / "gray_composite.tif"
    if aspect_path and aspect_blend > 0:
        # Scale aspect from 0-360° to 0-255 grayscale, then blend.
        # NE-facing slopes (45°) → dark, SW-facing (225°) → bright,
        # using cosine mapping: 127.5 + 127.5 * cos(aspect_rad - sun_az_rad)
        hs_weight = 1.0 - aspect_blend
        calc_expr = (
            f"numpy.clip("
            f"{hs_weight} * ({w_multi}*A + {w_igor}*B + {w_combined}*C) + "
            f"{aspect_blend} * numpy.where(D == -1, 128, "
            f"127.5 + 127.5 * numpy.cos(numpy.radians(D) - {azimuth * 3.14159265 / 180.0}))"
            f", 0, 255).astype(numpy.uint8)"
        )
        cmd = [
            "gdal_calc.py",
            "-A", str(layer_paths[0]),
            "-B", str(layer_paths[1]),
            "-C", str(layer_paths[2]),
            "-D", str(aspect_path),
            f"--calc={calc_expr}",
            f"--outfile={composite_path}",
            "--type=Byte",
            "--co=COMPRESS=LZW",
            "--co=TILED=YES",
            "--co=BIGTIFF=YES",
            "--quiet",
        ]
    else:
        calc_expr = (
            f"numpy.clip({w_multi}*A + {w_igor}*B + {w_combined}*C, 0, 255).astype(numpy.uint8)"
        )
        cmd = [
            "gdal_calc.py",
            "-A", str(layer_paths[0]),
            "-B", str(layer_paths[1]),
            "-C", str(layer_paths[2]),
            f"--calc={calc_expr}",
            f"--outfile={composite_path}",
            "--type=Byte",
            "--co=COMPRESS=LZW",
            "--co=TILED=YES",
            "--co=BIGTIFF=YES",
            "--quiet",
        ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdal_calc.py (composite) failed: {result.stderr}")

    return composite_path


def _apply_elevation_color(
    input_dem: Path,
    gray_path: Path,
    output_path: Path,
    ramp_file: Path,
    aspect_blend: float = 0.0,
    gamma: float = 0.75,
    chunk_size: int = 1000,
) -> None:
    """
    Elevation-mapped color mode: apply color-relief to the DEM based on actual
    elevation, then modulate by the grayscale hillshade for 3D effect.

    Ramp files can use percentage notation (0%, 50%, 100%) which are auto-scaled
    to the DEM's actual min/max, or absolute elevation values.

    The hillshade is gamma-adjusted and multiplied into the elevation colors
    so that shadows darken the color and highlights brighten it.
    """
    if not HAS_GDAL_PYTHON:
        raise RuntimeError("Elevation color mode requires GDAL Python bindings")

    input_dem = Path(input_dem)
    gray_path = Path(gray_path)

    # Read ramp file and resolve percentage values if needed
    ramp_lines = Path(ramp_file).read_text().strip().splitlines()
    has_percentages = any("%" in line.split()[0] for line in ramp_lines
                         if line.strip() and not line.strip().startswith("nv"))

    if has_percentages:
        # Get DEM min/max for scaling
        dem_ds = gdal.Open(str(input_dem))
        dem_band = dem_ds.GetRasterBand(1)
        dem_stats = dem_band.ComputeStatistics(False)  # min, max, mean, stddev
        dem_min, dem_max = dem_stats[0], dem_stats[1]
        dem_ds = None

        # Rewrite ramp with absolute values
        resolved_lines = []
        for line in ramp_lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if parts[0] == "nv":
                resolved_lines.append(line)
            elif "%" in parts[0]:
                pct = float(parts[0].replace("%", "")) / 100.0
                elev = dem_min + pct * (dem_max - dem_min)
                resolved_lines.append(f"{elev:.2f} {' '.join(parts[1:])}")
            else:
                resolved_lines.append(line)

        # Write temporary resolved ramp
        resolved_ramp = Path(str(ramp_file) + ".resolved.tmp")
        resolved_ramp.write_text("\n".join(resolved_lines) + "\n")
    else:
        resolved_ramp = Path(ramp_file)

    try:
        # Step 1: color-relief on the DEM
        with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
            elev_color_path = Path(tmp.name)

        cmd = [
            "gdaldem", "color-relief",
            str(input_dem), str(resolved_ramp), str(elev_color_path),
            "-alpha",
            "-co", "COMPRESS=LZW",
            "-co", "TILED=YES",
            "-co", "BIGTIFF=YES",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"gdaldem color-relief (elevation) failed: {result.stderr}")

        # Step 2: modulate elevation colors by hillshade
        gray_ds = gdal.Open(str(gray_path))
        color_ds = gdal.Open(str(elev_color_path))
        xsize = gray_ds.RasterXSize
        ysize = gray_ds.RasterYSize

        driver = gdal.GetDriverByName("GTiff")
        out_ds = driver.Create(
            str(output_path), xsize, ysize, 4, gdal.GDT_Byte,
            ["COMPRESS=DEFLATE", "TILED=YES", "BIGTIFF=YES"],
        )
        out_ds.SetProjection(gray_ds.GetProjection())
        out_ds.SetGeoTransform(gray_ds.GetGeoTransform())

        gray_band = gray_ds.GetRasterBand(1)
        r_band = color_ds.GetRasterBand(1)
        g_band = color_ds.GetRasterBand(2)
        b_band = color_ds.GetRasterBand(3)
        a_band = color_ds.GetRasterBand(4) if color_ds.RasterCount >= 4 else None

        for y0 in range(0, ysize, chunk_size):
            rows = min(chunk_size, ysize - y0)
            hs = gray_band.ReadAsArray(0, y0, xsize, rows).astype(np.float32)
            r = r_band.ReadAsArray(0, y0, xsize, rows).astype(np.float32)
            g = g_band.ReadAsArray(0, y0, xsize, rows).astype(np.float32)
            b = b_band.ReadAsArray(0, y0, xsize, rows).astype(np.float32)

            # Gamma-adjusted hillshade as illumination factor
            hs_norm = np.power(np.clip(hs / 255.0, 0.001, 1.0), gamma)

            # Modulate
            r_out = np.clip(r * hs_norm, 0, 255).astype(np.uint8)
            g_out = np.clip(g * hs_norm, 0, 255).astype(np.uint8)
            b_out = np.clip(b * hs_norm, 0, 255).astype(np.uint8)

            # Alpha: opaque where hillshade > 0
            if a_band is not None:
                a = a_band.ReadAsArray(0, y0, xsize, rows)
            else:
                a = np.where(hs > 0, 255, 0).astype(np.uint8)

            out_ds.GetRasterBand(1).WriteArray(r_out, 0, y0)
            out_ds.GetRasterBand(2).WriteArray(g_out, 0, y0)
            out_ds.GetRasterBand(3).WriteArray(b_out, 0, y0)
            out_ds.GetRasterBand(4).WriteArray(a, 0, y0)

        out_ds.FlushCache()
        out_ds = None
        gray_ds = None
        color_ds = None

    finally:
        # Clean up temp files
        if has_percentages and resolved_ramp.exists():
            resolved_ramp.unlink()
        if elev_color_path.exists():
            elev_color_path.unlink()


def generate_color_relief(
    input_gray: Path,
    output_path: Path,
    ramp_file: Path,
) -> None:
    """
    Apply a GDAL color-relief ramp to a grayscale hillshade.

    Args:
        input_gray: Grayscale hillshade GeoTIFF
        output_path: Output colored GeoTIFF
        ramp_file: GDAL color-relief compatible ramp file
    """
    cmd = [
        "gdaldem", "color-relief",
        str(input_gray),
        str(ramp_file),
        str(output_path),
        "-alpha",
        "-co", "COMPRESS=DEFLATE",
        "-co", "TILED=YES",
        "-co", "BIGTIFF=YES",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdaldem color-relief failed: {result.stderr}")


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
        shutil.rmtree(tmp_dir, ignore_errors=True)


def get_styles() -> Dict[str, Dict]:
    """Return available color styles."""
    return STYLES.copy()
