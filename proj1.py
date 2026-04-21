import sys
import unittest
import math
from typing import *
from dataclasses import dataclass

sys.setrecursionlimit(10**6)

EARTH_RADIUS_KM: float = 6378.1


@dataclass(frozen=True)
class GlobeRect:
    """A rectangular region on the globe."""

    lo_lat: float
    hi_lat: float
    west_long: float
    east_long: float


@dataclass(frozen=True)
class Region:
    """The identity and terrain for a globe rectangle."""

    rect: GlobeRect
    name: str
    terrain: str


@dataclass(frozen=True)
class RegionCondition:
    """A region's condition in a particular year."""

    region: Region
    year: int
    pop: int
    ghg_rate: float


tokyo_condition = RegionCondition(
    region=Region(
        rect=GlobeRect(lo_lat=35.5, hi_lat=35.9, west_long=139.5, east_long=140.0),
        name="Tokyo Metro",
        terrain="other",
    ),
    year=2025,
    pop=37000000,
    ghg_rate=175000000.0,
)

lagos_condition = RegionCondition(
    region=Region(
        rect=GlobeRect(lo_lat=6.2, hi_lat=6.8, west_long=3.0, east_long=3.7),
        name="Lagos Metro",
        terrain="other",
    ),
    year=2025,
    pop=16000000,
    ghg_rate=80000000.0,
)

pacific_patch_condition = RegionCondition(
    region=Region(
        rect=GlobeRect(lo_lat=10.0, hi_lat=20.0, west_long=170.0, east_long=-170.0),
        name="Central Pacific Patch",
        terrain="ocean",
    ),
    year=2025,
    pop=0,
    ghg_rate=120000.0,
)

cal_poly_condition = RegionCondition(
    region=Region(
        rect=GlobeRect(lo_lat=35.18, hi_lat=35.38, west_long=-120.77, east_long=-120.55),
        name="Cal Poly San Luis Obispo",
        terrain="other",
    ),
    year=2025,
    pop=26000,
    ghg_rate=95000.0,
)

region_conditions: List[RegionCondition] = [
    tokyo_condition,
    lagos_condition,
    pacific_patch_condition,
    cal_poly_condition,
]


# Purpose: Return annual greenhouse-gas emissions per person for a region condition.
# Type: RegionCondition -> float
# Examples/tests:
# emissions_per_capita(RegionCondition(Region(GlobeRect(0.0, 1.0, 0.0, 1.0), "A", "other"), 2025, 100, 250.0)) == 2.5
# emissions_per_capita(RegionCondition(Region(GlobeRect(0.0, 1.0, 0.0, 1.0), "B", "other"), 2025, 0, 250.0)) == 0.0
def emissions_per_capita(rc: RegionCondition) -> float:
    if rc.pop <= 0:
        return 0.0
    return rc.ghg_rate / rc.pop


def _longitude_width_radians(west_long: float, east_long: float) -> float:
    """Return eastward longitude width in radians, correcting for date-line wraparound."""

    west_radians = math.radians(west_long)
    east_radians = math.radians(east_long)
    width = east_radians - west_radians
    if width < 0:
        return width + (2 * math.pi)
    return width


# Purpose: Return the spherical surface area of a globe rectangle in square kilometers.
# Type: GlobeRect -> float
# Examples/tests:
# area(GlobeRect(0.0, 0.0, 0.0, 10.0)) == 0.0
# area(GlobeRect(-90.0, 90.0, -180.0, 180.0)) is approximately 4 * pi * EARTH_RADIUS_KM ** 2
def area(gr: GlobeRect) -> float:
    lo_lat_radians = math.radians(gr.lo_lat)
    hi_lat_radians = math.radians(gr.hi_lat)
    longitude_width = _longitude_width_radians(gr.west_long, gr.east_long)
    latitude_height = math.sin(hi_lat_radians) - math.sin(lo_lat_radians)
    return (EARTH_RADIUS_KM ** 2) * abs(longitude_width) * abs(latitude_height)


# Purpose: Return emissions per square kilometer for a region condition.
# Type: RegionCondition -> float
# Examples/tests:
# emissions_per_square_km(RegionCondition(Region(GlobeRect(0.0, 1.0, 0.0, 1.0), "A", "other"), 2025, 100, 50.0)) > 0.0
# emissions_per_square_km(RegionCondition(Region(GlobeRect(1.0, 1.0, 2.0, 2.0), "B", "other"), 2025, 100, 50.0)) == 0.0
def emissions_per_square_km(rc: RegionCondition) -> float:
    region_area = area(rc.region.rect)
    if region_area == 0.0:
        return 0.0
    return rc.ghg_rate / region_area


def _population_density(rc: RegionCondition) -> float:
    """Return population density, treating positive population in zero area as infinite."""

    region_area = area(rc.region.rect)
    if region_area == 0.0:
        if rc.pop > 0:
            return float("inf")
        return 0.0
    return rc.pop / region_area


def _densest_region(rc_list: List[RegionCondition]) -> RegionCondition:
    """Return the densest region condition from a non-empty list."""

    if len(rc_list) == 1:
        return rc_list[0]

    densest_rest = _densest_region(rc_list[1:])
    if _population_density(rc_list[0]) >= _population_density(densest_rest):
        return rc_list[0]
    return densest_rest


# Purpose: Return the name of the region with the greatest population density.
# Type: List[RegionCondition] -> str
# Examples/tests:
# densest([]) == ""
# densest([RegionCondition(Region(GlobeRect(0.0, 1.0, 0.0, 1.0), "A", "other"), 2025, 10, 5.0)]) == "A"
def densest(rc_list: List[RegionCondition]) -> str:
    if rc_list == []:
        return ""
    return _densest_region(rc_list).region.name


def _terrain_growth_rate(terrain: str) -> float:
    """Return the annual population growth rate for a terrain."""

    if terrain == "ocean":
        return 0.0001
    if terrain == "mountains":
        return 0.0005
    if terrain == "forest":
        return -0.00001
    return 0.0003


def _compound_growth_factor(rate: float, years: int) -> float:
    """Return compound growth factor after a non-negative number of years."""

    if years <= 0:
        return 1.0
    return (1.0 + rate) * _compound_growth_factor(rate, years - 1)


# Purpose: Return a new region condition projected forward by a number of years.
# Type: RegionCondition, int -> RegionCondition
# Examples/tests:
# project_condition(RegionCondition(Region(GlobeRect(0.0, 1.0, 0.0, 1.0), "A", "other"), 2025, 1000, 500.0), 0).year == 2025
# project_condition(RegionCondition(Region(GlobeRect(0.0, 1.0, 0.0, 1.0), "A", "other"), 2025, 1000, 500.0), 2).year == 2027
def project_condition(rc: RegionCondition, years: int) -> RegionCondition:
    if years <= 0:
        return RegionCondition(
            region=rc.region,
            year=rc.year + years,
            pop=rc.pop,
            ghg_rate=rc.ghg_rate,
        )
    growth_rate = _terrain_growth_rate(rc.region.terrain)
    growth_factor = _compound_growth_factor(growth_rate, years)
    return RegionCondition(
        region=rc.region,
        year=rc.year + years,
        pop=int(rc.pop * growth_factor),
        ghg_rate=rc.ghg_rate * growth_factor,
    )
