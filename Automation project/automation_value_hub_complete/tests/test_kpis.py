import pandas as pd

from src.calculate_kpis import calculate_kpis


def _register() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "automation_id": "AUT-001",
                "automation_name": "Clean process",
                "process_name": "Process A",
                "technology": "Power Automate",
                "frequency": "Monthly",
                "expected_runs_per_month": 1,
                "execution_mode": "Unattended",
                "manual_active_minutes": 180,
                "automated_active_minutes": 5,
                "machine_runtime_minutes": 10,
                "owner": "Owner",
                "baseline_method": "Measured",
                "status": "Production",
                "requires_validation": False,
                "logging_start_date": pd.NaT,
            },
            {
                "automation_id": "AUT-002",
                "automation_name": "Rework process",
                "process_name": "Process B",
                "technology": "Power Automate",
                "frequency": "Monthly",
                "expected_runs_per_month": 1,
                "execution_mode": "Unattended",
                "manual_active_minutes": 120,
                "automated_active_minutes": 5,
                "machine_runtime_minutes": 15,
                "owner": "Owner",
                "baseline_method": "Reconstructed",
                "status": "Production",
                "requires_validation": True,
                "logging_start_date": pd.NaT,
            },
        ]
    )


def _performance() -> pd.DataFrame:
    return pd.DataFrame(
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
                "data_source": "Owner Report",
            },
            {
                "record_key": "AUT-002-2026-08",
                "automation_id": "AUT-002",
                "reporting_month": pd.Timestamp("2026-08-01"),
                "clean_success_runs": 0,
                "completed_with_rework_runs": 1,
                "failed_runs": 0,
                "retry_count": 1,
                "rework_minutes": 10,
                "maintenance_minutes": 0,
                "validation_status": "Passed with Issues",
                "comment": "One retry",
                "records_processed": None,
                "data_source": "Owner Report",
            },
        ]
    )


def test_clean_run_calculations() -> None:
    result = calculate_kpis(_register(), _performance())
    row = result[result["automation_id"] == "AUT-001"].iloc[0]
    assert row["actual_process_runs"] == 1
    assert row["first_pass_success_rate"] == 1
    assert row["gross_saved_minutes"] == 175
    assert round(row["net_saved_hours"], 2) == 2.92


def test_rework_run_calculations() -> None:
    result = calculate_kpis(_register(), _performance())
    row = result[result["automation_id"] == "AUT-002"].iloc[0]
    assert row["actual_process_runs"] == 1
    assert row["completion_rate"] == 1
    assert row["first_pass_success_rate"] == 0
    assert row["gross_saved_minutes"] == 115
    assert row["net_saved_minutes"] == 105
    assert round(row["net_saved_hours"], 2) == 1.75
