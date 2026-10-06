from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.io_utils import write_json


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_manifest(
    *,
    reporting_month: str,
    calculation_version: str,
    status: str,
    register_rows: int,
    performance_rows: int,
    kpi_rows: int,
    issues: pd.DataFrame,
    published: bool,
    input_files: list[Path],
    output_files: list[Path],
    output_path: Path,
    started_at: datetime,
) -> dict:
    finished_at = datetime.now(timezone.utc)
    payload = {
        "pipeline_run_id": f"RUN-{finished_at.strftime('%Y%m%d-%H%M%S')}",
        "reporting_month": reporting_month,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "status": status,
        "calculation_version": calculation_version,
        "source_rows": {
            "automation_register": register_rows,
            "performance_maintenance": performance_rows,
        },
        "output_rows": {
            "automation_kpi": kpi_rows,
            "data_quality_issues": int(len(issues)),
        },
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
        "published": published,
        "input_files": [
            {
                "path": str(path),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for path in input_files
        ],
        "output_files": [
            {
                "path": str(path),
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for path in output_files
        ],
    }
    write_json(output_path, payload)
    return payload
