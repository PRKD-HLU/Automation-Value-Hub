from __future__ import annotations

import numpy as np
import pandas as pd


REGISTER_COLUMNS = [
    "automation_id",
    "automation_name",
    "process_name",
    "technology",
    "frequency",
    "expected_runs_per_month",
    "execution_mode",
    "manual_active_minutes",
    "automated_active_minutes",
    "machine_runtime_minutes",
    "owner",
    "baseline_method",
    "status",
    "requires_validation",
    "logging_start_date",
]


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide two Series and return NaN where the denominator is zero or missing."""
    result = numerator.astype(float).div(denominator.astype(float))
    return result.where(denominator.notna() & denominator.ne(0), np.nan)


def _baseline_confidence(method: object) -> str:
    mapping = {
        "Measured": "High",
        "Reconstructed": "Medium",
        "Estimated": "Low",
        "Not Available": "Unknown",
    }
    return mapping.get(str(method), "Unknown")


def calculate_kpis(
    register: pd.DataFrame,
    performance: pd.DataFrame,
) -> pd.DataFrame:
    """Merge source lists and calculate automation value and reliability KPIs."""
    available_register_columns = [
        column for column in REGISTER_COLUMNS if column in register.columns
    ]

    merged = performance.merge(
        register[available_register_columns],
        on="automation_id",
        how="left",
        validate="many_to_one",
    )

    numeric_defaults = {
        "clean_success_runs": 0,
        "completed_with_rework_runs": 0,
        "failed_runs": 0,
        "retry_count": 0,
        "rework_minutes": 0,
        "maintenance_minutes": 0,
    }
    for column, default in numeric_defaults.items():
        merged[column] = merged[column].fillna(default).astype(float)

    merged["reporting_month"] = pd.to_datetime(
        merged["reporting_month"], errors="coerce"
    ).dt.to_period("M").dt.to_timestamp()

    merged["expected_runs_used"] = merged["expected_runs_per_month"]
    merged["manual_minutes_used"] = merged["manual_active_minutes"]
    merged["automated_minutes_used"] = merged["automated_active_minutes"]
    merged["baseline_method_used"] = merged["baseline_method"]
    merged["baseline_confidence"] = merged["baseline_method_used"].map(
        _baseline_confidence
    )

    merged["actual_process_runs"] = (
        merged["clean_success_runs"]
        + merged["completed_with_rework_runs"]
        + merged["failed_runs"]
    )
    merged["completed_runs"] = (
        merged["clean_success_runs"] + merged["completed_with_rework_runs"]
    )

    merged["first_pass_success_rate"] = safe_divide(
        merged["clean_success_runs"], merged["actual_process_runs"]
    )
    merged["completion_rate"] = safe_divide(
        merged["completed_runs"], merged["actual_process_runs"]
    )
    merged["failure_rate"] = safe_divide(
        merged["failed_runs"], merged["actual_process_runs"]
    )
    merged["rework_rate"] = safe_divide(
        merged["completed_with_rework_runs"], merged["actual_process_runs"]
    )
    merged["retry_rate"] = safe_divide(
        merged["retry_count"], merged["actual_process_runs"]
    )
    merged["execution_rate"] = safe_divide(
        merged["actual_process_runs"], merged["expected_runs_used"]
    )

    merged["saved_minutes_per_completed_run"] = (
        merged["manual_minutes_used"] - merged["automated_minutes_used"]
    )
    merged["gross_saved_minutes"] = (
        merged["saved_minutes_per_completed_run"] * merged["completed_runs"]
    )
    merged["gross_saved_hours"] = merged["gross_saved_minutes"] / 60

    merged["net_saved_minutes"] = (
        merged["gross_saved_minutes"]
        - merged["rework_minutes"]
        - merged["maintenance_minutes"]
    )
    merged["net_saved_hours"] = merged["net_saved_minutes"] / 60
    merged["rework_hours"] = merged["rework_minutes"] / 60
    merged["maintenance_hours"] = merged["maintenance_minutes"] / 60
    merged["maintenance_ratio"] = safe_divide(
        merged["maintenance_minutes"], merged["gross_saved_minutes"]
    )

    merged["machine_runtime_total_minutes"] = (
        merged["machine_runtime_minutes"] * merged["actual_process_runs"]
    )
    merged["machine_runtime_total_hours"] = (
        merged["machine_runtime_total_minutes"] / 60
    )

    return merged


def build_portfolio_monthly_summary(kpis: pd.DataFrame) -> pd.DataFrame:
    """Aggregate automation-month results into a portfolio-month dataset."""
    if kpis.empty:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for month, group in kpis.groupby("reporting_month", dropna=False):
        actual_runs = float(group["actual_process_runs"].sum())
        clean_runs = float(group["clean_success_runs"].sum())
        completed_runs = float(group["completed_runs"].sum())
        failed_runs = float(group["failed_runs"].sum())
        expected_runs = float(group["expected_runs_used"].sum())

        rows.append(
            {
                "reporting_month": month,
                "active_automations": int(group["automation_id"].nunique()),
                "expected_runs": expected_runs,
                "actual_process_runs": actual_runs,
                "completed_runs": completed_runs,
                "clean_success_runs": clean_runs,
                "failed_runs": failed_runs,
                "retry_count": float(group["retry_count"].sum()),
                "first_pass_success_rate": clean_runs / actual_runs
                if actual_runs
                else np.nan,
                "completion_rate": completed_runs / actual_runs
                if actual_runs
                else np.nan,
                "failure_rate": failed_runs / actual_runs
                if actual_runs
                else np.nan,
                "execution_rate": actual_runs / expected_runs
                if expected_runs
                else np.nan,
                "gross_saved_hours": float(group["gross_saved_hours"].sum()),
                "net_saved_hours": float(group["net_saved_hours"].sum()),
                "rework_hours": float(group["rework_hours"].sum()),
                "maintenance_hours": float(group["maintenance_hours"].sum()),
                "healthy_count": int((group["health_status"] == "Healthy").sum())
                if "health_status" in group.columns
                else 0,
                "monitor_count": int((group["health_status"] == "Monitor").sum())
                if "health_status" in group.columns
                else 0,
                "action_required_count": int(
                    (group["health_status"] == "Action Required").sum()
                )
                if "health_status" in group.columns
                else 0,
                "insufficient_data_count": int(
                    (group["health_status"] == "Insufficient Data").sum()
                )
                if "health_status" in group.columns
                else 0,
            }
        )

    return pd.DataFrame(rows).sort_values("reporting_month").reset_index(drop=True)
