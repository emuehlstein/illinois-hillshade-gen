"""
Illinois county catalog with ILHMP data availability.
Data sourced from: https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp
"""

from typing import Optional, Dict, List

# ISGS base URLs
CLEARINGHOUSE_BASE = "https://clearinghouse.isgs.illinois.edu/distribute"
IMAGESERVER_BASE = "https://data.isgs.illinois.edu/arcgis/rest/services/Elevation"

# Illinois counties with ILHMP LiDAR data
# Format: county_id -> {name, fips, district, years available, zip URLs, imageserver URLs}
COUNTIES = {
    "adams": {
        "name": "Adams",
        "fips": "17001",
        "district": "district6",
        "dtm_zip": "adam_dtm_2018.zip",
        "dsm_zip": "adam_dsm_2018.zip",
        "dtm_imageserver": "IL_Adams_DTM_2019",
        "dsm_imageserver": "IL_Adams_DSM_2019",
        "year": "2018",
    },
    "alexander": {
        "name": "Alexander",
        "fips": "17003",
        "district": "district9",
        "dtm_zip": "alex_dtm_2020.zip",
        "dsm_zip": "alex_dsm_2020.zip",
        "dtm_imageserver": "IL_Alexander_DTM_2020",
        "dsm_imageserver": "IL_Alexander_DSM_2020",
        "year": "2020",
    },
    "bond": {
        "name": "Bond",
        "fips": "17005",
        "district": "district8",
        "dtm_zip": "bond_dtm_2015.zip",
        "dsm_zip": "bond_dsm_2015.zip",
        "dtm_imageserver": "IL_Bond_DTM_2015",
        "dsm_imageserver": "IL_Bond_DSM_2015",
        "year": "2015",
    },
    "cook": {
        "name": "Cook",
        "fips": "17031",
        "district": "district1",
        "dtm_zip": "cook_dtm_2022.zip",
        "dsm_zip": "cook_dsm_2022.zip",
        "dtm_imageserver": "IL_Cook_DTM_2022",
        "dsm_imageserver": "IL_Cook_DSM_2022",
        "year": "2022",
        "bounds": (-88.3, 41.4, -87.5, 42.2),
    },
    "dupage": {
        "name": "DuPage",
        "fips": "17043",
        "district": "district1",
        "dtm_zip": "dupa_dtm_2018.zip",
        "dsm_zip": "dupa_dsm_2018.zip",
        "dtm_imageserver": "IL_DuPage_DTM_2018",
        "dsm_imageserver": "IL_DuPage_DSM_2018",
        "year": "2018",
    },
    "kane": {
        "name": "Kane",
        "fips": "17089",
        "district": "district1",
        "dtm_zip": "kane_dtm_2008.zip",  # Note: older data, ArcGrid format
        "dsm_zip": None,
        "dtm_imageserver": "IL_Kane_DTM_2008",
        "dsm_imageserver": None,
        "year": "2008",
    },
    "lake": {
        "name": "Lake",
        "fips": "17097",
        "district": "district1",
        "dtm_zip": "lake_dtm_2017.zip",
        "dsm_zip": "lake_dsm_2017.zip",
        "dtm_imageserver": "IL_Lake_DTM_2017",
        "dsm_imageserver": "IL_Lake_DSM_2017",
        "year": "2017",
    },
    "mchenry": {
        "name": "McHenry",
        "fips": "17111",
        "district": "district1",
        "dtm_zip": "mche_dtm_2018.zip",
        "dsm_zip": "mche_dsm_2018.zip",
        "dtm_imageserver": "IL_McHenry_DTM_2018",
        "dsm_imageserver": "IL_McHenry_DSM_2018",
        "year": "2018",
    },
    "putnam": {
        "name": "Putnam",
        "fips": "17155",
        "district": "district4",
        "dtm_zip": "putn_dtm_2012.zip",
        "dsm_zip": "putn_dsm_2012.zip",
        "dtm_imageserver": "IL_Putnam_DTM_2012",
        "dsm_imageserver": "IL_Putnam_DSM_2012",
        "year": "2012",
        "bounds": (-89.48, 41.10, -89.15, 41.32),
    },
    "will": {
        "name": "Will",
        "fips": "17197",
        "district": "district1",
        "dtm_zip": "will_dtm_2019.zip",
        "dsm_zip": "will_dsm_2019.zip",
        "dtm_imageserver": "IL_Will_DTM_2019",
        "dsm_imageserver": "IL_Will_DSM_2019",
        "year": "2019",
    },
    # Add more counties as needed...
}


def get_county(name: str) -> Optional[Dict]:
    """Get county info by name (case-insensitive)."""
    key = name.lower().replace(" ", "").replace("county", "")
    if key in COUNTIES:
        county = COUNTIES[key].copy()
        county["id"] = key
        # Build full URLs
        if county.get("dtm_zip"):
            county["dtm_url"] = f"{CLEARINGHOUSE_BASE}/{county['district']}/{key}/{county['year']}/{county['dtm_zip']}"
        if county.get("dsm_zip"):
            county["dsm_url"] = f"{CLEARINGHOUSE_BASE}/{county['district']}/{key}/{county['year']}/{county['dsm_zip']}"
        if county.get("dtm_imageserver"):
            county["dtm_imageserver_url"] = f"{IMAGESERVER_BASE}/{county['dtm_imageserver']}/ImageServer"
        if county.get("dsm_imageserver"):
            county["dsm_imageserver_url"] = f"{IMAGESERVER_BASE}/{county['dsm_imageserver']}/ImageServer"
        return county
    return None


def list_all() -> List[Dict]:
    """List all counties with ILHMP data."""
    result = []
    for key, data in sorted(COUNTIES.items()):
        county = get_county(key)
        if county:
            result.append(county)
    return result


def get_imageserver_url(county: str, dem_type: str = "dtm") -> Optional[str]:
    """Get the ArcGIS ImageServer URL for a county."""
    info = get_county(county)
    if not info:
        return None
    key = f"{dem_type.lower()}_imageserver_url"
    return info.get(key)


def get_zip_url(county: str, dem_type: str = "dtm") -> Optional[str]:
    """Get the clearinghouse ZIP download URL for a county."""
    info = get_county(county)
    if not info:
        return None
    key = f"{dem_type.lower()}_url"
    return info.get(key)


# County boundaries source
BOUNDARIES_URL = "https://clearinghouse.isgs.illinois.edu/sites/clearinghouse.isgs/files/data/IL_BNDY_County.zip"
BOUNDARIES_SOURCE = "https://clearinghouse.isgs.illinois.edu/data/reference/illinois-county-boundaries-polygons-and-lines"
