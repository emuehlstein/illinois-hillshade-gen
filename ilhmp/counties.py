"""
Illinois county catalog with ILHMP LiDAR data availability.
Data sourced from: https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp

Each county entry has a 'collections' list (newest first) with verified download URLs
extracted directly from the ISGS clearinghouse HTML on 2026-04-21.

URL structure:
  https://clearinghouse.isgs.illinois.edu/distribute/{district}/{county_folder}/{year}/{filename}.zip

Note: Some older collections are physically stored in a newer year's directory on the server.
      dtm_url / dsm_url are stored explicitly to avoid year-path mismatches.
      dtm_type is "dtm" for hydro-conditioned bare-earth, "dem" for bare-earth without breaklines.
"""

from typing import Optional, Dict, List

# ISGS base URLs
CLEARINGHOUSE_BASE = "https://clearinghouse.isgs.illinois.edu/distribute"
IMAGESERVER_BASE = "https://data.isgs.illinois.edu/arcgis/rest/services/Elevation"

# Helper to build clearinghouse download URL
def _url(district: str, folder: str, year: str, filename: str) -> str:
    return f"{CLEARINGHOUSE_BASE}/{district}/{folder}/{year}/{filename}"


# Illinois counties with ILHMP LiDAR data (all 102 counties)
# collections[] sorted newest-first; get_county() returns the latest by default.
COUNTIES: Dict[str, Dict] = {

    # --- Adams ---
    "adams": {
        "name": "Adams",
        "fips": "17001",
        "district": "district6",
        "collections": [
            {
                "year": "2018",
                "dtm_type": "dtm",
                "dtm_zip": "adam_dtm_2018.zip",
                "dsm_zip": "adam_dsm_2018.zip",
                "dtm_url": _url("district6", "adams", "2018", "adam_dtm_2018.zip"),
                "dsm_url": _url("district6", "adams", "2018", "adam_dsm_2018.zip"),
                "dtm_imageserver": "IL_Adams_DTM_2019",
                "dsm_imageserver": "IL_Adams_DSM_2019",
                "dtm_size_gb": 48.4,
                "dsm_size_gb": 51.8,
            },
            {
                "year": "2009",
                "dtm_type": "dem",
                "dtm_zip": "adams-dem-2009.zip",
                "dsm_zip": "adams-dsm-2009.zip",
                "dtm_url": _url("district6", "adams", "2009", "adams-dem-2009.zip"),
                "dsm_url": _url("district6", "adams", "2009", "adams-dsm-2009.zip"),
                "dtm_imageserver": "IL_Adams_DEM_2009",
                "dsm_imageserver": "IL_Adams_DSM_2009",
                "dtm_size_gb": 9.7,
                "dsm_size_gb": 9.8,
            },
        ],
    },

    # --- Alexander ---
    "alexander": {
        "name": "Alexander",
        "fips": "17003",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "alex_dtm_2020.zip",
                "dsm_zip": "alex_dsm_2020.zip",
                "dtm_url": _url("district9", "alexander", "2020", "alex_dtm_2020.zip"),
                "dsm_url": _url("district9", "alexander", "2020", "alex_dsm_2020.zip"),
                "dtm_imageserver": "IL_Alexander_DTM_2020",
                "dsm_imageserver": "IL_Alexander_DSM_2020",
                "dtm_size_gb": 14.8,
                "dsm_size_gb": 16.2,
            },
            {
                "year": "2009",
                "dtm_type": "dem",
                "dtm_zip": "alex_dem_2009.zip",
                "dsm_zip": "alex_dsm_2009.zip",
                "dtm_url": _url("district9", "alexander", "2009", "alex_dem_2009.zip"),
                "dsm_url": _url("district9", "alexander", "2009", "alex_dsm_2009.zip"),
                "dtm_imageserver": "IL_Alexander_DEM_2009",
                "dsm_imageserver": "IL_Alexander_DSM_2009",
                "dtm_size_gb": 1.6,
                "dsm_size_gb": 1.6,
            },
        ],
    },

    # --- Bond ---
    "bond": {
        "name": "Bond",
        "fips": "17005",
        "district": "district8",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "bond_dtm_2021.zip",
                "dsm_zip": "bond_dsm_2021.zip",
                "dtm_url": _url("district8", "bond", "2021", "bond_dtm_2021.zip"),
                "dsm_url": _url("district8", "bond", "2021", "bond_dsm_2021.zip"),
                "dtm_imageserver": "IL_Bond_DTM_2021",
                "dsm_imageserver": "IL_Bond_DSM_2021",
                "dtm_size_gb": 20.4,
                "dsm_size_gb": 21.5,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "bond_dtm_2015.zip",
                "dsm_zip": "bond_dsm_2015.zip",
                # Note: 2015 files are physically stored under the 2021 directory
                "dtm_url": _url("district8", "bond", "2021", "bond_dtm_2015.zip"),
                "dsm_url": _url("district8", "bond", "2021", "bond_dsm_2015.zip"),
                "dtm_imageserver": "IL_Bond_DTM_2015",
                "dsm_imageserver": "IL_Bond_DSM_2015",
                "dtm_size_gb": 5.8,
                "dsm_size_gb": 6.2,
            },
        ],
    },

    # --- Boone ---
    "boone": {
        "name": "Boone",
        "fips": "17007",
        "district": "district2",
        "collections": [
            {
                "year": "2018",
                "dtm_type": "dtm",
                "dtm_zip": "boon_dtm_2018.zip",
                "dsm_zip": "boon_dsm_2018.zip",
                "dtm_url": _url("district2", "boone", "2018", "boon_dtm_2018.zip"),
                "dsm_url": _url("district2", "boone", "2018", "boon_dsm_2018.zip"),
                "dtm_imageserver": "IL_Boone_DTM_2018",
                "dsm_imageserver": "IL_Boone_DSM_2018",
                "dtm_size_gb": 14.7,
                "dsm_size_gb": 15.2,
            },
            {
                "year": "2007",
                "dtm_type": "dtm",
                "dtm_zip": "boon_dtm_2007.zip",
                "dsm_zip": "boon_dsm_2007.zip",
                "dtm_url": _url("district2", "boone", "2007", "boon_dtm_2007.zip"),
                "dsm_url": _url("district2", "boone", "2007", "boon_dsm_2007.zip"),
                "dtm_imageserver": "IL_Boone_DEM_2007",
                "dsm_imageserver": "IL_Boone_DSM_2007",
                "dtm_size_gb": 2.0,
                "dsm_size_gb": 2.1,
            },
        ],
    },

    # --- Brown ---
    "brown": {
        "name": "Brown",
        "fips": "17009",
        "district": "district6",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "brow_dtm_2017.zip",
                "dsm_zip": "brow_dsm_2017.zip",
                "dtm_url": _url("district6", "brown", "2017", "brow_dtm_2017.zip"),
                "dsm_url": _url("district6", "brown", "2017", "brow_dsm_2017.zip"),
                "dtm_imageserver": "IL_Brown_DTM_2017",
                "dsm_imageserver": "IL_Brown_DSM_2017",
                "dtm_size_gb": 9.8,
                "dsm_size_gb": 10.3,
            },
        ],
    },

    # --- Bureau ---
    "bureau": {
        "name": "Bureau",
        "fips": "17011",
        "district": "district3",
        "collections": [
            {
                "year": "2023",
                "dtm_type": "dtm",
                "dtm_zip": "bureau_dtm_2023.zip",
                "dsm_zip": "bureau_dsm_2023.zip",
                "dtm_url": _url("district3", "bureau", "2023", "bureau_dtm_2023.zip"),
                "dsm_url": _url("district3", "bureau", "2023", "bureau_dsm_2023.zip"),
                "dtm_imageserver": "IL_Bureau_DTM_2023",
                "dsm_imageserver": "IL_Bureau_DSM_2023",
                "dtm_size_gb": 140.0,
                "dsm_size_gb": 101.0,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "bure_dtm_2015.zip",
                "dsm_zip": "bure_dsm_2015.zip",
                "dtm_url": _url("district3", "bureau", "2015", "bure_dtm_2015.zip"),
                "dsm_url": _url("district3", "bureau", "2015", "bure_dsm_2015.zip"),
                "dtm_imageserver": "IL_Bureau_DTM_2015",
                "dsm_imageserver": "IL_Bureau_DSM_2015",
                "dtm_size_gb": 25.3,
                "dsm_size_gb": 26.4,
            },
        ],
    },

    # --- Calhoun ---
    "calhoun": {
        "name": "Calhoun",
        "fips": "17013",
        "district": "district8",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "calh_dtm_2021.zip",
                "dsm_zip": "calh_dsm_2021.zip",
                "dtm_url": _url("district8", "calhoun", "2021", "calh_dtm_2021.zip"),
                "dsm_url": _url("district8", "calhoun", "2021", "calh_dsm_2021.zip"),
                "dtm_imageserver": "IL_Calhoun_DTM_2021",
                "dsm_imageserver": "IL_Calhoun_DSM_2021",
                "dtm_size_gb": 15.7,
                "dsm_size_gb": 17.8,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "calh_dtm_2011.zip",
                "dsm_zip": "calh_dsm_2011.zip",
                "dtm_url": _url("district8", "calhoun", "2011", "calh_dtm_2011.zip"),
                "dsm_url": _url("district8", "calhoun", "2011", "calh_dsm_2011.zip"),
                "dtm_imageserver": "IL_Calhoun_DEM_2011",
                "dsm_imageserver": "IL_Calhoun_DSM_2011",
                "dtm_size_gb": 1.8,
                "dsm_size_gb": 1.9,
            },
        ],
    },

    # --- Carroll ---
    "carroll": {
        "name": "Carroll",
        "fips": "17015",
        "district": "district2",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "carr_dtm_2020.zip",
                "dsm_zip": "carr_dsm_2020.zip",
                "dtm_url": _url("district2", "carroll", "2020", "carr_dtm_2020.zip"),
                "dsm_url": _url("district2", "carroll", "2020", "carr_dsm_2020.zip"),
                "dtm_imageserver": "IL_Carroll_DTM_2020",
                "dsm_imageserver": "IL_Carroll_DSM_2020",
                "dtm_size_gb": 23.6,
                "dsm_size_gb": 15.9,
            },
            {
                "year": "2009",
                "dtm_type": "dtm",
                "dtm_zip": "carr_dtm_2009.zip",
                "dsm_zip": "carr_dsm_2009.zip",
                # Stored under 2020 directory
                "dtm_url": _url("district2", "carroll", "2020", "carr_dtm_2009.zip"),
                "dsm_url": _url("district2", "carroll", "2020", "carr_dsm_2009.zip"),
                "dtm_imageserver": "IL_Carroll_DTM_2009",
                "dsm_imageserver": "IL_Carroll_DSM_2009",
                "dtm_size_gb": 4.4,
                "dsm_size_gb": 4.7,
            },
        ],
    },

    # --- Cass ---
    "cass": {
        "name": "Cass",
        "fips": "17017",
        "district": "district6",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "cass_dtm_2017.zip",
                "dsm_zip": "cass_dsm_2017.zip",
                "dtm_url": _url("district6", "cass", "2017", "cass_dtm_2017.zip"),
                "dsm_url": _url("district6", "cass", "2017", "cass_dsm_2017.zip"),
                "dtm_imageserver": "IL_Cass_DTM_2017",
                "dsm_imageserver": "IL_Cass_DSM_2017",
                "dtm_size_gb": 12.2,
                "dsm_size_gb": 12.1,
            },
        ],
    },

    # --- Champaign ---
    "champaign": {
        "name": "Champaign",
        "fips": "17019",
        "district": "district5",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "cham_dtm_2020.zip",
                "dsm_zip": "cham_dsm_2020.zip",
                "dtm_url": _url("district5", "champaign", "2020", "cham_dtm_2020.zip"),
                "dsm_url": _url("district5", "champaign", "2020", "cham_dsm_2020.zip"),
                "dtm_imageserver": "IL_Champaign_DTM_2020",
                "dsm_imageserver": "IL_Champaign_DSM_2020",
                "dtm_size_gb": 28.4,
                "dsm_size_gb": 47.8,
            },
            {
                "year": "2008",
                "dtm_type": "dtm",
                "dtm_zip": "cham_dtm_2008.zip",
                "dsm_zip": "cham_dsm_2008.zip",
                # Stored under 2020 directory
                "dtm_url": _url("district5", "champaign", "2020", "cham_dtm_2008.zip"),
                "dsm_url": _url("district5", "champaign", "2020", "cham_dsm_2008.zip"),
                "dtm_imageserver": "IL_Champaign_DTM_2008",
                "dsm_imageserver": "IL_Champaign_DSM_2008",
                "dtm_size_gb": 6.8,
                "dsm_size_gb": 7.0,
            },
        ],
    },

    # --- Christian ---
    "christian": {
        "name": "Christian",
        "fips": "17021",
        "district": "district6",
        "collections": [
            {
                "year": "2024",
                "dtm_type": "dtm",
                "dtm_zip": "chri_dtm_2024.zip",
                "dsm_zip": "chri_dsm_2024.zip",
                "dtm_url": _url("district6", "christian", "2024", "chri_dtm_2024.zip"),
                "dsm_url": _url("district6", "christian", "2024", "chri_dsm_2024.zip"),
                "dtm_imageserver": "IL_Christian_DTM_2024",
                "dsm_imageserver": "IL_Christian_DSM_2024",
                "dtm_size_gb": 73.5,
                "dsm_size_gb": 80.0,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "chri_dtm_2015.zip",
                "dsm_zip": "chri_dsm_2015.zip",
                "dtm_url": _url("district6", "christian", "2015", "chri_dtm_2015.zip"),
                "dsm_url": _url("district6", "christian", "2015", "chri_dsm_2015.zip"),
                "dtm_imageserver": "IL_Christian_DTM_2015",
                "dsm_imageserver": "IL_Christian_DSM_2015",
                "dtm_size_gb": 18.5,
                "dsm_size_gb": 16.8,
            },
        ],
    },

    # --- Clark ---
    "clark": {
        "name": "Clark",
        "fips": "17023",
        "district": "district7",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "clar_dtm_2020.zip",
                "dsm_zip": "clar_dsm_2020.zip",
                "dtm_url": _url("district7", "clark", "2020", "clar_dtm_2020.zip"),
                "dsm_url": _url("district7", "clark", "2020", "clar_dsm_2020.zip"),
                "dtm_imageserver": "IL_Clark_DTM_2020",
                "dsm_imageserver": "IL_Clark_DSM_2020",
                "dtm_size_gb": 27.2,
                "dsm_size_gb": 28.7,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "clar_dtm_2011.zip",
                "dsm_zip": "clar_dsm_2011.zip",
                "dtm_url": _url("district7", "clark", "2011", "clar_dtm_2011.zip"),
                "dsm_url": _url("district7", "clark", "2011", "clar_dsm_2011.zip"),
                "dtm_imageserver": "IL_Clark_DTM_2011",
                "dsm_imageserver": "IL_Clark_DSM_2011",
                "dtm_size_gb": 5.3,
                "dsm_size_gb": 5.5,
            },
        ],
    },

    # --- Clay ---
    "clay": {
        "name": "Clay",
        "fips": "17025",
        "district": "district7",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "clay_dtm_2021.zip",
                "dsm_zip": "clay_dsm_2021.zip",
                "dtm_url": _url("district7", "clay", "2021", "clay_dtm_2021.zip"),
                "dsm_url": _url("district7", "clay", "2021", "clay_dsm_2021.zip"),
                "dtm_imageserver": "IL_Clay_DTM_2021",
                "dsm_imageserver": "IL_Clay_DSM_2021",
                "dtm_size_gb": 25.3,
                "dsm_size_gb": 25.9,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "clay_dtm_2011.zip",
                "dsm_zip": "clay_dsm_2011.zip",
                "dtm_url": _url("district7", "clay", "2011", "clay_dtm_2011.zip"),
                "dsm_url": _url("district7", "clay", "2011", "clay_dsm_2011.zip"),
                "dtm_imageserver": "IL_Clay_DTM_2011",
                "dsm_imageserver": "IL_Clay_DSM_2011",
                "dtm_size_gb": 6.9,
                "dsm_size_gb": 7.1,
            },
        ],
    },

    # --- Clinton ---
    "clinton": {
        "name": "Clinton",
        "fips": "17027",
        "district": "district8",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "clin_dtm_2021.zip",
                "dsm_zip": "clin_dsm_2021.zip",
                "dtm_url": _url("district8", "clinton", "2021", "clin_dtm_2021.zip"),
                "dsm_url": _url("district8", "clinton", "2021", "clin_dsm_2021.zip"),
                "dtm_imageserver": "IL_Clinton_DTM_2021",
                "dsm_imageserver": "IL_Clinton_DSM_2021",
                "dtm_size_gb": 25.7,
                "dsm_size_gb": 26.7,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "clin_dtm_2015.zip",
                "dsm_zip": "clin_dsm_2015.zip",
                "dtm_url": _url("district8", "clinton", "2015", "clin_dtm_2015.zip"),
                "dsm_url": _url("district8", "clinton", "2015", "clin_dsm_2015.zip"),
                "dtm_imageserver": "IL_Clinton_DTM_2015",
                "dsm_imageserver": "IL_Clinton_DSM_2015",
                "dtm_size_gb": 7.3,
                "dsm_size_gb": 8.0,
            },
        ],
    },

    # --- Coles ---
    "coles": {
        "name": "Coles",
        "fips": "17029",
        "district": "district7",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "cole_dtm_2020.zip",
                "dsm_zip": "cole_dsm_2020.zip",
                "dtm_url": _url("district7", "coles", "2020", "cole_dtm_2020.zip"),
                "dsm_url": _url("district7", "coles", "2020", "cole_dsm_2020.zip"),
                "dtm_imageserver": "IL_Coles_DTM_2020",
                "dsm_imageserver": "IL_Coles_DSM_2020",
                "dtm_size_gb": 26.0,
                "dsm_size_gb": 26.8,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "cole_dtm_2011.zip",
                "dsm_zip": "cole_dsm_2011.zip",
                "dtm_url": _url("district7", "coles", "2011", "cole_dtm_2011.zip"),
                "dsm_url": _url("district7", "coles", "2011", "cole_dsm_2011.zip"),
                "dtm_imageserver": "IL_Coles_DTM_2011",
                "dsm_imageserver": "IL_Coles_DSM_2011",
                "dtm_size_gb": 4.2,
                "dsm_size_gb": 4.3,
            },
        ],
    },

    # --- Cook ---
    "cook": {
        "name": "Cook",
        "fips": "17031",
        "district": "district1",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "cook_dtm_2022.zip",
                "dsm_zip": "cook_dsm_2022.zip",
                "dtm_url": _url("district1", "cook", "2022", "cook_dtm_2022.zip"),
                "dsm_url": _url("district1", "cook", "2022", "cook_dsm_2022.zip"),
                "dtm_imageserver": "IL_Cook_DTM_2022",
                "dsm_imageserver": "IL_Cook_DSM_2022",
                "dtm_size_gb": 131.0,
                "dsm_size_gb": 147.0,
            },
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "cook_dtm_2017.zip",
                "dsm_zip": "cook_dsm_2017.zip",
                "dtm_url": _url("district1", "cook", "2017", "cook_dtm_2017.zip"),
                "dsm_url": _url("district1", "cook", "2017", "cook_dsm_2017.zip"),
                "dtm_imageserver": "IL_Cook_DEM_2018",
                "dsm_imageserver": "IL_Cook_DSM_2018",
                "dtm_size_gb": 58.9,
                "dsm_size_gb": 67.4,
            },
        ],
        "bounds": (-88.3, 41.4, -87.5, 42.2),
    },

    # --- Crawford ---
    "crawford": {
        "name": "Crawford",
        "fips": "17033",
        "district": "district7",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "craw_dtm_2020.zip",
                "dsm_zip": "craw_dsm_2020.zip",
                "dtm_url": _url("district7", "crawford", "2020", "craw_dtm_2020.zip"),
                "dsm_url": _url("district7", "crawford", "2020", "craw_dsm_2020.zip"),
                "dtm_imageserver": "IL_Crawford_DTM_2020",
                "dsm_imageserver": "IL_Crawford_DSM_2020",
                "dtm_size_gb": 26.6,
                "dsm_size_gb": 28.4,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "craw_dtm_2011.zip",
                "dsm_zip": "craw_dsm_2011.zip",
                "dtm_url": _url("district7", "crawford", "2011", "craw_dtm_2011.zip"),
                "dsm_url": _url("district7", "crawford", "2011", "craw_dsm_2011.zip"),
                "dtm_imageserver": "IL_Crawford_DTM_2011",
                "dsm_imageserver": "IL_Crawford_DSM_2011",
                "dtm_size_gb": 4.7,
                "dsm_size_gb": 5.0,
            },
        ],
    },

    # --- Cumberland ---
    "cumberland": {
        "name": "Cumberland",
        "fips": "17035",
        "district": "district7",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "cumb_dtm_2020.zip",
                "dsm_zip": "cumb_dsm_2020.zip",
                "dtm_url": _url("district7", "cumberland", "2020", "cumb_dtm_2020.zip"),
                "dsm_url": _url("district7", "cumberland", "2020", "cumb_dsm_2020.zip"),
                "dtm_imageserver": "IL_Cumberland_DTM_2020",
                "dsm_imageserver": "IL_Cumberland_DSM_2020",
                "dtm_size_gb": 18.1,
                "dsm_size_gb": 19.0,
            },
            {
                "year": "2011",
                "dtm_type": "dem",
                "dtm_zip": "cumb_dem_2011.zip",
                "dsm_zip": "cumb_dsm_2011.zip",
                "dtm_url": _url("district7", "cumberland", "2011", "cumb_dem_2011.zip"),
                "dsm_url": _url("district7", "cumberland", "2011", "cumb_dsm_2011.zip"),
                "dtm_imageserver": "IL_Cumberland_DEM_2011",
                "dsm_imageserver": "IL_Cumberland_DSM_2011",
                "dtm_size_gb": 3.7,
                "dsm_size_gb": 3.8,
            },
        ],
    },

    # --- DeKalb ---
    "dekalb": {
        "name": "DeKalb",
        "fips": "17037",
        "district": "district3",
        "collections": [
            {
                "year": "2018",
                "dtm_type": "dtm",
                "dtm_zip": "deka_dtm_2018.zip",
                "dsm_zip": "deka_dsm_2018.zip",
                "dtm_url": _url("district3", "dekalb", "2018", "deka_dtm_2018.zip"),
                "dsm_url": _url("district3", "dekalb", "2018", "deka_dsm_2018.zip"),
                "dtm_imageserver": "IL_DeKalb_DEM_2018",
                "dsm_imageserver": "IL_DeKalb_DSM_2018",
                "dtm_size_gb": 16.8,
                "dsm_size_gb": 17.6,
            },
            {
                "year": "2009",
                "dtm_type": "dem",
                "dtm_zip": "deka_dem_2009.zip",
                "dsm_zip": "deka_dsm_2009.zip",
                "dtm_url": _url("district3", "dekalb", "2009", "deka_dem_2009.zip"),
                "dsm_url": _url("district3", "dekalb", "2009", "deka_dsm_2009.zip"),
                "dtm_imageserver": "IL_DeKalb_DEM_2009",
                "dsm_imageserver": "IL_DeKalb_DSM_2009",
                "dtm_size_gb": 7.4,
                "dsm_size_gb": 7.8,
            },
        ],
    },

    # --- DeWitt ---
    "dewitt": {
        "name": "DeWitt",
        "fips": "17039",
        "district": "district5",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "dewi_dtm_2022.zip",
                "dsm_zip": "dewi_dsm_2022.zip",
                "dtm_url": _url("district5", "dewitt", "2022", "dewi_dtm_2022.zip"),
                "dsm_url": _url("district5", "dewitt", "2022", "dewi_dsm_2022.zip"),
                "dtm_imageserver": "IL_Dewitt_DTM_2022",
                "dsm_imageserver": "IL_Dewitt_DSM_2022",
                "dtm_size_gb": 22.1,
                "dsm_size_gb": 22.8,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "dewi_dtm_2012.zip",
                "dsm_zip": "dewi_dsm_2012.zip",
                "dtm_url": _url("district5", "dewitt", "2012", "dewi_dtm_2012.zip"),
                "dsm_url": _url("district5", "dewitt", "2012", "dewi_dsm_2012.zip"),
                "dtm_imageserver": "IL_Dewitt_DTM_2012",
                "dsm_imageserver": "IL_Dewitt_DSM_2012",
                "dtm_size_gb": 7.5,
                "dsm_size_gb": 7.8,
            },
        ],
    },

    # --- Douglas ---
    "douglas": {
        "name": "Douglas",
        "fips": "17041",
        "district": "district5",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "doug_dtm_2020.zip",
                "dsm_zip": "doug_dsm_2020.zip",
                "dtm_url": _url("district5", "douglas", "2020", "doug_dtm_2020.zip"),
                "dsm_url": _url("district5", "douglas", "2020", "doug_dsm_2020.zip"),
                "dtm_imageserver": "IL_Douglas_DTM_2020",
                "dsm_imageserver": "IL_Douglas_DSM_2020",
                "dtm_size_gb": 20.7,
                "dsm_size_gb": 21.0,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "doug_dtm_2012.zip",
                "dsm_zip": "doug_dsm_2012.zip",
                "dtm_url": _url("district5", "douglas", "2012", "doug_dtm_2012.zip"),
                "dsm_url": _url("district5", "douglas", "2012", "doug_dsm_2012.zip"),
                "dtm_imageserver": "IL_Douglas_DTM_2012",
                "dsm_imageserver": "IL_Douglas_DSM_2012",
                "dtm_size_gb": 7.5,
                "dsm_size_gb": 7.7,
            },
        ],
    },

    # --- DuPage ---
    "dupage": {
        "name": "DuPage",
        "fips": "17043",
        "district": "district1",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "dupage_dtm_2022.zip",
                "dsm_zip": "dupage_dsm_2022.zip",
                "dtm_url": _url("district1", "dupage", "2022", "dupage_dtm_2022.zip"),
                "dsm_url": _url("district1", "dupage", "2022", "dupage_dsm_2022.zip"),
                "dtm_imageserver": "IL_DuPage_DTM_2022",
                "dsm_imageserver": "IL_DuPage_DSM_2022",
                "dtm_size_gb": 18.9,
                "dsm_size_gb": 20.3,
            },
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "dupa_dtm_2017.zip",
                "dsm_zip": "dupa_dsm_2017.zip",
                "dtm_url": _url("district1", "dupage", "2017", "dupa_dtm_2017.zip"),
                "dsm_url": _url("district1", "dupage", "2017", "dupa_dsm_2017.zip"),
                "dtm_imageserver": "IL_DuPage_DTM_2017",
                "dsm_imageserver": "IL_DuPage_DSM_2017",
                "dtm_size_gb": 20.4,
                "dsm_size_gb": 23.2,
            },
            {
                "year": "2014",
                "dtm_type": "dtm",
                "dtm_zip": "dupa_dtm_2014.zip",
                "dsm_zip": "dupa_dsm_2014.zip",
                "dtm_url": _url("district1", "dupage", "2014", "dupa_dtm_2014.zip"),
                "dsm_url": _url("district1", "dupage", "2014", "dupa_dsm_2014.zip"),
                "dtm_imageserver": "IL_DuPage_DTM_2014",
                "dsm_imageserver": "IL_DuPage_DSM_2014",
                "dtm_size_gb": 20.4,
                "dsm_size_gb": 23.4,
            },
            {
                "year": "2006",
                "dtm_type": "dem",
                "dtm_zip": "dupa_dtm_2006.zip",
                "dsm_zip": None,
                "dtm_url": _url("district1", "dupage", "2006", "dupa_dtm_2006.zip"),
                "dsm_url": None,
                "dtm_imageserver": "IL_DuPage_DEM_2006",
                "dsm_imageserver": None,
                "dtm_size_gb": 2.9,
                "dsm_size_gb": None,
            },
        ],
    },

    # --- Edgar ---
    "edgar": {
        "name": "Edgar",
        "fips": "17045",
        "district": "district5",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "edga_dtm_2020.zip",
                "dsm_zip": "edga_dsm_2020.zip",
                "dtm_url": _url("district5", "edgar", "2020", "edga_dtm_2020.zip"),
                "dsm_url": _url("district5", "edgar", "2020", "edga_dsm_2020.zip"),
                "dtm_imageserver": "IL_Edgar_DTM_2020",
                "dsm_imageserver": "IL_Edgar_DSM_2020",
                "dtm_size_gb": 34.7,
                "dsm_size_gb": 33.3,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "edga_dtm_2012.zip",
                "dsm_zip": "edga_dsm_2012.zip",
                "dtm_url": _url("district5", "edgar", "2012", "edga_dtm_2012.zip"),
                "dsm_url": _url("district5", "edgar", "2012", "edga_dsm_2012.zip"),
                "dtm_imageserver": "IL_Edgar_DTM_2012",
                "dsm_imageserver": "IL_Edgar_DSM_2012",
                "dtm_size_gb": 12.8,
                "dsm_size_gb": 12.6,
            },
        ],
    },

    # --- Edwards ---
    "edwards": {
        "name": "Edwards",
        "fips": "17047",
        "district": "district7",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "edwa_dtm_2020.zip",
                "dsm_zip": "edwa_dsm_2020.zip",
                "dtm_url": _url("district7", "edwards", "2020", "edwa_dtm_2020.zip"),
                "dsm_url": _url("district7", "edwards", "2020", "edwa_dsm_2020.zip"),
                "dtm_imageserver": "IL_Edwards_DTM_2020",
                "dsm_imageserver": "IL_Edwards_DSM_2020",
                "dtm_size_gb": 14.5,
                "dsm_size_gb": 14.9,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "edwa_dtm_2011.zip",
                "dsm_zip": "edwa_dsm_2011.zip",
                "dtm_url": _url("district7", "edwards", "2011", "edwa_dtm_2011.zip"),
                "dsm_url": _url("district7", "edwards", "2011", "edwa_dsm_2011.zip"),
                "dtm_imageserver": "IL_Edwards_DTM_2011",
                "dsm_imageserver": "IL_Edwards_DSM_2011",
                "dtm_size_gb": 2.7,
                "dsm_size_gb": 2.8,
            },
        ],
    },

    # --- Effingham ---
    "effingham": {
        "name": "Effingham",
        "fips": "17049",
        "district": "district7",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "effi_dtm_2021.zip",
                "dsm_zip": "effi_dsm_2021.zip",
                "dtm_url": _url("district7", "effingham", "2021", "effi_dtm_2021.zip"),
                "dsm_url": _url("district7", "effingham", "2021", "effi_dsm_2021.zip"),
                "dtm_imageserver": "IL_Effingham_DTM_2021",
                "dsm_imageserver": "IL_Effingham_DSM_2021",
                "dtm_size_gb": 26.7,
                "dsm_size_gb": 27.0,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "effi_dtm_2011.zip",
                "dsm_zip": "effi_dsm_2011.zip",
                "dtm_url": _url("district7", "effingham", "2011", "effi_dtm_2011.zip"),
                "dsm_url": _url("district7", "effingham", "2011", "effi_dsm_2011.zip"),
                "dtm_imageserver": "IL_Effingham_DTM_2011",
                "dsm_imageserver": "IL_Effingham_DSM_2011",
                "dtm_size_gb": 5.3,
                "dsm_size_gb": 5.5,
            },
        ],
    },

    # --- Fayette ---
    "fayette": {
        "name": "Fayette",
        "fips": "17051",
        "district": "district7",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "faye_dtm_2021.zip",
                "dsm_zip": "faye_dsm_2021.zip",
                "dtm_url": _url("district7", "fayette", "2021", "faye_dtm_2021.zip"),
                "dsm_url": _url("district7", "fayette", "2021", "faye_dsm_2021.zip"),
                "dtm_imageserver": "IL_Fayette_DTM_2021",
                "dsm_imageserver": "IL_Fayette_DSM_2021",
                "dtm_size_gb": 47.8,
                "dsm_size_gb": 42.0,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "faye_dtm_2011.zip",
                "dsm_zip": "faye_dsm_2011.zip",
                "dtm_url": _url("district7", "fayette", "2011", "faye_dtm_2011.zip"),
                "dsm_url": _url("district7", "fayette", "2011", "faye_dsm_2011.zip"),
                "dtm_imageserver": "IL_Fayette_DTM_2011",
                "dsm_imageserver": "IL_Fayette_DSM_2011",
                "dtm_size_gb": 7.5,
                "dsm_size_gb": 8.1,
            },
        ],
    },

    # --- Ford ---
    "ford": {
        "name": "Ford",
        "fips": "17053",
        "district": "district3",
        "collections": [
            {
                "year": "2023",
                "dtm_type": "dtm",
                "dtm_zip": "ford_dtm_2023.zip",
                "dsm_zip": "ford_dsm_2023.zip",
                "dtm_url": _url("district3", "ford", "2023", "ford_dtm_2023.zip"),
                "dsm_url": _url("district3", "ford", "2023", "ford_dsm_2023.zip"),
                "dtm_imageserver": "IL_Ford_DTM_2023",
                "dsm_imageserver": "IL_Ford_DSM_2023",
                "dtm_size_gb": 56.5,
                "dsm_size_gb": 57.2,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "ford_dtm_2015.zip",
                "dsm_zip": "ford_dsm_2015.zip",
                "dtm_url": _url("district3", "ford", "2015", "ford_dtm_2015.zip"),
                "dsm_url": _url("district3", "ford", "2015", "ford_dsm_2015.zip"),
                "dtm_imageserver": "IL_Ford_DTM_2015",
                "dsm_imageserver": "IL_Ford_DSM_2015",
                "dtm_size_gb": 14.9,
                "dsm_size_gb": 15.1,
            },
        ],
    },

    # --- Franklin ---
    "franklin": {
        "name": "Franklin",
        "fips": "17055",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "fran_dtm_2020.zip",
                "dsm_zip": "fran_dsm_2020.zip",
                "dtm_url": _url("district9", "franklin", "2020", "fran_dtm_2020.zip"),
                "dsm_url": _url("district9", "franklin", "2020", "fran_dsm_2020.zip"),
                "dtm_imageserver": "IL_Franklin_DTM_2020",
                "dsm_imageserver": "IL_Franklin_DSM_2020",
                "dtm_size_gb": 24.0,
                "dsm_size_gb": 26.1,
            },
            {
                "year": "2014",
                "dtm_type": "dtm",
                "dtm_zip": "fran_dtm_2014.zip",
                "dsm_zip": "fran_dsm_2014.zip",
                "dtm_url": _url("district9", "franklin", "2014", "fran_dtm_2014.zip"),
                "dsm_url": _url("district9", "franklin", "2014", "fran_dsm_2014.zip"),
                "dtm_imageserver": "IL_Franklin_DTM_2014",
                "dsm_imageserver": "IL_Franklin_DSM_2014",
                "dtm_size_gb": 6.0,
                "dsm_size_gb": 7.3,
            },
        ],
    },

    # --- Fulton ---
    "fulton": {
        "name": "Fulton",
        "fips": "17057",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "fulton_dtm_2022.zip",
                "dsm_zip": "fulton_dsm_2022.zip",
                "dtm_url": _url("district4", "fulton", "2022", "fulton_dtm_2022.zip"),
                "dsm_url": _url("district4", "fulton", "2022", "fulton_dsm_2022.zip"),
                "dtm_imageserver": "IL_Fulton_DTM_2022",
                "dsm_imageserver": "IL_Fulton_DSM_2022",
                "dtm_size_gb": 48.2,
                "dsm_size_gb": 51.2,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "fult_dtm_2012.zip",
                "dsm_zip": "fult_dsm_2012.zip",
                "dtm_url": _url("district4", "fulton", "2012", "fult_dtm_2012.zip"),
                "dsm_url": _url("district4", "fulton", "2012", "fult_dsm_2012.zip"),
                "dtm_imageserver": "IL_Fulton_DTM_2012",
                "dsm_imageserver": "IL_Fulton_DSM_2012",
                "dtm_size_gb": 9.6,
                "dsm_size_gb": 10.0,
            },
        ],
    },

    # --- Gallatin ---
    "gallatin": {
        "name": "Gallatin",
        "fips": "17059",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "gall_dtm_2020.zip",
                "dsm_zip": "gall_dsm_2020.zip",
                "dtm_url": _url("district9", "gallatin", "2020", "gall_dtm_2020.zip"),
                "dsm_url": _url("district9", "gallatin", "2020", "gall_dsm_2020.zip"),
                "dtm_imageserver": "IL_Gallatin_DTM_2020",
                "dsm_imageserver": None,
                "dtm_size_gb": 19.7,
                "dsm_size_gb": 19.4,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "gall_dtm_2011.zip",
                "dsm_zip": "gall_dsm_2011.zip",
                "dtm_url": _url("district9", "gallatin", "2011", "gall_dtm_2011.zip"),
                "dsm_url": _url("district9", "gallatin", "2011", "gall_dsm_2011.zip"),
                "dtm_imageserver": "IL_Gallatin_DTM_2011",
                "dsm_imageserver": "IL_Gallatin_DSM_2011",
                "dtm_size_gb": 2.1,
                "dsm_size_gb": 2.2,
            },
        ],
    },

    # --- Greene ---
    "greene": {
        "name": "Greene",
        "fips": "17061",
        "district": "district8",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "gree_dtm_2017.zip",
                "dsm_zip": "gree_dsm_2017.zip",
                "dtm_url": _url("district8", "greene", "2017", "gree_dtm_2017.zip"),
                "dsm_url": _url("district8", "greene", "2017", "gree_dsm_2017.zip"),
                "dtm_imageserver": "IL_Greene_DTM_2017",
                "dsm_imageserver": "IL_Greene_DSM_2017",
                "dtm_size_gb": 18.5,
                "dsm_size_gb": 19.0,
            },
        ],
    },

    # --- Grundy ---
    "grundy": {
        "name": "Grundy",
        "fips": "17063",
        "district": "district3",
        "collections": [
            {
                "year": "2018",
                "dtm_type": "dtm",
                "dtm_zip": "grun_dtm_2018.zip",
                "dsm_zip": "grun_dsm_2018.zip",
                "dtm_url": _url("district3", "grundy", "2018", "grun_dtm_2018.zip"),
                "dsm_url": _url("district3", "grundy", "2018", "grun_dsm_2018.zip"),
                "dtm_imageserver": None,
                "dsm_imageserver": None,
                "dtm_size_gb": 11.7,
                "dsm_size_gb": 12.5,
            },
            {
                "year": "2008",
                "dtm_type": "dtm",
                "dtm_zip": "grun_dtm_2008.zip",
                "dsm_zip": "grun_dsm_2008.zip",
                "dtm_url": _url("district3", "grundy", "2008", "grun_dtm_2008.zip"),
                "dsm_url": _url("district3", "grundy", "2008", "grun_dsm_2008.zip"),
                "dtm_imageserver": "IL_Grundy_DTM_2008",
                "dsm_imageserver": "IL_Grundy_DSM_2008",
                "dtm_size_gb": 2.9,
                "dsm_size_gb": 3.1,
            },
        ],
    },

    # --- Hamilton ---
    "hamilton": {
        "name": "Hamilton",
        "fips": "17065",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "hami_dtm_2020.zip",
                "dsm_zip": "hami_dsm_2020.zip",
                "dtm_url": _url("district9", "hamilton", "2020", "hami_dtm_2020.zip"),
                "dsm_url": _url("district9", "hamilton", "2020", "hami_dsm_2020.zip"),
                "dtm_imageserver": "IL_Hamilton_DTM_2021",
                "dsm_imageserver": "IL_Hamilton_DSM_2021",
                "dtm_size_gb": 32.9,
                "dsm_size_gb": 32.6,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "hami_dtm_2011.zip",
                "dsm_zip": "hami_dsm_2011.zip",
                "dtm_url": _url("district9", "hamilton", "2011", "hami_dtm_2011.zip"),
                "dsm_url": _url("district9", "hamilton", "2011", "hami_dsm_2011.zip"),
                "dtm_imageserver": "IL_Hamilton_DTM_2011",
                "dsm_imageserver": "IL_Hamilton_DSM_2011",
                "dtm_size_gb": 2.9,
                "dsm_size_gb": 3.0,
            },
        ],
    },

    # --- Hancock ---
    "hancock": {
        "name": "Hancock",
        "fips": "17067",
        "district": "district6",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "hanc_dtm_2017.zip",
                "dsm_zip": "hanc_dsm_2017.zip",
                "dtm_url": _url("district6", "hancock", "2017", "hanc_dtm_2017.zip"),
                "dsm_url": _url("district6", "hancock", "2017", "hanc_dsm_2017.zip"),
                "dtm_imageserver": None,
                "dsm_imageserver": None,
                "dtm_size_gb": 24.4,
                "dsm_size_gb": 25.4,
            },
        ],
    },

    # --- Hardin ---
    "hardin": {
        "name": "Hardin",
        "fips": "17069",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "hard_dtm_2020.zip",
                "dsm_zip": "hard_dsm_2020.zip",
                "dtm_url": _url("district9", "hardin", "2020", "hard_dtm_2020.zip"),
                "dsm_url": _url("district9", "hardin", "2020", "hard_dsm_2020.zip"),
                "dtm_imageserver": "IL_Hardin_DTM_2020",
                "dsm_imageserver": "IL_Hardin_DSM_2020",
                "dtm_size_gb": 11.4,
                "dsm_size_gb": 12.1,
            },
            {
                "year": "2014",
                "dtm_type": "dtm",
                "dtm_zip": "hard_dtm_2014.zip",
                "dsm_zip": "hard_dsm_2014.zip",
                "dtm_url": _url("district9", "hardin", "2014", "hard_dtm_2014.zip"),
                "dsm_url": _url("district9", "hardin", "2014", "hard_dsm_2014.zip"),
                "dtm_imageserver": None,
                "dsm_imageserver": None,
                "dtm_size_gb": 4.8,
                "dsm_size_gb": 5.3,
            },
        ],
    },

    # --- Henderson ---
    "henderson": {
        "name": "Henderson",
        "fips": "17071",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "hend_dtm_2022.zip",
                "dsm_zip": "hend_dsm_2022.zip",
                "dtm_url": _url("district4", "henderson", "2022", "hend_dtm_2022.zip"),
                "dsm_url": _url("district4", "henderson", "2022", "hend_dsm_2022.zip"),
                "dtm_imageserver": None,
                "dsm_imageserver": None,
                "dtm_size_gb": 20.0,
                "dsm_size_gb": 21.6,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "hend_dtm_2012.zip",
                "dsm_zip": "hend_dsm_2012.zip",
                "dtm_url": _url("district4", "henderson", "2012", "hend_dtm_2012.zip"),
                "dsm_url": _url("district4", "henderson", "2012", "hend_dsm_2012.zip"),
                "dtm_imageserver": "IL_Henderson_DTM_2012",
                "dsm_imageserver": "IL_Henderson_DSM_2012",
                "dtm_size_gb": 4.3,
                "dsm_size_gb": 4.5,
            },
        ],
    },

    # --- Henry ---
    "henry": {
        "name": "Henry",
        "fips": "17073",
        "district": "district2",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "henr_dtm_2020.zip",
                "dsm_zip": "henr_dsm_2020.zip",
                "dtm_url": _url("district2", "henry", "2020", "henr_dtm_2020.zip"),
                "dsm_url": _url("district2", "henry", "2020", "henr_dsm_2020.zip"),
                "dtm_imageserver": "IL_Henry_DTM_2020",
                "dsm_imageserver": "IL_Henry_DSM_2020",
                "dtm_size_gb": 25.4,
                "dsm_size_gb": 26.1,
            },
            {
                "year": "2009",
                "dtm_type": "dtm",
                "dtm_zip": "henr_dtm_2009.zip",
                "dsm_zip": "henr_dsm_2009.zip",
                "dtm_url": _url("district2", "henry", "2009", "henr_dtm_2009.zip"),
                "dsm_url": _url("district2", "henry", "2009", "henr_dsm_2009.zip"),
                "dtm_imageserver": "IL_Henry_DTM_2009",
                "dsm_imageserver": "IL_Henry_DSM_2009",
                "dtm_size_gb": 7.5,
                "dsm_size_gb": 7.8,
            },
        ],
    },

    # --- Iroquois ---
    "iroquois": {
        "name": "Iroquois",
        "fips": "17075",
        "district": "district3",
        "collections": [
            {
                "year": "2024",
                "dtm_type": "dtm",
                "dtm_zip": "iroquois_dtm_2024.zip",
                "dsm_zip": "iroquois_dsm_2024.zip",
                "dtm_url": _url("district3", "iroquois", "2024", "iroquois_dtm_2024.zip"),
                "dsm_url": _url("district3", "iroquois", "2024", "iroquois_dsm_2024.zip"),
                "dtm_imageserver": "IL_Iroquois_DTM_2024",
                "dsm_imageserver": "IL_Iroquois_DTM_2024",
                "dtm_size_gb": 116.0,
                "dsm_size_gb": 119.0,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "iroq_dtm_2015.zip",
                "dsm_zip": "iroq_dsm_2015.zip",
                "dtm_url": _url("district3", "iroquois", "2015", "iroq_dtm_2015.zip"),
                "dsm_url": _url("district3", "iroquois", "2015", "iroq_dsm_2015.zip"),
                "dtm_imageserver": "IL_Iroquois_DTM_2015",
                "dsm_imageserver": "IL_Iroquois_DSM_2015",
                "dtm_size_gb": 32.9,
                "dsm_size_gb": 33.8,
            },
        ],
    },

    # --- Jackson ---
    "jackson": {
        "name": "Jackson",
        "fips": "17077",
        "district": "district9",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "jack_dtm_2021.zip",
                "dsm_zip": "jack_dsm_2021.zip",
                "dtm_url": _url("district9", "jackson", "2021", "jack_dtm_2021.zip"),
                "dsm_url": _url("district9", "jackson", "2021", "jack_dsm_2021.zip"),
                "dtm_imageserver": "IL_Jackson_DTM_2021",
                "dsm_imageserver": "IL_Jackson_DSM_2021",
                "dtm_size_gb": 34.4,
                "dsm_size_gb": 36.1,
            },
            {
                "year": "2014",
                "dtm_type": "dtm",
                "dtm_zip": "jack_dtm_2014.zip",
                "dsm_zip": "jack_dsm_2014.zip",
                "dtm_url": _url("district9", "jackson", "2014", "jack_dtm_2014.zip"),
                "dsm_url": _url("district9", "jackson", "2014", "jack_dsm_2014.zip"),
                "dtm_imageserver": "IL_Jackson_DTM_2014",
                "dsm_imageserver": "IL_Jackson_DSM_2014",
                "dtm_size_gb": 10.0,
                "dsm_size_gb": 10.7,
            },
        ],
    },

    # --- Jasper ---
    "jasper": {
        "name": "Jasper",
        "fips": "17079",
        "district": "district7",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "jasp_dtm_2020.zip",
                "dsm_zip": "jasp_dsm_2020.zip",
                "dtm_url": _url("district7", "jasper", "2020", "jasp_dtm_2020.zip"),
                "dsm_url": _url("district7", "jasper", "2020", "jasp_dsm_2020.zip"),
                "dtm_imageserver": "IL_Jasper_DTM_2020",
                "dsm_imageserver": "IL_Jasper_DSM_2020",
                "dtm_size_gb": 29.3,
                "dsm_size_gb": 30.4,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "jasp_dtm_2011.zip",
                "dsm_zip": "jasp_dsm_2011.zip",
                "dtm_url": _url("district7", "jasper", "2011", "jasp_dtm_2011.zip"),
                "dsm_url": _url("district7", "jasper", "2011", "jasp_dsm_2011.zip"),
                "dtm_imageserver": "IL_Jasper_DTM_2011",
                "dsm_imageserver": "IL_Jasper_DSM_2011",
                "dtm_size_gb": 5.4,
                "dsm_size_gb": 5.6,
            },
        ],
    },

    # --- Jefferson ---
    "jefferson": {
        "name": "Jefferson",
        "fips": "17081",
        "district": "district9",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "jeff_dtm_2021.zip",
                "dsm_zip": "jeff_dsm_2021.zip",
                "dtm_url": _url("district9", "jefferson", "2021", "jeff_dtm_2021.zip"),
                "dsm_url": _url("district9", "jefferson", "2021", "jeff_dsm_2021.zip"),
                "dtm_imageserver": "IL_Jefferson_DTM_2021",
                "dsm_imageserver": "IL_Jefferson_DSM_2021",
                "dtm_size_gb": 32.7,
                "dsm_size_gb": 35.1,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "jeff_dtm_2015.zip",
                "dsm_zip": "jeff_dsm_2015.zip",
                "dtm_url": _url("district9", "jefferson", "2015", "jeff_dtm_2015.zip"),
                "dsm_url": _url("district9", "jefferson", "2015", "jeff_dsm_2015.zip"),
                "dtm_imageserver": "IL_Jefferson_DTM_2015",
                "dsm_imageserver": "IL_Jefferson_DSM_2015",
                "dtm_size_gb": 8.2,
                "dsm_size_gb": 8.8,
            },
            {
                "year": "2012",
                "dtm_type": "dem",
                "dtm_zip": "jeff_dem_2012.zip",
                "dsm_zip": "jeff_dsm_2012.zip",
                "dtm_url": _url("district9", "jefferson", "2012", "jeff_dem_2012.zip"),
                "dsm_url": _url("district9", "jefferson", "2012", "jeff_dsm_2012.zip"),
                "dtm_imageserver": "IL_Jefferson_DEM_2012",
                "dsm_imageserver": "IL_Jefferson_DSM_2012",
                "dtm_size_gb": 3.1,
                "dsm_size_gb": 3.2,
            },
        ],
    },

    # --- Jersey ---
    "jersey": {
        "name": "Jersey",
        "fips": "17083",
        "district": "district8",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "jers_dtm_2021.zip",
                "dsm_zip": "jers_dsm_2021.zip",
                "dtm_url": _url("district8", "jersey", "2021", "jers_dtm_2021.zip"),
                "dsm_url": _url("district8", "jersey", "2021", "jers_dsm_2021.zip"),
                "dtm_imageserver": "IL_Jersey_DTM_2021",
                "dsm_imageserver": "IL_Jersey_DSM_2021",
                "dtm_size_gb": 22.2,
                "dsm_size_gb": 22.8,
            },
            {
                "year": "2011",
                "dtm_type": "dem",
                "dtm_zip": "jers_dem_2011.zip",
                "dsm_zip": "jers_dsm_2011.zip",
                "dtm_url": _url("district8", "jersey", "2011", "jers_dem_2011.zip"),
                "dsm_url": _url("district8", "jersey", "2011", "jers_dsm_2011.zip"),
                "dtm_imageserver": "IL_Jersey_DEM_2011",
                "dsm_imageserver": "IL_Jersey_DSM_2011",
                "dtm_size_gb": 2.4,
                "dsm_size_gb": 2.5,
            },
        ],
    },

    # --- Jo Daviess ---
    "jodaviess": {
        "name": "Jo Daviess",
        "fips": "17085",
        "district": "district2",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "joda_dtm_2020.zip",
                "dsm_zip": "joda_dsm_2020.zip",
                "dtm_url": _url("district2", "jodaviess", "2020", "joda_dtm_2020.zip"),
                "dsm_url": _url("district2", "jodaviess", "2020", "joda_dsm_2020.zip"),
                "dtm_imageserver": "IL_Jo_Daviess_DTM_2020",
                "dsm_imageserver": "IL_Jo_Daviess_DSM_2020",
                "dtm_size_gb": 21.5,
                "dsm_size_gb": 21.7,
            },
            {
                "year": "2009",
                "dtm_type": "dtm",
                "dtm_zip": "joda_dtm_2009.zip",
                "dsm_zip": "joda_dsm_2009.zip",
                "dtm_url": _url("district2", "jodaviess", "2009", "joda_dtm_2009.zip"),
                "dsm_url": _url("district2", "jodaviess", "2009", "joda_dsm_2009.zip"),
                "dtm_imageserver": "IL_Jo_Daviess_DTM_2009",
                "dsm_imageserver": "IL_Jo_Daviess_DSM_2009",
                "dtm_size_gb": 6.4,
                "dsm_size_gb": 6.7,
            },
        ],
    },

    # --- Johnson ---
    "johnson": {
        "name": "Johnson",
        "fips": "17087",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "john_dtm_2020.zip",
                "dsm_zip": "john_dsm_2020.zip",
                "dtm_url": _url("district9", "johnson", "2020", "john_dtm_2020.zip"),
                "dsm_url": _url("district9", "johnson", "2020", "john_dsm_2020.zip"),
                "dtm_imageserver": "IL_Johnson_DTM_2020",
                "dsm_imageserver": "IL_Johnson_DSM_2020",
                "dtm_size_gb": 21.7,
                "dsm_size_gb": 22.9,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "john_dtm_2012.zip",
                "dsm_zip": "john_dsm_2012.zip",
                "dtm_url": _url("district9", "johnson", "2012", "john_dtm_2012.zip"),
                "dsm_url": _url("district9", "johnson", "2012", "john_dsm_2012.zip"),
                "dtm_imageserver": "IL_Johnson_DTM_2012",
                "dsm_imageserver": "IL_Johnson_DSM_2012",
                "dtm_size_gb": 5.7,
                "dsm_size_gb": 5.9,
            },
        ],
    },

    # --- Kane ---
    "kane": {
        "name": "Kane",
        "fips": "17089",
        "district": "district1",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "kane_dtm_2017.zip",
                "dsm_zip": "kane_dsm_2017.zip",
                "dtm_url": _url("district1", "kane", "2017", "kane_dtm_2017.zip"),
                "dsm_url": _url("district1", "kane", "2017", "kane_dsm_2017.zip"),
                "dtm_imageserver": "IL_Kane_DTM_2017",
                "dsm_imageserver": "IL_Kane_DSM_2017",
                "dtm_size_gb": 24.6,
                "dsm_size_gb": 26.8,
            },
            {
                "year": "2008",
                "dtm_type": "dtm",
                "dtm_zip": "kane_dtm_2008.zip",
                "dsm_zip": "kane_dsm_2008.zip",
                "dtm_url": _url("district1", "kane", "2008", "kane_dtm_2008.zip"),
                "dsm_url": _url("district1", "kane", "2008", "kane_dtm_2008.zip"),  # clearinghouse has same URL for both
                "dtm_imageserver": "IL_Kane_DTM_2008",
                "dsm_imageserver": "IL_Kane_DSM_2008",
                "dtm_size_gb": 3.7,
                "dsm_size_gb": 3.9,
            },
        ],
    },

    # --- Kankakee ---
    "kankakee": {
        "name": "Kankakee",
        "fips": "17091",
        "district": "district3",
        "collections": [
            {
                "year": "2023",
                "dtm_type": "dtm",
                "dtm_zip": "kankakee_dtm_2023.zip",
                "dsm_zip": "kankakee_dsm_2023.zip",
                "dtm_url": _url("district3", "kankakee", "2023", "kankakee_dtm_2023.zip"),
                "dsm_url": _url("district3", "kankakee", "2023", "kankakee_dsm_2023.zip"),
                "dtm_imageserver": "IL_Kankakee_DTM_2023",
                "dsm_imageserver": "IL_Kankakee_DSM_2023",
                "dtm_size_gb": 90.9,
                "dsm_size_gb": 78.3,
            },
            {
                "year": "2014",
                "dtm_type": "dtm",
                "dtm_zip": "kank_dtm_2014.zip",
                "dsm_zip": "kank_dsm_2014.zip",
                "dtm_url": _url("district3", "kankakee", "2014", "kank_dtm_2014.zip"),
                "dsm_url": _url("district3", "kankakee", "2014", "kank_dsm_2014.zip"),
                "dtm_imageserver": "IL_Kankakee_DTM_2014",
                "dsm_imageserver": "IL_Kankakee_DSM_2014",
                "dtm_size_gb": 21.4,
                "dsm_size_gb": 22.2,
            },
        ],
    },

    # --- Kendall ---
    "kendall": {
        "name": "Kendall",
        "fips": "17093",
        "district": "district3",
        "collections": [
            {
                "year": "2018",
                "dtm_type": "dtm",
                "dtm_zip": "kend_dtm_2018.zip",
                "dsm_zip": "kend_dsm_2018.zip",
                "dtm_url": _url("district3", "kendall", "2018", "kend_dtm_2018.zip"),
                "dsm_url": _url("district3", "kendall", "2018", "kend_dsm_2018.zip"),
                "dtm_imageserver": None,
                "dsm_imageserver": None,
                "dtm_size_gb": 8.8,
                "dsm_size_gb": 9.3,
            },
            {
                "year": "2010",
                "dtm_type": "dtm",
                "dtm_zip": "kend_dtm_2010.zip",
                "dsm_zip": "kend_dsm_2010.zip",
                "dtm_url": _url("district3", "kendall", "2010", "kend_dtm_2010.zip"),
                "dsm_url": _url("district3", "kendall", "2010", "kend_dsm_2010.zip"),
                "dtm_imageserver": "IL_Kendall_DTM_2010",
                "dsm_imageserver": "IL_Kendall_DSM_2010",
                "dtm_size_gb": 3.6,
                "dsm_size_gb": 3.9,
            },
        ],
    },

    # --- Knox ---
    "knox": {
        "name": "Knox",
        "fips": "17095",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "knox_DTM_2022.zip",
                "dsm_zip": "knox_DSM_2022.zip",
                "dtm_url": _url("district4", "knox", "2022", "knox_DTM_2022.zip"),
                "dsm_url": _url("district4", "knox", "2022", "knox_DSM_2022.zip"),
                "dtm_imageserver": "IL_Knox_DTM_2022",
                "dsm_imageserver": "IL_Knox_DSM_2022",
                "dtm_size_gb": 38.1,
                "dsm_size_gb": 39.1,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "knox_dtm_2012.zip",
                "dsm_zip": "knox_dsm_2012.zip",
                "dtm_url": _url("district4", "knox", "2012", "knox_dtm_2012.zip"),
                "dsm_url": _url("district4", "knox", "2012", "knox_dsm_2012.zip"),
                "dtm_imageserver": "IL_Knox_DTM_2012",
                "dsm_imageserver": "IL_Knox_DSM_2012",
                "dtm_size_gb": 12.8,
                "dsm_size_gb": 13.2,
            },
        ],
    },

    # --- Lake ---
    "lake": {
        "name": "Lake",
        "fips": "17097",
        "district": "district1",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "lake_dtm_2017.zip",
                "dsm_zip": "lake_dsm_2017.zip",
                "dtm_url": _url("district1", "lake", "2017", "lake_dtm_2017.zip"),
                "dsm_url": _url("district1", "lake", "2017", "lake_dsm_2017.zip"),
                "dtm_imageserver": "IL_Lake_DTM_2017",
                "dsm_imageserver": "IL_Lake_DSM_2017",
                "dtm_size_gb": 22.8,
                "dsm_size_gb": 26.7,
            },
            {
                "year": "2007",
                "dtm_type": "dtm",
                "dtm_zip": "lake_dtm_2007.zip",
                "dsm_zip": "lake_dsm_2007.zip",
                "dtm_url": _url("district1", "lake", "2007", "lake_dtm_2007.zip"),
                "dsm_url": _url("district1", "lake", "2007", "lake_dsm_2007.zip"),
                "dtm_imageserver": "IL_Lake_DTM_2007",
                "dsm_imageserver": "IL_Lake_DSM_2007",
                "dtm_size_gb": 9.2,
                "dsm_size_gb": 7.0,
            },
        ],
    },

    # --- LaSalle ---
    "lasalle": {
        "name": "LaSalle",
        "fips": "17099",
        "district": "district3",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "lasa_dtm_2017.zip",
                "dsm_zip": "lasa_dsm_2017.zip",
                "dtm_url": _url("district3", "lasalle", "2017", "lasa_dtm_2017.zip"),
                "dsm_url": _url("district3", "lasalle", "2017", "lasa_dsm_2017.zip"),
                "dtm_imageserver": "IL_LaSalle_DTM_2017",
                "dsm_imageserver": "IL_LaSalle_DSM_2017",
                "dtm_size_gb": 57.4,
                "dsm_size_gb": 60.1,
            },
        ],
    },

    # --- Lawrence ---
    "lawrence": {
        "name": "Lawrence",
        "fips": "17101",
        "district": "district7",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "lawr_dtm_2020.zip",
                "dsm_zip": "lawr_dsm_2020.zip",
                "dtm_url": _url("district7", "lawrence", "2020", "lawr_dtm_2020.zip"),
                "dsm_url": _url("district7", "lawrence", "2020", "lawr_dsm_2020.zip"),
                "dtm_imageserver": "IL_Lawrence_DTM_2020",
                "dsm_imageserver": "IL_Lawrence_DSM_2020",
                "dtm_size_gb": 23.6,
                "dsm_size_gb": 25.1,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "lawr_dtm_2011.zip",
                "dsm_zip": "lawr_dsm_2011.zip",
                "dtm_url": _url("district7", "lawrence", "2011", "lawr_dtm_2011.zip"),
                "dsm_url": _url("district7", "lawrence", "2011", "lawr_dsm_2011.zip"),
                "dtm_imageserver": "IL_Lawrence_DTM_2011",
                "dsm_imageserver": "IL_Lawrence_DSM_2011",
                "dtm_size_gb": 4.3,
                "dsm_size_gb": 4.4,
            },
        ],
    },

    # --- Lee ---
    "lee": {
        "name": "Lee",
        "fips": "17103",
        "district": "district2",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "lee_dtm_2020.zip",
                "dsm_zip": "lee_dsm_2020.zip",
                "dtm_url": _url("district2", "lee", "2020", "lee_dtm_2020.zip"),
                "dsm_url": _url("district2", "lee", "2020", "lee_dsm_2020.zip"),
                "dtm_imageserver": "IL_Lee_DTM_2020",
                "dsm_imageserver": "IL_Lee_DSM_2020",
                "dtm_size_gb": 22.2,
                "dsm_size_gb": 23.0,
            },
            {
                "year": "2009",
                "dtm_type": "dtm",
                "dtm_zip": "lee_dtm_2009.zip",
                "dsm_zip": "lee_dsm_2009.zip",
                "dtm_url": _url("district2", "lee", "2009", "lee_dtm_2009.zip"),
                "dsm_url": _url("district2", "lee", "2009", "lee_dsm_2009.zip"),
                "dtm_imageserver": "IL_Lee_DTM_2009",
                "dsm_imageserver": "IL_Lee_DSM_2009",
                "dtm_size_gb": 6.9,
                "dsm_size_gb": 7.1,
            },
        ],
    },

    # --- Livingston ---
    "livingston": {
        "name": "Livingston",
        "fips": "17105",
        "district": "district3",
        "collections": [
            {
                "year": "2024",
                "dtm_type": "dtm",
                "dtm_zip": "livi_dtm_2024.zip",
                "dsm_zip": "livi_dsm_2024.zip",
                "dtm_url": _url("district3", "livingston", "2024", "livi_dtm_2024.zip"),
                "dsm_url": _url("district3", "livingston", "2024", "livi_dsm_2024.zip"),
                "dtm_imageserver": "IL_Livingston_DTM_2024",
                "dsm_imageserver": "IL_Livingston_DTM_2024",
                "dtm_size_gb": 114.0,
                "dsm_size_gb": 117.0,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "livi_dtm_2015.zip",
                "dsm_zip": "livi_dsm_2015.zip",
                "dtm_url": _url("district3", "livingston", "2015", "livi_dtm_2015.zip"),
                "dsm_url": _url("district3", "livingston", "2015", "livi_dsm_2015.zip"),
                "dtm_imageserver": "IL_Livingston_DTM_2015",
                "dsm_imageserver": "IL_Livingston_DSM_2015",
                "dtm_size_gb": 30.9,
                "dsm_size_gb": 31.9,
            },
        ],
    },

    # --- Logan ---
    "logan": {
        "name": "Logan",
        "fips": "17107",
        "district": "district6",
        "collections": [
            {
                "year": "2023",
                "dtm_type": "dtm",
                "dtm_zip": "loga_dtm_2023.zip",
                "dsm_zip": "loga_dsm_2023.zip",
                "dtm_url": _url("district6", "logan", "2023", "loga_dtm_2023.zip"),
                "dsm_url": _url("district6", "logan", "2023", "loga_dsm_2023.zip"),
                "dtm_imageserver": "IL_Logan_DTM_2023",
                "dsm_imageserver": "IL_Logan_DSM_2023",
                "dtm_size_gb": 73.1,
                "dsm_size_gb": 74.0,
            },
            {
                "year": "2013",
                "dtm_type": "dtm",
                "dtm_zip": "loga_dtm_2013.zip",
                "dsm_zip": "loga_dsm_2013.zip",
                "dtm_url": _url("district6", "logan", "2013", "loga_dtm_2013.zip"),
                "dsm_url": _url("district6", "logan", "2013", "loga_dsm_2013.zip"),
                "dtm_imageserver": "IL_Logan_DTM_2013",
                "dsm_imageserver": None,
                "dtm_size_gb": 31.7,
                "dsm_size_gb": 33.6,
            },
        ],
    },

    # --- Macon ---
    "macon": {
        "name": "Macon",
        "fips": "17115",
        "district": "district7",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "maco_dtm_2021.zip",
                "dsm_zip": "maco_dsm_2021.zip",
                "dtm_url": _url("district7", "macon", "2021", "maco_dtm_2021.zip"),
                "dsm_url": _url("district7", "macon", "2021", "maco_dsm_2021.zip"),
                "dtm_imageserver": "IL_Macon_DTM_2021",
                "dsm_imageserver": "IL_Macon_DSM_2021",
                "dtm_size_gb": 31.7,
                "dsm_size_gb": 32.2,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "maco_dtm_2011.zip",
                "dsm_zip": "maco_dsm_2011.zip",
                "dtm_url": _url("district7", "macon", "2011", "maco_dtm_2011.zip"),
                "dsm_url": _url("district7", "macon", "2011", "maco_dsm_2011.zip"),
                "dtm_imageserver": "IL_Macon_DTM_2011",
                "dsm_imageserver": "IL_Macon_DSM_2011",
                "dtm_size_gb": 4.7,
                "dsm_size_gb": 4.8,
            },
        ],
    },

    # --- Macoupin ---
    "macoupin": {
        "name": "Macoupin",
        "fips": "17117",
        "district": "district6",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "macu_dtm_2017.zip",
                "dsm_zip": "macu_dsm_2017.zip",
                "dtm_url": _url("district6", "macoupin", "2017", "macu_dtm_2017.zip"),
                "dsm_url": _url("district6", "macoupin", "2017", "macu_dsm_2017.zip"),
                "dtm_imageserver": "IL_Macoupin_DTM_2017",
                "dsm_imageserver": "IL_Macoupin_DSM_2017",
                "dtm_size_gb": 27.9,
                "dsm_size_gb": 28.9,
            },
        ],
    },

    # --- Madison ---
    "madison": {
        "name": "Madison",
        "fips": "17119",
        "district": "district8",
        "collections": [
            {
                "year": "2023",
                "dtm_type": "dtm",
                "dtm_zip": "madi_dtm_2023.zip",
                "dsm_zip": "madi_dsm_2023.zip",
                "dtm_url": _url("district8", "madison", "2023", "madi_dtm_2023.zip"),
                "dsm_url": _url("district8", "madison", "2023", "madi_dsm_2023.zip"),
                "dtm_imageserver": "IL_Madison_DTM_2023",
                "dsm_imageserver": "IL_Madison_DSM_2023",
                "dtm_size_gb": 80.8,
                "dsm_size_gb": 85.8,
            },
            {
                "year": "2014",
                "dtm_type": "dtm",
                "dtm_zip": "madi_dtm_2014.zip",
                "dsm_zip": "madi_dsm_2014.zip",
                "dtm_url": _url("district8", "madison", "2014", "madi_dtm_2014.zip"),
                "dsm_url": _url("district8", "madison", "2014", "madi_dsm_2014.zip"),
                "dtm_imageserver": "IL_Madison_DTM_2014",
                "dsm_imageserver": "IL_Madison_DSM_2014",
                "dtm_size_gb": 27.2,
                "dsm_size_gb": 29.0,
            },
        ],
    },

    # --- Marion ---
    "marion": {
        "name": "Marion",
        "fips": "17121",
        "district": "district8",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "mari_dtm_2021.zip",
                "dsm_zip": "mari_dsm_2021.zip",
                "dtm_url": _url("district8", "marion", "2021", "mari_dtm_2021.zip"),
                "dsm_url": _url("district8", "marion", "2021", "mari_dsm_2021.zip"),
                "dtm_imageserver": "IL_Marion_DTM_2021",
                "dsm_imageserver": "IL_Marion_DSM_2021",
                "dtm_size_gb": 32.5,
                "dsm_size_gb": 33.8,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "mari_dtm_2015.zip",
                "dsm_zip": "mari_dsm_2015.zip",
                "dtm_url": _url("district8", "marion", "2015", "mari_dtm_2015.zip"),
                "dsm_url": _url("district8", "marion", "2015", "mari_dsm_2015.zip"),
                "dtm_imageserver": "IL_Marion_DTM_2015",
                "dsm_imageserver": "IL_Marion_DSM_2015",
                "dtm_size_gb": 8.1,
                "dsm_size_gb": 8.5,
            },
        ],
    },

    # --- Marshall ---
    "marshall": {
        "name": "Marshall",
        "fips": "17123",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "marshall_DTM_2022.zip",
                "dsm_zip": "marshall_DSM_2022.zip",
                "dtm_url": _url("district4", "marshall", "2022", "marshall_DTM_2022.zip"),
                "dsm_url": _url("district4", "marshall", "2022", "marshall_DSM_2022.zip"),
                "dtm_imageserver": "IL_Marshall_DTM_2022",
                "dsm_imageserver": "IL_Marshall_DSM_2022",
                "dtm_size_gb": 20.8,
                "dsm_size_gb": 22.3,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "mars_dtm_2012.zip",
                "dsm_zip": "mars_dsm_2012.zip",
                "dtm_url": _url("district4", "marshall", "2012", "mars_dtm_2012.zip"),
                "dsm_url": _url("district4", "marshall", "2012", "mars_dsm_2012.zip"),
                "dtm_imageserver": "IL_Marshall_DTM_2012",
                "dsm_imageserver": "IL_Marshall_DSM_2012",
                "dtm_size_gb": 4.4,
                "dsm_size_gb": 4.6,
            },
        ],
    },

    # --- Mason ---
    "mason": {
        "name": "Mason",
        "fips": "17125",
        "district": "district6",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "maso_dtm_2017.zip",
                "dsm_zip": "maso_dsm_2017.zip",
                "dtm_url": _url("district6", "mason", "2017", "maso_dtm_2017.zip"),
                "dsm_url": _url("district6", "mason", "2017", "maso_dsm_2017.zip"),
                "dtm_imageserver": "IL_Mason_DTM_2017",
                "dsm_imageserver": "IL_Mason_DSM_2017",
                "dtm_size_gb": 16.4,
                "dsm_size_gb": 17.7,
            },
        ],
    },

    # --- Massac ---
    "massac": {
        "name": "Massac",
        "fips": "17127",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "mass_dtm_2020.zip",
                "dsm_zip": "mass_dsm_2020.zip",
                "dtm_url": _url("district9", "massac", "2020", "mass_dtm_2020.zip"),
                "dsm_url": _url("district9", "massac", "2020", "mass_dsm_2020.zip"),
                "dtm_imageserver": "IL_Massac_DTM_2020",
                "dsm_imageserver": "IL_Massac_DSM_2020",
                "dtm_size_gb": 14.5,
                "dsm_size_gb": 15.3,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "mass_dtm_2012.zip",
                "dsm_zip": "mass_dsm_2012.zip",
                "dtm_url": _url("district9", "massac", "2012", "mass_dtm_2012.zip"),
                "dsm_url": _url("district9", "massac", "2012", "mass_dsm_2012.zip"),
                "dtm_imageserver": None,
                "dsm_imageserver": None,
                "dtm_size_gb": 3.5,
                "dsm_size_gb": 3.8,
            },
        ],
    },

    # --- McDonough ---
    "mcdonough": {
        "name": "McDonough",
        "fips": "17109",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "mcdo_DTM_2022.zip",
                "dsm_zip": "mcdo_DSM_2022.zip",
                "dtm_url": _url("district4", "mcdonough", "2022", "mcdo_DTM_2022.zip"),
                "dsm_url": _url("district4", "mcdonough", "2022", "mcdo_DSM_2022.zip"),
                "dtm_imageserver": "IL_McDonough_DTM_2022",
                "dsm_imageserver": "IL_McDonough_DSM_2022",
                "dtm_size_gb": 31.9,
                "dsm_size_gb": 32.3,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "mcdo_dtm_2012.zip",
                "dsm_zip": "mcdo_dsm_2012.zip",
                "dtm_url": _url("district4", "mcdonough", "2012", "mcdo_dtm_2012.zip"),
                "dsm_url": _url("district4", "mcdonough", "2012", "mcdo_dsm_2012.zip"),
                "dtm_imageserver": "IL_McDonough_DTM_2012",
                "dsm_imageserver": "IL_McDonough_DSM_2012",
                "dtm_size_gb": 7.9,
                "dsm_size_gb": 8.1,
            },
        ],
    },

    # --- McHenry ---
    "mchenry": {
        "name": "McHenry",
        "fips": "17111",
        "district": "district1",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "mchenry_dtm_2022.zip",
                "dsm_zip": "mchenry_dsm_2022.zip",
                "dtm_url": _url("district1", "mchenry", "2022", "mchenry_dtm_2022.zip"),
                "dsm_url": _url("district1", "mchenry", "2022", "mchenry_dsm_2022.zip"),
                "dtm_imageserver": "IL_McHenry_DTM_2022",
                "dsm_imageserver": "IL_McHenry_DSM_2022",
                "dtm_size_gb": 68.6,
                "dsm_size_gb": 73.4,
            },
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "mche_dtm_2017.zip",
                "dsm_zip": "mche_dsm_2017.zip",
                "dtm_url": _url("district1", "mchenry", "2017", "mche_dtm_2017.zip"),
                "dsm_url": _url("district1", "mchenry", "2017", "mche_dsm_2017.zip"),
                "dtm_imageserver": "IL_McHenry_DTM_2017",
                "dsm_imageserver": "IL_McHenry_DSM_2017",
                "dtm_size_gb": 31.1,
                "dsm_size_gb": 33.5,
            },
            {
                "year": "2008",
                "dtm_type": "dtm",
                "dtm_zip": "mche_dtm_2008.zip",
                "dsm_zip": "mche_dsm_2008.zip",
                "dtm_url": _url("district1", "mchenry", "2008", "mche_dtm_2008.zip"),
                "dsm_url": _url("district1", "mchenry", "2008", "mche_dsm_2008.zip"),
                "dtm_imageserver": "IL_McHenry_DTM_2008",
                "dsm_imageserver": "IL_McHenry_DSM_2008",
                "dtm_size_gb": 4.5,
                "dsm_size_gb": 4.8,
            },
        ],
    },
    # --- McLean ---
    "mclean": {
        "name": "McLean",
        "fips": "17113",
        "district": "district5",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "mclean_dtm_2022.zip",
                "dsm_zip": "mclean_dsm_2022.zip",
                "dtm_url": _url("district5", "mclean", "2022", "mclean_dtm_2022.zip"),
                "dsm_url": _url("district5", "mclean", "2022", "mclean_dsm_2022.zip"),
                "dtm_imageserver": "IL_McLean_DTM_2022",
                "dsm_imageserver": "IL_McLean_DSM_2022",
                "dtm_size_gb": 58.8,
                "dsm_size_gb": 59.6,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "mcle_dtm_2012.zip",
                "dsm_zip": "mcle_dsm_2012.zip",
                "dtm_url": _url("district5", "mclean", "2012", "mcle_dtm_2012.zip"),
                "dsm_url": _url("district5", "mclean", "2012", "mcle_dsm_2012.zip"),
                "dtm_imageserver": "IL_McLean_DTM_2012",
                "dsm_imageserver": "IL_McLean_DSM_2012",
                "dtm_size_gb": 23.4,
                "dsm_size_gb": 24.1,
            },
        ],
    },

    # --- Menard ---
    "menard": {
        "name": "Menard",
        "fips": "17129",
        "district": "district6",
        "collections": [
            {
                "year": "2018",
                "dtm_type": "dtm",
                "dtm_zip": "mena_dtm_2018.zip",
                "dsm_zip": "mena_dsm_2018.zip",
                "dtm_url": _url("district6", "menard", "2018", "mena_dtm_2018.zip"),
                "dsm_url": _url("district6", "menard", "2018", "mena_dsm_2018.zip"),
                "dtm_imageserver": "IL_Menard_DTM_2018",
                "dsm_imageserver": "IL_Menard_DSM_2018",
                "dtm_size_gb": 9.9,
                "dsm_size_gb": 10.3,
            },
        ],
    },

    # --- Mercer ---
    "mercer": {
        "name": "Mercer",
        "fips": "17131",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "merc_dtm_2022.zip",
                "dsm_zip": "merc_dsm_2022.zip",
                "dtm_url": _url("district4", "mercer", "2022", "merc_dtm_2022.zip"),
                "dsm_url": _url("district4", "mercer", "2022", "merc_dsm_2022.zip"),
                "dtm_imageserver": "IL_Mercer_DTM_2022",
                "dsm_imageserver": "IL_Mercer_DSM_2022",
                "dtm_size_gb": 31.5,
                "dsm_size_gb": 32.5,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "merc_dtm_2012.zip",
                "dsm_zip": "merc_dsm_2012.zip",
                "dtm_url": _url("district4", "mercer", "2012", "merc_dtm_2012.zip"),
                "dsm_url": _url("district4", "mercer", "2012", "merc_dsm_2012.zip"),
                "dtm_imageserver": "IL_Mercer_DTM_2012",
                "dsm_imageserver": "IL_Mercer_DSM_2012",
                "dtm_size_gb": 8.0,
                "dsm_size_gb": 8.4,
            },
        ],
    },

    # --- Monroe ---
    "monroe": {
        "name": "Monroe",
        "fips": "17133",
        "district": "district8",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "monr_dtm_2020.zip",
                "dsm_zip": "monr_dsm_2020.zip",
                "dtm_url": _url("district8", "monroe", "2020", "monr_dtm_2020.zip"),
                "dsm_url": _url("district8", "monroe", "2020", "monr_dsm_2020.zip"),
                "dtm_imageserver": "IL_Monroe_DTM_2020",
                "dsm_imageserver": "IL_Monroe_DSM_2020",
                "dtm_size_gb": 23.9,
                "dsm_size_gb": 25.1,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "monr_dtm_2012.zip",
                "dsm_zip": "monr_dsm_2012.zip",
                "dtm_url": _url("district8", "monroe", "2012", "monr_dtm_2012.zip"),
                "dsm_url": _url("district8", "monroe", "2012", "monr_dsm_2012.zip"),
                "dtm_imageserver": "IL_Monroe_DTM_2012",
                "dsm_imageserver": "IL_Monroe_DSM_2012",
                "dtm_size_gb": 5.6,
                "dsm_size_gb": 5.8,
            },
        ],
    },

    # --- Montgomery ---
    "montgomery": {
        "name": "Montgomery",
        "fips": "17135",
        "district": "district6",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "mont_dtm_2017.zip",
                "dsm_zip": "mont_dsm_2017.zip",
                "dtm_url": _url("district6", "montgomery", "2017", "mont_dtm_2017.zip"),
                "dsm_url": _url("district6", "montgomery", "2017", "mont_dsm_2017.zip"),
                "dtm_imageserver": "IL_Montgomery_DTM_2017",
                "dsm_imageserver": "IL_Montgomery_DSM_2017",
                "dtm_size_gb": 23.5,
                "dsm_size_gb": 24.1,
            },
        ],
    },

    # --- Morgan ---
    "morgan": {
        "name": "Morgan",
        "fips": "17137",
        "district": "district6",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "morg_dtm_2017.zip",
                "dsm_zip": "morg_dsm_2017.zip",
                "dtm_url": _url("district6", "morgan", "2017", "morg_dtm_2017.zip"),
                "dsm_url": _url("district6", "morgan", "2017", "morg_dsm_2017.zip"),
                "dtm_imageserver": "IL_Morgan_DTM_2017",
                "dsm_imageserver": "IL_Morgan_DSM_2017",
                "dtm_size_gb": 17.1,
                "dsm_size_gb": 17.7,
            },
        ],
    },

    # --- Moultrie ---
    "moultrie": {
        "name": "Moultrie",
        "fips": "17139",
        "district": "district7",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "moul_dtm_2021.zip",
                "dsm_zip": "moul_dsm_2021.zip",
                "dtm_url": _url("district7", "moultrie", "2021", "moul_dtm_2021.zip"),
                "dsm_url": _url("district7", "moultrie", "2021", "moul_dsm_2021.zip"),
                "dtm_imageserver": "IL_Moultrie_DTM_2021",
                "dsm_imageserver": "IL_Moultrie_DSM_2021",
                "dtm_size_gb": 18.9,
                "dsm_size_gb": 19.1,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "moul_dtm_2011.zip",
                "dsm_zip": "moul_dsm_2011.zip",
                "dtm_url": _url("district7", "moultrie", "2011", "moul_dtm_2011.zip"),
                "dsm_url": _url("district7", "moultrie", "2011", "moul_dsm_2011.zip"),
                "dtm_imageserver": "IL_Moultrie_DTM_2011",
                "dsm_imageserver": "IL_Moultrie_DSM_2011",
                "dtm_size_gb": 2.9,
                "dsm_size_gb": 3.0,
            },
        ],
    },

    # --- Ogle ---
    "ogle": {
        "name": "Ogle",
        "fips": "17141",
        "district": "district2",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "ogle_dtm_2020.zip",
                "dsm_zip": "ogle_dsm_2020.zip",
                "dtm_url": _url("district2", "ogle", "2020", "ogle_dtm_2020.zip"),
                "dsm_url": _url("district2", "ogle", "2020", "ogle_dsm_2020.zip"),
                "dtm_imageserver": "IL_Ogle_DTM_2020",
                "dsm_imageserver": "IL_Ogle_DSM_2020",
                "dtm_size_gb": 24.2,
                "dsm_size_gb": 25.2,
            },
            {
                "year": "2009",
                "dtm_type": "dtm",
                "dtm_zip": "ogle_dtm_2009.zip",
                "dsm_zip": "ogle_dsm_2009.zip",
                "dtm_url": _url("district2", "ogle", "2009", "ogle_dtm_2009.zip"),
                "dsm_url": _url("district2", "ogle", "2009", "ogle_dsm_2009.zip"),
                "dtm_imageserver": "IL_Ogle_DTM_2009",
                "dsm_imageserver": "IL_Ogle_DSM_2009",
                "dtm_size_gb": 7.5,
                "dsm_size_gb": 7.7,
            },
        ],
    },

    # --- Peoria ---
    "peoria": {
        "name": "Peoria",
        "fips": "17143",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "peoria_dtm_2022.zip",
                "dsm_zip": "peoria_dsm_2022.zip",
                "dtm_url": _url("district4", "peoria", "2022", "peoria_dtm_2022.zip"),
                "dsm_url": _url("district4", "peoria", "2022", "peoria_dsm_2022.zip"),
                "dtm_imageserver": "IL_Peoria_DTM_2022",
                "dsm_imageserver": "IL_Peoria_DSM_2022",
                "dtm_size_gb": 41.6,
                "dsm_size_gb": 36.3,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "peor_dtm_2012.zip",
                "dsm_zip": "peor_dsm_2012.zip",
                "dtm_url": _url("district4", "peoria", "2012", "peor_dtm_2012.zip"),
                "dsm_url": _url("district4", "peoria", "2012", "peor_dsm_2012.zip"),
                "dtm_imageserver": "IL_Peoria_DTM_2012",
                "dsm_imageserver": "IL_Peoria_DSM_2012",
                "dtm_size_gb": 6.8,
                "dsm_size_gb": 7.3,
            },
            {
                "year": "2008",
                "dtm_type": "dem",
                "dtm_zip": "peor_dem_2008.zip",
                "dsm_zip": "peor_dsm_2008.zip",
                "dtm_url": _url("district4", "peoria", "2008", "peor_dem_2008.zip"),
                "dsm_url": _url("district4", "peoria", "2008", "peor_dsm_2008.zip"),
                "dtm_imageserver": "IL_Peoria_DEM_2008",
                "dsm_imageserver": "IL_Peoria_DSM_2008",
                "dtm_size_gb": 3.9,
                "dsm_size_gb": 3.8,
            },
        ],
    },

    # --- Perry ---
    "perry": {
        "name": "Perry",
        "fips": "17145",
        "district": "district9",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "perr_dtm_2021.zip",
                "dsm_zip": "perr_dsm_2021.zip",
                "dtm_url": _url("district9", "perry", "2021", "perr_dtm_2021.zip"),
                "dsm_url": _url("district9", "perry", "2021", "perr_dsm_2021.zip"),
                "dtm_imageserver": "IL_Perry_DTM_2021",
                "dsm_imageserver": "IL_Perry_DSM_2021",
                "dtm_size_gb": 25.8,
                "dsm_size_gb": 27.7,
            },
            {
                "year": "2014",
                "dtm_type": "dtm",
                "dtm_zip": "perr_dtm_2014.zip",
                "dsm_zip": "perr_dsm_2014.zip",
                "dtm_url": _url("district9", "perry", "2014", "perr_dtm_2014.zip"),
                "dsm_url": _url("district9", "perry", "2014", "perr_dsm_2014.zip"),
                "dtm_imageserver": "IL_Perry_DTM_2014",
                "dsm_imageserver": "IL_Perry_DSM_2014",
                "dtm_size_gb": 8.2,
                "dsm_size_gb": 7.9,
            },
        ],
    },

    # --- Piatt ---
    "piatt": {
        "name": "Piatt",
        "fips": "17147",
        "district": "district5",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "piatt-dtm-2022.zip",
                "dsm_zip": "piatt-dsm-2022.zip",
                "dtm_url": _url("district5", "piatt", "2022", "piatt-dtm-2022.zip"),
                "dsm_url": _url("district5", "piatt", "2022", "piatt-dsm-2022.zip"),
                "dtm_imageserver": "IL_Piatt_DTM_2022",
                "dsm_imageserver": "IL_Piatt_DSM_2022",
                "dtm_size_gb": 21.6,
                "dsm_size_gb": 22.1,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "piat_dtm_2012.zip",
                "dsm_zip": "piat_dsm_2012.zip",
                "dtm_url": _url("district5", "piatt", "2012", "piat_dtm_2012.zip"),
                "dsm_url": _url("district5", "piatt", "2012", "piat_dsm_2012.zip"),
                "dtm_imageserver": "IL_Piatt_DTM_2012",
                "dsm_imageserver": "IL_Piatt_DSM_2012",
                "dtm_size_gb": 8.8,
                "dsm_size_gb": 9.0,
            },
            {
                "year": "2011",
                "dtm_type": "dem",
                "dtm_zip": "piat_dem_2011.zip",
                "dsm_zip": "piat_dsm_2011.zip",
                "dtm_url": _url("district5", "piatt", "2011", "piat_dem_2011.zip"),
                "dsm_url": _url("district5", "piatt", "2011", "piat_dsm_2011.zip"),
                "dtm_imageserver": "IL_Piatt_DEM_2011",
                "dsm_imageserver": "IL_Piatt_DSM_2011",
                "dtm_size_gb": 16.5,
                "dsm_size_gb": 17.9,
            },
        ],
    },

    # --- Pike ---
    "pike": {
        "name": "Pike",
        "fips": "17149",
        "district": "district6",
        "collections": [
            {
                "year": "2023",
                "dtm_type": "dtm",
                "dtm_zip": "pike_dtm_2023.zip",
                "dsm_zip": "pike_dsm_2023.zip",
                "dtm_url": _url("district6", "pike", "2023", "pike_dtm_2023.zip"),
                "dsm_url": _url("district6", "pike", "2023", "pike_dsm_2023.zip"),
                "dtm_imageserver": "IL_Pike_DTM_2023",
                "dsm_imageserver": "IL_Pike_DSM_2023",
                "dtm_size_gb": 97.7,
                "dsm_size_gb": 101.0,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "pike_dtm_2015.zip",
                "dsm_zip": "pike_dsm_2015.zip",
                "dtm_url": _url("district6", "pike", "2015", "pike_dtm_2015.zip"),
                "dsm_url": _url("district6", "pike", "2015", "pike_dsm_2015.zip"),
                "dtm_imageserver": "IL_Pike_DTM_2015",
                "dsm_imageserver": "IL_Pike_DSM_2015",
                "dtm_size_gb": 45.5,
                "dsm_size_gb": 106.7,
            },
        ],
    },

    # --- Pope ---
    "pope": {
        "name": "Pope",
        "fips": "17151",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "pope_dtm_2020.zip",
                "dsm_zip": "pope_dsm_2020.zip",
                "dtm_url": _url("district9", "pope", "2020", "pope_dtm_2020.zip"),
                "dsm_url": _url("district9", "pope", "2020", "pope_dsm_2020.zip"),
                "dtm_imageserver": "IL_Pope_DTM_2020",
                "dsm_imageserver": "IL_Pope_DSM_2020",
                "dtm_size_gb": 23.3,
                "dsm_size_gb": 38.8,
            },
            {
                "year": "2014",
                "dtm_type": "dtm",
                "dtm_zip": "pope_dtm_2014.zip",
                "dsm_zip": "pope_dsm_2014.zip",
                "dtm_url": _url("district9", "pope", "2014", "pope_dtm_2014.zip"),
                "dsm_url": _url("district9", "pope", "2014", "pope_dsm_2014.zip"),
                "dtm_imageserver": "IL_Pope_DTM_2014",
                "dsm_imageserver": "IL_Pope_DSM_2014",
                "dtm_size_gb": 10.5,
                "dsm_size_gb": 9.7,
            },
        ],
    },

    # --- Pulaski ---
    "pulaski": {
        "name": "Pulaski",
        "fips": "17153",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "pula_dtm_2020.zip",
                "dsm_zip": "pula_dsm_2020.zip",
                "dtm_url": _url("district9", "pulaski", "2020", "pula_dtm_2020.zip"),
                "dsm_url": _url("district9", "pulaski", "2020", "pula_dsm_2020.zip"),
                "dtm_imageserver": "IL_Pulaski_DTM_2020",
                "dsm_imageserver": "IL_Pulaski_DSM_2020",
                "dtm_size_gb": 12.3,
                "dsm_size_gb": 13.4,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "pula_dtm_2012.zip",
                "dsm_zip": "pula_dsm_2012.zip",
                "dtm_url": _url("district9", "pulaski", "2012", "pula_dtm_2012.zip"),
                "dsm_url": _url("district9", "pulaski", "2012", "pula_dsm_2012.zip"),
                "dtm_imageserver": "IL_Pulaski_DTM_2012",
                "dsm_imageserver": "IL_Pulaski_DSM_2012",
                "dtm_size_gb": 2.2,
                "dsm_size_gb": 2.3,
            },
        ],
    },

    # --- Putnam ---
    "putnam": {
        "name": "Putnam",
        "fips": "17155",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "putnam_dtm_2022.zip",
                "dsm_zip": "putnam_dsm_2022.zip",
                "dtm_url": _url("district4", "putnam", "2022", "putnam_dtm_2022.zip"),
                "dsm_url": _url("district4", "putnam", "2022", "putnam_dsm_2022.zip"),
                "dtm_imageserver": "IL_Putnam_DTM_2022",
                "dsm_imageserver": "IL_Putnam_DSM_2022",
                "dtm_size_gb": 16.4,
                "dsm_size_gb": 10.6,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "putn_dtm_2012.zip",
                "dsm_zip": "putn_dsm_2012.zip",
                "dtm_url": _url("district4", "putnam", "2012", "putn_dtm_2012.zip"),
                "dsm_url": _url("district4", "putnam", "2012", "putn_dsm_2012.zip"),
                "dtm_imageserver": "IL_Putnam_DTM_2012",
                "dsm_imageserver": "IL_Putnam_DSM_2012",
                "dtm_size_gb": 2.0,
                "dsm_size_gb": 2.2,
            },
        ],
        "bounds": (-89.48, 41.10, -89.15, 41.32),
    },

    # --- Randolph ---
    "randolph": {
        "name": "Randolph",
        "fips": "17157",
        "district": "district8",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "rand_dtm_2020.zip",
                "dsm_zip": "rand_dsm_2020.zip",
                "dtm_url": _url("district8", "randolph", "2020", "rand_dtm_2020.zip"),
                "dsm_url": _url("district8", "randolph", "2020", "rand_dsm_2020.zip"),
                "dtm_imageserver": "IL_Randolph_DTM_2020",
                "dsm_imageserver": "IL_Randolph_DSM_2020",
                "dtm_size_gb": 35.3,
                "dsm_size_gb": 37.2,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "rand_dtm_2012.zip",
                "dsm_zip": "rand_dsm_2012.zip",
                "dtm_url": _url("district8", "randolph", "2012", "rand_dtm_2012.zip"),
                "dsm_url": _url("district8", "randolph", "2012", "rand_dsm_2012.zip"),
                "dtm_imageserver": "IL_Randolph_DTM_2012",
                "dsm_imageserver": "IL_Randolph_DSM_2012",
                "dtm_size_gb": 8.4,
                "dsm_size_gb": 8.8,
            },
        ],
    },

    # --- Richland ---
    "richland": {
        "name": "Richland",
        "fips": "17159",
        "district": "district7",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "rich_dtm_2021.zip",
                "dsm_zip": "rich_dsm_2021.zip",
                "dtm_url": _url("district7", "richland", "2021", "rich_dtm_2021.zip"),
                "dsm_url": _url("district7", "richland", "2021", "rich_dsm_2021.zip"),
                "dtm_imageserver": "IL_Richland_DTM_2021",
                "dsm_imageserver": "IL_Richland_DSM_2021",
                "dtm_size_gb": 21.2,
                "dsm_size_gb": 21.5,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "rich_dtm_2011.zip",
                "dsm_zip": "rich_dsm_2011.zip",
                "dtm_url": _url("district7", "richland", "2011", "rich_dtm_2011.zip"),
                "dsm_url": _url("district7", "richland", "2011", "rich_dsm_2011.zip"),
                "dtm_imageserver": "IL_Richland_DTM_2011",
                "dsm_imageserver": "IL_Richland_DSM_2011",
                "dtm_size_gb": 4.9,
                "dsm_size_gb": 5.1,
            },
        ],
    },

    # --- Rock Island ---
    "rockisland": {
        "name": "Rock Island",
        "fips": "17161",
        "district": "district2",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "rock_dtm_2020.zip",
                "dsm_zip": "rock_dsm_2020.zip",
                "dtm_url": _url("district2", "rockisland", "2020", "rock_dtm_2020.zip"),
                "dsm_url": _url("district2", "rockisland", "2020", "rock_dsm_2020.zip"),
                "dtm_imageserver": "IL_Rock_Island_DTM_2020",
                "dsm_imageserver": "IL_Rock_Island_DSM_2020",
                "dtm_size_gb": 14.6,
                "dsm_size_gb": 16.3,
            },
            {
                "year": "2009",
                "dtm_type": "dtm",
                "dtm_zip": "rock_dtm_2009.zip",
                "dsm_zip": "rock_dsm_2009.zip",
                "dtm_url": _url("district2", "rockisland", "2009", "rock_dtm_2009.zip"),
                "dsm_url": _url("district2", "rockisland", "2009", "rock_dsm_2009.zip"),
                "dtm_imageserver": "IL_Rock_Island_DTM_2009",
                "dsm_imageserver": "IL_Rock_Island_DSM_2009",
                "dtm_size_gb": 4.3,
                "dsm_size_gb": 4.7,
            },
        ],
    },

    # --- Saline ---
    "saline": {
        "name": "Saline",
        "fips": "17165",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "sali_dtm_2020.zip",
                "dsm_zip": "sali_dsm_2020.zip",
                "dtm_url": _url("district9", "saline", "2020", "sali_dtm_2020.zip"),
                "dsm_url": _url("district9", "saline", "2020", "sali_dsm_2020.zip"),
                "dtm_imageserver": "IL_Saline_DTM_2020",
                "dsm_imageserver": "IL_Saline_DSM_2020",
                "dtm_size_gb": 23.8,
                "dsm_size_gb": 25.0,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "sali_dtm_2011.zip",
                "dsm_zip": "sali_dsm_2011.zip",
                "dtm_url": _url("district9", "saline", "2011", "sali_dtm_2011.zip"),
                "dsm_url": _url("district9", "saline", "2011", "sali_dsm_2011.zip"),
                "dtm_imageserver": "IL_Saline_DTM_2011",
                "dsm_imageserver": "IL_Saline_DSM_2011",
                "dtm_size_gb": 2.6,
                "dsm_size_gb": 2.8,
            },
        ],
    },

    # --- Sangamon ---
    "sangamon": {
        "name": "Sangamon",
        "fips": "17167",
        "district": "district6",
        "collections": [
            {
                "year": "2018",
                "dtm_type": "dtm",
                "dtm_zip": "sang_dtm_2018.zip",
                "dsm_zip": "sang_dsm_2018.zip",
                "dtm_url": _url("district6", "sangamon", "2018", "sang_dtm_2018.zip"),
                "dsm_url": _url("district6", "sangamon", "2018", "sang_dsm_2018.zip"),
                "dtm_imageserver": "IL_Sangamon_DTM_2018",
                "dsm_imageserver": "IL_Sangamon_DSM_2018",
                "dtm_size_gb": 25.5,
                "dsm_size_gb": 26.8,
            },
        ],
    },

    # --- Schuyler ---
    "schuyler": {
        "name": "Schuyler",
        "fips": "17169",
        "district": "district6",
        "collections": [
            {
                "year": "2017",
                "dtm_type": "dtm",
                "dtm_zip": "schu_dtm_2017.zip",
                "dsm_zip": "schu_dsm_2017.zip",
                "dtm_url": _url("district6", "schuyler", "2017", "schu_dtm_2017.zip"),
                "dsm_url": _url("district6", "schuyler", "2017", "schu_dsm_2017.zip"),
                "dtm_imageserver": "IL_Schuyler_DTM_2017",
                "dsm_imageserver": "IL_Schuyler_DSM_2017",
                "dtm_size_gb": 14.3,
                "dsm_size_gb": 15.0,
            },
        ],
    },

    # --- Scott ---
    "scott": {
        "name": "Scott",
        "fips": "17171",
        "district": "district6",
        "collections": [
            {
                "year": "2023",
                "dtm_type": "dtm",
                "dtm_zip": "scott_dtm_2023.zip",
                "dsm_zip": "scott_dsm_2023.zip",
                "dtm_url": _url("district6", "scott", "2023", "scott_dtm_2023.zip"),
                "dsm_url": _url("district6", "scott", "2023", "scott_dsm_2023.zip"),
                "dtm_imageserver": "IL_Scott_DTM_2023",
                "dsm_imageserver": "IL_Scott_DSM_2023",
                "dtm_size_gb": 31.6,
                "dsm_size_gb": 32.5,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "scot_dtm_2015.zip",
                "dsm_zip": "scot_dsm_2015.zip",
                "dtm_url": _url("district6", "scott", "2015", "scot_dtm_2015.zip"),
                "dsm_url": _url("district6", "scott", "2015", "scot_dsm_2015.zip"),
                "dtm_imageserver": "IL_Scott_DTM_2015",
                "dsm_imageserver": "IL_Scott_DSM_2015",
                "dtm_size_gb": 30.5,
                "dsm_size_gb": 30.9,
            },
        ],
    },

    # --- Shelby ---
    "shelby": {
        "name": "Shelby",
        "fips": "17173",
        "district": "district7",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "shel_dtm_2021.zip",
                "dsm_zip": "shel_dsm_2021.zip",
                "dtm_url": _url("district7", "shelby", "2021", "shel_dtm_2021.zip"),
                "dsm_url": _url("district7", "shelby", "2021", "shel_dsm_2021.zip"),
                "dtm_imageserver": "IL_Shelby_DTM_2021",
                "dsm_imageserver": "IL_Shelby_DSM_2021",
                "dtm_size_gb": 42.4,
                "dsm_size_gb": 43.3,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "shel_dtm_2011.zip",
                "dsm_zip": "shel_dsm_2011.zip",
                "dtm_url": _url("district7", "shelby", "2011", "shel_dtm_2011.zip"),
                "dsm_url": _url("district7", "shelby", "2011", "shel_dsm_2011.zip"),
                "dtm_imageserver": "IL_Shelby_DTM_2011",
                "dsm_imageserver": "IL_Shelby_DSM_2011",
                "dtm_size_gb": 8.2,
                "dsm_size_gb": 8.5,
            },
        ],
    },

    # --- St. Clair ---
    "stclair": {
        "name": "St. Clair",
        "fips": "17163",
        "district": "district8",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "stcl_dtm_2020.zip",
                "dsm_zip": "stcl_dsm_2020.zip",
                "dtm_url": _url("district8", "stclair", "2020", "stcl_dtm_2020.zip"),
                "dsm_url": _url("district8", "stclair", "2020", "stcl_dsm_2020.zip"),
                "dtm_imageserver": "IL_St_Clair_DTM_2020",
                "dsm_imageserver": "IL_St_Clair_DSM_2020",
                "dtm_size_gb": 38.7,
                "dsm_size_gb": 41.0,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "stcl_dtm_2012.zip",
                "dsm_zip": "stcl_dsm_2012.zip",
                "dtm_url": _url("district8", "stclair", "2012", "stcl_dtm_2012.zip"),
                "dsm_url": _url("district8", "stclair", "2012", "stcl_dsm_2012.zip"),
                "dtm_imageserver": "IL_St_Clair_DTM_2012",
                "dsm_imageserver": "IL_St_Clair_DSM_2012",
                "dtm_size_gb": 9.4,
                "dsm_size_gb": 9.8,
            },
        ],
    },

    # --- Stark ---
    "stark": {
        "name": "Stark",
        "fips": "17175",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "stark_dtm_2022.zip",
                "dsm_zip": "stark_dsm_2022.zip",
                "dtm_url": _url("district4", "stark", "2022", "stark_dtm_2022.zip"),
                "dsm_url": _url("district4", "stark", "2022", "stark_dsm_2022.zip"),
                "dtm_imageserver": "IL_Stark_DTM_2022",
                "dsm_imageserver": "IL_Stark_DSM_2022",
                "dtm_size_gb": 15.4,
                "dsm_size_gb": 15.6,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "star_dtm_2012.zip",
                "dsm_zip": "star_dsm_2012.zip",
                "dtm_url": _url("district4", "stark", "2012", "star_dtm_2012.zip"),
                "dsm_url": _url("district4", "stark", "2012", "star_dsm_2012.zip"),
                "dtm_imageserver": "IL_Stark_DTM_2012",
                "dsm_imageserver": "IL_Stark_DSM_2012",
                "dtm_size_gb": 4.2,
                "dsm_size_gb": 4.3,
            },
        ],
    },

    # --- Stephenson ---
    "stephenson": {
        "name": "Stephenson",
        "fips": "17177",
        "district": "district2",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "step_dtm_2020.zip",
                "dsm_zip": "step_dsm_2020.zip",
                "dtm_url": _url("district2", "stephenson", "2020", "step_dtm_2020.zip"),
                "dsm_url": _url("district2", "stephenson", "2020", "step_dsm_2020.zip"),
                "dtm_imageserver": "IL_Stephenson_DTM_2020",
                "dsm_imageserver": "IL_Stephenson_DSM_2020",
                "dtm_size_gb": 18.6,
                "dsm_size_gb": 20.4,
            },
            {
                "year": "2009",
                "dtm_type": "dtm",
                "dtm_zip": "step_dtm_2009.zip",
                "dsm_zip": "step_dsm_2009.zip",
                "dtm_url": _url("district2", "stephenson", "2009", "step_dtm_2009.zip"),
                "dsm_url": _url("district2", "stephenson", "2009", "step_dsm_2009.zip"),
                "dtm_imageserver": "IL_Stepenson_DTM_2009",
                "dsm_imageserver": "IL_Stephenson_DSM_2009",
                "dtm_size_gb": 6.6,
                "dsm_size_gb": 6.2,
            },
        ],
    },

    # --- Tazewell ---
    "tazewell": {
        "name": "Tazewell",
        "fips": "17179",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "taze_DTM_2022.zip",
                "dsm_zip": "taze_DSM_2022.zip",
                "dtm_url": _url("district4", "tazewell", "2022", "taze_DTM_2022.zip"),
                "dsm_url": _url("district4", "tazewell", "2022", "taze_DSM_2022.zip"),
                "dtm_imageserver": "IL_Tazewell_DTM_2022",
                "dsm_imageserver": "IL_Tazewell_DSM_2022",
                "dtm_size_gb": 35.7,
                "dsm_size_gb": 38.1,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "taze_dtm_2012.zip",
                "dsm_zip": "taze_dsm_2012.zip",
                "dtm_url": _url("district4", "tazewell", "2012", "taze_dtm_2012.zip"),
                "dsm_url": _url("district4", "tazewell", "2012", "taze_dsm_2012.zip"),
                "dtm_imageserver": "IL_Tazewell_DTM_2012",
                "dsm_imageserver": "IL_Tazewell_DSM_2012",
                "dtm_size_gb": 7.0,
                "dsm_size_gb": 7.3,
            },
        ],
    },

    # --- Union ---
    "union": {
        "name": "Union",
        "fips": "17181",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "unio_dtm_2020.zip",
                "dsm_zip": "unio_dsm_2020.zip",
                "dtm_url": _url("district9", "union", "2020", "unio_dtm_2020.zip"),
                "dsm_url": _url("district9", "union", "2020", "unio_dsm_2020.zip"),
                "dtm_imageserver": "IL_Union_DTM_2020",
                "dsm_imageserver": "IL_Union_DSM_2020",
                "dtm_size_gb": 26.5,
                "dsm_size_gb": 27.9,
            },
            {
                "year": "2011",
                "dtm_type": "dem",
                "dtm_zip": "unio_dem_2011.zip",
                "dsm_zip": "unio_dsm_2011.zip",
                "dtm_url": _url("district9", "union", "2011", "unio_dem_2011.zip"),
                "dsm_url": _url("district9", "union", "2011", "unio_dsm_2011.zip"),
                "dtm_imageserver": "IL_Union_DEM_2011",
                "dsm_imageserver": "IL_Union_DSM_2011",
                "dtm_size_gb": 2.8,
                "dsm_size_gb": 2.9,
            },
        ],
    },

    # --- Vermilion ---
    "vermilion": {
        "name": "Vermilion",
        "fips": "17183",
        "district": "district5",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "verm_dtm_2021.zip",
                "dsm_zip": "verm_dsm_2021.zip",
                "dtm_url": _url("district5", "vermilion", "2021", "verm_dtm_2021.zip"),
                "dsm_url": _url("district5", "vermilion", "2021", "verm_dsm_2021.zip"),
                "dtm_imageserver": "IL_Vermilion_DTM_2021",
                "dsm_imageserver": "IL_Vermilion_DSM_2021",
                "dtm_size_gb": 48.1,
                "dsm_size_gb": 49.2,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "verm_dtm_2012.zip",
                "dsm_zip": "verm_dsm_2012.zip",
                "dtm_url": _url("district5", "vermilion", "2012", "verm_dtm_2012.zip"),
                "dsm_url": _url("district5", "vermilion", "2012", "verm_dsm_2012.zip"),
                "dtm_imageserver": "IL_Vermilion_DTM_2012",
                "dsm_imageserver": "IL_Vermilion_DSM_2012",
                "dtm_size_gb": 17.9,
                "dsm_size_gb": 18.6,
            },
        ],
    },

    # --- Wabash ---
    "wabash": {
        "name": "Wabash",
        "fips": "17185",
        "district": "district7",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "waba_dtm_2020.zip",
                "dsm_zip": "waba_dsm_2020.zip",
                "dtm_url": _url("district7", "wabash", "2020", "waba_dtm_2020.zip"),
                "dsm_url": _url("district7", "wabash", "2020", "waba_dsm_2020.zip"),
                "dtm_imageserver": "IL_Wabash_DTM_2020",
                "dsm_imageserver": "IL_Wabash_DSM_2020",
                "dtm_size_gb": 14.7,
                "dsm_size_gb": 15.4,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "waba_dtm_2011.zip",
                "dsm_zip": "waba_dsm_2011.zip",
                "dtm_url": _url("district7", "wabash", "2011", "waba_dtm_2011.zip"),
                "dsm_url": _url("district7", "wabash", "2011", "waba_dsm_2011.zip"),
                "dtm_imageserver": "IL_Wabash_DTM_2011",
                "dsm_imageserver": "IL_Wabash_DSM_2011",
                "dtm_size_gb": 2.8,
                "dsm_size_gb": 3.0,
            },
        ],
    },

    # --- Warren ---
    "warren": {
        "name": "Warren",
        "fips": "17187",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "warren_DTM_2022.zip",
                "dsm_zip": "warren_DSM_2022.zip",
                "dtm_url": _url("district4", "warren", "2022", "warren_DTM_2022.zip"),
                "dsm_url": _url("district4", "warren", "2022", "warren_DSM_2022.zip"),
                "dtm_imageserver": "IL_Warren_DTM_2022",
                "dsm_imageserver": "IL_Warren_DSM_2022",
                "dtm_size_gb": 28.4,
                "dsm_size_gb": 28.9,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "warr_dtm_2012.zip",
                "dsm_zip": "warr_dsm_2012.zip",
                "dtm_url": _url("district4", "warren", "2012", "warr_dtm_2012.zip"),
                "dsm_url": _url("district4", "warren", "2012", "warr_dsm_2012.zip"),
                "dtm_imageserver": "IL_Warren_DTM_2012",
                "dsm_imageserver": "IL_Warren_DSM_2012",
                "dtm_size_gb": 7.4,
                "dsm_size_gb": 7.3,
            },
        ],
    },

    # --- Washington ---
    "washington": {
        "name": "Washington",
        "fips": "17189",
        "district": "district8",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "wash_dtm_2021.zip",
                "dsm_zip": "wash_dsm_2021.zip",
                "dtm_url": _url("district8", "washington", "2021", "wash_dtm_2021.zip"),
                "dsm_url": _url("district8", "washington", "2021", "wash_dsm_2021.zip"),
                "dtm_imageserver": "IL_Washington_DTM_2021",
                "dsm_imageserver": "IL_Washington_DSM_2021",
                "dtm_size_gb": 32.5,
                "dsm_size_gb": 33.7,
            },
            {
                "year": "2015",
                "dtm_type": "dtm",
                "dtm_zip": "wash_dtm_2015.zip",
                "dsm_zip": "wash_dsm_2015.zip",
                "dtm_url": _url("district8", "washington", "2015", "wash_dtm_2015.zip"),
                "dsm_url": _url("district8", "washington", "2015", "wash_dsm_2015.zip"),
                "dtm_imageserver": "IL_Washington_DTM_2015",
                "dsm_imageserver": "IL_Washington_DSM_2015",
                "dtm_size_gb": 8.7,
                "dsm_size_gb": 9.1,
            },
        ],
    },

    # --- Wayne ---
    "wayne": {
        "name": "Wayne",
        "fips": "17191",
        "district": "district7",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "wayn_dtm_2020.zip",
                "dsm_zip": "wayn_dsm_2020.zip",
                "dtm_url": _url("district7", "wayne", "2020", "wayn_dtm_2020.zip"),
                "dsm_url": _url("district7", "wayne", "2020", "wayn_dsm_2020.zip"),
                "dtm_imageserver": "IL_Wayne_DTM_2020",
                "dsm_imageserver": "IL_Wayne_DSM_2020",
                "dtm_size_gb": 41.8,
                "dsm_size_gb": 43.4,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "wayn_dtm_2011.zip",
                "dsm_zip": "wayn_dsm_2011.zip",
                "dtm_url": _url("district7", "wayne", "2011", "wayn_dtm_2011.zip"),
                "dsm_url": _url("district7", "wayne", "2011", "wayn_dsm_2011.zip"),
                "dtm_imageserver": "IL_Wayne_DTM_2011",
                "dsm_imageserver": "IL_Wayne_DSM_2011",
                "dtm_size_gb": 8.3,
                "dsm_size_gb": 8.5,
            },
        ],
    },

    # --- White ---
    "white": {
        "name": "White",
        "fips": "17193",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "whit_dtm_2020.zip",
                "dsm_zip": "whit_dsm_2020.zip",
                "dtm_url": _url("district9", "white", "2020", "whit_dtm_2020.zip"),
                "dsm_url": _url("district9", "white", "2020", "whit_dsm_2020.zip"),
                "dtm_imageserver": "IL_White_DTM_2020",
                "dsm_imageserver": "IL_White_DSM_2020",
                "dtm_size_gb": 29.9,
                "dsm_size_gb": 30.9,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "whit_dtm_2011.zip",
                "dsm_zip": "whit_dsm_2011.zip",
                "dtm_url": _url("district9", "white", "2011", "whit_dtm_2011.zip"),
                "dsm_url": _url("district9", "white", "2011", "whit_dsm_2011.zip"),
                "dtm_imageserver": "IL_White_DTM_2011",
                "dsm_imageserver": "IL_White_DSM_2011",
                "dtm_size_gb": 3.6,
                "dsm_size_gb": 3.4,
            },
        ],
    },

    # --- Whiteside ---
    # Note: prefix is 'whie' (not 'whit') - confirmed from clearinghouse HTML
    "whiteside": {
        "name": "Whiteside",
        "fips": "17195",
        "district": "district2",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "whie_dtm_2020.zip",
                "dsm_zip": "whie_dsm_2020.zip",
                "dtm_url": _url("district2", "whiteside", "2020", "whie_dtm_2020.zip"),
                "dsm_url": _url("district2", "whiteside", "2020", "whie_dsm_2020.zip"),
                "dtm_imageserver": "IL_Whiteside_DTM_2020",
                "dsm_imageserver": None,
                "dtm_size_gb": 22.0,
                "dsm_size_gb": 23.0,
            },
            {
                "year": "2009",
                "dtm_type": "dtm",
                "dtm_zip": "whie_dtm_2009.zip",
                "dsm_zip": "whie_dsm_2009.zip",
                "dtm_url": _url("district2", "whiteside", "2009", "whie_dtm_2009.zip"),
                "dsm_url": _url("district2", "whiteside", "2009", "whie_dsm_2009.zip"),
                "dtm_imageserver": "IL_Whiteside_DTM_2009",
                "dsm_imageserver": "IL_Whiteside_DSM_2009",
                "dtm_size_gb": 6.6,
                "dsm_size_gb": 6.9,
            },
        ],
    },

    # --- Will ---
    "will": {
        "name": "Will",
        "fips": "17197",
        "district": "district1",
        "collections": [
            {
                "year": "2021",
                "dtm_type": "dtm",
                "dtm_zip": "will_dtm_2021.zip",
                "dsm_zip": "will_dsm_2021.zip",
                "dtm_url": _url("district1", "will", "2021", "will_dtm_2021.zip"),
                "dsm_url": _url("district1", "will", "2021", "will_dsm_2021.zip"),
                "dtm_imageserver": "IL_Will_DTM_2021",
                "dsm_imageserver": None,
                "dtm_size_gb": 83.5,
                "dsm_size_gb": 110.5,
            },
            {
                "year": "2014",
                "dtm_type": "dtm",
                "dtm_zip": "will_dtm_2014.zip",
                "dsm_zip": "will_dsm_2014.zip",
                "dtm_url": _url("district1", "will", "2014", "will_dtm_2014.zip"),
                "dsm_url": _url("district1", "will", "2014", "will_dsm_2014.zip"),
                "dtm_imageserver": "IL_Will_DTM_2014",
                "dsm_imageserver": "IL_Will_DSM_2014",
                "dtm_size_gb": 28.7,
                "dsm_size_gb": 31.2,
            },
            {
                "year": "2004",
                "dtm_type": "dem",
                "dtm_zip": "will_dem_2004.zip",
                "dsm_zip": "will_dsm_2004.zip",
                "dtm_url": _url("district1", "will", "2004", "will_dem_2004.zip"),
                "dsm_url": _url("district1", "will", "2004", "will_dsm_2004.zip"),
                "dtm_imageserver": "IL_Will_DEM_2004",
                "dsm_imageserver": None,
                "dtm_size_gb": 7.2,
                "dsm_size_gb": 24.6,
            },
        ],
    },

    # --- Williamson ---
    # Note: prefix is 'wilm' (not 'wmsn') - confirmed from clearinghouse HTML
    "williamson": {
        "name": "Williamson",
        "fips": "17199",
        "district": "district9",
        "collections": [
            {
                "year": "2020",
                "dtm_type": "dtm",
                "dtm_zip": "wilm_dtm_2020.zip",
                "dsm_zip": "wilm_dsm_2020.zip",
                "dtm_url": _url("district9", "williamson", "2020", "wilm_dtm_2020.zip"),
                "dsm_url": _url("district9", "williamson", "2020", "wilm_dsm_2020.zip"),
                "dtm_imageserver": "IL_Williamson_DTM_2020",
                "dsm_imageserver": "IL_Williamson_DSM_2020",
                "dtm_size_gb": 26.6,
                "dsm_size_gb": 29.0,
            },
            {
                "year": "2011",
                "dtm_type": "dtm",
                "dtm_zip": "wilm_dtm_2011.zip",
                "dsm_zip": "wilm_dsm_2011.zip",
                "dtm_url": _url("district9", "williamson", "2011", "wilm_dtm_2011.zip"),
                "dsm_url": _url("district9", "williamson", "2011", "wilm_dsm_2011.zip"),
                "dtm_imageserver": "IL_Williamson_DTM_2011",
                "dsm_imageserver": "IL_Williamson_DSM_2011",
                "dtm_size_gb": 2.3,
                "dsm_size_gb": 3.3,
            },
        ],
    },

    # --- Winnebago ---
    "winnebago": {
        "name": "Winnebago",
        "fips": "17201",
        "district": "district2",
        "collections": [
            {
                "year": "2018",
                "dtm_type": "dtm",
                "dtm_zip": "winn_dtm_2018.zip",
                "dsm_zip": "winn_dsm_2018.zip",
                "dtm_url": _url("district2", "winnebago", "2018", "winn_dtm_2018.zip"),
                "dsm_url": _url("district2", "winnebago", "2018", "winn_dsm_2018.zip"),
                "dtm_imageserver": "IL_Winnebago_DTM_2018",
                "dsm_imageserver": "IL_Winnebago_DSM_2018",
                "dtm_size_gb": 29.6,
                "dsm_size_gb": 31.0,
            },
            {
                "year": "2007",
                "dtm_type": "dtm",
                "dtm_zip": "winn_dtm_2007.zip",
                "dsm_zip": "winn_dsm_2007.zip",
                "dtm_url": _url("district2", "winnebago", "2007", "winn_dtm_2007.zip"),
                "dsm_url": _url("district2", "winnebago", "2007", "winn_dsm_2007.zip"),
                "dtm_imageserver": None,
                "dsm_imageserver": None,
                "dtm_size_gb": 3.3,
                "dsm_size_gb": 3.2,
            },
        ],
    },

    # --- Woodford ---
    "woodford": {
        "name": "Woodford",
        "fips": "17203",
        "district": "district4",
        "collections": [
            {
                "year": "2022",
                "dtm_type": "dtm",
                "dtm_zip": "woodford_dtm_2022.zip",
                "dsm_zip": "woodford_dsm_2022.zip",
                "dtm_url": _url("district4", "woodford", "2022", "woodford_dtm_2022.zip"),
                "dsm_url": _url("district4", "woodford", "2022", "woodford_dsm_2022.zip"),
                "dtm_imageserver": "IL_Woodford_DTM_2022",
                "dsm_imageserver": "IL_Woodford_DSM_2022",
                "dtm_size_gb": 29.7,
                "dsm_size_gb": 30.9,
            },
            {
                "year": "2012",
                "dtm_type": "dtm",
                "dtm_zip": "wood_dtm_2012.zip",
                "dsm_zip": "wood_dsm_2012.zip",
                "dtm_url": _url("district4", "woodford", "2012", "wood_dtm_2012.zip"),
                "dsm_url": _url("district4", "woodford", "2012", "wood_dsm_2012.zip"),
                "dtm_imageserver": "IL_Woodford_DTM_2012",
                "dsm_imageserver": "IL_Woodford_DSM_2012",
                "dtm_size_gb": 5.8,
                "dsm_size_gb": 6.1,
            },
        ],
    },

}


def get_county(name: str) -> Optional[Dict]:
    """Get county info by name (case-insensitive).
    Returns the latest collection's data in a flattened dict for backward compatibility.
    Also includes 'collections' list for multi-year access.
    """
    key = name.lower().replace(" ", "").replace(".", "").replace("county", "")
    if key not in COUNTIES:
        return None

    county = COUNTIES[key].copy()
    county["id"] = key

    # Flatten the latest collection into top-level fields
    if county.get("collections"):
        coll = county["collections"][0]  # newest first
        county["year"] = coll["year"]
        county["dtm_zip"] = coll.get("dtm_zip")
        county["dsm_zip"] = coll.get("dsm_zip")
        county["dtm_type"] = coll.get("dtm_type", "dtm")
        county["dtm_url"] = coll.get("dtm_url")
        county["dsm_url"] = coll.get("dsm_url")
        county["dtm_imageserver"] = coll.get("dtm_imageserver")
        county["dsm_imageserver"] = coll.get("dsm_imageserver")
        county["dtm_size_gb"] = coll.get("dtm_size_gb")
        county["dsm_size_gb"] = coll.get("dsm_size_gb")
        if coll.get("dtm_imageserver"):
            county["dtm_imageserver_url"] = f"{IMAGESERVER_BASE}/{coll['dtm_imageserver']}/ImageServer"
        if coll.get("dsm_imageserver"):
            county["dsm_imageserver_url"] = f"{IMAGESERVER_BASE}/{coll['dsm_imageserver']}/ImageServer"

    return county


def list_all() -> List[Dict]:
    """List all counties with ILHMP data, sorted alphabetically by name."""
    result = []
    for key in sorted(COUNTIES.keys()):
        county = get_county(key)
        if county:
            result.append(county)
    return result


def get_county_years(name: str) -> List[str]:
    """Return all available collection years for a county, newest first."""
    key = name.lower().replace(" ", "").replace(".", "").replace("county", "")
    if key not in COUNTIES:
        return []
    return [c["year"] for c in COUNTIES[key].get("collections", [])]


def get_imageserver_url(county: str, dem_type: str = "dtm") -> Optional[str]:
    """Get the ArcGIS ImageServer URL for a county (latest collection)."""
    info = get_county(county)
    if not info:
        return None
    key = f"{dem_type.lower()}_imageserver_url"
    return info.get(key)


def get_zip_url(county: str, dem_type: str = "dtm") -> Optional[str]:
    """Get the clearinghouse ZIP download URL for a county (latest collection)."""
    info = get_county(county)
    if not info:
        return None
    key = f"{dem_type.lower()}_url"
    return info.get(key)


# County boundaries source
BOUNDARIES_URL = "https://clearinghouse.isgs.illinois.edu/sites/clearinghouse.isgs/files/data/IL_BNDY_County.zip"
BOUNDARIES_SOURCE = "https://clearinghouse.isgs.illinois.edu/data/reference/illinois-county-boundaries-polygons-and-lines"
