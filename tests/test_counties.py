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
    assert "putn_dtm" in url
    assert ".zip" in url
