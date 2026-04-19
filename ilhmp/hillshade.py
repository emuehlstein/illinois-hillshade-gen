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
from osgeo import gdal

gdal.UseExceptions()

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
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        gray_path = tmp_dir / "hillshade_gray.tif"
        
        # Step 1: Generate grayscale hillshade
        _generate_grayscale(input_dem, gray_path, exaggeration, azimuth, altitude)
        
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
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gdaldem failed: {result.stderr}")


def _apply_color_tint(
    input_gray: Path,
    output_path: Path,
    tint: Tuple[int, int, int],
    bg: Tuple[int, int, int],
) -> None:
    """
    Apply color tint to grayscale hillshade.
    
    Uses numpy for correct alpha channel handling.
    Hillshade value 0 = nodata (transparent), 1-255 = valid data.
    """
    src = gdal.Open(str(input_gray))
    hs = src.GetRasterBand(1).ReadAsArray().astype(np.float32)
    
    # Normalize hillshade 0-255 -> 0-1
    hs_norm = hs / 255.0
    
    # Calculate RGB: interpolate from bg to tint based on hillshade
    bg_arr = np.array(bg, dtype=np.float32)
    tint_arr = np.array(tint, dtype=np.float32)
    
    r = (bg_arr[0] + hs_norm * (tint_arr[0] - bg_arr[0])).astype(np.uint8)
    g = (bg_arr[1] + hs_norm * (tint_arr[1] - bg_arr[1])).astype(np.uint8)
    b = (bg_arr[2] + hs_norm * (tint_arr[2] - bg_arr[2])).astype(np.uint8)
    
    # Alpha: 255 where hillshade > 0, 0 where nodata
    alpha = np.where(hs > 0, 255, 0).astype(np.uint8)
    
    # Write RGBA output
    driver = gdal.GetDriverByName('GTiff')
    out = driver.Create(
        str(output_path),
        src.RasterXSize,
        src.RasterYSize,
        4,  # RGBA
        gdal.GDT_Byte,
        options=['COMPRESS=DEFLATE', 'TILED=YES', 'BIGTIFF=IF_SAFER']
    )
    out.SetGeoTransform(src.GetGeoTransform())
    out.SetProjection(src.GetProjection())
    out.GetRasterBand(1).WriteArray(r)
    out.GetRasterBand(2).WriteArray(g)
    out.GetRasterBand(3).WriteArray(b)
    out.GetRasterBand(4).WriteArray(alpha)
    out.FlushCache()
    out = None
    src = None


def get_styles() -> Dict[str, Dict]:
    """Return available color styles."""
    return STYLES.copy()
