# SharePoint Setup

## Lista 1: Automation Register

Minimalne kolumny:

1. Automation Name
2. Automation ID
3. Process Name
4. Technology
5. Frequency
6. Expected Runs per Month
7. Execution Mode
8. Manual Active Minutes per Run
9. Automated Active Minutes per Run
10. Machine Runtime
11. Owner

Rekomendowane rozszerzenia:

- Baseline Method
- Status
- Requires Validation
- Logging Start Date

`Automation ID` powinno mieć włączone `Enforce unique values`.

## Lista 2: Automation Performance & Maintenance

1. Record Key
2. Automation ID
3. Reporting Month
4. Clean Success Runs
5. Completed with Rework
6. Failed Runs
7. Retry Count
8. Rework Minutes
9. Maintenance Minutes
10. Validation Status
11. Comment
12. Records Processed — opcjonalnie

`Record Key` powinno mieć format `AUT-001-2026-08` i być unikalne.

## Ważna zasada

Jeśli proces został uruchomiony ponownie po korekcie, nadal jest to jedno biznesowe wykonanie:

```text
Clean Success = 0
Completed with Rework = 1
Retry Count = 1
```
