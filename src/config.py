from pathlib import Path
from dataclasses import dataclass, field

# ── Paths ──────────────────────────────────────────────────────────────────
CURR_PATH     = Path(__file__).resolve().parent   # src/
REPO_PATH     = CURR_PATH.parent                  # repo root
NOTEBOOK_PATH = REPO_PATH / "notebooks"
DATA_PATH     = REPO_PATH / "data"
DEMO_PATH     = DATA_PATH / "demo-data"
SRC_PATH      = REPO_PATH / "src"

# Aliases used by newer notebooks
REPO_ROOT = REPO_PATH
DATA_ROOT = DATA_PATH

# ── Known city CRS lookup ──────────────────────────────────────────────────
# Manually verified UTM CRS per city slug (= folder name under data/raw/).
# If a city is not listed here, the CRS is auto-detected from its name via
# pyproj + geopy. Add entries here to skip the geocoding call and guarantee
# the correct zone for known project cities.
CITY_CRS: dict[str, str] = {
    "abuja"        : "EPSG:32632",  # UTM 32N
    "algiers"      : "EPSG:32631",  # UTM 31N
    "baghdad"      : "EPSG:32638",  # UTM 38N
    "buenos_aires" : "EPSG:32721",  # UTM 21S
    "cairo"        : "EPSG:32636",  # UTM 36N
    "cape_town"    : "EPSG:32734",  # UTM 34S
    "dakar"        : "EPSG:32628",  # UTM 28N
    "lima"         : "EPSG:32718",  # UTM 18S
    "los_angeles"  : "EPSG:32611",  # UTM 11N
    "madrid"       : "EPSG:32630",  # UTM 30N
    "mexico_city"  : "EPSG:32614",  # UTM 14N
    "mumbai"       : "EPSG:32643",  # UTM 43N
    "new_york"     : "EPSG:32618",  # UTM 18N
    "santiago"     : "EPSG:32719",  # UTM 19S
    "yangon"       : "EPSG:32647",  # UTM 47N
    "cebu"         : "EPSG:32651",  # UTM 51N
    "nairobi"      : "EPSG:32637",  # UTM 37N
    "barcelona"    : "EPSG:32631",  # UTM 31N
}


def _detect_utm_crs(city: str) -> str:
    """
    Auto-detect the best UTM CRS for a city by geocoding its name.
    Requires: pyproj (bundled with geopandas), geopy (pip install geopy).
    """
    try:
        from geopy.geocoders import Nominatim
        from pyproj.aoi import AreaOfInterest
        from pyproj.database import query_utm_crs_info
    except ImportError as e:
        raise ImportError(
            f"Auto-detection of UTM CRS requires geopy: pip install geopy\n"
            f"Or add '{city}' manually to CITY_CRS in src/config.py."
        ) from e

    geolocator = Nominatim(user_agent="tci_project")
    location   = geolocator.geocode(city.replace("_", " "))
    if location is None:
        raise ValueError(
            f"Could not geocode city: '{city}'. "
            f"Add it manually to CITY_CRS in src/config.py."
        )

    utm_crs_list = query_utm_crs_info(
        datum_name       = "WGS 84",
        area_of_interest = AreaOfInterest(
            west_lon_degree  = location.longitude,
            south_lat_degree = location.latitude,
            east_lon_degree  = location.longitude,
            north_lat_degree = location.latitude,
        ),
    )
    epsg = f"EPSG:{utm_crs_list[0].code}"
    print(
        f"  Auto-detected CRS for '{city}': "
        f"lat={location.latitude:.2f}, lon={location.longitude:.2f} → {epsg}"
    )
    return epsg


@dataclass
class CityConfig:
    city          : str
    projected_crs : str = ""   # auto-filled from CITY_CRS or geocoding if blank

    def __post_init__(self):
        if not self.projected_crs:
            if self.city in CITY_CRS:
                self.projected_crs = CITY_CRS[self.city]
            else:
                print(
                    f"  '{self.city}' not in CITY_CRS — auto-detecting UTM CRS via geocoding …"
                )
                self.projected_crs = _detect_utm_crs(self.city)
                print(
                    f"  Tip: add \"{self.city}\" : \"{self.projected_crs}\" "
                    f"to CITY_CRS in src/config.py to skip this next time."
                )

    # ── Derived paths ──────────────────────────────────────────────────────
    @property
    def raw_root(self) -> Path:
        return DATA_ROOT / "raw" / self.city

    @property
    def boundary_path(self) -> Path:
        return self.raw_root / "boundary"

    @property
    def grid_path(self) -> Path:
        return self.raw_root / "grid" / f"grid_{self.city}.gpkg"

    @property
    def no2_path(self) -> Path:
        return self.raw_root / "no2"

    @property
    def lst_path(self) -> Path:
        return self.raw_root / "lst"

    @property
    def ntl_path(self) -> Path:
        return self.raw_root / "ntl"

    @property
    def osm_path(self) -> Path:
        return self.raw_root / "osm"

    @property
    def output_root(self) -> Path:
        return DATA_ROOT / "processed" / self.city

    def build(self) -> None:
        """Create output directory and print a path summary."""
        self.output_root.mkdir(parents=True, exist_ok=True)
        print(f"City          : {self.city}")
        print(f"Projected CRS : {self.projected_crs}")
        print(f"Raw root      : {self.raw_root}")
        print(f"Boundary      : {self.boundary_path}")
        print(f"Grid          : {self.grid_path}")
        print(f"Output root   : {self.output_root}")


# ── Example usage ──────────────────────────────────────────────────────────
# Known city (instant, no geocoding):
#   city_config = CityConfig(city="baghdad")
#
# Unknown city (auto-detected via geocoding, prints a tip to add it manually):
#   city_config = CityConfig(city="kinshasa")
#
# Override manually at any time:
#   city_config = CityConfig(city="kinshasa", projected_crs="EPSG:32634")
#
# city_config.build()
