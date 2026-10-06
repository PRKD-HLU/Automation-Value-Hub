# Methodology

## Zasada jednostki analizy

Jeden rekord miesięczny oznacza jedną automatyzację i jeden miesiąc. Kilka makr prowadzących do jednego wyniku biznesowego traktujemy jako jeden proces.

## Czas

- **Manual Active Time** — aktywna praca człowieka przed automatyzacją.
- **Automated Active Time** — aktywna praca człowieka, która pozostała po automatyzacji.
- **Machine Runtime** — czas technicznego działania rozwiązania.
- **Rework** — dodatkowy czas potrzebny do ukończenia konkretnego wykonania.
- **Maintenance** — czas zmiany lub naprawy samego rozwiązania.

## Formuły

```text
Actual Process Runs = Clean Success + Completed with Rework + Failed
Completed Runs = Clean Success + Completed with Rework
First-Pass Success Rate = Clean Success / Actual Process Runs
Completion Rate = Completed Runs / Actual Process Runs
Failure Rate = Failed / Actual Process Runs
Execution Rate = Actual Process Runs / Expected Runs
Gross Saved Minutes = (Manual - Automated) x Completed Runs
Net Saved Minutes = Gross Saved Minutes - Rework - Maintenance
Maintenance Ratio = Maintenance / Gross Saved Minutes
```

## Baseline confidence

- Measured -> High
- Reconstructed -> Medium
- Estimated -> Low
- Not Available -> Unknown

## Publikacja

Błędy blokujące zatrzymują publikację oficjalnego KPI. Warningi i informacje są publikowane wraz z raportem jakości danych.
