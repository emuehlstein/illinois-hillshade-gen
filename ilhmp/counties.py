"""
Illinois county catalog with ILHMP data availability.
Data sourced from: https://clearinghouse.isgs.illinois.edu/data/elevation/illinois-height-modernization-ilhmp

URL pattern:
  https://clearinghouse.isgs.illinois.edu/distribute/{district}/{county_key}/{year}/{prefix}_{dem_type}_{year}.zip

Districts: district1 (NE IL/Chicago), district2 (N IL), district3 (NW/W-central),
           district4 (Central), district5 (E-central), district6 (W IL),
           district7 (SW IL), district8 (S-central), district9 (S IL)

Note: URLs marked with # TODO have not been verified against the clearinghouse.
      prefix is the 4-char abbreviation used in ZIP filenames.
      dsm_zip=None means DSM data is not available for that county.
"""

from typing import Optional, Dict, List

# ISGS base URLs
CLEARINGHOUSE_BASE = "https://clearinghouse.isgs.illinois.edu/distribute"
IMAGESERVER_BASE = "https://data.isgs.illinois.edu/arcgis/rest/services/Elevation"

# Illinois counties with ILHMP LiDAR data (all 102 counties)
# Format: county_key -> {name, fips, district, year, dtm_zip, dsm_zip, imageserver names}
COUNTIES = {
    # --- District 1: NE Illinois / Chicago metro ---
    "boone": {
        "name": "Boone",
        "fips": "17007",
        "district": "district1",
        "dtm_zip": "boon_dtm_2017.zip",  # TODO: verify
        "dsm_zip": "boon_dsm_2017.zip",  # TODO: verify
        "dtm_imageserver": "IL_Boone_DTM_2017",
        "dsm_imageserver": "IL_Boone_DSM_2017",
        "year": "2017",
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
    "grundy": {
        "name": "Grundy",
        "fips": "17063",
        "district": "district1",
        "dtm_zip": "grun_dtm_2019.zip",  # TODO: verify
        "dsm_zip": "grun_dsm_2019.zip",  # TODO: verify
        "dtm_imageserver": "IL_Grundy_DTM_2019",
        "dsm_imageserver": "IL_Grundy_DSM_2019",
        "year": "2019",
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
    "kankakee": {
        "name": "Kankakee",
        "fips": "17091",
        "district": "district1",
        "dtm_zip": "kank_dtm_2019.zip",  # TODO: verify
        "dsm_zip": "kank_dsm_2019.zip",  # TODO: verify
        "dtm_imageserver": "IL_Kankakee_DTM_2019",
        "dsm_imageserver": "IL_Kankakee_DSM_2019",
        "year": "2019",
    },
    "kendall": {
        "name": "Kendall",
        "fips": "17093",
        "district": "district1",
        "dtm_zip": "kend_dtm_2019.zip",  # TODO: verify
        "dsm_zip": "kend_dsm_2019.zip",  # TODO: verify
        "dtm_imageserver": "IL_Kendall_DTM_2019",
        "dsm_imageserver": "IL_Kendall_DSM_2019",
        "year": "2019",
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
    "winnebago": {
        "name": "Winnebago",
        "fips": "17201",
        "district": "district1",
        "dtm_zip": "winn_dtm_2017.zip",  # TODO: verify
        "dsm_zip": "winn_dsm_2017.zip",  # TODO: verify
        "dtm_imageserver": "IL_Winnebago_DTM_2017",
        "dsm_imageserver": "IL_Winnebago_DSM_2017",
        "year": "2017",
    },

    # --- District 2: N Illinois ---
    "bureau": {
        "name": "Bureau",
        "fips": "17011",
        "district": "district2",
        "dtm_zip": "bure_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "bure_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Bureau_DTM_2012",
        "dsm_imageserver": "IL_Bureau_DSM_2012",
        "year": "2012",
    },
    "carroll": {
        "name": "Carroll",
        "fips": "17015",
        "district": "district2",
        "dtm_zip": "carr_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "carr_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Carroll_DTM_2012",
        "dsm_imageserver": "IL_Carroll_DSM_2012",
        "year": "2012",
    },
    "dekalb": {
        "name": "DeKalb",
        "fips": "17037",
        "district": "district2",
        "dtm_zip": "deka_dtm_2017.zip",  # TODO: verify
        "dsm_zip": "deka_dsm_2017.zip",  # TODO: verify
        "dtm_imageserver": "IL_DeKalb_DTM_2017",
        "dsm_imageserver": "IL_DeKalb_DSM_2017",
        "year": "2017",
    },
    "henry": {
        "name": "Henry",
        "fips": "17073",
        "district": "district2",
        "dtm_zip": "henr_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "henr_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Henry_DTM_2012",
        "dsm_imageserver": "IL_Henry_DSM_2012",
        "year": "2012",
    },
    "jodaviess": {
        "name": "Jo Daviess",
        "fips": "17085",
        "district": "district2",
        "dtm_zip": "joda_dtm_2011.zip",  # TODO: verify
        "dsm_zip": "joda_dsm_2011.zip",  # TODO: verify
        "dtm_imageserver": "IL_JoDaviess_DTM_2011",
        "dsm_imageserver": "IL_JoDaviess_DSM_2011",
        "year": "2011",
    },
    "knox": {
        "name": "Knox",
        "fips": "17095",
        "district": "district2",
        "dtm_zip": "knox_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "knox_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Knox_DTM_2012",
        "dsm_imageserver": "IL_Knox_DSM_2012",
        "year": "2012",
    },
    "lee": {
        "name": "Lee",
        "fips": "17103",
        "district": "district2",
        "dtm_zip": "lee_dtm_2012.zip",  # TODO: verify (3-char prefix)
        "dsm_zip": "lee_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Lee_DTM_2012",
        "dsm_imageserver": "IL_Lee_DSM_2012",
        "year": "2012",
    },
    "mercer": {
        "name": "Mercer",
        "fips": "17131",
        "district": "district2",
        "dtm_zip": "merc_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "merc_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Mercer_DTM_2012",
        "dsm_imageserver": "IL_Mercer_DSM_2012",
        "year": "2012",
    },
    "ogle": {
        "name": "Ogle",
        "fips": "17141",
        "district": "district2",
        "dtm_zip": "ogle_dtm_2017.zip",  # TODO: verify
        "dsm_zip": "ogle_dsm_2017.zip",  # TODO: verify
        "dtm_imageserver": "IL_Ogle_DTM_2017",
        "dsm_imageserver": "IL_Ogle_DSM_2017",
        "year": "2017",
    },
    "rockisland": {
        "name": "Rock Island",
        "fips": "17161",
        "district": "district2",
        "dtm_zip": "roci_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "roci_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_RockIsland_DTM_2012",
        "dsm_imageserver": "IL_RockIsland_DSM_2012",
        "year": "2012",
    },
    "stark": {
        "name": "Stark",
        "fips": "17175",
        "district": "district2",
        "dtm_zip": "star_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "star_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Stark_DTM_2012",
        "dsm_imageserver": "IL_Stark_DSM_2012",
        "year": "2012",
    },
    "stephenson": {
        "name": "Stephenson",
        "fips": "17177",
        "district": "district2",
        "dtm_zip": "step_dtm_2011.zip",  # TODO: verify
        "dsm_zip": "step_dsm_2011.zip",  # TODO: verify
        "dtm_imageserver": "IL_Stephenson_DTM_2011",
        "dsm_imageserver": "IL_Stephenson_DSM_2011",
        "year": "2011",
    },
    "warren": {
        "name": "Warren",
        "fips": "17187",
        "district": "district2",
        "dtm_zip": "warr_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "warr_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Warren_DTM_2012",
        "dsm_imageserver": "IL_Warren_DSM_2012",
        "year": "2012",
    },
    "whiteside": {
        "name": "Whiteside",
        "fips": "17195",
        "district": "district2",
        "dtm_zip": "whsd_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "whsd_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Whiteside_DTM_2012",
        "dsm_imageserver": "IL_Whiteside_DSM_2012",
        "year": "2012",
    },

    # --- District 3: W-central Illinois ---
    "cass": {
        "name": "Cass",
        "fips": "17017",
        "district": "district3",
        "dtm_zip": "cass_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "cass_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Cass_DTM_2014",
        "dsm_imageserver": "IL_Cass_DSM_2014",
        "year": "2014",
    },
    "fulton": {
        "name": "Fulton",
        "fips": "17057",
        "district": "district3",
        "dtm_zip": "fult_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "fult_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Fulton_DTM_2014",
        "dsm_imageserver": "IL_Fulton_DSM_2014",
        "year": "2014",
    },
    "hancock": {
        "name": "Hancock",
        "fips": "17067",
        "district": "district3",
        "dtm_zip": "hanc_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "hanc_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Hancock_DTM_2014",
        "dsm_imageserver": "IL_Hancock_DSM_2014",
        "year": "2014",
    },
    "henderson": {
        "name": "Henderson",
        "fips": "17071",
        "district": "district3",
        "dtm_zip": "hend_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "hend_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Henderson_DTM_2014",
        "dsm_imageserver": "IL_Henderson_DSM_2014",
        "year": "2014",
    },
    "logan": {
        "name": "Logan",
        "fips": "17107",
        "district": "district3",
        "dtm_zip": "loga_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "loga_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Logan_DTM_2014",
        "dsm_imageserver": "IL_Logan_DSM_2014",
        "year": "2014",
    },
    "mason": {
        "name": "Mason",
        "fips": "17125",
        "district": "district3",
        "dtm_zip": "maso_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "maso_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Mason_DTM_2014",
        "dsm_imageserver": "IL_Mason_DSM_2014",
        "year": "2014",
    },
    "mcdonough": {
        "name": "McDonough",
        "fips": "17109",
        "district": "district3",
        "dtm_zip": "mcdo_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "mcdo_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_McDonough_DTM_2014",
        "dsm_imageserver": "IL_McDonough_DSM_2014",
        "year": "2014",
    },
    "menard": {
        "name": "Menard",
        "fips": "17129",
        "district": "district3",
        "dtm_zip": "mena_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "mena_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Menard_DTM_2014",
        "dsm_imageserver": "IL_Menard_DSM_2014",
        "year": "2014",
    },
    "morgan": {
        "name": "Morgan",
        "fips": "17137",
        "district": "district3",
        "dtm_zip": "morg_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "morg_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Morgan_DTM_2014",
        "dsm_imageserver": "IL_Morgan_DSM_2014",
        "year": "2014",
    },
    "pike": {
        "name": "Pike",
        "fips": "17149",
        "district": "district3",
        "dtm_zip": "pike_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "pike_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Pike_DTM_2014",
        "dsm_imageserver": "IL_Pike_DSM_2014",
        "year": "2014",
    },
    "schuyler": {
        "name": "Schuyler",
        "fips": "17169",
        "district": "district3",
        "dtm_zip": "schu_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "schu_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Schuyler_DTM_2014",
        "dsm_imageserver": "IL_Schuyler_DSM_2014",
        "year": "2014",
    },
    "scott": {
        "name": "Scott",
        "fips": "17171",
        "district": "district3",
        "dtm_zip": "scot_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "scot_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Scott_DTM_2014",
        "dsm_imageserver": "IL_Scott_DSM_2014",
        "year": "2014",
    },

    # --- District 4: Central Illinois ---
    "dewitt": {
        "name": "De Witt",
        "fips": "17039",
        "district": "district4",
        "dtm_zip": "dewi_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "dewi_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_DeWitt_DTM_2016",
        "dsm_imageserver": "IL_DeWitt_DSM_2016",
        "year": "2016",
    },
    "ford": {
        "name": "Ford",
        "fips": "17053",
        "district": "district4",
        "dtm_zip": "ford_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "ford_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Ford_DTM_2016",
        "dsm_imageserver": "IL_Ford_DSM_2016",
        "year": "2016",
    },
    "iroquois": {
        "name": "Iroquois",
        "fips": "17075",
        "district": "district4",
        "dtm_zip": "iroq_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "iroq_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Iroquois_DTM_2016",
        "dsm_imageserver": "IL_Iroquois_DSM_2016",
        "year": "2016",
    },
    "lasalle": {
        "name": "La Salle",
        "fips": "17099",
        "district": "district4",
        "dtm_zip": "lasa_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "lasa_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_LaSalle_DTM_2012",
        "dsm_imageserver": "IL_LaSalle_DSM_2012",
        "year": "2012",
    },
    "livingston": {
        "name": "Livingston",
        "fips": "17105",
        "district": "district4",
        "dtm_zip": "livi_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "livi_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Livingston_DTM_2016",
        "dsm_imageserver": "IL_Livingston_DSM_2016",
        "year": "2016",
    },
    "marshall": {
        "name": "Marshall",
        "fips": "17123",
        "district": "district4",
        "dtm_zip": "mars_dtm_2012.zip",  # TODO: verify
        "dsm_zip": "mars_dsm_2012.zip",  # TODO: verify
        "dtm_imageserver": "IL_Marshall_DTM_2012",
        "dsm_imageserver": "IL_Marshall_DSM_2012",
        "year": "2012",
    },
    "mclean": {
        "name": "McLean",
        "fips": "17113",
        "district": "district4",
        "dtm_zip": "mcle_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "mcle_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_McLean_DTM_2016",
        "dsm_imageserver": "IL_McLean_DSM_2016",
        "year": "2016",
    },
    "peoria": {
        "name": "Peoria",
        "fips": "17143",
        "district": "district4",
        "dtm_zip": "peor_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "peor_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Peoria_DTM_2014",
        "dsm_imageserver": "IL_Peoria_DSM_2014",
        "year": "2014",
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
    "tazewell": {
        "name": "Tazewell",
        "fips": "17179",
        "district": "district4",
        "dtm_zip": "taze_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "taze_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Tazewell_DTM_2014",
        "dsm_imageserver": "IL_Tazewell_DSM_2014",
        "year": "2014",
    },
    "woodford": {
        "name": "Woodford",
        "fips": "17203",
        "district": "district4",
        "dtm_zip": "wood_dtm_2014.zip",  # TODO: verify
        "dsm_zip": "wood_dsm_2014.zip",  # TODO: verify
        "dtm_imageserver": "IL_Woodford_DTM_2014",
        "dsm_imageserver": "IL_Woodford_DSM_2014",
        "year": "2014",
    },

    # --- District 5: E-central Illinois ---
    "champaign": {
        "name": "Champaign",
        "fips": "17019",
        "district": "district5",
        "dtm_zip": "cham_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "cham_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Champaign_DTM_2016",
        "dsm_imageserver": "IL_Champaign_DSM_2016",
        "year": "2016",
    },
    "clark": {
        "name": "Clark",
        "fips": "17023",
        "district": "district5",
        "dtm_zip": "clar_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "clar_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Clark_DTM_2016",
        "dsm_imageserver": "IL_Clark_DSM_2016",
        "year": "2016",
    },
    "coles": {
        "name": "Coles",
        "fips": "17029",
        "district": "district5",
        "dtm_zip": "cole_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "cole_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Coles_DTM_2016",
        "dsm_imageserver": "IL_Coles_DSM_2016",
        "year": "2016",
    },
    "crawford": {
        "name": "Crawford",
        "fips": "17033",
        "district": "district5",
        "dtm_zip": "craw_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "craw_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Crawford_DTM_2016",
        "dsm_imageserver": "IL_Crawford_DSM_2016",
        "year": "2016",
    },
    "cumberland": {
        "name": "Cumberland",
        "fips": "17035",
        "district": "district5",
        "dtm_zip": "cumb_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "cumb_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Cumberland_DTM_2016",
        "dsm_imageserver": "IL_Cumberland_DSM_2016",
        "year": "2016",
    },
    "douglas": {
        "name": "Douglas",
        "fips": "17041",
        "district": "district5",
        "dtm_zip": "doug_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "doug_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Douglas_DTM_2016",
        "dsm_imageserver": "IL_Douglas_DSM_2016",
        "year": "2016",
    },
    "edgar": {
        "name": "Edgar",
        "fips": "17045",
        "district": "district5",
        "dtm_zip": "edga_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "edga_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Edgar_DTM_2016",
        "dsm_imageserver": "IL_Edgar_DSM_2016",
        "year": "2016",
    },
    "macon": {
        "name": "Macon",
        "fips": "17115",
        "district": "district5",
        "dtm_zip": "maco_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "maco_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Macon_DTM_2016",
        "dsm_imageserver": "IL_Macon_DSM_2016",
        "year": "2016",
    },
    "moultrie": {
        "name": "Moultrie",
        "fips": "17139",
        "district": "district5",
        "dtm_zip": "moul_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "moul_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Moultrie_DTM_2016",
        "dsm_imageserver": "IL_Moultrie_DSM_2016",
        "year": "2016",
    },
    "piatt": {
        "name": "Piatt",
        "fips": "17147",
        "district": "district5",
        "dtm_zip": "piat_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "piat_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Piatt_DTM_2016",
        "dsm_imageserver": "IL_Piatt_DSM_2016",
        "year": "2016",
    },
    "shelby": {
        "name": "Shelby",
        "fips": "17173",
        "district": "district5",
        "dtm_zip": "shel_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "shel_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Shelby_DTM_2016",
        "dsm_imageserver": "IL_Shelby_DSM_2016",
        "year": "2016",
    },
    "vermilion": {
        "name": "Vermilion",
        "fips": "17183",
        "district": "district5",
        "dtm_zip": "verm_dtm_2016.zip",  # TODO: verify
        "dsm_zip": "verm_dsm_2016.zip",  # TODO: verify
        "dtm_imageserver": "IL_Vermilion_DTM_2016",
        "dsm_imageserver": "IL_Vermilion_DSM_2016",
        "year": "2016",
    },

    # --- District 6: W Illinois ---
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
    "brown": {
        "name": "Brown",
        "fips": "17009",
        "district": "district6",
        "dtm_zip": "brow_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "brow_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Brown_DTM_2018",
        "dsm_imageserver": "IL_Brown_DSM_2018",
        "year": "2018",
    },
    "calhoun": {
        "name": "Calhoun",
        "fips": "17013",
        "district": "district6",
        "dtm_zip": "calh_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "calh_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Calhoun_DTM_2018",
        "dsm_imageserver": "IL_Calhoun_DSM_2018",
        "year": "2018",
    },
    "greene": {
        "name": "Greene",
        "fips": "17061",
        "district": "district6",
        "dtm_zip": "gree_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "gree_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Greene_DTM_2018",
        "dsm_imageserver": "IL_Greene_DSM_2018",
        "year": "2018",
    },
    "jersey": {
        "name": "Jersey",
        "fips": "17083",
        "district": "district6",
        "dtm_zip": "jers_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "jers_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Jersey_DTM_2018",
        "dsm_imageserver": "IL_Jersey_DSM_2018",
        "year": "2018",
    },
    "macoupin": {
        "name": "Macoupin",
        "fips": "17117",
        "district": "district6",
        "dtm_zip": "macp_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "macp_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Macoupin_DTM_2018",
        "dsm_imageserver": "IL_Macoupin_DSM_2018",
        "year": "2018",
    },
    "madison": {
        "name": "Madison",
        "fips": "17119",
        "district": "district6",
        "dtm_zip": "madi_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "madi_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Madison_DTM_2018",
        "dsm_imageserver": "IL_Madison_DSM_2018",
        "year": "2018",
    },
    "montgomery": {
        "name": "Montgomery",
        "fips": "17135",
        "district": "district6",
        "dtm_zip": "mont_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "mont_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Montgomery_DTM_2018",
        "dsm_imageserver": "IL_Montgomery_DSM_2018",
        "year": "2018",
    },
    "sangamon": {
        "name": "Sangamon",
        "fips": "17167",
        "district": "district6",
        "dtm_zip": "sang_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "sang_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Sangamon_DTM_2018",
        "dsm_imageserver": "IL_Sangamon_DSM_2018",
        "year": "2018",
    },

    # --- District 7: SW Illinois ---
    "alexander": {
        "name": "Alexander",
        "fips": "17003",
        "district": "district9",  # southernmost tip; some sources use district9
        "dtm_zip": "alex_dtm_2020.zip",
        "dsm_zip": "alex_dsm_2020.zip",
        "dtm_imageserver": "IL_Alexander_DTM_2020",
        "dsm_imageserver": "IL_Alexander_DSM_2020",
        "year": "2020",
    },
    "jackson": {
        "name": "Jackson",
        "fips": "17077",
        "district": "district7",
        "dtm_zip": "jack_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "jack_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Jackson_DTM_2020",
        "dsm_imageserver": "IL_Jackson_DSM_2020",
        "year": "2020",
    },
    "johnson": {
        "name": "Johnson",
        "fips": "17087",
        "district": "district7",
        "dtm_zip": "john_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "john_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Johnson_DTM_2020",
        "dsm_imageserver": "IL_Johnson_DSM_2020",
        "year": "2020",
    },
    "monroe": {
        "name": "Monroe",
        "fips": "17133",
        "district": "district7",
        "dtm_zip": "monr_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "monr_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Monroe_DTM_2020",
        "dsm_imageserver": "IL_Monroe_DSM_2020",
        "year": "2020",
    },
    "perry": {
        "name": "Perry",
        "fips": "17145",
        "district": "district7",
        "dtm_zip": "perr_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "perr_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Perry_DTM_2020",
        "dsm_imageserver": "IL_Perry_DSM_2020",
        "year": "2020",
    },
    "pulaski": {
        "name": "Pulaski",
        "fips": "17153",
        "district": "district7",
        "dtm_zip": "pula_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "pula_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Pulaski_DTM_2020",
        "dsm_imageserver": "IL_Pulaski_DSM_2020",
        "year": "2020",
    },
    "randolph": {
        "name": "Randolph",
        "fips": "17157",
        "district": "district7",
        "dtm_zip": "rand_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "rand_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Randolph_DTM_2020",
        "dsm_imageserver": "IL_Randolph_DSM_2020",
        "year": "2020",
    },
    "stclair": {
        "name": "St. Clair",
        "fips": "17163",
        "district": "district7",
        "dtm_zip": "stcl_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "stcl_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_StClair_DTM_2020",
        "dsm_imageserver": "IL_StClair_DSM_2020",
        "year": "2020",
    },
    "union": {
        "name": "Union",
        "fips": "17181",
        "district": "district7",
        "dtm_zip": "unio_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "unio_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Union_DTM_2020",
        "dsm_imageserver": "IL_Union_DSM_2020",
        "year": "2020",
    },
    "williamson": {
        "name": "Williamson",
        "fips": "17199",
        "district": "district7",
        "dtm_zip": "wmsn_dtm_2020.zip",  # TODO: verify (wmsn to avoid collision with will)
        "dsm_zip": "wmsn_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Williamson_DTM_2020",
        "dsm_imageserver": "IL_Williamson_DSM_2020",
        "year": "2020",
    },

    # --- District 8: S-central Illinois ---
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
    "christian": {
        "name": "Christian",
        "fips": "17021",
        "district": "district8",
        "dtm_zip": "chri_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "chri_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Christian_DTM_2018",
        "dsm_imageserver": "IL_Christian_DSM_2018",
        "year": "2018",
    },
    "clay": {
        "name": "Clay",
        "fips": "17025",
        "district": "district8",
        "dtm_zip": "clay_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "clay_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Clay_DTM_2018",
        "dsm_imageserver": "IL_Clay_DSM_2018",
        "year": "2018",
    },
    "clinton": {
        "name": "Clinton",
        "fips": "17027",
        "district": "district8",
        "dtm_zip": "clin_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "clin_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Clinton_DTM_2018",
        "dsm_imageserver": "IL_Clinton_DSM_2018",
        "year": "2018",
    },
    "effingham": {
        "name": "Effingham",
        "fips": "17049",
        "district": "district8",
        "dtm_zip": "effi_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "effi_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Effingham_DTM_2018",
        "dsm_imageserver": "IL_Effingham_DSM_2018",
        "year": "2018",
    },
    "fayette": {
        "name": "Fayette",
        "fips": "17051",
        "district": "district8",
        "dtm_zip": "faye_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "faye_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Fayette_DTM_2018",
        "dsm_imageserver": "IL_Fayette_DSM_2018",
        "year": "2018",
    },
    "jefferson": {
        "name": "Jefferson",
        "fips": "17081",
        "district": "district8",
        "dtm_zip": "jeff_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "jeff_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Jefferson_DTM_2018",
        "dsm_imageserver": "IL_Jefferson_DSM_2018",
        "year": "2018",
    },
    "marion": {
        "name": "Marion",
        "fips": "17121",
        "district": "district8",
        "dtm_zip": "mari_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "mari_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Marion_DTM_2018",
        "dsm_imageserver": "IL_Marion_DSM_2018",
        "year": "2018",
    },
    "washington": {
        "name": "Washington",
        "fips": "17189",
        "district": "district8",
        "dtm_zip": "wash_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "wash_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Washington_DTM_2018",
        "dsm_imageserver": "IL_Washington_DSM_2018",
        "year": "2018",
    },
    "wayne": {
        "name": "Wayne",
        "fips": "17191",
        "district": "district8",
        "dtm_zip": "wayn_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "wayn_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Wayne_DTM_2018",
        "dsm_imageserver": "IL_Wayne_DSM_2018",
        "year": "2018",
    },

    # --- District 9: S Illinois ---
    "edwards": {
        "name": "Edwards",
        "fips": "17047",
        "district": "district9",
        "dtm_zip": "edwa_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "edwa_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Edwards_DTM_2020",
        "dsm_imageserver": "IL_Edwards_DSM_2020",
        "year": "2020",
    },
    "franklin": {
        "name": "Franklin",
        "fips": "17055",
        "district": "district9",
        "dtm_zip": "fran_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "fran_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Franklin_DTM_2020",
        "dsm_imageserver": "IL_Franklin_DSM_2020",
        "year": "2020",
    },
    "gallatin": {
        "name": "Gallatin",
        "fips": "17059",
        "district": "district9",
        "dtm_zip": "gall_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "gall_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Gallatin_DTM_2020",
        "dsm_imageserver": "IL_Gallatin_DSM_2020",
        "year": "2020",
    },
    "hamilton": {
        "name": "Hamilton",
        "fips": "17065",
        "district": "district9",
        "dtm_zip": "hami_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "hami_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Hamilton_DTM_2020",
        "dsm_imageserver": "IL_Hamilton_DSM_2020",
        "year": "2020",
    },
    "hardin": {
        "name": "Hardin",
        "fips": "17069",
        "district": "district9",
        "dtm_zip": "hard_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "hard_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Hardin_DTM_2020",
        "dsm_imageserver": "IL_Hardin_DSM_2020",
        "year": "2020",
    },
    "jasper": {
        "name": "Jasper",
        "fips": "17079",
        "district": "district9",
        "dtm_zip": "jasp_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "jasp_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Jasper_DTM_2018",
        "dsm_imageserver": "IL_Jasper_DSM_2018",
        "year": "2018",
    },
    "lawrence": {
        "name": "Lawrence",
        "fips": "17101",
        "district": "district9",
        "dtm_zip": "lawr_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "lawr_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Lawrence_DTM_2020",
        "dsm_imageserver": "IL_Lawrence_DSM_2020",
        "year": "2020",
    },
    "massac": {
        "name": "Massac",
        "fips": "17127",
        "district": "district9",
        "dtm_zip": "mass_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "mass_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Massac_DTM_2020",
        "dsm_imageserver": "IL_Massac_DSM_2020",
        "year": "2020",
    },
    "pope": {
        "name": "Pope",
        "fips": "17151",
        "district": "district9",
        "dtm_zip": "pope_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "pope_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Pope_DTM_2020",
        "dsm_imageserver": "IL_Pope_DSM_2020",
        "year": "2020",
    },
    "richland": {
        "name": "Richland",
        "fips": "17159",
        "district": "district9",
        "dtm_zip": "rich_dtm_2018.zip",  # TODO: verify
        "dsm_zip": "rich_dsm_2018.zip",  # TODO: verify
        "dtm_imageserver": "IL_Richland_DTM_2018",
        "dsm_imageserver": "IL_Richland_DSM_2018",
        "year": "2018",
    },
    "saline": {
        "name": "Saline",
        "fips": "17165",
        "district": "district9",
        "dtm_zip": "sali_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "sali_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Saline_DTM_2020",
        "dsm_imageserver": "IL_Saline_DSM_2020",
        "year": "2020",
    },
    "wabash": {
        "name": "Wabash",
        "fips": "17185",
        "district": "district9",
        "dtm_zip": "waba_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "waba_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_Wabash_DTM_2020",
        "dsm_imageserver": "IL_Wabash_DSM_2020",
        "year": "2020",
    },
    "white": {
        "name": "White",
        "fips": "17193",
        "district": "district9",
        "dtm_zip": "whit_dtm_2020.zip",  # TODO: verify
        "dsm_zip": "whit_dsm_2020.zip",  # TODO: verify
        "dtm_imageserver": "IL_White_DTM_2020",
        "dsm_imageserver": "IL_White_DSM_2020",
        "year": "2020",
    },
}


def get_county(name: str) -> Optional[Dict]:
    """Get county info by name (case-insensitive)."""
    key = name.lower().replace(" ", "").replace(".", "").replace("county", "")
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
    for key in sorted(COUNTIES.keys()):
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
