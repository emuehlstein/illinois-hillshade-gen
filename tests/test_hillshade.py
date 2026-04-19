"""Tests for hillshade generation."""

import pytest
from ilhmp import hillshade


def test_styles_defined():
    assert "dark" in hillshade.STYLES
    assert "light" in hillshade.STYLES
    assert "tactical" in hillshade.STYLES
    assert "gray" in hillshade.STYLES


def test_style_structure():
    for name, style in hillshade.STYLES.items():
        assert "tint" in style
        assert "bg" in style
        assert len(style["tint"]) == 3
        assert len(style["bg"]) == 3
