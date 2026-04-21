"""Tests for county catalog."""

import pytest
from ilhmp import counties


def test_get_known_county():
    info = counties.get_county("putnam")
    assert info is not None
    assert info["name"] == "Putnam"
    assert info["fips"] == "17155"
    assert "dtm_url" in info
    assert "dtm_imageserver_url" in info


def test_get_county_case_insensitive():
    info1 = counties.get_county("Cook")
    info2 = counties.get_county("COOK")
    info3 = counties.get_county("cook")
    assert info1 == info2 == info3


def test_get_unknown_county():
    info = counties.get_county("notacounty")
    assert info is None


def test_list_all():
    all_counties = counties.list_all()
    assert len(all_counties) > 0
    assert all("name" in c for c in all_counties)
    assert all("fips" in c for c in all_counties)


def test_imageserver_url():
    url = counties.get_imageserver_url("putnam", "dtm")
    assert url is not None
    assert "ImageServer" in url
    assert "Putnam" in url


def test_zip_url():
    url = counties.get_zip_url("putnam", "dtm")
    assert url is not None
    # Putnam 2022 uses 'putnam_dtm_2022.zip' (2012 used 'putn_dtm_2012.zip')
    assert "putnam_dtm" in url
    assert ".zip" in url


def test_zip_url_old_year():
    """Older collection (2012) still uses 'putn' prefix."""
    coll2012 = next(
        (c for c in counties.COUNTIES["putnam"]["collections"] if c["year"] == "2012"),
        None,
    )
    assert coll2012 is not None
    assert "putn_dtm" in coll2012["dtm_zip"]


def test_get_county_years():
    years = counties.get_county_years("dupage")
    assert set(years) == {"2022", "2017", "2014", "2006"}
    assert years[0] == "2022"  # newest first


def test_county_years_unknown():
    years = counties.get_county_years("notacounty")
    assert years == []


def test_size_fields():
    info = counties.get_county("cook")
    assert info["dtm_size_gb"] == 131.0
    assert info["dsm_size_gb"] == 147.0


def test_dtm_type_dem():
    """Adams 2009 should have dtm_type='dem'."""
    coll2009 = next(
        (c for c in counties.COUNTIES["adams"]["collections"] if c["year"] == "2009"),
        None,
    )
    assert coll2009 is not None
    assert coll2009["dtm_type"] == "dem"


def test_dupage_no_2018():
    """DuPage should NOT have 2018 (old catalog was wrong)."""
    years = counties.get_county_years("dupage")
    assert "2018" not in years
    assert "2022" in years


def test_williamson_prefix():
    """Williamson uses 'wilm' prefix, not 'wmsn'."""
    info = counties.get_county("williamson")
    assert "wilm_dtm" in info["dtm_url"]
