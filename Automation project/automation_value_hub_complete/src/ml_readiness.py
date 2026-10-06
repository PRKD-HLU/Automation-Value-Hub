from __future__ import annotations

import pandas as pd


def assess_ml_readiness(kpis: pd.DataFrame, thresholds: dict) -> dict:
    """Assess whether the collected history is sufficient for planned ML use cases."""
    settings = thresholds.get("ml_readiness", {})

    rows = int(len(kpis))
    automations = int(kpis["automation_id"].nunique()) if rows else 0
    months = int(pd.to_datetime(kpis["reporting_month"]).nunique()) if rows else 0
    positive_cases = int(
        (
            kpis["failed_runs"].fillna(0).gt(0)
            | kpis["completed_with_rework_runs"].fillna(0).gt(0)
            | kpis["retry_count"].fillna(0).gt(0)
        ).sum()
    ) if rows else 0
    rows_with_volume = int(kpis["records_processed"].notna().sum()) if rows else 0

    anomaly_ready = (
        rows >= int(settings.get("anomaly_detection_min_rows", 30))
        and months >= int(settings.get("anomaly_detection_min_months", 6))
    )
    forecast_ready = months >= int(settings.get("forecast_min_months", 6))
    classification_ready = (
        rows >= int(settings.get("classification_min_rows", 50))
        and positive_cases
        >= int(settings.get("classification_min_positive_cases", 10))
    )
    regression_ready = rows_with_volume >= int(
        settings.get("regression_min_rows_with_volume", 10)
    )

    return {
        "dataset": {
            "automation_month_rows": rows,
            "automations": automations,
            "months": months,
            "problem_or_rework_cases": positive_cases,
            "rows_with_records_processed": rows_with_volume,
        },
        "use_cases": {
            "anomaly_detection": {
                "ready": anomaly_ready,
                "reason": "Sufficient portfolio history is available."
                if anomaly_ready
                else "Collect more automation-month rows and at least six reporting months.",
            },
            "portfolio_forecast": {
                "ready": forecast_ready,
                "reason": "Sufficient monthly history is available."
                if forecast_ready
                else "Collect at least six reporting months before publishing a forecast.",
            },
            "failure_risk_classification": {
                "ready": classification_ready,
                "reason": "Sufficient labelled cases are available."
                if classification_ready
                else "Collect more rows and more examples of failure, rework or retry.",
            },
            "manual_time_regression": {
                "ready": regression_ready,
                "reason": "Sufficient volume observations are available."
                if regression_ready
                else "Add Records Processed and measured manual-time observations for more runs.",
            },
        },
        "recommendation": (
            "Use transparent rules and descriptive statistics in the prototype. "
            "Start ML only when the relevant readiness condition becomes true."
        ),
    }
