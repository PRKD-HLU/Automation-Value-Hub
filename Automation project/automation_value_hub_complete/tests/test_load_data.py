from pathlib import Path

import pandas as pd

from src.load_data import load_input_data


def test_loads_and_maps_csv_headers(tmp_path: Path) -> None:
    register = pd.DataFrame(
        [
            {
                "Automation Name": "Test",
                "Automation ID": "AUT-001",
                "Process Name": "Process",
                "Technology": "Power Automate",
                "Frequency": "Monthly",
                "Expected Runs per Month": 1,
                "Execution Mode": "Unattended",
                "Manual Active Minutes per Run": 60,
                "Automated Active Minutes per Run": 5,
                "Machine Runtime": 10,
                "Owner": "Owner",
            }
        ]
    )
    performance = pd.DataFrame(
        [
            {
                "Record Key": "AUT-001-2026-08",
                "Automation ID": "AUT-001",
                "Reporting Month": "2026-08-01",
                "Clean Success Runs": 1,
                "Completed with Rework": 0,
                "Failed Runs": 0,
                "Retry Count": 0,
                "Rework Minutes": 0,
                "Maintenance Minutes": 0,
                "Validation Status": "Passed",
            }
        ]
    )
    register_path = tmp_path / "register.csv"
    performance_path = tmp_path / "performance.csv"
    register.to_csv(register_path, index=False, encoding="utf-8-sig")
    performance.to_csv(performance_path, index=False, encoding="utf-8-sig")

    mapped_register, mapped_performance = load_input_data(
        register_path,
        performance_path,
        Path("config/column_mapping.yaml"),
    )

    assert mapped_register.loc[0, "automation_id"] == "AUT-001"
    assert mapped_register.loc[0, "manual_active_minutes"] == 60
    assert mapped_performance.loc[0, "clean_success_runs"] == 1
    assert mapped_performance.loc[0, "validation_status"] == "Passed"
