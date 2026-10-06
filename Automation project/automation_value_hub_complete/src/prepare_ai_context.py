from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.io_utils import write_json, write_text


def _month_data(kpis: pd.DataFrame, reporting_month: str) -> pd.DataFrame:
    month = pd.Timestamp(f"{reporting_month}-01")
    return kpis[pd.to_datetime(kpis["reporting_month"]) == month].copy()


def build_deterministic_summary(
    context: dict,
) -> str:
    """Create a factual summary without calling an external AI service."""
    summary = context["portfolio_summary"]
    health = context["health_status_summary"]
    data_quality = context["data_quality"]
    attention = context["automations_requiring_attention"]

    lines = [
        f"# Automation Value & Reliability Hub - {context['reporting_month']}",
        "",
        "## Executive Summary",
        (
            f"The prototype covers {summary['active_automations']} automation(s) and "
            f"{summary['actual_process_runs']} recorded business process run(s). "
            f"The portfolio generated {summary['net_saved_hours']:.2f} net saved hours "
            f"after deducting rework and maintenance."
        ),
        "",
        (
            f"First-pass success rate was {summary['first_pass_success_rate']:.1%} and "
            f"completion rate was {summary['completion_rate']:.1%}. "
            f"The data contains {summary['failed_runs']} failed run(s), "
            f"{summary['rework_hours']:.2f} rework hour(s) and "
            f"{summary['maintenance_hours']:.2f} maintenance hour(s)."
        ),
        "",
        "## Health Status",
        (
            f"Healthy: {health.get('Healthy', 0)}, Monitor: {health.get('Monitor', 0)}, "
            f"Action Required: {health.get('Action Required', 0)}, "
            f"Insufficient Data: {health.get('Insufficient Data', 0)}."
        ),
        "",
        "## Automations Requiring Attention",
    ]

    if attention:
        for item in attention:
            lines.append(
                f"- {item['automation_id']} - {item['automation_name']}: "
                f"{item['health_status']} ({item['reason']})."
            )
    else:
        lines.append("- No automation requires attention based on the current rules.")

    lines.extend(
        [
            "",
            "## Data Quality",
            (
                f"Blocking errors: {data_quality['critical_errors']}; "
                f"warnings: {data_quality['warnings']}; information items: "
                f"{data_quality['information_items']}."
            ),
            "",
            "This text is generated deterministically from validated KPI data. "
            "An approved AI tool may later improve the wording, but should not recalculate the figures.",
        ]
    )
    return "\n".join(lines)


def prepare_ai_context(
    kpis: pd.DataFrame,
    issues: pd.DataFrame,
    ml_readiness: dict,
    reporting_month: str,
    json_output_path: Path,
    summary_output_path: Path,
) -> dict:
    """Prepare a compact JSON payload and a deterministic monthly summary."""
    monthly = _month_data(kpis, reporting_month)

    actual_runs = float(monthly["actual_process_runs"].sum())
    clean_runs = float(monthly["clean_success_runs"].sum())
    completed_runs = float(monthly["completed_runs"].sum())

    context = {
        "reporting_month": reporting_month,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "portfolio_summary": {
            "active_automations": int(monthly["automation_id"].nunique()),
            "actual_process_runs": int(actual_runs),
            "completed_runs": int(completed_runs),
            "gross_saved_hours": round(float(monthly["gross_saved_hours"].sum()), 2),
            "net_saved_hours": round(float(monthly["net_saved_hours"].sum()), 2),
            "first_pass_success_rate": round(clean_runs / actual_runs, 4)
            if actual_runs
            else 0.0,
            "completion_rate": round(completed_runs / actual_runs, 4)
            if actual_runs
            else 0.0,
            "failed_runs": int(monthly["failed_runs"].sum()),
            "retry_count": int(monthly["retry_count"].sum()),
            "maintenance_hours": round(
                float(monthly["maintenance_minutes"].sum()) / 60, 2
            ),
            "rework_hours": round(float(monthly["rework_minutes"].sum()) / 60, 2),
        },
        "health_status_summary": {
            status: int(count)
            for status, count in monthly["health_status"].value_counts().items()
        },
        "baseline_method_summary": {
            method: int(count)
            for method, count in monthly["baseline_method_used"].fillna("Not Available").value_counts().items()
        },
        "automations": [
            {
                "automation_id": row["automation_id"],
                "automation_name": row["automation_name"],
                "technology": row["technology"],
                "health_status": row["health_status"],
                "health_reason": row["health_reason"],
                "actual_process_runs": int(row["actual_process_runs"]),
                "net_saved_hours": round(float(row["net_saved_hours"]), 2)
                if pd.notna(row["net_saved_hours"])
                else None,
                "first_pass_success_rate": round(float(row["first_pass_success_rate"]), 4)
                if pd.notna(row["first_pass_success_rate"])
                else None,
                "validation_status": row["validation_status"],
                "data_quality_status": row["data_quality_status"],
            }
            for _, row in monthly.iterrows()
        ],
        "automations_requiring_attention": [
            {
                "automation_id": row["automation_id"],
                "automation_name": row["automation_name"],
                "health_status": row["health_status"],
                "reason": row["health_reason"],
                "net_saved_hours": round(float(row["net_saved_hours"]), 2)
                if pd.notna(row["net_saved_hours"])
                else None,
            }
            for _, row in monthly[
                monthly["health_status"].isin(["Monitor", "Action Required"])
            ].iterrows()
        ],
        "data_quality": {
            "critical_errors": int(
                ((issues["severity"] == "Error") & issues["is_blocking"]).sum()
            )
            if not issues.empty
            else 0,
            "warnings": int((issues["severity"] == "Warning").sum())
            if not issues.empty
            else 0,
            "information_items": int((issues["severity"] == "Info").sum())
            if not issues.empty
            else 0,
            "total_issues": int(len(issues)),
        },
        "ml_readiness": ml_readiness,
        "ai_instructions": [
            "Use only the supplied figures.",
            "Do not invent missing values or root causes.",
            "Do not recalculate KPI values.",
            "Clearly mention estimated or incomplete data.",
            "Separate factual findings from possible interpretations.",
            "Keep the summary concise and suitable for a manager.",
        ],
    }

    write_json(json_output_path, context)
    write_text(summary_output_path, build_deterministic_summary(context))
    return context
