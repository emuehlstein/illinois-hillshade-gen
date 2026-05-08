# exaggeratedrelief.com — Catalog Design

## Concept

"Shopping for hillshades" — a product configurator backed by GitHub Actions CI.

## Layout

```
┌────────────────────────────────────────────────────────────┐
│  Exaggerated Relief                          [GitHub] [?]  │
├──────────────────────┬─────────────────────────────────────┤
│                      │                                     │
│   Illinois Map       │   Configuration Panel               │
│   (county outlines)  │                                     │
│                      │   County: [Cook          ▼]         │
│   Click county to    │   DEM:    [DTM ○] [DSM ○]          │
│   select             │   Theme:  [simmon       ▼]         │
│                      │   Zoom:   [10] — [16]              │
│   ● = available      │   Exag:   [auto ○] [9x ○] [15x ○] │
│   ○ = can generate   │                                     │
│                      │   ─────────────────────────         │
│   Highlighted =      │                                     │
│   selected           │   Status: ✅ Available               │
│                      │   Size: 1.2 GB (PMTiles)            │
│                      │   Generated: 2026-05-08             │
│                      │   Source: ISGS ILHMP DTM 2022       │
│                      │                                     │
│                      │   [👁 Preview]  [⬇ Download]        │
│                      │                                     │
│                      │   — or if not generated —           │
│                      │                                     │
│                      │   Status: ⏳ Not yet generated       │
│                      │                                     │
│                      │   [🔧 Generate]                     │
│                      │   Files a PR to requests.yaml       │
│                      │   Est. time: ~30 min                │
│                      │   Est. cost: ~$0.07                  │
│                      │                                     │
├──────────────────────┴─────────────────────────────────────┤
│  Preview Map (full width, appears when Preview clicked)    │
│  PMTiles rendered via MapLibre                             │
└────────────────────────────────────────────────────────────┘
```

## catalog.json v2

```json
{
  "generated": "2026-05-08T...",
  "counties": {
    "cook": {
      "name": "Cook",
      "fips": "17031",
      "bounds": [-88.26, 41.47, -87.52, 42.16],
      "center": [-87.89, 41.82],
      "sources": {
        "dtm": { "year": "2022", "resolution": "1m", "size_gb": 131.0 },
        "dsm": { "year": "2022", "resolution": "1m", "size_gb": 147.0 }
      },
      "tiles": [
        {
          "id": "cook-simmon-dtm-9x-z10-16",
          "theme": "simmon",
          "dem": "dtm",
          "exaggeration": 9,
          "zoom": [10, 16],
          "pmtiles": "tiles/cook-simmon-dtm-9x-z10-16.pmtiles",
          "mbtiles_size_mb": 1200,
          "pmtiles_size_mb": 1100,
          "tile_count": 122186,
          "generated_at": "2026-05-08T00:00:00Z"
        }
      ]
    },
    "adams": {
      "name": "Adams",
      "fips": "17001",
      "bounds": [...],
      "center": [...],
      "sources": {
        "dtm": { "year": "2018", "resolution": "1m", "size_gb": 48.4 },
        "dsm": { "year": "2018", "resolution": "1m", "size_gb": 51.8 }
      },
      "tiles": []
    }
  },
  "themes": ["simmon", "simmon-light", "atak-dark", "atak-light", "tactical", "flat-terrain", "grayscale"],
  "generate_url": "https://github.com/emuehlstein/illinois-hillshade-gen/edit/v2-simmon/requests.yaml"
}
```

## Generate Flow

1. User selects county + options, clicks "Generate"
2. JS opens GitHub edit URL for `requests.yaml` with pre-filled content
3. User submits PR (requires GitHub account)
4. GitHub Actions picks up the new pending request
5. EC2 spot worker generates tiles
6. CI uploads pmtiles to S3, updates catalog.json
7. Site auto-refreshes to show new tile

## County Boundaries

GeoJSON of IL county boundaries for the map overlay.
Source: US Census TIGER/Line or Natural Earth.
Baked into the page as a static asset (~200KB).
