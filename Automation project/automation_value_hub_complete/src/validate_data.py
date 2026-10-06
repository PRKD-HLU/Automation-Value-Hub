from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


ISSUE_COLUMNS = [
    "issue_id",
    "severity",
    "automation_id",
    "reporting_month",
    "rule_code",
    "field_name",
    "issue_description",
    "is_blocking",
    "detected_at",
]


def _format_month(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    try:
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    except Exception:
        return str(value)


def _issue(
    issues: list[dict[str, object]],
    severity: str,
    rule_code: str,
    description: str,
    *,
    automation_id: object = "",
    reporting_month: object = "",
    field_name: str = "",
    blocking: bool = False,
) -> None:
    issues.append(
        {
            "issue_id": f"DQ-{len(issues) + 1:04d}",
            "severity": severity,
            "automation_id": "" if pd.isna(automation_id) else str(automation_id),
            "reporting_month": _format_month(reporting_month),
            "rule_code": rule_code,
            "field_name": field_name,
            "issue_description": description,
            "is_blocking": bool(blocking),
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def _blank(value: object) -> bool:
    return value is None or pd.isna(value) or not str(value).strip()


def validate_source_data(
    register: pd.DataFrame,
    performance: pd.DataFrame,
    thresholds: dict,
) -> pd.DataFrame:
    """Validate input data before KPI calculations."""
    issues: list[dict[str, object]] = []

    required_register_text = [
        "automation_name",
        "automation_id",
        "process_name",
        "technology",
        "frequency",
        "execution_mode",
        "owner",
    ]
    for column in required_register_text:
        for _, row in register[register[column].isna() | register[column].eq("")].iterrows():
            _issue(
                issues,
                "Error",
                "MISSING_REGISTER_VALUE",
                f"Required register field '{column}' is blank.",
                automation_id=row.get("automation_id", ""),
                field_name=column,
                blocking=True,
            )

    required_performance_fields = [
        "record_key",
        "automation_id",
        "reporting_month",
        "clean_success_runs",
        "completed_with_rework_runs",
        "failed_runs",
        "rework_minutes",
        "maintenance_minutes",
    ]
    for column in required_performance_fields:
        missing = performance[column].isna()
        if performance[column].dtype.name in {"string", "object"}:
            missing = missing | performance[column].astype("string").str.strip().eq("")
        for _, row in performance[missing].iterrows():
            _issue(
                issues,
                "Error",
                "MISSING_PERFORMANCE_VALUE",
                f"Required performance field '{column}' is blank.",
                automation_id=row.get("automation_id", ""),
                reporting_month=row.get("reporting_month", ""),
                field_name=column,
                blocking=True,
            )

    duplicate_register = register[
        register["automation_id"].duplicated(keep=False)
    ]
    for _, row in duplicate_register.iterrows():
        _issue(
            issues,
            "Error",
            "DUPLICATE_AUTOMATION_ID",
            "Automation ID is duplicated in the register.",
            automation_id=row["automation_id"],
            field_name="automation_id",
            blocking=True,
        )

    duplicate_keys = performance[
        performance["record_key"].duplicated(keep=False)
    ]
    for _, row in duplicate_keys.iterrows():
        _issue(
            issues,
            "Error",
            "DUPLICATE_RECORD_KEY",
            "Record Key is duplicated in the monthly performance list.",
            automation_id=row["automation_id"],
            reporting_month=row["reporting_month"],
            field_name="record_key",
            blocking=True,
        )

    duplicate_months = performance[
        performance.duplicated(
            subset=["automation_id", "reporting_month"], keep=False
        )
    ]
    for _, row in duplicate_months.iterrows():
        _issue(
            issues,
            "Error",
            "DUPLICATE_AUTOMATION_MONTH",
            "More than one record exists for the same automation and reporting month.",
            automation_id=row["automation_id"],
            reporting_month=row["reporting_month"],
            blocking=True,
        )

    known_ids = set(register["automation_id"].dropna().astype(str))
    unknown_rows = performance[
        ~performance["automation_id"].astype(str).isin(known_ids)
    ]
    for _, row in unknown_rows.iterrows():
        _issue(
            issues,
            "Error",
            "UNKNOWN_AUTOMATION_ID",
            "Automation ID does not exist in the Automation Register.",
            automation_id=row["automation_id"],
            reporting_month=row["reporting_month"],
            field_name="automation_id",
            blocking=True,
        )

    invalid_months = performance[performance["reporting_month"].isna()]
    for _, row in invalid_months.iterrows():
        _issue(
            issues,
            "Error",
            "INVALID_REPORTING_MONTH",
            "Reporting Month is blank or cannot be parsed as a date.",
            automation_id=row.get("automation_id", ""),
            field_name="reporting_month",
            blocking=True,
        )

    require_first_day = thresholds.get("validation", {}).get(
        "require_first_day_of_month", True
    )
    for _, row in performance[performance["reporting_month"].notna()].iterrows():
        month = pd.Timestamp(row["reporting_month"])
        if require_first_day and month.day != 1:
            _issue(
                issues,
                "Warning",
                "REPORTING_MONTH_NOT_FIRST_DAY",
                "Reporting Month should be stored as the first day of the month.",
                automation_id=row["automation_id"],
                reporting_month=month,
                field_name="reporting_month",
            )

        expected_key = f"{row['automation_id']}-{month.strftime('%Y-%m')}"
        if str(row["record_key"]).strip() != expected_key:
            _issue(
                issues,
                "Warning",
                "RECORD_KEY_MISMATCH",
                f"Record Key should be '{expected_key}'.",
                automation_id=row["automation_id"],
                reporting_month=month,
                field_name="record_key",
            )

    numeric_register = [
        "expected_runs_per_month",
        "manual_active_minutes",
        "automated_active_minutes",
        "machine_runtime_minutes",
    ]
    numeric_performance = [
        "clean_success_runs",
        "completed_with_rework_runs",
        "failed_runs",
        "retry_count",
        "rework_minutes",
        "maintenance_minutes",
        "records_processed",
    ]

    for column in numeric_register:
        for _, row in register[register[column].notna() & register[column].lt(0)].iterrows():
            _issue(
                issues,
                "Error",
                "NEGATIVE_REGISTER_VALUE",
                f"Negative value is not allowed in '{column}'.",
                automation_id=row["automation_id"],
                field_name=column,
                blocking=True,
            )

    for column in numeric_performance:
        for _, row in performance[
            performance[column].notna() & performance[column].lt(0)
        ].iterrows():
            _issue(
                issues,
                "Error",
                "NEGATIVE_PERFORMANCE_VALUE",
                f"Negative value is not allowed in '{column}'.",
                automation_id=row["automation_id"],
                reporting_month=row["reporting_month"],
                field_name=column,
                blocking=True,
            )

    for _, row in register.iterrows():
        automation_id = row["automation_id"]
        if pd.isna(row["expected_runs_per_month"]) or row["expected_runs_per_month"] <= 0:
            _issue(
                issues,
                "Warning",
                "INVALID_EXPECTED_RUNS",
                "Expected Runs per Month should be greater than zero.",
                automation_id=automation_id,
                field_name="expected_runs_per_month",
            )
        if pd.isna(row["manual_active_minutes"]):
            _issue(
                issues,
                "Warning",
                "MISSING_MANUAL_BASELINE",
                "Manual Active Minutes is missing; time savings cannot be calculated.",
                automation_id=automation_id,
                field_name="manual_active_minutes",
            )
        if pd.isna(row["automated_active_minutes"]):
            _issue(
                issues,
                "Warning",
                "MISSING_AUTOMATED_TIME",
                "Automated Active Minutes is missing; time savings cannot be calculated.",
                automation_id=automation_id,
                field_name="automated_active_minutes",
            )
        if (
            pd.notna(row["manual_active_minutes"])
            and pd.notna(row["automated_active_minutes"])
            and row["automated_active_minutes"] > row["manual_active_minutes"]
        ):
            _issue(
                issues,
                "Warning",
                "AUTOMATED_TIME_ABOVE_MANUAL",
                "Automated Active Minutes is greater than Manual Active Minutes.",
                automation_id=automation_id,
                field_name="automated_active_minutes",
            )
        if thresholds.get("validation", {}).get(
            "warning_if_baseline_method_missing", True
        ) and str(row.get("baseline_method", "Not Available")) == "Not Available":
            _issue(
                issues,
                "Info",
                "BASELINE_METHOD_NOT_REPORTED",
                "Baseline Method is not available. Mark the time as Measured, Reconstructed or Estimated when known.",
                automation_id=automation_id,
                field_name="baseline_method",
            )

    valid_statuses = set(
        thresholds.get("validation", {}).get("valid_validation_statuses", [])
    )
    if valid_statuses:
        invalid_statuses = performance[
            ~performance["validation_status"].fillna("").isin(valid_statuses)
        ]
        for _, row in invalid_statuses.iterrows():
            _issue(
                issues,
                "Error",
                "INVALID_VALIDATION_STATUS",
                "Validation Status is not one of the approved values.",
                automation_id=row["automation_id"],
                reporting_month=row["reporting_month"],
                field_name="validation_status",
                blocking=True,
            )

    maintenance_limit = thresholds.get("validation", {}).get(
        "require_comment_when_maintenance_minutes_above", 0
    )
    rework_limit = thresholds.get("validation", {}).get(
        "require_comment_when_rework_minutes_above", 0
    )
    warn_passed_with_rework = thresholds.get("validation", {}).get(
        "warning_if_passed_status_with_rework", True
    )

    register_lookup = register.set_index("automation_id", drop=False)
    for _, row in performance.iterrows():
        automation_id = row["automation_id"]
        month = row["reporting_month"]
        comment_blank = _blank(row.get("comment", ""))

        if pd.notna(row["maintenance_minutes"]) and row["maintenance_minutes"] > maintenance_limit and comment_blank:
            _issue(
                issues,
                "Warning",
                "MAINTENANCE_WITHOUT_COMMENT",
                "Maintenance Minutes is above zero but Comment is blank.",
                automation_id=automation_id,
                reporting_month=month,
                field_name="comment",
            )
        if pd.notna(row["rework_minutes"]) and row["rework_minutes"] > rework_limit and comment_blank:
            _issue(
                issues,
                "Warning",
                "REWORK_WITHOUT_COMMENT",
                "Rework Minutes is above zero but Comment is blank.",
                automation_id=automation_id,
                reporting_month=month,
                field_name="comment",
            )
        if row["validation_status"] == "Not Reported":
            _issue(
                issues,
                "Warning",
                "VALIDATION_NOT_REPORTED",
                "Monthly Validation Status has not been reported.",
                automation_id=automation_id,
                reporting_month=month,
                field_name="validation_status",
            )
        if (
            warn_passed_with_rework
            and pd.notna(row["completed_with_rework_runs"])
            and row["completed_with_rework_runs"] > 0
            and row["validation_status"] == "Passed"
        ):
            _issue(
                issues,
                "Warning",
                "REWORK_WITH_PASSED_STATUS",
                "Completed with Rework is above zero; consider using 'Passed with Issues'.",
                automation_id=automation_id,
                reporting_month=month,
                field_name="validation_status",
            )
        if pd.notna(row["failed_runs"]) and row["failed_runs"] > 0 and row["validation_status"] != "Failed":
            _issue(
                issues,
                "Error",
                "FAILED_RUN_WITHOUT_FAILED_VALIDATION",
                "Failed Runs is above zero but Validation Status is not 'Failed'.",
                automation_id=automation_id,
                reporting_month=month,
                field_name="validation_status",
                blocking=True,
            )

        if automation_id in register_lookup.index:
            requires_validation = bool(register_lookup.loc[automation_id, "requires_validation"])
            if requires_validation and row["validation_status"] == "Not Required":
                _issue(
                    issues,
                    "Warning",
                    "VALIDATION_REQUIRED_BUT_NOT_REQUIRED_STATUS",
                    "The register marks this automation as requiring validation, but the monthly status is 'Not Required'.",
                    automation_id=automation_id,
                    reporting_month=month,
                    field_name="validation_status",
                )

    return pd.DataFrame(issues, columns=ISSUE_COLUMNS)


def validate_calculated_data(kpis: pd.DataFrame) -> pd.DataFrame:
    """Validate derived KPI values after calculations."""
    issues: list[dict[str, object]] = []

    rate_columns = [
        "first_pass_success_rate",
        "completion_rate",
        "failure_rate",
        "rework_rate",
    ]
    for column in rate_columns:
        invalid = kpis[
            kpis[column].notna() & ((kpis[column] < 0) | (kpis[column] > 1))
        ]
        for _, row in invalid.iterrows():
            _issue(
                issues,
                "Error",
                "RATE_OUT_OF_RANGE",
                f"Calculated rate '{column}' is outside the range 0 to 1.",
                automation_id=row["automation_id"],
                reporting_month=row["reporting_month"],
                field_name=column,
                blocking=True,
            )

    for _, row in kpis.iterrows():
        automation_id = row["automation_id"]
        month = row["reporting_month"]
        if row["actual_process_runs"] <= 0:
            _issue(
                issues,
                "Warning",
                "NO_ACTUAL_RUNS",
                "No business process run was recorded for this automation and month.",
                automation_id=automation_id,
                reporting_month=month,
                field_name="actual_process_runs",
            )
        if pd.notna(row["execution_rate"]) and row["execution_rate"] < 1:
            _issue(
                issues,
                "Warning",
                "EXECUTION_BELOW_PLAN",
                "Actual Process Runs is below Expected Runs per Month.",
                automation_id=automation_id,
                reporting_month=month,
                field_name="execution_rate",
            )
        if pd.notna(row["gross_saved_minutes"]) and pd.notna(row["net_saved_minutes"]):
            if row["net_saved_minutes"] > row["gross_saved_minutes"]:
                _issue(
                    issues,
                    "Error",
                    "NET_SAVINGS_ABOVE_GROSS",
                    "Net Saved Minutes cannot be greater than Gross Saved Minutes.",
                    automation_id=automation_id,
                    reporting_month=month,
                    field_name="net_saved_minutes",
                    blocking=True,
                )

    return pd.DataFrame(issues, columns=ISSUE_COLUMNS)
