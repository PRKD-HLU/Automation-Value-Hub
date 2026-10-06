import pandas as pd

from src.health_status import assign_health_status


THRESHOLDS = {
    "health_status": {
        "monitor_maintenance_ratio": 0.25,
        "action_maintenance_ratio": 0.50,
        "action_when_failed_runs_above": 0,
        "action_when_net_saved_minutes_at_or_below": 0,
        "monitor_when_execution_rate_below": 1.0,
    }
}


def test_rework_results_in_monitor() -> None:
    data = pd.DataFrame(
        [
            {
                "manual_minutes_used": 120,
                "automated_minutes_used": 5,
                "actual_process_runs": 1,
                "failed_runs": 0,
                "validation_status": "Passed with Issues",
                "net_saved_minutes": 105,
                "maintenance_ratio": 0,
                "completed_with_rework_runs": 1,
                "retry_count": 1,
                "execution_rate": 1,
            }
        ]
    )
    result = assign_health_status(data, THRESHOLDS)
    assert result.iloc[0]["health_status"] == "Monitor"


def test_failure_results_in_action_required() -> None:
    data = pd.DataFrame(
        [
            {
                "manual_minutes_used": 120,
                "automated_minutes_used": 5,
                "actual_process_runs": 1,
                "failed_runs": 1,
                "validation_status": "Failed",
                "net_saved_minutes": -10,
                "maintenance_ratio": 0.6,
                "completed_with_rework_runs": 0,
                "retry_count": 1,
                "execution_rate": 1,
            }
        ]
    )
    result = assign_health_status(data, THRESHOLDS)
    assert result.iloc[0]["health_status"] == "Action Required"
