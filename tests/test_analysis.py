import math
import unittest

from analysis import analyze_formats, calculate_format_metrics, recommend_primary_metric, DEFAULT_TARGETS


class AnalysisTests(unittest.TestCase):
    def test_no_touches_results_in_infinite_mtbt(self):
        metrics = calculate_format_metrics(
            {
                "name": "A",
                "count": 100,
                "runtime_minutes": 240,
                "full_speed": 100,
                "actual_speed": 80,
                "staffing": 1,
                "unplanned_touches": 0,
                "planned_touches": 0,
            },
            baseline_staffing=4,
            targets=DEFAULT_TARGETS,
        )
        self.assertTrue(math.isinf(metrics.unplanned_mtbt_minutes))
        self.assertTrue(math.isinf(metrics.planned_mtbt_minutes))

    def test_primary_metric_chooses_biggest_bottleneck(self):
        result = analyze_formats(
            {
                "formats": [
                    {
                        "name": "A",
                        "count": 100,
                        "runtime_minutes": 240,
                        "full_speed": 100,
                        "actual_speed": 75,
                        "staffing": 1,
                        "unplanned_touches": 1,
                        "planned_touches": 5,
                    },
                    {
                        "name": "B",
                        "count": 100,
                        "runtime_minutes": 240,
                        "full_speed": 100,
                        "actual_speed": 80,
                        "staffing": 1,
                        "unplanned_touches": 4,
                        "planned_touches": 5,
                    },
                ]
            }
        )
        self.assertEqual(result["primary_metric_for_test"], "unplanned_mtbt")

    def test_reference_count_delta_is_returned(self):
        result = analyze_formats(
            {
                "reference_format": "Ref",
                "formats": [
                    {
                        "name": "Ref",
                        "count": 200,
                        "runtime_minutes": 240,
                        "full_speed": 100,
                        "actual_speed": 80,
                        "staffing": 1,
                        "unplanned_touches": 1,
                        "planned_touches": 8,
                    },
                    {
                        "name": "Other",
                        "count": 260,
                        "runtime_minutes": 240,
                        "full_speed": 100,
                        "actual_speed": 80,
                        "staffing": 1,
                        "unplanned_touches": 1,
                        "planned_touches": 8,
                    },
                ],
            }
        )
        formatted = {f["name"]: f for f in result["formats"]}
        self.assertEqual(formatted["Ref"]["count_delta_vs_reference_pct"], 0.0)
        self.assertEqual(formatted["Other"]["count_delta_vs_reference_pct"], 30.0)

    def test_can_use_stop_lists_and_returns_context(self):
        result = analyze_formats(
            {
                "test_setup": {"speed": "1250 - 70%"},
                "prework": ["Unattended readiness checklist"],
                "questions": ["Safety"],
                "formats": [
                    {
                        "name": "A",
                        "count": 100,
                        "runtime_minutes": 240,
                        "full_speed": 100,
                        "actual_speed": 80,
                        "staffing": 1,
                        "unplanned_stops": [{"minute": 30}],
                        "planned_stops": [],
                    }
                ],
            }
        )
        self.assertEqual(result["run_context"]["test_setup"]["speed"], "1250 - 70%")
        self.assertEqual(result["formats"][0]["unplanned_mtbt_minutes"], 240.0)
        self.assertIsNone(result["formats"][0]["planned_mtbt_minutes"])


if __name__ == "__main__":
    unittest.main()
