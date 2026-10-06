import pandas as pd
import pytest

from src.ml_models import forecast_portfolio_net_savings


def test_forecast_refuses_too_little_history() -> None:
    summary = pd.DataFrame(
        {
            "reporting_month": [pd.Timestamp("2026-08-01")],
            "net_saved_hours": [4.67],
        }
    )
    with pytest.raises(ValueError):
        forecast_portfolio_net_savings(summary, minimum_months=6)
