import unittest
import math
from proj1 import *


class TestStudentRegionFunctions(unittest.TestCase):
    base_rect: GlobeRect
    base_region: Region
    base_condition: RegionCondition

    def setUp(self) -> None:
        self.base_rect = GlobeRect(10.0, 20.0, 30.0, 40.0)
        self.base_region = Region(self.base_rect, "Base", "other")
        self.base_condition = RegionCondition(self.base_region, 2025, 1000, 2500.0)

    def test_region_conditions_has_four_examples(self) -> None:
        self.assertEqual(len(region_conditions), 4)
        self.assertIsInstance(region_conditions[0], RegionCondition)
        self.assertIsInstance(region_conditions[1], RegionCondition)
        self.assertIsInstance(region_conditions[2], RegionCondition)
        self.assertIsInstance(region_conditions[3], RegionCondition)

    def test_region_conditions_contains_cal_poly_example(self) -> None:
        self.assertEqual(region_conditions[3].region.name, "Cal Poly San Luis Obispo")
        self.assertEqual(region_conditions[3].region.terrain, "other")

    def test_emissions_per_capita_regular_value(self) -> None:
        self.assertAlmostEqual(emissions_per_capita(self.base_condition), 2.5, places=7)

    def test_emissions_per_capita_zero_population(self) -> None:
        zero_pop_condition = RegionCondition(self.base_region, 2025, 0, 2500.0)
        self.assertEqual(emissions_per_capita(zero_pop_condition), 0.0)

    def test_area_matches_full_sphere_for_whole_globe(self) -> None:
        whole_globe = GlobeRect(-90.0, 90.0, -180.0, 180.0)
        expected = 4.0 * math.pi * (EARTH_RADIUS_KM ** 2)
        self.assertAlmostEqual(area(whole_globe), expected, places=5)

    def test_area_handles_date_line_wraparound(self) -> None:
        wrapped_rect = GlobeRect(10.0, 20.0, 170.0, -170.0)
        expected = (
            (EARTH_RADIUS_KM ** 2)
            * math.radians(20.0)
            * (math.sin(math.radians(20.0)) - math.sin(math.radians(10.0)))
        )
        self.assertAlmostEqual(area(wrapped_rect), expected, places=5)

    def test_emissions_per_square_km_zero_area(self) -> None:
        point_rect = GlobeRect(35.0, 35.0, -120.0, -120.0)
        point_region = Region(point_rect, "Point", "other")
        point_condition = RegionCondition(point_region, 2025, 100, 500.0)
        self.assertEqual(emissions_per_square_km(point_condition), 0.0)

    def test_emissions_per_square_km_positive_area(self) -> None:
        expected = 2500.0 / area(self.base_rect)
        self.assertAlmostEqual(emissions_per_square_km(self.base_condition), expected, places=7)

    def test_densest_picks_highest_density_region(self) -> None:
        sparse = RegionCondition(
            Region(GlobeRect(0.0, 10.0, 0.0, 10.0), "Sparse", "other"),
            2025,
            1000,
            100.0,
        )
        dense = RegionCondition(
            Region(GlobeRect(0.0, 1.0, 0.0, 1.0), "Dense", "other"),
            2025,
            5000,
            100.0,
        )
        self.assertEqual(densest([sparse, dense, self.base_condition]), "Dense")

    def test_densest_empty_list_returns_empty_string(self) -> None:
        self.assertEqual(densest([]), "")

    def test_project_condition_uses_other_growth_rate(self) -> None:
        projected = project_condition(self.base_condition, 10)
        growth_factor = (1.0003) ** 10
        self.assertEqual(projected.year, 2035)
        self.assertEqual(projected.pop, int(1000 * growth_factor))
        self.assertAlmostEqual(projected.ghg_rate, 2500.0 * growth_factor, places=7)
        self.assertEqual(projected.region, self.base_region)
        self.assertEqual(self.base_condition.year, 2025)
        self.assertEqual(self.base_condition.pop, 1000)
        self.assertAlmostEqual(self.base_condition.ghg_rate, 2500.0, places=7)

    def test_project_condition_preserves_values_when_years_is_zero(self) -> None:
        projected = project_condition(self.base_condition, 0)
        self.assertEqual(projected, self.base_condition)

    def test_project_condition_handles_forest_decline(self) -> None:
        forest_region = Region(self.base_rect, "Forest", "forest")
        forest_condition = RegionCondition(forest_region, 2025, 500000, 1000000.0)
        projected = project_condition(forest_condition, 3)
        growth_factor = (0.99999) ** 3
        self.assertEqual(projected.pop, int(500000 * growth_factor))
        self.assertAlmostEqual(projected.ghg_rate, 1000000.0 * growth_factor, places=7)


if __name__ == "__main__":
    unittest.main()
