# AGENTS.md — ilhmp agent usage guide

`ilhmp` (Illinois Hillshade Map Products) is a CLI tool that downloads 1-meter-resolution LiDAR elevation data from the Illinois State Geological Survey (ISGS) clearinghouse and produces styled hillshade map tiles suitable for offline GIS applications such as ATAK. The pipeline covers download → reprojection → hillshade generation → MBTiles/PMTiles output → interactive HTML viewer, with caching of all intermediate files to avoid redundant processing.

---

## System requirements

- **Python 3.10+**
- **GDAL** (provides `gdaldem`, `gdalwarp`, `gdal2tiles.py`, `ogr2ogr`) — install via Homebrew: `brew install gdal`
- **mb-util** — `pip install mbutil` or `brew install mb-util`
- **pmtiles CLI** (optional, only for PMTiles output) — `brew install protomaps/homebrew-protomaps/pmtiles`

---

## Installation

```bash
git clone <repo>
cd illinois-hillshade-gen
pip install -e .
```

---

## Common agent workflows

### List available counties (JSON)

```bash
ilhmp counties --json
```

Returns a JSON array. Each entry has `id`, `name`, `fips`, `district`, `year`, `dtm_url`, `dsm_url`, `dtm_imageserver_url`, `dsm_imageserver_url`, and `bounds` (nullable).

### Run the full pipeline for a county

```bash
ilhmp run putnam --dem dtm --style dark --zoom 10-16 --json
```

Use `--json` to get a machine-readable result object with paths to all generated files. Without `--json`, Rich-formatted progress is printed to stdout.

### Download only

```bash
ilhmp download cook --dem dtm --output ./cook_dtm.tif
```

Downloads the ZIP from the ISGS clearinghouse and extracts/converts the raster. Large counties (Cook ~3.7 GB, Bond ~1.7 GB) can take 10–40 minutes depending on connection speed.

### Use a pre-downloaded ZIP (skip network download)

```bash
# Extract + convert a local ZIP, then run the full pipeline
ilhmp run cook --dem dsm --source-zip /Volumes/MAPSTORE/IL/cook_dsm_2022.zip

# Or just extract to a GeoTIFF without running the pipeline
ilhmp download cook --dem dsm --source-zip /Volumes/MAPSTORE/IL/cook_dsm_2022.zip --output ./cook_dsm.tif
```

Useful for large counties (Cook DSM is ~148 GB zipped) where the ZIP is already on disk.

### Use an already-extracted GeoTIFF (skip download and extraction)

```bash
ilhmp run cook --dem dsm --source /Volumes/ssdtmp/cook_dsm.tif
```

Skips both the download and extraction steps entirely; the provided GeoTIFF is used as-is for reprojection.

### Separate intermediate files from outputs with --cache-dir

```bash
ilhmp run cook --dem dsm \
  --cache-dir /Volumes/ssdtmp/cache \
  --output /Volumes/ssdtmp/output
```

Intermediate files (`cook_dsm.tif`, `cook_dsm_4326.tif`, `cook_hillshade_dark.tif`) go to the cache dir. Final outputs (tiles, MBTiles, viewer, GeoJSON) go to the output dir. The cache dir can be wiped without losing results.

These flags can be combined:

```bash
ilhmp run cook --dem dsm \
  --source-zip /Volumes/MAPSTORE/IL/cook_dsm_2022.zip \
  --cache-dir /Volumes/ssdtmp/cache \
  --output /Volumes/ssdtmp/output \
  --json
```

### Generate hillshade from an existing DEM

```bash
ilhmp hillshade ./cook_dtm_4326.tif --style dark --exaggeration 3
```

### Generate tiles from an existing hillshade

```bash
ilhmp tile ./cook_hillshade_dark.tif --zoom 10-16 --format mbtiles
```

### Get a county boundary as GeoJSON

```bash
ilhmp boundary cook --json
# → {"county": "cook", "geojson": "/abs/path/to/cook.geojson"}
```

### View tiles locally

```bash
ilhmp view ./cook-hillshade/tiles_dark --port 9999
```

---

## Output file structure

After `ilhmp run cook --style dark`, the output directory (`./cook-hillshade/` by default) contains:

```
cook-hillshade/
├── cook_dtm.tif                   # Raw 1m DEM (native projection)
├── cook_dtm_4326.tif              # DEM reprojected to WGS84
├── cook_hillshade_dark.tif        # RGBA hillshade GeoTIFF
├── tiles_dark/                    # XYZ tile directory (z10–16)
│   └── {z}/{x}/{y}.png
├── cook-hillshade-dark.mbtiles    # Packed MBTiles archive
├── cook-hillshade-dark.pmtiles    # PMTiles archive (--pmtiles only)
├── cook.geojson                   # County boundary
└── viewer.html                    # Interactive Leaflet viewer
```

---

## JSON output reference

### `ilhmp counties --json`

```json
[
  {
    "id": "putnam",
    "name": "Putnam",
    "fips": "17155",
    "district": "district4",
    "year": "2012",
    "dtm_url": "https://clearinghouse.isgs.illinois.edu/distribute/district4/putnam/2012/putn_dtm_2012.zip",
    "dsm_url": "https://clearinghouse.isgs.illinois.edu/distribute/district4/putnam/2012/putn_dsm_2012.zip",
    "dtm_imageserver_url": "https://data.isgs.illinois.edu/arcgis/rest/services/Elevation/IL_Putnam_DTM_2012/ImageServer",
    "dsm_imageserver_url": "https://data.isgs.illinois.edu/arcgis/rest/services/Elevation/IL_Putnam_DSM_2012/ImageServer",
    "bounds": [-89.48, 41.10, -89.15, 41.32]
  },
  ...
]
```

`bounds` is `[west, south, east, north]` in WGS84. It is `null` for counties without pre-computed bounds.

### `ilhmp run <county> --json`

```json
{
  "county": "Putnam",
  "dem": "DTM",
  "style": "dark",
  "output_dir": "/abs/path/to/putnam-hillshade",
  "files": {
    "dem": "/abs/path/putnam_dtm.tif",
    "dem_4326": "/abs/path/putnam_dtm_4326.tif",
    "hillshade": "/abs/path/putnam_hillshade_dark.tif",
    "tiles_dir": "/abs/path/tiles_dark",
    "mbtiles": "/abs/path/putnam-hillshade-dark.mbtiles",
    "viewer": "/abs/path/viewer.html",
    "geojson": "/abs/path/putnam.geojson",
    "pmtiles": null
  }
}
```

### `ilhmp boundary <county> --json`

```json
{"county": "cook", "geojson": "/abs/path/cook.geojson"}
```

---

## Error handling tips

- **Disk space**: Reserve at least 10 GB per county before running. Cook county raw data is ~3.7 GB; intermediate TIFFs add another 5–8 GB.
- **Download time**: ISGS downloads run 5–40 minutes for large counties. The tool does not resume partial downloads; if interrupted, delete the partial `.tif` and retry.
- **Caching**: All intermediate files are cached. Re-running `ilhmp run` skips already-completed steps. To force a re-run, delete the specific output file.
- **Missing DSM**: Some counties (e.g. Kane 2008) only have DTM data. Use `--dem dtm` for those. `ilhmp counties --json` shows `"dsm_url": null` when DSM is unavailable.
- **Unknown county**: `ilhmp run` exits with code 1 and prints `{"error": "Unknown county: ..."}` in `--json` mode. Run `ilhmp counties --json` to get the full list of valid county IDs.
- **URL verification**: Most county URLs follow the documented pattern and are not individually verified. If a download fails with HTTP 404, the ZIP filename or district may differ from the catalog — check the ISGS clearinghouse directly.
- **Large rasters**: The hillshade step processes large rasters in 1000-row chunks to avoid OOM. It still requires enough RAM for one chunk (~width × 1000 × 4 bytes).

---

## County catalog format

The catalog is defined in `ilhmp/counties.py`. Each entry:

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | Lookup key (lowercase, no spaces) |
| `name` | str | Display name |
| `fips` | str | 5-digit Illinois FIPS code |
| `district` | str | ISGS district (`district1`–`district9`) |
| `year` | str | Survey year |
| `dtm_zip` | str\|None | ZIP filename for bare-earth DTM |
| `dsm_zip` | str\|None | ZIP filename for surface DSM |
| `dtm_url` | str | Full clearinghouse download URL (built at runtime) |
| `dsm_url` | str\|None | Full DSM URL, or absent if unavailable |
| `dtm_imageserver_url` | str | ArcGIS ImageServer REST URL |
| `bounds` | list\|None | `[west, south, east, north]` in WGS84, if known |

District assignments follow ISGS geographic regions: district1 = NE IL / Chicago metro, districts 2–3 = N/NW IL, district4 = central, district5 = east-central, district6 = western, districts 7–9 = southern IL.
