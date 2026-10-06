from __future__ import annotations

import pandas as pd


STATUS_ORDER = {
    "Healthy": 1,
    "Monitor": 2,
    "Action Required": 3,
    "Insufficient Data": 4,
}


def _evaluate_row(row: pd.Series, thresholds: dict) -> tuple[str, str]:
    settings = thresholds.get("health_status", {})
    monitor_maintenance = float(settings.get("monitor_maintenance_ratio", 0.25))
    action_maintenance = float(settings.get("action_maintenance_ratio", 0.50))
    failed_limit = float(settings.get("action_when_failed_runs_above", 0))
    net_limit = float(settings.get("action_when_net_saved_minutes_at_or_below", 0))
    execution_limit = float(settings.get("monitor_when_execution_rate_below", 1.0))

    missing_baseline = pd.isna(row.get("manual_minutes_used")) or pd.isna(
        row.get("automated_minutes_used")
    )
    no_activity = pd.isna(row.get("actual_process_runs")) or row.get(
        "actual_process_runs", 0
    ) <= 0

    if missing_baseline or no_activity:
        reasons = []
        if missing_baseline:
            reasons.append("manual or automated baseline is missing")
        if no_activity:
            reasons.append("no process run was recorded")
        return "Insufficient Data", "; ".join(reasons)

    action_reasons: list[str] = []
    if row.get("failed_runs", 0) > failed_limit:
        action_reasons.append("failed process run recorded")
    if str(row.get("validation_status", "")) == "Failed":
        action_reasons.append("validation failed")
    if pd.notna(row.get("net_saved_minutes")) and row.get(
        "net_saved_minutes"
    ) <= net_limit:
        action_reasons.append("net time saving is non-positive")
    if pd.notna(row.get("maintenance_ratio")) and row.get(
        "maintenance_ratio"
    ) >= action_maintenance:
        action_reasons.append("maintenance ratio is high")

    if action_reasons:
        return "Action Required", "; ".join(action_reasons)

    monitor_reasons: list[str] = []
    if row.get("completed_with_rework_runs", 0) > 0:
        monitor_reasons.append("process completed with rework")
    if row.get("retry_count", 0) > 0:
        monitor_reasons.append("technical retry recorded")
    if str(row.get("validation_status", "")) == "Passed with Issues":
        monitor_reasons.append("validation passed with issues")
    if pd.notna(row.get("maintenance_ratio")) and row.get(
        "maintenance_ratio"
    ) >= monitor_maintenance:
        monitor_reasons.append("maintenance ratio is elevated")
    if pd.notna(row.get("execution_rate")) and row.get(
        "execution_rate"
    ) < execution_limit:
        monitor_reasons.append("actual runs are below plan")

    if monitor_reasons:
        return "Monitor", "; ".join(dict.fromkeys(monitor_reasons))

    return "Healthy", "no failure, rework, retry or material maintenance issue"


def assign_health_status(kpis: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    """Assign an explainable rule-based Health Status to every automation-month."""
    result = kpis.copy()
    evaluated = result.apply(
        lambda row: _evaluate_row(row, thresholds), axis=1, result_type="expand"
    )
    result["health_status"] = evaluated[0]
    result["health_reason"] = evaluated[1]
    result["health_status_sort"] = result["health_status"].map(STATUS_ORDER)
    return result
