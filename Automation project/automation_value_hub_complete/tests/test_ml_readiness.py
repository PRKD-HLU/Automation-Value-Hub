import pandas as pd

from src.ml_readiness import assess_ml_readiness


def test_small_prototype_is_not_ml_ready() -> None:
    kpis = pd.DataFrame(
        [
            {
                "automation_id": "AUT-001",
                "reporting_month": pd.Timestamp("2026-08-01"),
                "failed_runs": 0,
                "completed_with_rework_runs": 0,
                "retry_count": 0,
                "records_processed": None,
            },
            {
                "automation_id": "AUT-002",
                "reporting_month": pd.Timestamp("2026-08-01"),
                "failed_runs": 0,
                "completed_with_rework_runs": 1,
                "retry_count": 1,
                "records_processed": None,
            },
        ]
    )
    thresholds = {
        "ml_readiness": {
            "anomaly_detection_min_rows": 30,
            "anomaly_detection_min_months": 6,
            "forecast_min_months": 6,
            "classification_min_rows": 50,
            "classification_min_positive_cases": 10,
            "regression_min_rows_with_volume": 10,
        }
    }
    result = assess_ml_readiness(kpis, thresholds)
    assert result["use_cases"]["anomaly_detection"]["ready"] is False
    assert result["use_cases"]["portfolio_forecast"]["ready"] is False
