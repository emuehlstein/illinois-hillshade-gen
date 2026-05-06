"""
Tests for ilhmp v2 hillshade features.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from ilhmp.hillshade import ShadingMode, generate, _generate_grayscale, get_styles
from ilhmp.auto_exag import compute_auto_exaggeration, zoom_scale, ExaggerationConfig


# ---------------------------------------------------------------------------
# ShadingMode enum
# ---------------------------------------------------------------------------

def test_shading_mode_values():
    assert ShadingMode.STANDARD.value == "standard"
    assert ShadingMode.MULTIDIRECTIONAL.value == "multidirectional"
    assert ShadingMode.COMBINED.value == "combined"
    assert ShadingMode.IGOR.value == "igor"
    assert ShadingMode.COMPOSITE.value == "composite"


def test_shading_mode_from_string():
    assert ShadingMode("multidirectional") == ShadingMode.MULTIDIRECTIONAL
    assert ShadingMode("standard") == ShadingMode.STANDARD


def test_shading_mode_invalid():
    with pytest.raises(ValueError):
        ShadingMode("invalid_mode")


# ---------------------------------------------------------------------------
# Auto-exaggeration computation (mocked gdalinfo)
# ---------------------------------------------------------------------------

_GDALINFO_JSON = json.dumps({
    "bands": [
        {
            "band": 1,
            "stdDev": 25.0,
            "minimum": 100.0,
            "maximum": 500.0,
        }
    ]
})


def test_compute_auto_exaggeration_basic():
    """stddev=25, target=40 → exaggeration=40/25=1.6"""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = _GDALINFO_JSON

    with patch("subprocess.run", return_value=mock_result):
        exag = compute_auto_exaggeration(Path("fake.tif"), target_contrast=40.0)

    assert abs(exag - 1.6) < 1e-6


def test_compute_auto_exaggeration_clamp_high():
    """Very small stddev should clamp to max (10.0)"""
    info = json.dumps({"bands": [{"stdDev": 0.5}]})
    mock_result = MagicMock(returncode=0, stdout=info)

    with patch("subprocess.run", return_value=mock_result):
        exag = compute_auto_exaggeration(Path("fake.tif"), target_contrast=40.0)

    assert exag == 10.0


def test_compute_auto_exaggeration_clamp_low():
    """Very large stddev should clamp to min (0.5)"""
    info = json.dumps({"bands": [{"stdDev": 1000.0}]})
    mock_result = MagicMock(returncode=0, stdout=info)

    with patch("subprocess.run", return_value=mock_result):
        exag = compute_auto_exaggeration(Path("fake.tif"), target_contrast=40.0)

    assert exag == 0.5


def test_compute_auto_exaggeration_gdalinfo_failure():
    """If gdalinfo fails, fall back to 3.0"""
    mock_result = MagicMock(returncode=1, stdout="", stderr="error")

    with patch("subprocess.run", return_value=mock_result):
        exag = compute_auto_exaggeration(Path("fake.tif"))

    assert exag == 3.0


def test_compute_auto_exaggeration_bad_json():
    """If gdalinfo returns unparseable output, fall back to 3.0"""
    mock_result = MagicMock(returncode=0, stdout="not json")

    with patch("subprocess.run", return_value=mock_result):
        exag = compute_auto_exaggeration(Path("fake.tif"))

    assert exag == 3.0


def test_compute_auto_exaggeration_missing_stddev():
    """If bands have no stdDev, fall back to 3.0"""
    info = json.dumps({"bands": [{"band": 1}]})
    mock_result = MagicMock(returncode=0, stdout=info)

    with patch("subprocess.run", return_value=mock_result):
        exag = compute_auto_exaggeration(Path("fake.tif"))

    assert exag == 3.0


# ---------------------------------------------------------------------------
# zoom_scale curve
# ---------------------------------------------------------------------------

def test_zoom_scale_low_zooms():
    """z0-6 should use 0.4x"""
    base = 5.0
    for z in range(0, 7):
        assert abs(zoom_scale(z, base) - base * 0.4) < 1e-9, f"Failed at zoom {z}"


def test_zoom_scale_mid_zooms():
    """z7-9 → 0.7x"""
    base = 4.0
    for z in (7, 8, 9):
        assert abs(zoom_scale(z, base) - base * 0.7) < 1e-9


def test_zoom_scale_working_zooms():
    """z10-13 → 1.0x"""
    base = 3.0
    for z in (10, 11, 12, 13):
        assert abs(zoom_scale(z, base) - base * 1.0) < 1e-9


def test_zoom_scale_high_detail():
    """z14-16 → 1.2x"""
    base = 2.0
    for z in (14, 15, 16):
        assert abs(zoom_scale(z, base) - base * 1.2) < 1e-9


def test_zoom_scale_lidar():
    """z17-19 → 0.6x (LiDAR buildings provide own contrast)"""
    base = 3.0
    for z in (17, 18, 19):
        assert abs(zoom_scale(z, base) - base * 0.6) < 1e-9


def test_zoom_scale_very_high():
    """z20+ → 0.4x"""
    base = 5.0
    for z in (20, 21, 25):
        assert abs(zoom_scale(z, base) - base * 0.4) < 1e-9


# ---------------------------------------------------------------------------
# ExaggerationConfig dataclass
# ---------------------------------------------------------------------------

def test_exaggeration_config_fixed():
    cfg = ExaggerationConfig(mode="fixed", base_value=3.0)
    assert cfg.mode == "fixed"
    assert cfg.base_value == 3.0
    assert cfg.zoom_curve is True  # default


def test_exaggeration_config_auto():
    cfg = ExaggerationConfig(mode="auto", base_value=1.6, zoom_curve=False)
    assert cfg.mode == "auto"
    assert cfg.zoom_curve is False


# ---------------------------------------------------------------------------
# Ramp file loading
# ---------------------------------------------------------------------------

def test_ramp_files_exist():
    ramps_dir = Path(__file__).parent.parent / "ilhmp" / "ramps"
    for name in ("dark", "light", "tactical", "terrain", "gray"):
        ramp = ramps_dir / f"{name}.txt"
        assert ramp.exists(), f"Missing ramp file: {name}.txt"


def test_ramp_file_format():
    """Each ramp file should have 5 data lines + nv line."""
    ramps_dir = Path(__file__).parent.parent / "ilhmp" / "ramps"
    for name in ("dark", "light", "tactical", "terrain", "gray"):
        ramp = ramps_dir / f"{name}.txt"
        lines = [l.strip() for l in ramp.read_text().splitlines() if l.strip()]
        assert len(lines) == 6, f"{name}.txt should have 6 lines (5 data + nv), got {len(lines)}"
        assert lines[-1].startswith("nv"), f"{name}.txt last line should be 'nv ...' nodata"
        for line in lines[:-1]:
            parts = line.split()
            assert len(parts) == 5, f"{name}.txt data line has wrong field count: {line!r}"
            assert int(parts[0]) in range(256), f"Value out of range: {parts[0]}"


# ---------------------------------------------------------------------------
# _generate_grayscale passes correct flags
# ---------------------------------------------------------------------------

def test_generate_grayscale_multidirectional_flag():
    """MULTIDIRECTIONAL mode must pass -multidirectional to gdaldem."""
    captured = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        return MagicMock(returncode=0, stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        _generate_grayscale(
            Path("dem.tif"), Path("out.tif"),
            exaggeration=3.0, azimuth=315.0, altitude=45.0,
            shading_mode=ShadingMode.MULTIDIRECTIONAL,
        )

    assert captured, "subprocess.run was never called"
    cmd = captured[0]
    assert "-multidirectional" in cmd
    assert "-igor" not in cmd
    assert "-combined" not in cmd


def test_generate_grayscale_igor_flag():
    captured = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        return MagicMock(returncode=0, stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        _generate_grayscale(
            Path("dem.tif"), Path("out.tif"),
            exaggeration=3.0, azimuth=315.0, altitude=45.0,
            shading_mode=ShadingMode.IGOR,
        )

    cmd = captured[0]
    assert "-igor" in cmd
    assert "-multidirectional" not in cmd


def test_generate_grayscale_combined_flag():
    captured = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        return MagicMock(returncode=0, stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        _generate_grayscale(
            Path("dem.tif"), Path("out.tif"),
            exaggeration=3.0, azimuth=315.0, altitude=45.0,
            shading_mode=ShadingMode.COMBINED,
        )

    cmd = captured[0]
    assert "-combined" in cmd


def test_generate_grayscale_standard_uses_azimuth():
    """STANDARD mode passes -az, not -multidirectional."""
    captured = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        return MagicMock(returncode=0, stderr="")

    with patch("subprocess.run", side_effect=fake_run):
        _generate_grayscale(
            Path("dem.tif"), Path("out.tif"),
            exaggeration=3.0, azimuth=270.0, altitude=45.0,
            shading_mode=ShadingMode.STANDARD,
        )

    cmd = captured[0]
    assert "-az" in cmd
    assert "270.0" in cmd
    assert "-multidirectional" not in cmd
    assert "-igor" not in cmd
    assert "-combined" not in cmd


# ---------------------------------------------------------------------------
# v1 compatibility: get_styles() still works
# ---------------------------------------------------------------------------

def test_styles_still_present():
    styles = get_styles()
    for name in ("dark", "light", "tactical", "terrain", "gray"):
        assert name in styles
