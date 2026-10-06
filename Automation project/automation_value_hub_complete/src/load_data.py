from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.exceptions import DataLoadError
from src.io_utils import read_yaml


REGISTER_REQUIRED = [
    "automation_name",
    "automation_id",
    "process_name",
    "technology",
    "frequency",
    "expected_runs_per_month",
    "execution_mode",
    "manual_active_minutes",
    "automated_active_minutes",
    "owner",
]

PERFORMANCE_REQUIRED = [
    "record_key",
    "automation_id",
    "reporting_month",
    "clean_success_runs",
    "completed_with_rework_runs",
    "failed_runs",
    "rework_minutes",
    "maintenance_minutes",
]

REGISTER_OPTIONAL_DEFAULTS: dict[str, Any] = {
    "machine_runtime_minutes": np.nan,
    "baseline_method": "Not Available",
    "status": "Production",
    "requires_validation": False,
    "logging_start_date": pd.NaT,
}

PERFORMANCE_OPTIONAL_DEFAULTS: dict[str, Any] = {
    "retry_count": 0,
    "validation_status": "Not Reported",
    "comment": "",
    "records_processed": np.nan,
    "data_source": "Owner Report",
}


def _normalise_header(value: object) -> str:
    return " ".join(str(value).replace("\n", " ").split()).strip().casefold()


def _read_tabular_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    suffix = path.suffix.casefold()
    if suffix == ".iqy":
        raise DataLoadError(
            f"{path.name} is an Excel web-query pointer, not a portable data file. "
            "Open it in Excel while signed in to SharePoint and save the loaded rows as CSV UTF-8 or XLSX."
        )
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "utf-8", "cp1250"):
            try:
                return pd.read_csv(path, encoding=encoding, sep=None, engine="python")
            except UnicodeDecodeError:
                continue
        raise DataLoadError(f"Could not decode CSV file: {path.name}")
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return pd.read_excel(path)
    raise DataLoadError(
        f"Unsupported input format: {path.suffix}. Use CSV, XLSX, XLSM or XLS."
    )


def _rename_using_aliases(
    df: pd.DataFrame,
    mapping: dict[str, list[str]],
    dataset_name: str,
) -> pd.DataFrame:
    current_lookup = {_normalise_header(column): column for column in df.columns}
    rename_map: dict[object, str] = {}

    for canonical, aliases in mapping.items():
        for alias in aliases:
            matched = current_lookup.get(_normalise_header(alias))
            if matched is not None:
                rename_map[matched] = canonical
                break

    renamed = df.rename(columns=rename_map).copy()
    duplicates = renamed.columns[renamed.columns.duplicated()].tolist()
    if duplicates:
        raise DataLoadError(
            f"Duplicate mapped columns in {dataset_name}: {duplicates}"
        )
    return renamed


def _assert_required_columns(
    df: pd.DataFrame,
    required: list[str],
    dataset_name: str,
) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise DataLoadError(
            f"Missing required columns in {dataset_name}: {', '.join(missing)}"
        )


def _clean_string_columns(df: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip()


def _clean_numeric_columns(df: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")


def _normalise_boolean(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.casefold()
        .map(
            {
                "true": True,
                "yes": True,
                "1": True,
                "tak": True,
                "false": False,
                "no": False,
                "0": False,
                "nie": False,
            }
        )
        .fillna(False)
        .astype(bool)
    )


def load_input_data(
    register_path: Path,
    performance_path: Path,
    mapping_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load, map and type both source datasets."""
    mapping = read_yaml(mapping_path)

    register = _read_tabular_file(register_path)
    performance = _read_tabular_file(performance_path)

    register = _rename_using_aliases(
        register,
        mapping.get("register", {}),
        "Automation Register",
    )
    performance = _rename_using_aliases(
        performance,
        mapping.get("performance", {}),
        "Automation Performance & Maintenance",
    )

    _assert_required_columns(register, REGISTER_REQUIRED, "Automation Register")
    _assert_required_columns(
        performance,
        PERFORMANCE_REQUIRED,
        "Automation Performance & Maintenance",
    )

    for column, default in REGISTER_OPTIONAL_DEFAULTS.items():
        if column not in register.columns:
            register[column] = default
    for column, default in PERFORMANCE_OPTIONAL_DEFAULTS.items():
        if column not in performance.columns:
            performance[column] = default

    _clean_string_columns(
        register,
        [
            "automation_name",
            "automation_id",
            "process_name",
            "technology",
            "frequency",
            "execution_mode",
            "owner",
            "baseline_method",
            "status",
        ],
    )
    _clean_string_columns(
        performance,
        [
            "record_key",
            "automation_id",
            "validation_status",
            "comment",
            "data_source",
        ],
    )

    _clean_numeric_columns(
        register,
        [
            "expected_runs_per_month",
            "manual_active_minutes",
            "automated_active_minutes",
            "machine_runtime_minutes",
        ],
    )
    _clean_numeric_columns(
        performance,
        [
            "clean_success_runs",
            "completed_with_rework_runs",
            "failed_runs",
            "retry_count",
            "rework_minutes",
            "maintenance_minutes",
            "records_processed",
        ],
    )

    performance["reporting_month"] = pd.to_datetime(
        performance["reporting_month"], errors="coerce"
    )
    register["logging_start_date"] = pd.to_datetime(
        register["logging_start_date"], errors="coerce"
    )
    register["requires_validation"] = _normalise_boolean(
        register["requires_validation"]
    )

    register["source_row_number"] = np.arange(2, len(register) + 2)
    performance["source_row_number"] = np.arange(2, len(performance) + 2)

    return register, performance
