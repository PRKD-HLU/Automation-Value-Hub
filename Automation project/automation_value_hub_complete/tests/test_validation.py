import pandas as pd

from src.validate_data import validate_source_data


THRESHOLDS = {
    "validation": {
        "valid_validation_statuses": [
            "Passed",
            "Passed with Issues",
            "Failed",
            "Not Required",
            "Not Reported",
        ],
        "require_comment_when_maintenance_minutes_above": 0,
        "require_comment_when_rework_minutes_above": 0,
        "require_first_day_of_month": True,
        "warning_if_baseline_method_missing": True,
        "warning_if_passed_status_with_rework": True,
    }
}


def _register() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "automation_name": "Test",
                "automation_id": "AUT-001",
                "process_name": "Process",
                "technology": "Power Automate",
                "frequency": "Monthly",
                "expected_runs_per_month": 1,
                "execution_mode": "Unattended",
                "manual_active_minutes": 60,
                "automated_active_minutes": 5,
                "machine_runtime_minutes": 10,
                "owner": "Owner",
                "baseline_method": "Measured",
                "status": "Production",
                "requires_validation": True,
                "logging_start_date": pd.NaT,
            }
        ]
    )


def test_duplicate_key_is_blocking_error() -> None:
    performance = pd.DataFrame(
        [
            {
                "record_key": "AUT-001-2026-08",
                "automation_id": "AUT-001",
                "reporting_month": pd.Timestamp("2026-08-01"),
                "clean_success_runs": 1,
                "completed_with_rework_runs": 0,
                "failed_runs": 0,
                "retry_count": 0,
                "rework_minutes": 0,
                "maintenance_minutes": 0,
                "validation_status": "Passed",
                "comment": "",
                "records_processed": None,
            },
            {
                "record_key": "AUT-001-2026-08",
                "automation_id": "AUT-001",
                "reporting_month": pd.Timestamp("2026-08-01"),
                "clean_success_runs": 1,
                "completed_with_rework_runs": 0,
                "failed_runs": 0,
                "retry_count": 0,
                "rework_minutes": 0,
                "maintenance_minutes": 0,
                "validation_status": "Passed",
                "comment": "",
                "records_processed": None,
            },
        ]
    )
    issues = validate_source_data(_register(), performance, THRESHOLDS)
    duplicate = issues[issues["rule_code"] == "DUPLICATE_RECORD_KEY"]
    assert not duplicate.empty
    assert duplicate["is_blocking"].all()


def test_rework_without_comment_and_passed_status_create_warnings() -> None:
    performance = pd.DataFrame(
        [
            {
                "record_key": "AUT-001-2026-08",
                "automation_id": "AUT-001",
                "reporting_month": pd.Timestamp("2026-08-01"),
                "clean_success_runs": 0,
                "completed_with_rework_runs": 1,
                "failed_runs": 0,
                "retry_count": 1,
                "rework_minutes": 10,
                "maintenance_minutes": 0,
                "validation_status": "Passed",
                "comment": "",
                "records_processed": None,
            }
        ]
    )
    issues = validate_source_data(_register(), performance, THRESHOLDS)
    codes = set(issues["rule_code"])
    assert "REWORK_WITHOUT_COMMENT" in codes
    assert "REWORK_WITH_PASSED_STATUS" in codes
