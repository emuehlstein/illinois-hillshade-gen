# AGENTS.md — ilhmp agent usage guide

`ilhmp` is the CLI for the **illinois-hillshade-gen** platform. It downloads 1m-resolution LiDAR elevation data from the Illinois State Geological Survey (ISGS) clearinghouse and produces styled hillshade tiles for ATAK, offline use, and web publication.

**Full pipeline:** download → reproject → hillshade → tile → MBTiles → push/publish

---

## System requirements

- **Python 3.10+**
- **GDAL** (`gdaldem`, `gdalwarp`, `gdal2tiles.py`) — `brew install gdal`
- **mb-util** — `pip install mbutil`
- **pmtiles CLI** (publish workflow) — `brew install protomaps/homebrew-protomaps/pmtiles`
- **AWS CLI** (publish workflow) — configured with access to `s3://exaggeratedrelief`
- **SSH key** `~/.ssh/mapserver-ec2.pem` (push workflow) — access to tile server EC2

---

## Installation

```bash
git clone https://github.com/emuehlstein/illinois-hillshade-gen
cd illinois-hillshade-gen
pip install -e .
```

---

## Themes

Themes are named presets covering shading mode, color ramp, and exaggeration. Always use `--theme` rather than `--style` for new work.

```bash
ilhmp themes                    # list all themes
ilhmp themes --show simmon      # full details + equivalent CLI flags
```

Key themes for Illinois flat terrain:

| Theme | Best for |
|-------|----------|
| `atak-dark` | ATAK dark mode overlays |
| `atak-light` | ATAK light mode overlays |
| `simmon` | Best overall rendering |
| `flat-terrain` | Maximum visibility, flat IL/IN terrain (15× fixed) |
| `tactical` | Military/olive style |
| `cool-elevation` | Elevation-mapped cartographic |
| `vivid` / `vivid-elevation` | High-contrast false color |
| `grayscale` | Base layer for custom coloring |

---

## Common agent workflows

### Full pipeline for a county

```bash
# Preferred: named theme
ilhmp run putnam --theme atak-dark --zoom 9-16

# With local DEM cache (skips re-download on reruns)
ilhmp run putnam --theme atak-dark --zoom 9-16 \
  --cache-dir /Volumes/ExtSSD1TB/dem/IL/putnam-cache \
  --output /Volumes/ExtSSD1TB/dem/IL/putnam-themes-9x/atak-dark

# Multiple themes from the same cached DEM (run sequentially, cache reused)
ilhmp run putnam --theme atak-dark   --cache-dir ./cache
ilhmp run putnam --theme atak-light  --cache-dir ./cache
ilhmp run putnam --theme flat-terrain --cache-dir ./cache

# Force-recompute (bypass cached hillshade TIF — use when cache is corrupt)
ilhmp run putnam --theme tactical --force-recompute --cache-dir ./cache

# JSON output for scripting
ilhmp run putnam --theme atak-dark --json
```

### List available counties

```bash
ilhmp counties           # rich table
ilhmp counties --json    # machine-readable array
```

### Use a pre-downloaded source

```bash
# Local ZIP (skip network download)
ilhmp run cook --theme simmon --source-zip /path/to/cook_dtm.zip

# Existing GeoTIFF (skip download + extraction entirely)
ilhmp run cook --theme simmon --source /path/to/cook_dtm.tif
```

### Auxiliary terrain layers

```bash
ilhmp layers cook --dem dtm --output aspect,slope,roughness,TRI
```

### Local preview (all tiles in a directory)

```bash
ilhmp serve --dirs /Volumes/ExtSSD1TB/dem/IL/kendall-themes-9x
# → opens http://localhost:9999 with a layer switcher
```

---

## Publishing workflow

There are two separate publication targets:

| Command | Output | Destination |
|---------|--------|-------------|
| `ilhmp push` | MBTiles → tile server | `tiles.exaggeratedrelief.com` (XYZ) |
| `ilhmp publish` | MBTiles → PMTiles → S3 | `exaggeratedrelief.com` (PMTiles via CloudFront) |

### Push to tiles.exaggeratedrelief.com

```bash
# Single file
ilhmp push putnam-atak-dark-z9-16.mbtiles

# Whole output directory (skips already-present files)
ilhmp push-all /Volumes/ExtSSD1TB/dem/IL/putnam-themes-9x/

# Dry run
ilhmp push putnam-atak-dark-z9-16.mbtiles --dry-run
```

Copies via SCP to `/data/tiles/` on the EC2. mbtileserver auto-discovers new files — no restart needed. First push also adds the `tiles.exaggeratedrelief.com` Caddy vhost if missing.

**XYZ endpoint after push:**
```
https://tiles.exaggeratedrelief.com/services/{stem}/tiles/{z}/{x}/{y}.png
https://tiles.exaggeratedrelief.com/services/{stem}/map   # built-in preview
```

### Publish to exaggeratedrelief.com (PMTiles)

```bash
ilhmp publish putnam-atak-dark-z9-16.mbtiles \
  --county putnam --theme atak-dark --exag auto --no-pr

# With PR (for tracked publication)
ilhmp publish putnam-atak-dark-z9-16.mbtiles \
  --county putnam --theme atak-dark
```

Steps: convert to PMTiles → upload to `s3://exaggeratedrelief/tiles/` → update `web/catalog.json` → optionally open a GitHub PR.

### Catalog management

```bash
ilhmp catalog list                        # all registered tiles
ilhmp catalog list --county putnam        # filter by county
ilhmp catalog add ./putnam-atak-dark.mbtiles --county putnam --theme atak-dark
ilhmp catalog scan /Volumes/ExtSSD1TB/dem/IL/  # find unregistered mbtiles
```

---

## AWS EC2 generation (chimesh-tileserver)

For large counties or all-themes runs, use the EC2 pipeline in `~/chimesh-tileserver/`:

```bash
# Single county, one or more themes
./generate-aws.sh putnam --theme atak-dark,atak-light --zoom 9-16

# All themes
./generate-aws.sh putnam --theme all

# Multiple counties
./generate-aws.sh grundy dekalb --theme atak-dark,simmon,flat-terrain

# Dry run
./generate-aws.sh putnam --theme all --dry-run
```

Pull results when done:

```bash
./pull-aws-tiles-s3.sh putnam    # recommended: pull from S3 checkpoint
./pull-aws-tiles.sh putnam       # fallback: pull directly from worker
```

Then publish:

```bash
ilhmp push-all ./output/putnam/
ilhmp publish ./output/putnam/atak-dark/putnam-atak-dark-z9-16.mbtiles \
  --county putnam --theme atak-dark
```

---

## Output file structure

After `ilhmp run putnam --theme atak-dark --output ./out --cache-dir ./cache`:

```
cache/
├── putnam_dtm.tif                         # Raw 1m DEM (native projection)
├── putnam_dtm_4326.tif                    # DEM reprojected to WGS84
└── putnam_hillshade_dark_z9.0_*.tif       # Cached grayscale hillshade

out/
├── tiles-atak-dark-z9-16/                 # XYZ tile directory
│   └── {z}/{x}/{y}.png
├── putnam-atak-dark-z9-16.mbtiles         # Packed MBTiles
├── putnam.geojson                         # County boundary
└── viewer.html                            # Local Leaflet preview
```

---

## Error handling

- **Empty mbtiles (0 tiles):** Corrupt cached hillshade TIF. Delete the specific `*_hillshade_*.tif` from the cache dir and rerun with `--force-recompute`.
- **Disk space:** Reserve ~5–10 GB per county (cache + tiles). McHenry ~419 GB cache from all 11 themes — clear between counties.
- **Download failures:** ISGS downloads don't resume. Delete the partial `.tif` and retry.
- **Missing DSM:** Some counties have DTM only (`dsm_url: null` in `ilhmp counties --json`). Use `--dem dtm`.
- **AWS session expired:** `ilhmp publish` will fail at upload. Re-auth with `aws sso login` or `aws configure`.

---

## Infrastructure

| Component | Host | Details |
|-----------|------|---------|
| Tile server | `tiles.exaggeratedrelief.com` (3.20.103.82) | EC2 t4g.small, mbtileserver + Caddy, `/data/tiles/` |
| PMTiles CDN | `exaggeratedrelief.com` | CloudFront → `s3://exaggeratedrelief` |
| EC2 workers | AWS us-east-2 | c7g.2xlarge spot, launched by `generate-aws.sh` |
| SSH key | `~/.ssh/mapserver-ec2.pem` | Key pair name: `mapserver` |
| IAM instance profile | `hillshade-worker-s3` | Attached at launch; grants S3 read/write on `ilhmp-dem-cache`. **Required** — without it S3 caching silently fails. |
| S3 intermediates | `s3://ilhmp-dem-cache` | DEM + grayscale TIF cache for large counties |
| Catalog | `web/catalog.json` | Source of truth for all published tiles |
| Legacy tile server | `tiles.chicagooffline.com` | Same EC2, kept alive for existing ATAK configs |

---

## County catalog format (`ilhmp counties --json`)

```json
[
  {
    "id": "putnam",
    "name": "Putnam",
    "fips": "17155",
    "district": "district4",
    "year": "2022",
    "dtm_url": "https://clearinghouse.isgs.illinois.edu/...",
    "dsm_url": "https://clearinghouse.isgs.illinois.edu/...",
    "bounds": [-89.48, 41.10, -89.15, 41.32]
  }
]
```

`bounds` is `[west, south, east, north]` in WGS84, null if unknown.
