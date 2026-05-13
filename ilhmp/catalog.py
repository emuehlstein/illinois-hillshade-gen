"""
Local tile catalog management for ilhmp.

catalog.json lives at web/catalog.json in the repo root (or a path you specify).
It tracks every generated tile set — locally produced or CI-generated.

Key operations:
  - add(mbtiles_path)   — register a local mbtiles in the catalog
  - remove(tile_id)     — remove a catalog entry
  - list_tiles()        — return all tile entries
  - find_local_tiles()  — scan filesystem for mbtiles not yet in catalog
"""

import json
import re
import sqlite3
import datetime
from pathlib import Path
from typing import Optional

# Default catalog path: repo-root/web/catalog.json
_REPO_ROOT = Path(__file__).parent.parent
DEFAULT_CATALOG = _REPO_ROOT / "web" / "catalog.json"


def load(catalog_path: Path = DEFAULT_CATALOG) -> dict:
    """Load catalog.json, returning empty structure if missing."""
    if catalog_path.exists():
        with open(catalog_path) as f:
            return json.load(f)
    return {"generated": "", "counties": {}}


def save(catalog: dict, catalog_path: Path = DEFAULT_CATALOG) -> None:
    """Write catalog.json with stable formatting."""
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog["generated"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(catalog_path, "w") as f:
        json.dump(catalog, f, indent=2)
        f.write("\n")


def mbtiles_info(mbtiles_path: Path) -> dict:
    """
    Extract tile metadata from an mbtiles file.

    Returns dict with keys: zoom_min, zoom_max, zoom_list, tile_count, size_mb,
    bounds, center, scheme, name, description.
    """
    path = Path(mbtiles_path)
    size_mb = path.stat().st_size / 1024 / 1024

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row

    # Metadata table
    meta = {}
    try:
        for row in conn.execute("SELECT name, value FROM metadata"):
            meta[row["name"]] = row["value"]
    except Exception:
        pass

    # Zoom levels + tile count
    zoom_rows = []
    tile_count = 0
    try:
        for row in conn.execute(
            "SELECT zoom_level, count(*) as n FROM tiles GROUP BY zoom_level ORDER BY zoom_level"
        ):
            zoom_rows.append(int(row["zoom_level"]))
            tile_count += int(row["n"])
    except Exception:
        pass

    conn.close()

    zoom_min = min(zoom_rows) if zoom_rows else None
    zoom_max = max(zoom_rows) if zoom_rows else None

    # Parse bounds from metadata
    bounds = None
    if "bounds" in meta:
        try:
            bounds = [float(x) for x in meta["bounds"].split(",")]
        except Exception:
            pass

    center = None
    if "center" in meta:
        try:
            parts = [float(x) for x in meta["center"].split(",")]
            center = parts[:2]
        except Exception:
            pass

    return {
        "zoom_min": zoom_min,
        "zoom_max": zoom_max,
        "zoom_list": sorted(zoom_rows),
        "tile_count": tile_count,
        "size_mb": round(size_mb, 1),
        "bounds": bounds,
        "center": center,
        "scheme": meta.get("scheme", "tms"),
        "name": meta.get("name", ""),
        "description": meta.get("description", ""),
    }


def parse_mbtiles_name(filename: str) -> dict:
    """
    Parse metadata from an ilhmp mbtiles filename.

    Expected pattern: {county}-{theme}-z{zoom}.mbtiles
    e.g. putnam-flat-terrain-z9-16.mbtiles
         cook-atak-dark-z9-16.mbtiles

    Returns dict with county, theme, zoom_str, exaggeration (if encoded),
    dem (dtm assumed if not present).
    """
    stem = Path(filename).stem  # e.g. putnam-flat-terrain-z9-16

    # Strip zoom suffix: -z{zoom}
    zoom_match = re.search(r"-z([\d,\-]+)$", stem)
    zoom_str = zoom_match.group(1) if zoom_match else None
    base = stem[: zoom_match.start()] if zoom_match else stem

    # Try to match county from known counties list
    # (lazy: split on first '-' and check later; caller can override)
    parts = base.split("-", 1)
    county = parts[0] if parts else base
    theme_raw = parts[1] if len(parts) > 1 else ""

    # Exaggeration may be encoded as last segment: e.g. flat-terrain-9x
    exag = None
    exag_match = re.search(r"-(\d+x|autox)$", theme_raw)
    if exag_match:
        exag = exag_match.group(1).rstrip("x")  # "9" or "auto"
        theme_raw = theme_raw[: exag_match.start()]

    return {
        "county": county,
        "theme": theme_raw,
        "zoom_str": zoom_str,
        "exaggeration": exag or "auto",
        "dem": "dtm",  # default; caller can override
    }


def add_entry(
    mbtiles_path: Path,
    catalog_path: Path = DEFAULT_CATALOG,
    *,
    county: Optional[str] = None,
    theme: Optional[str] = None,
    dem: str = "dtm",
    exaggeration: Optional[str] = None,
    local_path: Optional[str] = None,
    pmtiles_path: Optional[Path] = None,
    force: bool = False,
) -> dict:
    """
    Register an mbtiles file in the catalog.

    Auto-parses county/theme/exag from filename if not provided.
    Returns the catalog entry dict.
    """
    mbtiles_path = Path(mbtiles_path).resolve()
    if not mbtiles_path.exists():
        raise FileNotFoundError(f"MBTiles not found: {mbtiles_path}")

    parsed = parse_mbtiles_name(mbtiles_path.name)
    county = county or parsed["county"]
    theme = theme or parsed["theme"]
    dem = dem or parsed.get("dem", "dtm")
    exaggeration = exaggeration or parsed["exaggeration"]
    zoom_str = parsed.get("zoom_str") or "9-16"

    info = mbtiles_info(mbtiles_path)

    # Build tile ID from filename stem
    tile_id = mbtiles_path.stem  # e.g. putnam-flat-terrain-z9-16

    entry = {
        "id": tile_id,
        "theme": theme,
        "dem": dem,
        "exaggeration": exaggeration,
        "zoom": [info["zoom_min"], info["zoom_max"]] if info["zoom_min"] is not None else [],
        "zoom_str": zoom_str,
        "tile_count": info["tile_count"],
        "size_mb": info["size_mb"],
        "local_mbtiles": str(mbtiles_path),
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    if pmtiles_path and Path(pmtiles_path).exists():
        entry["pmtiles"] = f"tiles/{Path(pmtiles_path).name}"
        entry["pmtiles_size_mb"] = round(Path(pmtiles_path).stat().st_size / 1024 / 1024, 1)

    if local_path:
        entry["local_mbtiles"] = local_path

    catalog = load(catalog_path)

    if county not in catalog.get("counties", {}):
        # Add stub county entry
        catalog.setdefault("counties", {})[county] = {
            "name": county.replace("-", " ").title(),
            "tiles": [],
        }

    tiles = catalog["counties"][county].get("tiles", [])
    existing = [i for i, t in enumerate(tiles) if t.get("id") == tile_id]
    if existing and not force:
        # Update in place
        tiles[existing[0]] = entry
    elif existing:
        tiles[existing[0]] = entry
    else:
        tiles.append(entry)

    catalog["counties"][county]["tiles"] = tiles
    save(catalog, catalog_path)
    return {"county": county, **entry}


def remove_entry(
    tile_id: str,
    catalog_path: Path = DEFAULT_CATALOG,
    county: Optional[str] = None,
) -> bool:
    """Remove a tile entry by ID. Returns True if found and removed."""
    catalog = load(catalog_path)
    for c_key, c_data in catalog.get("counties", {}).items():
        if county and c_key != county:
            continue
        tiles = c_data.get("tiles", [])
        new_tiles = [t for t in tiles if t.get("id") != tile_id]
        if len(new_tiles) < len(tiles):
            catalog["counties"][c_key]["tiles"] = new_tiles
            save(catalog, catalog_path)
            return True
    return False


def list_entries(
    catalog_path: Path = DEFAULT_CATALOG,
    county: Optional[str] = None,
) -> list:
    """Return all tile entries, optionally filtered by county."""
    catalog = load(catalog_path)
    entries = []
    for c_key, c_data in catalog.get("counties", {}).items():
        if county and c_key != county:
            continue
        for t in c_data.get("tiles", []):
            entries.append({"county": c_key, **t})
    return entries


def find_unregistered(
    search_dirs: list,
    catalog_path: Path = DEFAULT_CATALOG,
) -> list:
    """
    Scan directories for mbtiles files not yet in the catalog.
    Returns list of Path objects.
    """
    catalog = load(catalog_path)
    registered_ids = set()
    for c_data in catalog.get("counties", {}).values():
        for t in c_data.get("tiles", []):
            registered_ids.add(t.get("id"))

    unregistered = []
    for d in search_dirs:
        for p in Path(d).rglob("*.mbtiles"):
            if p.stem not in registered_ids:
                unregistered.append(p)
    return sorted(unregistered)
