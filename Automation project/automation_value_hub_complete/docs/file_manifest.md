# File Manifest

## Root

| File | Purpose |
|---|---|
| `README.md` | Main Polish setup and usage guide. |
| `main.py` | Pipeline entry point. Loads data, validates, calculates KPI, generates outputs and manifest. |
| `requirements.txt` | Dependencies required for the working prototype. |
| `requirements-ml.txt` | Optional dependencies for the later ML stage. |
| `pytest.ini` | Pytest configuration. |
| `.gitignore` | Excludes real company data, generated reports, logs and local environments from Git. |
| `run_pipeline.ps1` | Windows PowerShell runner. |
| `run_pipeline.bat` | Windows Command Prompt runner. |
| `project_manifest.json` | Machine-readable description of the project architecture. |

## `config/`

| File | Purpose |
|---|---|
| `settings.yaml` | Input paths, output folders, project version and publication settings. |
| `column_mapping.yaml` | Maps SharePoint display names to stable Python column names. |
| `thresholds.yaml` | Health, validation, alert and ML readiness thresholds. |

## `data/input/`

| File | Purpose |
|---|---|
| `Automation Register.csv` | Real export supplied by the user. |
| `Automation Performance & Maintenance.csv` | Real monthly performance export supplied by the user. |
| `README.md` | Rules for replacing the exports in later months. |

## `data/processed/`

| File | Purpose |
|---|---|
| `automation_kpi.csv` | Main Power BI-ready dataset with all calculated KPI and statuses. |
| `portfolio_monthly_summary.csv` | Portfolio-level monthly aggregation. |
| `data_quality_issues.csv` | One row per validation error, warning or information item. |
| `ml_readiness.json` | Honest readiness assessment for anomaly detection, forecasting, classification and regression. |

## `data/templates/`

| File | Purpose |
|---|---|
| `Automation_Value_Hub_Input_Templates.xlsx` | Two formatted input templates with dropdowns, validation and automatic Record Key formulas. |

## `src/`

| File | Purpose |
|---|---|
| `__init__.py` | Marks `src` as a Python package. |
| `exceptions.py` | Project-specific exceptions. |
| `io_utils.py` | YAML, JSON and text I/O helpers. |
| `load_data.py` | Reads CSV/XLSX, maps headers and converts data types. |
| `validate_data.py` | Source and calculated data-quality rules. |
| `calculate_kpis.py` | KPI engine and portfolio monthly aggregation. |
| `health_status.py` | Transparent Health Status rules with explanations. |
| `ml_readiness.py` | Checks whether enough history exists for ML use cases. |
| `ml_models.py` | Optional future Isolation Forest and forecast functions; disabled by readiness gates. |
| `generate_charts.py` | Generates separate PNG charts using Matplotlib. |
| `prepare_ai_context.py` | Creates validated JSON and a deterministic monthly summary. |
| `generate_excel.py` | Produces the formatted monthly Excel report with formulas and charts. |
| `manifest.py` | Creates an auditable run manifest with file hashes. |

## `tests/`

| File | Purpose |
|---|---|
| `test_load_data.py` | Tests SharePoint export header mapping. |
| `test_kpis.py` | Tests clean-success and rework KPI calculations. |
| `test_validation.py` | Tests blocking duplicate checks and warning rules. |
| `test_health_status.py` | Tests Monitor and Action Required logic. |
| `test_ml_readiness.py` | Verifies that the current prototype is not falsely declared ML-ready. |
| `test_ml_models.py` | Verifies that forecasting refuses insufficient history. |

## `reports/`

| File | Purpose |
|---|---|
| `Automation_Value_Hub_Report_2026-08.xlsx` | Monthly management report generated from the supplied CSV files. |
| `README.md` | Report folder description. |

## `charts/`

| File | Purpose |
|---|---|
| `net_saved_hours_by_automation.png` | Net value comparison by automation. |
| `gross_vs_net_savings.png` | Shows the effect of rework and maintenance. |
| `health_status_distribution.png` | Distribution of Healthy, Monitor and other statuses. |
| `data_quality_issues_by_severity.png` | Count of errors, warnings and information items. |

## `ai/`

| File | Purpose |
|---|---|
| `automation_ai_context_2026-08.json` | Validated structured input for an approved AI tool. |
| `monthly_summary_example_2026-08.md` | Deterministic factual summary generated without an external AI call. |
| `ai_prompt_template.txt` | Prompt that instructs AI to describe rather than recalculate results. |

## `powerbi/`

| File | Purpose |
|---|---|
| `README.md` | Power BI import and dashboard instructions. |
| `measures.dax` | Ready-to-copy weighted DAX measures. |

## `logs/`

| File | Purpose |
|---|---|
| `pipeline_2026-08.log` | Human-readable pipeline log. |
| `pipeline_manifest_2026-08.json` | Run status, counts, hashes, warnings and published files. |

## `models/`

| File | Purpose |
|---|---|
| `README.md` | Explains why no model is stored yet and how the folder will be used later. |

## `docs/`

| File | Purpose |
|---|---|
| `data_dictionary.md` | Business and technical definitions for source and derived fields. |
| `methodology.md` | KPI formulas, time definitions and publication rules. |
| `sharepoint_setup.md` | Recommended list columns and valid values. |
| `roadmap.md` | Prototype, automation and ML rollout stages. |
| `prototype_demo_script.md` | Suggested manager demo sequence. |
| `ml_usage.md` | Optional ML installation and usage instructions. |
| `file_manifest.md` | This file. |
