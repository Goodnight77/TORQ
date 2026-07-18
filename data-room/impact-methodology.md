# Impact Methodology

How the headline numbers are derived. Industry ranges are published; per-plant
estimates are ours and clearly marked.

## Published industry ranges

- Predictive maintenance cuts unplanned downtime by 30-50% and maintenance costs
  by 10-40%.
- Downtime for mid-size plants is commonly valued at hundreds of dollars/minute.

## TORQ estimates

| Metric | Basis |
|--------|-------|
| Time to diagnosis: ~30 min -> < 1 min | Manual lookup time replaced by automated retrieval + reasoning. |
| Dispatch lag: 15-60 min -> instant | Skill-matched routing replaces phone calls. |
| MTTR: 20-30% lower | Diagnosis + dispatch removed from the critical path. |
| Knowledge retention: 100% of logged fixes | Every outcome captured, vs lost at staff turnover. |
| Supervisor admin: ~5 h/week saved | One-tap approval vs authoring/assigning each order. |

## Worked example

A plant with 10 significant faults/week saves ~5 h/week of diagnosis alone. At a
conservative $100/min downtime cost, removing 30 minutes from even half of those
failures avoids about **$78,000/year** of downtime, from a software-only tool.

## Measured live

The dashboard computes these from real work-order timestamps:

- Average time to diagnosis (fault to dispatch)
- Average time to fix (technician-reported)
- Resolution rate
