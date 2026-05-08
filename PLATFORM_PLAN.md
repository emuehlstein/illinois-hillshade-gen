# ilhmp Platform Plan — exaggeratedrelief.com

## Goal

Self-maintaining Illinois hillshade generator that:
1. Generates hillshade tiles from ISGS DEMs automatically
2. Caches all intermediates in S3 for style/exaggeration re-runs
3. Serves tiles publicly via exaggeratedrelief.com (PMTiles + CloudFront)
4. Keeps mbtiles canonical for ATAK offline packages
5. Runs entirely through GitHub Actions — no manual SSH, no babysitting

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI                         │
│                                                             │
│  requests.yaml ──→ EC2 spot worker ──→ ilhmp run            │
│                         │                                   │
│                    ┌────┴────┐                               │
│                    │  ilhmp  │                               │
│                    └────┬────┘                               │
│                         │                                   │
│              ┌──────────┼──────────┐                        │
│              ▼          ▼          ▼                         │
│         DEM cache   mbtiles    pmtiles                      │
│              │          │          │                         │
│              ▼          ▼          ▼                         │
│     s3://ilhmp-data    s3://ilhmp-data    s3://exaggeratedrelief │
│      /dem/{county}/    /mbtiles/...        /tiles/...       │
│      /intermediates/                       /catalog.json    │
│                                            /index.html      │
│                                                  │          │
│                                            CloudFront       │
│                                                  │          │
│                                         exaggeratedrelief.com│
└─────────────────────────────────────────────────────────────┘
                                                  │
                                            ┌─────┴─────┐
                                            │  Web map   │
                                            │  viewer    │
                                            └───────────┘

    mbtiles ──→ tiles.chicagooffline.com (ATAK / mbtileserver)
    mbtiles ──→ OTS packaging (bigmacpi)
```

## S3 Bucket Layout

### `s3://ilhmp-data` (private, build artifacts)

Consolidates the current `ilhmp-dem-cache` bucket into a cleaner structure.

```
s3://ilhmp-data/
├── dem/
│   ├── isgs/{county}/{county}_{dtm|dsm}.tif        # Raw ISGS downloads
│   ├── 3dep/{county}/n{lat}w{lon}.tif               # Raw 3DEP tiles
│   └── lidar/{county}/{county}_lidar.tif             # 1m LiDAR DEMs
│
├── intermediates/{county}/
│   ├── {county}_4326.tif                             # Reprojected to EPSG:4326
│   ├── {county}_4326_filled.tif                      # Nodata filled (LiDAR)
│   ├── {county}_gray_{exag}x.tif                     # Grayscale hillshade (reuse across styles)
│   ├── {county}_{style}_{exag}x.tif                  # Styled raster
│   └── manifest.json                                 # What's cached, checksums, timestamps
│
├── mbtiles/{county}/
│   ├── {county}-{style}-{exag}x.mbtiles              # Canonical output
│   └── {county}-combined-{style}-{exag}x.mbtiles     # Multi-source merged
│
└── catalog.json                                       # Master index of all outputs
```

### `s3://exaggeratedrelief` (public-read, web serving)

```
s3://exaggeratedrelief/
├── tiles/
│   ├── {county}-{style}-{exag}x.pmtiles              # Converted from mbtiles
│   └── ...
├── catalog.json                                       # Layer index for the viewer
├── index.html                                         # Landing page + map viewer
└── assets/
    ├── maplibre-gl.js                                 # Pinned MapLibre GL JS
    ├── pmtiles.js                                     # PMTiles protocol
    └── style.css
```

## Intermediate Caching Strategy

The DEM is the most expensive artifact. The caching hierarchy:

```
Level 0: Raw DEM download (ISGS/3DEP)          ← hours to download, never recompute
  Level 1: Reprojected to EPSG:4326            ← minutes, reuse across all styles+exags
    Level 2: Grayscale hillshade at Nx exag     ← minutes, reuse across all styles at same exag
      Level 3: Styled raster (dark/light/etc)   ← seconds, cheap
        Level 4: mbtiles (tiled)                ← minutes, canonical output
          Level 5: pmtiles (converted)          ← seconds, derived for web
```

**Key reuse patterns:**
- Change style only → reuse Level 2 (grayscale hillshade)
- Change exaggeration → reuse Level 1 (reprojected DEM)
- Change DEM source (DTM↔DSM) → reuse nothing, start from Level 0
- Change shading mode → reuse Level 1, recompute Level 2+

**ilhmp needs:** `--s3-cache s3://ilhmp-data/` flag that:
1. Before each step, check S3 for cached artifact
2. After each step, upload result to S3
3. Cache key = `{county}/{dem_type}/{step}_{params}.tif`

## CI Pipeline (GitHub Actions)

### Trigger: `requests.yaml` change or `workflow_dispatch`

```yaml
requests:
  - county: cook
    dem: dtm
    styles: [dark, light, tactical]
    exaggerations: [3, 9]
    zoom: "10-16"
    status: pending        # pending → running → done | failed

  - county: dupage
    dem: dtm
    styles: [dark]
    exaggerations: [9]
    zoom: "10-16"
    status: done
    completed_at: "2026-05-08T..."
```

### Pipeline steps:

1. **Parse** `requests.yaml` → find `status: pending`
2. **Launch** EC2 spot worker (ARM64, c7g.2xlarge, ~$0.14/hr)
3. **Worker runs:**
   ```bash
   ilhmp run {county} \
     --dem {dem} \
     --style {styles} \
     --exaggeration {exags} \
     --zoom {zoom} \
     --s3-cache s3://ilhmp-data/ \
     --output /data/output/
   ```
4. **Worker uploads** mbtiles → `s3://ilhmp-data/mbtiles/{county}/`
5. **Convert** mbtiles → pmtiles:
   ```bash
   pmtiles convert {county}-{style}-{exag}x.mbtiles {county}-{style}-{exag}x.pmtiles
   ```
6. **Upload** pmtiles → `s3://exaggeratedrelief/tiles/`
7. **Update** `catalog.json` in both buckets
8. **Update** `requests.yaml` → `status: done`
9. **Terminate** EC2 worker

### Optional: SCP to tile server
- If ATAK distribution is needed, SCP mbtiles to `tiles.chicagooffline.com`
- Triggered by `atak: true` flag in the request

## Web Viewer (exaggeratedrelief.com)

**Stack:** Static HTML + MapLibre GL JS + PMTiles protocol

**Features:**
- Auto-populates layer list from `catalog.json`
- Style switcher (dark/light/tactical/terrain/gray)
- Exaggeration comparison (side-by-side or slider)
- County boundaries overlay
- Zoom to county on click
- Mobile-friendly
- "Download mbtiles" link for ATAK users

**catalog.json format:**
```json
{
  "generated": "2026-05-08T...",
  "layers": [
    {
      "county": "cook",
      "name": "Cook County",
      "style": "dark",
      "exaggeration": 9,
      "dem": "dtm",
      "zoom": [10, 16],
      "bounds": [-88.26, 41.47, -87.52, 42.16],
      "center": [-87.89, 41.82],
      "pmtiles": "tiles/cook-dark-9x.pmtiles",
      "mbtiles_url": "https://tiles.chicagooffline.com/services/cook-dark-9x",
      "size_mb": 911,
      "tile_count": 31000,
      "generated_at": "2026-05-08T...",
      "source": "ISGS ILHMP DTM"
    }
  ]
}
```

## Infrastructure Setup

### Phase 1: S3 + CloudFront (Day 1)

```bash
# 1. Create public bucket for web serving
aws s3 mb s3://exaggeratedrelief --region us-east-2
# Enable static website hosting + CORS for range requests

# 2. Create CloudFront distribution
#    - Origin: s3://exaggeratedrelief
#    - Alternate domain: exaggeratedrelief.com, www.exaggeratedrelief.com
#    - ACM certificate (us-east-1, required for CloudFront)
#    - Cache policy: CachingOptimized with Range header forwarding

# 3. DNS at GoDaddy
#    - exaggeratedrelief.com → CNAME to CloudFront distribution
#    - www.exaggeratedrelief.com → same
```

### Phase 2: ilhmp S3 cache integration (Day 2-3)

Add `--s3-cache` flag to `ilhmp run`:
- New module: `ilhmp/s3cache.py`
- Before each processing step, check S3 for cached artifact
- After each step, upload to S3
- `manifest.json` per county tracks what's cached

### Phase 3: CI pipeline (Day 3-4)

Update GitHub Actions workflow:
- Add pmtiles conversion step
- Add S3 upload for pmtiles + catalog.json
- Add `requests.yaml` status update + commit
- Add optional tile server SCP

### Phase 4: Landing page (Day 4-5)

Build static viewer:
- MapLibre + PMTiles
- Layer picker from catalog.json
- Deploy to S3 bucket root

### Phase 5: Batch generation (Week 2)

- Generate all 102 IL counties (prioritize populated ones first)
- Batch `requests.yaml` with groups of ~10 counties
- Monitor costs (estimate: ~$15-25 for all 102 at z10-16)

## Cost Estimates

| Item | Monthly | Notes |
|------|---------|-------|
| S3 ilhmp-data | ~$12 | ~540GB current, growing |
| S3 exaggeratedrelief | ~$1 | PMTiles are smaller than mbtiles |
| CloudFront | $0 | Free tier: 1TB/mo |
| ACM cert | $0 | Free with CloudFront |
| EC2 spot (generation) | ~$2-5/run | c7g.2xlarge @ $0.14/hr × ~30min/county |
| **Total ongoing** | **~$15/mo** | Plus ~$0.05/county one-time generation |

## Migration from ilhmp-dem-cache

Current `s3://ilhmp-dem-cache` (540GB) can stay as-is initially. New pipeline writes to `s3://ilhmp-data` with the clean structure. Migrate existing Cook/SLC data later, or just let them coexist.

## ISGS Data Catalog (Full Scope)

All 102 Illinois counties from the ISGS ILHMP clearinghouse:
https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp

| Metric | Value |
|---|---|
| Counties | 102 |
| With ImageServer (streaming) | 98 |
| Multi-year collections | 90 |
| Latest DTM total | 3,432 GB |
| Latest DSM total | 3,553 GB |

**Data access methods:**
- **ImageServer** (preferred): Stream DEM tiles on-demand via ISGS ArcGIS REST. No full download needed. ilhmp requests only the pixels within county bounds at native resolution.
- **ZIP download** (fallback): Full county ZIP from clearinghouse. Huge files (Cook 2022 = 131GB × 4 parts).

**Available per county:**
- DTM (bare earth, hydro-conditioned) — primary for hillshades
- DSM (surface model, includes buildings/trees) — useful for urban terrain viz
- LAS point cloud (not needed for hillshade generation)
- Multiple collection years (newest = best resolution/coverage)

**Generation strategy:**
- Use ImageServer for all 98 counties that support it
- Fall back to ZIP download for the 4 without ImageServer
- Cache reprojected DEM in S3 → reuse for any style/exaggeration combo
- Generate default set: dark + light styles, 9x exaggeration, z10-16
- Batch in groups of ~10 counties per EC2 spot instance

**Estimated generation cost (all 102):**
- ~30 min/county average on c7g.2xlarge ($0.14/hr spot)
- ~51 hours total = ~$7.15 in compute
- S3 storage for DEMs + intermediates: ~$10-15/mo
- Total one-time: < $10; ongoing: ~$15/mo

## Decisions Made

1. ✅ **DNS:** Move to Route 53 (simpler ACM cert validation)
2. ✅ **Scope:** All ISGS ILHMP sources (102 counties, DTM + DSM)
3. ✅ **Buckets:** Two — `ilhmp-data` (private) + `exaggeratedrelief` (public)
4. ✅ **Formats:** mbtiles canonical (ATAK), pmtiles derived (web)
5. ✅ **Tile server:** Keep tiles.chicagooffline.com for ATAK mbtiles serving
