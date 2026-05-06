"""Tests for the themes system."""
import json
import tempfile
from pathlib import Path

from ilhmp.themes import (
    Theme, TerrainType, THEMES,
    get_theme, list_themes, load_custom_theme, save_theme,
)


def test_builtin_themes_exist():
    """All expected built-in themes should be registered."""
    expected = [
        "atak-dark", "atak-light", "tactical", "terrain",
        "simmon", "simmon-light", "flat-terrain", "mountain",
        "lidar-urban", "lidar-natural", "classic", "grayscale",
    ]
    for name in expected:
        assert name in THEMES, f"Missing theme: {name}"


def test_get_theme():
    t = get_theme("atak-dark")
    assert t is not None
    assert t.name == "atak-dark"
    assert t.ramp == "dark"


def test_get_theme_missing():
    assert get_theme("nonexistent") is None


def test_list_themes_all():
    themes = list_themes()
    assert len(themes) >= 12


def test_list_themes_by_tag():
    dark_themes = list_themes(tag="dark")
    assert len(dark_themes) >= 1
    for t in dark_themes:
        assert "dark" in t.tags


def test_theme_to_dict():
    t = get_theme("simmon")
    d = t.to_dict()
    assert d["name"] == "simmon"
    assert d["shading"] == "composite"
    assert isinstance(d["composite_weights"], list)
    assert len(d["composite_weights"]) == 3


def test_theme_to_cli_args():
    t = get_theme("simmon")
    args = t.to_cli_args()
    assert "--shading" in args
    assert "composite" in args
    assert "--composite-weights" in args


def test_theme_to_cli_args_simple():
    t = get_theme("atak-dark")
    args = t.to_cli_args()
    assert "--shading" in args
    assert "multidirectional" in args
    # No composite weights for non-composite theme
    assert "--composite-weights" not in args


def test_classic_theme_is_v1():
    """Classic theme should reproduce exact v1 behavior."""
    t = get_theme("classic")
    assert t.color_mode == "tint"
    assert t.shading == "standard"
    assert t.exaggeration == "3"


def test_get_exaggeration_value_auto():
    t = get_theme("atak-dark")
    assert t.get_exaggeration_value() is None


def test_get_exaggeration_value_fixed():
    t = get_theme("flat-terrain")
    assert t.get_exaggeration_value() == 15.0


def test_terrain_type_enum():
    assert TerrainType.FLAT.value == "flat"
    assert TerrainType.URBAN_LIDAR.value == "urban-lidar"


def test_save_and_load_custom_theme():
    """Round-trip a theme through JSON."""
    original = Theme(
        name="custom-test",
        description="Test theme",
        ramp="dark",
        shading="composite",
        composite_weights=(0.5, 0.3, 0.2),
        exaggeration="12",
        terrain_type="flat",
    )
    with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
        save_theme(original, Path(f.name))
        loaded = load_custom_theme(Path(f.name))
    
    assert loaded.name == "custom-test"
    assert loaded.shading == "composite"
    assert loaded.composite_weights == (0.5, 0.3, 0.2)
    assert loaded.exaggeration == "12"


def test_all_themes_have_valid_ramps():
    """Every theme's ramp should correspond to a ramp file."""
    ramps_dir = Path(__file__).parent.parent / "ilhmp" / "ramps"
    for name, t in THEMES.items():
        ramp_file = ramps_dir / f"{t.ramp}.txt"
        assert ramp_file.exists(), f"Theme '{name}' references missing ramp: {t.ramp}"


def test_all_themes_have_descriptions():
    for name, t in THEMES.items():
        assert t.description, f"Theme '{name}' has no description"
        assert len(t.description) > 10, f"Theme '{name}' description too short"
