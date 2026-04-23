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

## Usage

```bash
python /home/runner/work/proj/proj/analysis.py --input /path/to/input.json
```

Input example:

```json
{
  "baseline_staffing": 4,
  "reference_format": "Format-A",
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
    }
  ]
}
```
