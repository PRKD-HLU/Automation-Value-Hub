# Data Dictionary

## Automation Register

| Pole SharePoint | Nazwa techniczna | Znaczenie |
|---|---|---|
| Automation Name | `automation_name` | Czytelna nazwa automatyzacji. |
| Automation ID | `automation_id` | Stały, unikalny identyfikator, np. `AUT-001`. |
| Process Name | `process_name` | Proces biznesowy wspierany przez automatyzację. |
| Technology | `technology` | Główna technologia, np. Power Automate albo VBA. |
| Frequency | `frequency` | Częstotliwość procesu. |
| Expected Runs per Month | `expected_runs_per_month` | Oczekiwana liczba biznesowych wykonań w miesiącu. |
| Execution Mode | `execution_mode` | Attended, Semi-attended albo Unattended. |
| Manual Active Minutes per Run | `manual_active_minutes` | Aktywny czas użytkownika przed automatyzacją. |
| Automated Active Minutes per Run | `automated_active_minutes` | Aktywny czas użytkownika po automatyzacji. |
| Machine Runtime | `machine_runtime_minutes` | Techniczny czas pracy automatyzacji. |
| Owner | `owner` | Właściciel techniczny lub procesowy. |
| Baseline Method | `baseline_method` | Measured, Reconstructed, Estimated albo Not Available. |
| Status | `status` | Prototype, Testing, Production, Paused albo Retired. |
| Requires Validation | `requires_validation` | Czy wynik wymaga biznesowej walidacji. |

## Automation Performance & Maintenance

| Pole SharePoint | Nazwa techniczna | Znaczenie |
|---|---|---|
| Record Key | `record_key` | `Automation ID + miesiąc`, np. `AUT-001-2026-08`. |
| Automation ID | `automation_id` | Klucz do Automation Register. |
| Reporting Month | `reporting_month` | Pierwszy dzień miesiąca raportowego. |
| Clean Success Runs | `clean_success_runs` | Procesy zakończone poprawnie za pierwszym razem. |
| Completed with Rework | `completed_with_rework_runs` | Procesy zakończone po poprawce lub retry. |
| Failed Runs | `failed_runs` | Procesy bez poprawnego finalnego rezultatu. |
| Retry Count | `retry_count` | Dodatkowe techniczne uruchomienia. |
| Rework Minutes | `rework_minutes` | Dodatkowy czas potrzebny do zakończenia konkretnego wykonania. |
| Maintenance Minutes | `maintenance_minutes` | Czas poświęcony na zmianę lub naprawę automatyzacji. |
| Validation Status | `validation_status` | Passed, Passed with Issues, Failed, Not Required albo Not Reported. |
| Comment | `comment` | Wyjaśnienie reworku, maintenance albo failure. |
| Records Processed | `records_processed` | Opcjonalny wolumen do analiz wydajności i ML. |

## Pola wyliczane przez Python

- `actual_process_runs`
- `completed_runs`
- `first_pass_success_rate`
- `completion_rate`
- `failure_rate`
- `rework_rate`
- `retry_rate`
- `execution_rate`
- `gross_saved_minutes`
- `net_saved_minutes`
- `maintenance_ratio`
- `health_status`
- `health_reason`
- `data_quality_status`
