# proj

Production-line format analysis for dynamic runs.

## What it checks

For each format, the tool evaluates:
- Speed ratio (`actual_speed / full_speed`) against target **>= 70%**
- Staffing ratio (`staffing / baseline_staffing`) against target **<= 25%**
- Unplanned MTBT (`runtime_minutes / unplanned_touches`) against target **> 120 min**
- Planned MTBT (`runtime_minutes / planned_touches`) against target **< 60 min**

It also:
- Compares each format count vs. a reference format (optional)
- Recommends the primary test metric based on the weakest pass-rate bottleneck
- Lists formats that pass all targets
- Carries run-planning context (`test_setup`, `prework`, `questions`) from your format sheet

## Usage

```bash
python analysis.py --input /path/to/input.json
```

Input example:

```json
{
  "baseline_staffing": 4,
  "reference_format": "Format-A",
  "test_setup": {
    "setup": "Single milk man; multiple observers",
    "limitations": "No C/O, no manual palletization",
    "speed": "1250 - 70%"
  },
  "prework": ["Unattended readiness checklist", "BR information sharing"],
  "questions": ["Detailed financials", "Safety"],
  "formats": [
    {
      "name": "Format-A",
      "count": 1000,
      "runtime_minutes": 480,
      "full_speed": 100,
      "actual_speed": 72,
      "staffing": 1,
      "unplanned_touches": 3,
      "planned_touches": 10
    },
    {
      "name": "Format-B",
      "count": 850,
      "runtime_minutes": 480,
      "full_speed": 100,
      "actual_speed": 68,
      "staffing": 1,
      "unplanned_stops": [{"minute": 45}, {"minute": 210}],
      "planned_stops": [{"minute": 120}]
    }
  ]
}
```

Notes:
- For touches, you can provide either `*_touches` counts or `*_stops` lists.
- Infinite MTBT values (no touches/stops in a period) are returned as `null` in JSON output.
