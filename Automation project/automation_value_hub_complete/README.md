# Automation Value & Reliability Hub — kompletny prototyp

Projekt zamienia dwie listy SharePoint w zwalidowany zbiór KPI, miesięczny raport Excel, wykresy, dane dla Power BI oraz ustrukturyzowany JSON dla AI.

Python jest centralną warstwą analityczną projektu. Odpowiada za:

- odczyt i standaryzację eksportów z SharePoint,
- kontrolę jakości danych,
- obliczenie oszczędności czasu i wskaźników niezawodności,
- nadanie Health Status,
- ocenę gotowości danych do ML,
- przygotowanie plików dla Power BI,
- wygenerowanie raportu Excel i wykresów,
- przygotowanie kontekstu dla zatwierdzonego narzędzia AI,
- zapis audytowalnego manifestu uruchomienia.

## 1. Dane wejściowe

Projekt korzysta bezpośrednio z przesłanych eksportów:

```text
data/input/Automation Register.csv
data/input/Automation Performance & Maintenance.csv
```

Nazwy kolumn mogą pozostać takie jak w SharePoint. Mapowanie do nazw technicznych znajduje się w:

```text
config/column_mapping.yaml
```

## 2. Instalacja

### PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Command Prompt

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

## 3. Testy

```powershell
pytest
```

## 4. Uruchomienie pipeline'u

```powershell
python main.py --month 2026-08
```

Można też użyć:

```powershell
.\run_pipeline.ps1 -Month 2026-08
```

albo:

```bat
run_pipeline.bat 2026-08
```

## 5. Główne wyniki

```text
data/processed/automation_kpi.csv
data/processed/portfolio_monthly_summary.csv
data/processed/data_quality_issues.csv
data/processed/ml_readiness.json
reports/Automation_Value_Hub_Report_2026-08.xlsx
ai/automation_ai_context_2026-08.json
ai/monthly_summary_example_2026-08.md
logs/pipeline_manifest_2026-08.json
```

## 6. Najważniejsze obliczenia

```text
Actual Process Runs =
Clean Success Runs + Completed with Rework + Failed Runs
```

```text
Completed Runs =
Clean Success Runs + Completed with Rework
```

```text
First-Pass Success Rate =
Clean Success Runs / Actual Process Runs
```

```text
Gross Saved Minutes =
(Manual Active Minutes - Automated Active Minutes) x Completed Runs
```

```text
Net Saved Minutes =
Gross Saved Minutes - Rework Minutes - Maintenance Minutes
```

Machine Runtime jest przechowywany osobno. Nie jest odejmowany od oszczędności użytkownika dla procesów unattended i semi-attended.

## 7. Health Status

- **Healthy** — brak awarii, reworku, retry oraz istotnego kosztu utrzymania.
- **Monitor** — proces zakończył się, ale wystąpił rework, retry, niepełna realizacja planu albo podwyższony maintenance.
- **Action Required** — failure, nieudana walidacja, niedodatnia korzyść netto albo wysoki maintenance ratio.
- **Insufficient Data** — brakuje baseline'u lub miesięcznych danych.

Progi są konfigurowane w `config/thresholds.yaml`.

## 8. Power BI

Pierwszym źródłem Power BI powinien być:

```text
data/processed/automation_kpi.csv
```

Gotowe miary DAX znajdują się w:

```text
powerbi/measures.dax
```

## 9. AI

Python przygotowuje zwalidowany JSON. AI ma opisywać wyniki, a nie je przeliczać.

```text
Python liczy -> AI opisuje -> człowiek zatwierdza
```

Gotowy prompt znajduje się w `ai/ai_prompt_template.txt`.

## 10. Machine Learning

Przy dwóch rekordach model ML nie byłby wiarygodny. Projekt generuje więc `ml_readiness.json`, który jasno wskazuje, kiedy dane będą wystarczające do:

- anomaly detection,
- prognozowania,
- klasyfikacji ryzyka failure,
- regresji czasu manualnego względem wolumenu.

Na etapie prototypu wykorzystywane są transparentne reguły i statystyki opisowe.
