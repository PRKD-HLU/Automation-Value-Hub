from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def _month_data(kpis: pd.DataFrame, reporting_month: str) -> pd.DataFrame:
    month = pd.Timestamp(f"{reporting_month}-01")
    return kpis[pd.to_datetime(kpis["reporting_month"]) == month].copy()


def generate_charts(
    kpis: pd.DataFrame,
    issues: pd.DataFrame,
    output_dir: Path,
    reporting_month: str,
) -> dict[str, Path]:
    """Generate separate PNG charts for the monthly report and SharePoint library."""
    output_dir.mkdir(parents=True, exist_ok=True)
    monthly = _month_data(kpis, reporting_month)
    paths: dict[str, Path] = {}

    if not monthly.empty:
        monthly = monthly.sort_values("net_saved_hours", ascending=False)

        path = output_dir / "net_saved_hours_by_automation.png"
        fig, ax = plt.subplots(figsize=(10, 5.5))
        bars = ax.bar(monthly["automation_name"], monthly["net_saved_hours"])
        ax.set_title(f"Net saved hours by automation - {reporting_month}")
        ax.set_ylabel("Hours")
        ax.tick_params(axis="x", rotation=25)
        ax.bar_label(bars, fmt="%.2f", padding=3)
        fig.tight_layout()
        fig.savefig(path, dpi=170, bbox_inches="tight")
        plt.close(fig)
        paths["net_saved_hours"] = path

        path = output_dir / "gross_vs_net_savings.png"
        fig, ax = plt.subplots(figsize=(10, 5.5))
        positions = range(len(monthly))
        width = 0.36
        ax.bar(
            [position - width / 2 for position in positions],
            monthly["gross_saved_hours"],
            width=width,
            label="Gross saved hours",
        )
        ax.bar(
            [position + width / 2 for position in positions],
            monthly["net_saved_hours"],
            width=width,
            label="Net saved hours",
        )
        ax.set_xticks(list(positions), monthly["automation_name"], rotation=25)
        ax.set_ylabel("Hours")
        ax.set_title(f"Gross versus net savings - {reporting_month}")
        ax.legend()
        fig.tight_layout()
        fig.savefig(path, dpi=170, bbox_inches="tight")
        plt.close(fig)
        paths["gross_vs_net"] = path

        path = output_dir / "health_status_distribution.png"
        status_order = [
            "Healthy",
            "Monitor",
            "Action Required",
            "Insufficient Data",
        ]
        counts = monthly["health_status"].value_counts().reindex(status_order, fill_value=0)
        fig, ax = plt.subplots(figsize=(8.5, 5.2))
        bars = ax.bar(counts.index, counts.values)
        ax.set_title(f"Automation health status - {reporting_month}")
        ax.set_ylabel("Automations")
        ax.tick_params(axis="x", rotation=20)
        ax.bar_label(bars, padding=3)
        fig.tight_layout()
        fig.savefig(path, dpi=170, bbox_inches="tight")
        plt.close(fig)
        paths["health_status"] = path

    path = output_dir / "data_quality_issues_by_severity.png"
    severity_order = ["Error", "Warning", "Info"]
    if issues.empty:
        counts = pd.Series([0, 0, 0], index=severity_order)
    else:
        counts = issues["severity"].value_counts().reindex(severity_order, fill_value=0)
    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    bars = ax.bar(counts.index, counts.values)
    ax.set_title("Data-quality issues by severity")
    ax.set_ylabel("Issues")
    ax.bar_label(bars, padding=3)
    fig.tight_layout()
    fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)
    paths["data_quality"] = path

    return paths
