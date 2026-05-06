"""
Named themes — preset bundles of shading, color, and exaggeration parameters.

A theme captures everything needed to reproduce a specific visual style:
- Color ramp (or tint mode)
- Shading mode (multidirectional, composite, etc.)
- Exaggeration (fixed or auto with terrain-type hint)
- Composite weights (if composite shading)
- Azimuth/altitude

Usage:
    ilhmp run cook --theme atak-dark
    ilhmp themes                        # list all themes
    ilhmp themes --show atak-dark       # show theme details
"""

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class TerrainType(str, Enum):
    """Terrain classification for auto-exaggeration tuning."""
    FLAT = "flat"           # Illinois, Florida, Netherlands — needs heavy exagg
    ROLLING = "rolling"     # Midwest moraine, Piedmont — moderate exagg
    MOUNTAINOUS = "mountain"  # Rockies, Alps, Appalachians — light exagg
    URBAN_LIDAR = "urban-lidar"  # 1m LiDAR in urban areas — buildings provide contrast
    AUTO = "auto"           # Detect from DEM stats


@dataclass
class Theme:
    """A named preset capturing all visual parameters for hillshade generation."""
    name: str
    description: str
    
    # Color
    ramp: str = "dark"              # Name of ramp file (dark, light, tactical, terrain, gray)
    color_mode: str = "ramp"        # 'ramp' (gdaldem color-relief) or 'tint' (v1 legacy)
    
    # Shading
    shading: str = "multidirectional"  # standard, multidirectional, combined, igor, composite
    composite_weights: Tuple[float, ...] = (0.6, 0.3, 0.1)  # multi, igor, combined
    azimuth: float = 315.0
    altitude: float = 45.0
    
    # Exaggeration
    exaggeration: str = "auto"      # 'auto' or a fixed number as string
    terrain_type: str = "auto"      # Terrain hint for auto-exagg tuning
    
    # Zoom defaults
    default_zoom: str = "10-16"
    
    # Tags for filtering
    tags: List[str] = field(default_factory=list)
    
    def get_exaggeration_value(self) -> Optional[float]:
        """Return numeric exaggeration or None for auto."""
        if self.exaggeration == "auto":
            return None
        return float(self.exaggeration)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["composite_weights"] = list(d["composite_weights"])
        return d
    
    def to_cli_args(self) -> List[str]:
        """Generate CLI arguments that reproduce this theme."""
        args = [
            "--style", self.ramp,
            "--shading", self.shading,
            "--color-mode", self.color_mode,
            "--exaggeration", self.exaggeration,
        ]
        if self.shading == "composite":
            args += ["--composite-weights", ",".join(str(w) for w in self.composite_weights)]
        if self.azimuth != 315.0:
            args += ["--azimuth", str(self.azimuth)]
        if self.altitude != 45.0:
            args += ["--altitude", str(self.altitude)]
        return args


# ─── Built-in Themes ───────────────────────────────────────────

THEMES: Dict[str, Theme] = {}


def _register(theme: Theme) -> Theme:
    THEMES[theme.name] = theme
    return theme


# ATAK Dark — the original blue-grey, optimized for dark basemaps
_register(Theme(
    name="atak-dark",
    description="Blue-grey hillshade for ATAK dark mode overlays. "
                "Multi-directional shading with auto-exaggeration.",
    ramp="dark",
    shading="multidirectional",
    exaggeration="auto",
    terrain_type="auto",
    tags=["atak", "dark", "default"],
))

# ATAK Light — warm grey for light basemaps
_register(Theme(
    name="atak-light",
    description="Warm grey hillshade for ATAK light mode overlays.",
    ramp="light",
    shading="multidirectional",
    exaggeration="auto",
    terrain_type="auto",
    tags=["atak", "light"],
))

# Tactical — olive drab for military-style maps
_register(Theme(
    name="tactical",
    description="Olive drab hillshade for military/tactical overlays.",
    ramp="tactical",
    shading="multidirectional",
    exaggeration="auto",
    terrain_type="auto",
    tags=["military", "dark"],
))

# Terrain — earth tones for topo-style maps
_register(Theme(
    name="terrain",
    description="Earth-tone hillshade for topographic map style.",
    ramp="terrain",
    shading="multidirectional",
    exaggeration="auto",
    terrain_type="auto",
    tags=["topo", "light"],
))

# Simmon Composite — the full Simmon treatment
_register(Theme(
    name="simmon",
    description="Advanced composite blend (60% multidirectional + 30% igor + 10% combined). "
                "Best overall terrain rendering, inspired by Robert Simmon's techniques.",
    ramp="dark",
    shading="composite",
    composite_weights=(0.6, 0.3, 0.1),
    exaggeration="auto",
    terrain_type="auto",
    tags=["advanced", "composite", "dark"],
))

# Simmon Light
_register(Theme(
    name="simmon-light",
    description="Advanced composite blend on light background.",
    ramp="light",
    shading="composite",
    composite_weights=(0.6, 0.3, 0.1),
    exaggeration="auto",
    terrain_type="auto",
    tags=["advanced", "composite", "light"],
))

# Flat Terrain — heavy exaggeration for pancake-flat areas
_register(Theme(
    name="flat-terrain",
    description="Maximum terrain visibility for flat regions (Illinois, Indiana, Florida). "
                "15x fixed exaggeration with composite shading.",
    ramp="dark",
    shading="composite",
    composite_weights=(0.5, 0.3, 0.2),
    exaggeration="15",
    terrain_type="flat",
    tags=["flat", "midwest", "dark"],
))

# Mountain — subtle shading for steep terrain
_register(Theme(
    name="mountain",
    description="Subtle shading for mountainous terrain. Low exaggeration "
                "to avoid oversaturation on steep slopes.",
    ramp="dark",
    shading="composite",
    composite_weights=(0.7, 0.2, 0.1),
    exaggeration="2",
    terrain_type="mountain",
    tags=["mountain", "dark"],
))

# LiDAR Urban — optimized for 1m urban LiDAR
_register(Theme(
    name="lidar-urban",
    description="Optimized for 1m LiDAR in urban areas. Buildings and infrastructure "
                "provide natural contrast, so exaggeration is moderate (6x). "
                "Composite shading with extra roughness emphasis.",
    ramp="dark",
    shading="composite",
    composite_weights=(0.5, 0.3, 0.2),
    exaggeration="6",
    terrain_type="urban-lidar",
    default_zoom="15-20",
    tags=["lidar", "urban", "dark"],
))

# LiDAR Natural — for LiDAR in non-urban areas
_register(Theme(
    name="lidar-natural",
    description="For 1m LiDAR in natural/rural areas. Higher exaggeration (9x) "
                "to reveal subtle terrain features.",
    ramp="dark",
    shading="composite",
    composite_weights=(0.6, 0.3, 0.1),
    exaggeration="9",
    terrain_type="flat",
    default_zoom="15-20",
    tags=["lidar", "natural", "dark"],
))

# Classic v1 — exact v1 behavior for backward compatibility
_register(Theme(
    name="classic",
    description="Legacy v1 behavior: single-azimuth (315°) hillshade with "
                "tint-blend coloring and fixed 3x exaggeration.",
    ramp="dark",
    color_mode="tint",
    shading="standard",
    exaggeration="3",
    terrain_type="auto",
    tags=["legacy", "v1"],
))

# Grayscale — no color, pure hillshade
_register(Theme(
    name="grayscale",
    description="Pure grayscale hillshade with no color tint. "
                "Useful as a base layer for custom coloring.",
    ramp="gray",
    shading="multidirectional",
    exaggeration="auto",
    terrain_type="auto",
    tags=["gray", "base"],
))


# ─── API ────────────────────────────────────────────────────────

def get_theme(name: str) -> Optional[Theme]:
    """Get a theme by name."""
    return THEMES.get(name)


def list_themes(tag: Optional[str] = None) -> List[Theme]:
    """List all themes, optionally filtered by tag."""
    themes = list(THEMES.values())
    if tag:
        themes = [t for t in themes if tag in t.tags]
    return themes


def load_custom_theme(path: Path) -> Theme:
    """Load a custom theme from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    
    # Convert composite_weights list back to tuple
    if "composite_weights" in data and isinstance(data["composite_weights"], list):
        data["composite_weights"] = tuple(data["composite_weights"])
    
    return Theme(**data)


def save_theme(theme: Theme, path: Path) -> None:
    """Save a theme to a JSON file."""
    with open(path, "w") as f:
        json.dump(theme.to_dict(), f, indent=2)
