# Power BI setup

## Prototype source

Use:

```text
data/processed/automation_kpi.csv
```

Optionally add:

```text
data/processed/portfolio_monthly_summary.csv
data/processed/data_quality_issues.csv
```

## Recommended pages

### Overview

- Active Automations
- Net Saved Hours
- Gross Saved Hours
- First-Pass Success Rate
- Completion Rate
- Failed Runs
- Maintenance Hours
- Health Status distribution

### Automation Details

Add a slicer for Automation Name and display:

- manual and automated time,
- machine runtime,
- clean/rework/failed runs,
- retry count,
- net savings,
- validation and health status.

### Data Quality

Display blocking errors, warnings and information items from `data_quality_issues.csv`.

## Important

Do not use `AVERAGE(first_pass_success_rate)` for a portfolio KPI. Use weighted measures based on the summed run counts.
