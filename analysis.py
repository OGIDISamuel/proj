from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from typing import Any

DEFAULT_TARGETS = {
    "speed_ratio_min": 0.70,
    "staffing_ratio_max": 0.25,
    "unplanned_mtbt_min": 120.0,
    "planned_mtbt_max": 60.0,
}


@dataclass(frozen=True)
class FormatMetrics:
    name: str
    count: float
    runtime_minutes: float
    speed_ratio: float
    staffing_ratio: float
    unplanned_mtbt_minutes: float
    planned_mtbt_minutes: float
    passes_speed: bool
    passes_staffing: bool
    passes_unplanned_mtbt: bool
    passes_planned_mtbt: bool

    @property
    def passes_all(self) -> bool:
        return (
            self.passes_speed
            and self.passes_staffing
            and self.passes_unplanned_mtbt
            and self.passes_planned_mtbt
        )


def _safe_mtbt(runtime_minutes: float, touches: float) -> float:
    if touches <= 0:
        return math.inf
    return runtime_minutes / touches


def _require_non_negative(row: dict[str, Any], key: str) -> float:
    value = float(row.get(key, 0))
    if value < 0:
        raise ValueError(f"{key} must be >= 0 for format '{row.get('name', '<unknown>')}'")
    return value


def calculate_format_metrics(
    row: dict[str, Any],
    baseline_staffing: float,
    targets: dict[str, float],
) -> FormatMetrics:
    name = str(row["name"])
    count = _require_non_negative(row, "count")
    runtime_minutes = _require_non_negative(row, "runtime_minutes")
    if runtime_minutes <= 0:
        raise ValueError(f"runtime_minutes must be > 0 for format '{name}'")

    full_speed = _require_non_negative(row, "full_speed")
    actual_speed = _require_non_negative(row, "actual_speed")
    staffing = _require_non_negative(row, "staffing")
    unplanned_touches = _require_non_negative(row, "unplanned_touches")
    planned_touches = _require_non_negative(row, "planned_touches")

    speed_ratio = 0.0 if full_speed == 0 else actual_speed / full_speed
    staffing_ratio = 0.0 if baseline_staffing == 0 else staffing / baseline_staffing
    unplanned_mtbt = _safe_mtbt(runtime_minutes, unplanned_touches)
    planned_mtbt = _safe_mtbt(runtime_minutes, planned_touches)

    return FormatMetrics(
        name=name,
        count=count,
        runtime_minutes=runtime_minutes,
        speed_ratio=speed_ratio,
        staffing_ratio=staffing_ratio,
        unplanned_mtbt_minutes=unplanned_mtbt,
        planned_mtbt_minutes=planned_mtbt,
        passes_speed=speed_ratio >= targets["speed_ratio_min"],
        passes_staffing=staffing_ratio <= targets["staffing_ratio_max"],
        passes_unplanned_mtbt=unplanned_mtbt > targets["unplanned_mtbt_min"],
        passes_planned_mtbt=planned_mtbt < targets["planned_mtbt_max"],
    )


def recommend_primary_metric(metrics: list[FormatMetrics]) -> str:
    if not metrics:
        return "unplanned_mtbt"

    pass_rates = {
        "speed_ratio": sum(m.passes_speed for m in metrics) / len(metrics),
        "staffing_ratio": sum(m.passes_staffing for m in metrics) / len(metrics),
        "unplanned_mtbt": sum(m.passes_unplanned_mtbt for m in metrics) / len(metrics),
        "planned_mtbt": sum(m.passes_planned_mtbt for m in metrics) / len(metrics),
    }
    priority = ["unplanned_mtbt", "speed_ratio", "staffing_ratio", "planned_mtbt"]
    return min(pass_rates, key=lambda metric: (pass_rates[metric], priority.index(metric)))


def analyze_formats(payload: dict[str, Any]) -> dict[str, Any]:
    baseline_staffing = float(payload.get("baseline_staffing", 4))
    targets = {**DEFAULT_TARGETS, **payload.get("targets", {})}
    formats = payload.get("formats", [])
    if not formats:
        raise ValueError("payload must include a non-empty 'formats' list")

    metrics = [calculate_format_metrics(row, baseline_staffing, targets) for row in formats]

    reference_name = payload.get("reference_format")
    reference_count = None
    if reference_name:
        for m in metrics:
            if m.name == reference_name:
                reference_count = m.count
                break

    metrics_payload = []
    for m in metrics:
        item = {
            "name": m.name,
            "count": m.count,
            "runtime_minutes": m.runtime_minutes,
            "speed_ratio": round(m.speed_ratio, 4),
            "staffing_ratio": round(m.staffing_ratio, 4),
            "unplanned_mtbt_minutes": m.unplanned_mtbt_minutes,
            "planned_mtbt_minutes": m.planned_mtbt_minutes,
            "passes": {
                "speed_ratio": m.passes_speed,
                "staffing_ratio": m.passes_staffing,
                "unplanned_mtbt": m.passes_unplanned_mtbt,
                "planned_mtbt": m.passes_planned_mtbt,
                "all_targets": m.passes_all,
            },
        }
        if reference_count is not None:
            item["count_delta_vs_reference_pct"] = round(
                ((m.count - reference_count) / reference_count) * 100, 2
            ) if reference_count else 0.0
        metrics_payload.append(item)

    candidates = [m for m in metrics if m.passes_all]
    candidates.sort(key=lambda m: (-m.unplanned_mtbt_minutes, m.planned_mtbt_minutes, -m.count))

    return {
        "targets": targets,
        "primary_metric_for_test": recommend_primary_metric(metrics),
        "formats": metrics_payload,
        "recommended_formats": [m.name for m in candidates],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze production-line formats against speed/staffing/MTBT targets"
    )
    parser.add_argument("--input", required=True, help="Path to JSON input payload")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        payload = json.load(f)

    result = analyze_formats(payload)
    print(json.dumps(result, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
