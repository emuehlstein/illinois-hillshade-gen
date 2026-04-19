# Illinois Hillshade Generator (ilhmp)

Download Illinois ILHMP elevation data by county and generate styled hillshade tiles for ATAK and offline mapping.

## Features

- **Download**: Fetch full 1m resolution DTM/DSM data from [ISGS ILHMP](https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp)
- **Hillshade**: Generate hillshades with configurable exaggeration, lighting, and color schemes
- **Tile**: Output to MBTiles or PMTiles for offline mapping apps
- **View**: Built-in local tile viewer with basemap switching
- **Boundaries**: Extract county boundaries from ISGS shapefile

## Installation

```bash
pip install -e .
```

### Requirements

- Python 3.10+
- GDAL (with Python bindings)
- mb-util (`pip install mbutil`)
- pmtiles CLI (optional, for PMTiles output)

On macOS with Homebrew:
```bash
brew install gdal
pip install gdal mbutil numpy
brew install pmtiles  # optional
```

## Quick Start

```bash
# Full pipeline for a county (downloads ~2GB, generates tiles z10-16)
ilhmp run putnam --dem dtm --style dark --zoom 10-16 --view

# Just download
ilhmp download putnam --dem dtm --output putnam_dtm.tif

# Generate hillshade from existing DEM
ilhmp hillshade putnam_dtm.tif --style tactical --exaggeration 3

# Generate tiles
ilhmp tile putnam_hillshade.tif --zoom 10-16 --format mbtiles

# Launch viewer for existing tiles
ilhmp view ./putnam-hillshade/tiles --port 9999

# Download county boundary
ilhmp boundary putnam -o putnam.geojson
```

## Commands

| Command | Description |
|---------|-------------|
| `ilhmp run` | Full pipeline: download → hillshade → tile |
| `ilhmp download` | Download elevation data for a county |
| `ilhmp hillshade` | Generate styled hillshade from a DEM |
| `ilhmp tile` | Generate MBTiles/PMTiles from hillshade |
| `ilhmp view` | Launch local tile viewer |
| `ilhmp boundary` | Download county boundary as GeoJSON |
| `ilhmp counties` | List available counties |

## Color Styles

| Style | Tint | Background | Use Case |
|-------|------|------------|----------|
| `dark` | Blue-gray (77,102,153) | Near-black (18,18,18) | ATAK dark mode |
| `light` | Warm gray (217,209,199) | Near-white (250,250,250) | ATAK light mode |
| `tactical` | Olive drab (85,107,47) | Dark olive (24,24,20) | Low-visibility/military |
| `terrain` | Earth brown (140,120,100) | Cream (245,240,230) | Topographic overlays |
| `gray` | White (255,255,255) | Black (0,0,0) | Base for custom coloring |

### Custom Colors

```python
from ilhmp import hillshade

hillshade.generate(
    "dem.tif",
    "custom.tif",
    style="custom",
    custom_tint=(100, 50, 150),  # Purple
    custom_bg=(20, 10, 30),
    exaggeration=3.0,
)
```

## Data Sources

### Elevation Data
- **Source:** [ISGS Illinois Height Modernization Program (ILHMP)](https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp)
- **Resolution:** 1m native LiDAR
- **Format:** ZIP containing ESRI ArcGrid (.adf) or GeoTIFF
- **Coverage:** Most Illinois counties (check `ilhmp counties --available`)

### County Boundaries
- **Source:** [ISGS County Boundaries](https://clearinghouse.isgs.illinois.edu/data/reference/illinois-county-boundaries-polygons-and-lines)
- **File:** `IL_BNDY_County.zip`
- **Local cache:** `~/.cache/ilhmp/IL_BNDY_County/`

## Viewer

The built-in viewer provides:
- Hillshade overlay with opacity control
- Three basemaps: Dark, Light, Satellite (CARTO + ESRI)
- Real county boundary polygon (not just bounding box)
- Live zoom level display
- Layer toggle controls

Launch with:
```bash
ilhmp view ./tiles --port 9999
# or
ilhmp run putnam --view
```

## Pipeline Details

1. **Download:** Fetches ZIP from ISGS clearinghouse (~2GB for small counties)
2. **Extract:** Unzips and converts ESRI ArcGrid to GeoTIFF if needed
3. **Reproject:** Transforms to EPSG:4326 (WGS84) for web mapping
4. **Hillshade:** Generates grayscale hillshade with `gdaldem` (z=3, az=315, alt=45)
5. **Colorize:** Applies style tint with proper alpha channel handling
6. **Tile:** Creates XYZ tiles with `gdal2tiles.py` (z10-16 recommended)
7. **Pack:** Bundles into MBTiles/PMTiles for distribution

### Tile Zoom Levels

| Zoom | Ground Resolution | Use Case |
|------|------------------|----------|
| z10-12 | ~150-40m | Overview, state-level |
| z13-14 | ~20-10m | County-level detail |
| z15-16 | ~5-2.5m | Full 1m LiDAR detail |
| z17+ | <1.5m | Only if native >1m resolution |

## Tested Counties

- **Putnam** (smallest): 2.4GB ZIP, 5,384 tiles, ~5min pipeline
- **Cook** (largest): 148GB ZIP, ~500K tiles, ~9hr pipeline

## License

MIT

## Credits

- Elevation data: [Illinois State Geological Survey](https://www.isgs.illinois.edu/)
- ILHMP: [Illinois Height Modernization Program](https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp)
