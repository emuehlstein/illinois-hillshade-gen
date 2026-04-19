# Illinois Hillshade Generator

Download Illinois ILHMP elevation data by county and generate styled hillshade tiles for ATAK and offline mapping.

## Features

- **Download**: Fetch DTM/DSM data from [ISGS ILHMP](https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp) by county
- **Hillshade**: Generate hillshades with configurable exaggeration, lighting, and color schemes
- **Tile**: Output to MBTiles or PMTiles for offline mapping apps
- **View**: Built-in local tile viewer with basemap switching

## Installation

```bash
pip install ilhmp
```

### Requirements

- Python 3.10+
- GDAL (with Python bindings)
- mb-util (`pip install mbutil`)
- pmtiles CLI (optional, for PMTiles output)

On macOS with Homebrew:
```bash
brew install gdal
pip install gdal mbutil
brew install pmtiles  # optional
```

## Quick Start

```bash
# Full pipeline for a county (with viewer)
ilhmp run putnam --dem dtm --style dark --zoom 10-16 --view

# Just download
ilhmp download putnam --dem dtm --output putnam_dtm.tif

# Generate hillshade from existing DEM
ilhmp hillshade putnam_dtm.tif --style dark --exaggeration 3

# Generate tiles
ilhmp tile putnam_hillshade.tif --zoom 10-16 --format mbtiles

# Launch viewer for existing tiles
ilhmp view ./putnam-hillshade/tiles --port 9999
```

## Commands

| Command | Description |
|---------|-------------|
| `ilhmp run` | Full pipeline: download → hillshade → tile |
| `ilhmp download` | Download elevation data for a county |
| `ilhmp hillshade` | Generate styled hillshade from a DEM |
| `ilhmp tile` | Generate MBTiles/PMTiles from hillshade |
| `ilhmp view` | Launch local tile viewer |
| `ilhmp counties` | List available counties |

## Color Styles

| Style | Description | Use Case |
|-------|-------------|----------|
| `dark` | Blue-gray on dark background | ATAK dark mode |
| `light` | Warm gray on light background | ATAK light mode |
| `tactical` | Olive drab | Low-visibility displays |
| `terrain` | Earth tones | Topographic overlays |
| `gray` | Pure grayscale | Base for custom coloring |

## Viewer

The built-in viewer provides:
- Hillshade overlay with opacity control
- Three basemaps: Dark, Light, Satellite
- Layer toggle
- Metadata display

![Viewer Screenshot](docs/viewer.png)

Launch with:
```bash
ilhmp view ./output/tiles
# or
ilhmp run county --view
```

## Available Counties

```bash
ilhmp counties --available
```

See the [ISGS ILHMP page](https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp) for full data availability.

## Examples

### Generate tiles for Cook County

```bash
# Download and process (148GB ZIP, will take a while)
ilhmp run cook --dem dsm --style dark --zoom 10-16 --pmtiles

# Output: cook-hillshade/cook-hillshade-dark.mbtiles
#         cook-hillshade/cook-hillshade-dark.pmtiles
#         cook-hillshade/viewer.html
```

### Custom color scheme

```python
from ilhmp import hillshade

hillshade.generate(
    "cook_dtm.tif",
    "cook_custom.tif",
    style="custom",
    custom_tint=(0.4, 0.3, 0.5),  # Purple tint
    custom_bg=(20, 15, 25),
    exaggeration=3.0,
)
```

### Serve existing tiles

```bash
# From tiles directory
ilhmp view ./cook-hillshade/tiles

# From MBTiles
ilhmp view ./cook-hillshade/cook-dark.mbtiles
```

## License

MIT

## Credits

- Elevation data: [Illinois State Geological Survey](https://www.isgs.illinois.edu/)
- ILHMP: [Illinois Height Modernization Program](https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp)
