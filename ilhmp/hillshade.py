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

# Color presets: (R, G, B) multipliers for hillshade value, plus background RGB
STYLES: Dict[str, Dict] = {
    "dark": {
        "tint": (0.30, 0.40, 0.60),  # Blue-gray
        "bg": (18, 18, 18),           # Near-black
    },
    "light": {
        "tint": (0.85, 0.82, 0.78),  # Warm gray
        "bg": (250, 250, 250),        # Near-white
    },
    "tactical": {
        "tint": (0.33, 0.42, 0.18),  # Olive drab
        "bg": (24, 24, 20),
    },
    "terrain": {
        "tint": (0.55, 0.47, 0.40),  # Earth brown
        "bg": (245, 240, 230),
    },
    "gray": {
        "tint": (1.0, 1.0, 1.0),     # Pure grayscale
        "bg": (0, 0, 0),
    },
}


def generate(
    input_dem: Path,
    output_path: Path,
    style: str = "dark",
    exaggeration: float = 3.0,
    azimuth: float = 315.0,
    altitude: float = 45.0,
    custom_tint: Optional[Tuple[float, float, float]] = None,
    custom_bg: Optional[Tuple[int, int, int]] = None,
) -> Path:
    """
    Generate a styled hillshade from a DEM.
    
    Args:
        input_dem: Input DEM GeoTIFF
        output_path: Output styled hillshade GeoTIFF
        style: Color style name or 'custom'
        exaggeration: Vertical exaggeration factor
        azimuth: Sun azimuth in degrees (0-360, 0=N)
        altitude: Sun altitude in degrees (0-90)
        custom_tint: RGB multipliers (0-1) for custom style
        custom_bg: RGB background (0-255) for custom style
    
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
        
        # Step 2: Apply color tint
        if style == "gray":
            # Just copy the grayscale
            subprocess.run([
                "gdal_translate",
                "-co", "COMPRESS=DEFLATE",
                "-co", "TILED=YES",
                str(gray_path),
                str(output_path)
            ], check=True, capture_output=True)
        else:
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
    # Detect if input is in feet (common for ILHMP data)
    # Z-factor converts vertical to horizontal units
    # For WGS84 (degrees) input with feet elevation: z = exaggeration * 0.3048 / 111120
    # For now, assume reprojected to meters
    z_factor = exaggeration
    
    cmd = [
        "gdaldem", "hillshade",
        str(input_dem),
        str(output_path),
        "-z", str(z_factor),
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
    tint: Tuple[float, float, float],
    bg: Tuple[int, int, int],
) -> None:
    """Apply color tint to grayscale hillshade using GDAL."""
    from osgeo import gdal
    gdal.UseExceptions()
    
    src = gdal.Open(str(input_gray))
    band = src.GetRasterBand(1)
    data = band.ReadAsArray().astype(np.float32)
    nodata = band.GetNoDataValue()
    
    # Create nodata mask
    if nodata is not None:
        mask = (data == nodata) | (data < 1)
    else:
        mask = data < 1
    
    # Normalize to 0-1
    data = np.clip(data, 0, 255) / 255.0
    
    # Apply tint: blend from bg to tint based on hillshade value
    bg_norm = np.array(bg) / 255.0
    tint_arr = np.array(tint)
    
    r = (bg_norm[0] + data * (tint_arr[0] - bg_norm[0])) * 255
    g = (bg_norm[1] + data * (tint_arr[1] - bg_norm[1])) * 255
    b = (bg_norm[2] + data * (tint_arr[2] - bg_norm[2])) * 255
    
    # Alpha channel: transparent where nodata
    a = np.where(mask, 0, 255).astype(np.uint8)
    
    # Write output
    driver = gdal.GetDriverByName('GTiff')
    out = driver.Create(
        str(output_path),
        src.RasterXSize,
        src.RasterYSize,
        4,  # RGBA
        gdal.GDT_Byte,
        options=['COMPRESS=DEFLATE', 'TILED=YES']
    )
    out.SetGeoTransform(src.GetGeoTransform())
    out.SetProjection(src.GetProjection())
    out.GetRasterBand(1).WriteArray(np.clip(r, 0, 255).astype(np.uint8))
    out.GetRasterBand(2).WriteArray(np.clip(g, 0, 255).astype(np.uint8))
    out.GetRasterBand(3).WriteArray(np.clip(b, 0, 255).astype(np.uint8))
    out.GetRasterBand(4).WriteArray(a)
    out.FlushCache()
    out = None
    src = None
