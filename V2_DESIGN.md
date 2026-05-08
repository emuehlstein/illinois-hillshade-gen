# ilhmp v2 — Advanced Hillshade Rendering (Simmon-inspired)

## Reference
Robert Simmon, "A Gentle Introduction to GDAL Part 5: Shaded Relief"
https://medium.com/@robsimmon/a-gentle-introduction-to-gdal-part-5-shaded-relief-ec29601db654

## Changes from v1

### 1. Multi-Directional Shading (default)
- v1: single azimuth (315°) hillshade via `gdaldem hillshade`
- v2: `-multidirectional` flag by default, blending light from multiple angles
- New `--shading` option: `standard` (single-az, legacy), `multidirectional` (default), `combined`, `igor`, `composite`

### 2. Composite Hillshade Mode
When `--shading composite`:
- Generate multiple hillshade layers (multidirectional, igor, combined)
- Blend with configurable weights via `--composite-weights`
- Default weights: 0.6 multidirectional + 0.3 igor + 0.1 combined
- Uses gdal_calc.py for weighted blend

### 3. Auxiliary Terrain Layers
New `layers` subcommand:
```
ilhmp layers <county> --dem dtm --output aspect,slope,roughness,TRI
```
Each uses `gdaldem <mode>`:
- `aspect`: slope direction (0-360°)
- `slope`: steepness in degrees
- `roughness`: terrain roughness
- `TRI`: Terrain Ruggedness Index

### 4. Auto-Exaggeration
New `--exaggeration auto` mode:
- Computes elevation stddev from the DEM
- Scales to achieve target visual contrast (~40 gray levels)
- Applies zoom-level curve:
  - z0-6: 0.4x base
  - z7-9: 0.7x base  
  - z10-13: 1.0x base
  - z14-16: 1.2x base
  - z17-19: 0.6x base (LiDAR — buildings provide own contrast)
  - z20+: 0.4x base
- Falls back to fixed value if stats can't be computed
- Records computed exaggeration in output metadata

### 5. Color Ramp Overhaul
Replace hardcoded STYLES dict with JSON color ramp files:
- `ilhmp/ramps/dark.json`, `light.json`, `tactical.json`, etc.
- New `gdaldem color-relief` pipeline using 5-point gradient ramp files
- v1 tint-blend approach kept as `--color-mode tint` (legacy)
- v2 default: `--color-mode ramp` using color-relief
- Custom ramps: `--ramp path/to/ramp.json`

Ramp format (GDAL color-relief compatible):
```
0 20 30 50 255
64 35 48 73 255
128 51 68 103 255
192 80 100 145 255
255 120 145 195 255
nv 0 0 0 0
```

### 6. S3 Intermediate Caching
- `--s3-cache s3://bucket/prefix/` option
- Caches: reprojected DEM, grayscale hillshades (per shading mode), auxiliary layers
- Cache key includes: county, dem_type, exaggeration, shading_mode
- Download from S3 before recomputing; upload after computing

### 7. Backward Compatibility
- `ilhmp run cook --dem dtm --style dark --zoom 10-16` still works
- Defaults change: shading=multidirectional, color-mode=ramp
- `--legacy` flag restores v1 behavior exactly

## File Changes
- `ilhmp/hillshade.py` — add shading modes, composite blend, auto-exagg
- `ilhmp/layers.py` — NEW: aspect/slope/roughness/TRI generation
- `ilhmp/ramps/` — NEW: JSON color ramp definitions
- `ilhmp/s3cache.py` — NEW: S3 intermediate caching
- `ilhmp/cli.py` — add layers subcommand, new options
- `ilhmp/auto_exag.py` — NEW: auto-exaggeration computation
- `tests/test_hillshade_v2.py` — v2 shading tests
