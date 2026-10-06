# ML usage

## Why ML is not active in the prototype

Current data contains two automation-month rows and one month of history. Running a production anomaly or forecast model would create a misleading result.

The pipeline therefore creates:

```text
data/processed/ml_readiness.json
```

## Optional dependencies

```powershell
python -m pip install -r requirements-ml.txt
```

## Isolation Forest

Use only after the readiness gate is met:

```python
from src.ml_models import detect_anomalies_with_isolation_forest

result = detect_anomalies_with_isolation_forest(kpis)
```

## Portfolio forecast

```python
from src.ml_models import forecast_portfolio_net_savings

forecast = forecast_portfolio_net_savings(portfolio_summary, periods=3)
```

Before publishing any forecast, compare it with a simple baseline such as the last value or a three-month rolling mean.
