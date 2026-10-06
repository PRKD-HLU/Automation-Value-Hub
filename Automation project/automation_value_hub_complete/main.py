from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.calculate_kpis import build_portfolio_monthly_summary, calculate_kpis
from src.exceptions import AutomationHubError, BlockingDataQualityError
from src.generate_charts import generate_charts
from src.generate_excel import generate_excel_report
from src.health_status import assign_health_status
from src.io_utils import read_yaml, write_json
from src.load_data import load_input_data
from src.manifest import create_manifest
from src.ml_readiness import assess_ml_readiness
from src.prepare_ai_context import prepare_ai_context
from src.validate_data import ISSUE_COLUMNS, validate_calculated_data, validate_source_data


PROJECT_ROOT = Path(__file__).resolve().parent


def _resolve(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _configure_logging(log_path: Path, level: str = "INFO") -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


def _attach_data_quality_status(
    kpis: pd.DataFrame,
    issues: pd.DataFrame,
) -> pd.DataFrame:
    result = kpis.copy()
    result["data_quality_status"] = "Valid"
    if issues.empty:
        return result

    severity_rank = {"Info": 1, "Warning": 2, "Error": 3}
    rank_to_label = {0: "Valid", 1: "Info", 2: "Warning", 3: "Error"}

    working = issues.copy()
    working["severity_rank"] = working["severity"].map(severity_rank).fillna(0)
    working["issue_month"] = pd.to_datetime(
        working["reporting_month"], errors="coerce"
    )

    automation_level = (
        working[working["issue_month"].isna()]
        .groupby("automation_id", dropna=False)["severity_rank"]
        .max()
        .to_dict()
    )
    monthly_level = (
        working[working["issue_month"].notna()]
        .groupby(["automation_id", "issue_month"], dropna=False)["severity_rank"]
        .max()
        .to_dict()
    )

    statuses: list[str] = []
    for _, row in result.iterrows():
        automation_id = str(row["automation_id"])
        month = pd.Timestamp(row["reporting_month"])
        rank = max(
            int(automation_level.get(automation_id, 0)),
            int(monthly_level.get((automation_id, month), 0)),
        )
        statuses.append(rank_to_label.get(rank, "Valid"))

    result["data_quality_status"] = statuses
    return result


def _ordered_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    preferred = [
        "record_key",
        "automation_id",
        "automation_name",
        "process_name",
        "technology",
        "frequency",
        "owner",
        "status",
        "reporting_month",
        "expected_runs_used",
        "execution_mode",
        "manual_minutes_used",
        "automated_minutes_used",
        "machine_runtime_minutes",
        "baseline_method_used",
        "baseline_confidence",
        "requires_validation",
        "clean_success_runs",
        "completed_with_rework_runs",
        "failed_runs",
        "retry_count",
        "actual_process_runs",
        "completed_runs",
        "records_processed",
        "rework_minutes",
        "maintenance_minutes",
        "validation_status",
        "data_source",
        "comment",
        "first_pass_success_rate",
        "completion_rate",
        "failure_rate",
        "rework_rate",
        "retry_rate",
        "execution_rate",
        "saved_minutes_per_completed_run",
        "gross_saved_minutes",
        "gross_saved_hours",
        "net_saved_minutes",
        "net_saved_hours",
        "maintenance_hours",
        "rework_hours",
        "maintenance_ratio",
        "machine_runtime_total_minutes",
        "machine_runtime_total_hours",
        "health_status",
        "health_status_sort",
        "health_reason",
        "data_quality_status",
        "generated_at",
        "calculation_version",
    ]
    existing = [column for column in preferred if column in df.columns]
    return df[existing].copy()


def run_pipeline(config_path: Path, reporting_month: str | None) -> int:
    started_at = datetime.now(timezone.utc)
    settings = read_yaml(config_path)
    thresholds = read_yaml(PROJECT_ROOT / "config" / "thresholds.yaml")

    month = reporting_month or settings["project"]["default_reporting_month"]
    try:
        pd.Timestamp(f"{month}-01")
    except Exception as exc:
        raise ValueError("Reporting month must use YYYY-MM format.") from exc

    calculation_version = settings["project"]["calculation_version"]
    log_dir = _resolve(settings["output"]["logs_dir"])
    log_path = log_dir / f"pipeline_{month}.log"
    _configure_logging(log_path, settings.get("logging", {}).get("level", "INFO"))

    logging.info("Starting Automation Value Hub pipeline for %s", month)

    register_path = _resolve(settings["input"]["register_file"])
    performance_path = _resolve(settings["input"]["performance_file"])
    mapping_path = PROJECT_ROOT / "config" / "column_mapping.yaml"

    processed_dir = _resolve(settings["output"]["processed_dir"])
    reports_dir = _resolve(settings["output"]["reports_dir"])
    charts_dir = _resolve(settings["output"]["charts_dir"])
    ai_dir = _resolve(settings["output"]["ai_dir"])
    models_dir = _resolve(settings["output"]["models_dir"])

    for directory in [processed_dir, reports_dir, charts_dir, ai_dir, log_dir, models_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    issues_path = processed_dir / "data_quality_issues.csv"
    kpi_path = processed_dir / "automation_kpi.csv"
    portfolio_path = processed_dir / "portfolio_monthly_summary.csv"
    ml_readiness_path = processed_dir / "ml_readiness.json"
    report_path = reports_dir / f"Automation_Value_Hub_Report_{month}.xlsx"
    ai_json_path = ai_dir / f"automation_ai_context_{month}.json"
    ai_summary_path = ai_dir / f"monthly_summary_example_{month}.md"
    manifest_path = log_dir / f"pipeline_manifest_{month}.json"

    register_rows = 0
    performance_rows = 0
    kpi_rows = 0
    issues = pd.DataFrame(columns=ISSUE_COLUMNS)
    output_files: list[Path] = []

    try:
        register, performance = load_input_data(
            register_path,
            performance_path,
            mapping_path,
        )
        register_rows = len(register)
        performance_rows = len(performance)
        logging.info(
            "Loaded %s register row(s) and %s performance row(s)",
            register_rows,
            performance_rows,
        )

        selected_month = pd.Timestamp(f"{month}-01")
        if selected_month not in set(performance["reporting_month"].dropna().dt.to_period("M").dt.to_timestamp()):
            raise ValueError(
                f"No performance record exists for reporting month {month}."
            )

        source_issues = validate_source_data(register, performance, thresholds)
        kpis = calculate_kpis(register, performance)
        calculated_issues = validate_calculated_data(kpis)
        issues = pd.concat([source_issues, calculated_issues], ignore_index=True)
        issues.to_csv(
            issues_path,
            index=False,
            encoding=settings["publication"]["csv_encoding"],
        )
        output_files.append(issues_path)

        blocking_errors = int(
            ((issues["severity"] == "Error") & issues["is_blocking"]).sum()
        ) if not issues.empty else 0
        if blocking_errors and settings["publication"].get(
            "stop_on_blocking_errors", True
        ):
            raise BlockingDataQualityError(
                f"Detected {blocking_errors} blocking data-quality error(s)."
            )

        kpis = assign_health_status(kpis, thresholds)
        kpis = _attach_data_quality_status(kpis, issues)
        kpis["generated_at"] = datetime.now(timezone.utc).isoformat()
        kpis["calculation_version"] = calculation_version
        kpis = _ordered_output_columns(kpis)
        kpi_rows = len(kpis)

        kpis.to_csv(
            kpi_path,
            index=False,
            encoding=settings["publication"]["csv_encoding"],
            date_format="%Y-%m-%d",
        )
        output_files.append(kpi_path)
        logging.info("Published KPI dataset: %s", kpi_path)

        portfolio = build_portfolio_monthly_summary(kpis)
        portfolio.to_csv(
            portfolio_path,
            index=False,
            encoding=settings["publication"]["csv_encoding"],
            date_format="%Y-%m-%d",
        )
        output_files.append(portfolio_path)

        ml_readiness = assess_ml_readiness(kpis, thresholds)
        write_json(ml_readiness_path, ml_readiness)
        output_files.append(ml_readiness_path)

        chart_paths = generate_charts(kpis, issues, charts_dir, month)
        output_files.extend(chart_paths.values())

        ai_context = prepare_ai_context(
            kpis,
            issues,
            ml_readiness,
            month,
            ai_json_path,
            ai_summary_path,
        )
        output_files.extend([ai_json_path, ai_summary_path])

        ai_summary_text = ai_summary_path.read_text(encoding="utf-8")
        generate_excel_report(
            kpis,
            issues,
            chart_paths,
            month,
            ai_summary_text,
            report_path,
        )
        output_files.append(report_path)
        logging.info("Generated Excel report: %s", report_path)

        create_manifest(
            reporting_month=month,
            calculation_version=calculation_version,
            status="SUCCESS",
            register_rows=register_rows,
            performance_rows=performance_rows,
            kpi_rows=kpi_rows,
            issues=issues,
            published=True,
            input_files=[register_path, performance_path],
            output_files=output_files,
            output_path=manifest_path,
            started_at=started_at,
        )
        logging.info("Pipeline completed successfully")
        return 0

    except (AutomationHubError, FileNotFoundError, KeyError, ValueError) as exc:
        logging.exception("Pipeline failed: %s", exc)
        if issues.empty:
            issues = pd.DataFrame(
                [
                    {
                        "issue_id": "DQ-PIPELINE",
                        "severity": "Error",
                        "automation_id": "",
                        "reporting_month": f"{month}-01",
                        "rule_code": "PIPELINE_FAILURE",
                        "field_name": "",
                        "issue_description": str(exc),
                        "is_blocking": True,
                        "detected_at": datetime.now(timezone.utc).isoformat(),
                    }
                ],
                columns=ISSUE_COLUMNS,
            )
            issues.to_csv(issues_path, index=False, encoding="utf-8-sig")
            output_files.append(issues_path)

        create_manifest(
            reporting_month=month,
            calculation_version=calculation_version,
            status="FAILED",
            register_rows=register_rows,
            performance_rows=performance_rows,
            kpi_rows=kpi_rows,
            issues=issues,
            published=False,
            input_files=[register_path, performance_path],
            output_files=output_files,
            output_path=manifest_path,
            started_at=started_at,
        )
        return 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Automation Value & Reliability Hub prototype outputs."
    )
    parser.add_argument(
        "--config",
        default="config/settings.yaml",
        help="Path to the YAML configuration file.",
    )
    parser.add_argument(
        "--month",
        help="Reporting month in YYYY-MM format. Defaults to config value.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    config = _resolve(arguments.config)
    raise SystemExit(run_pipeline(config, arguments.month))
