from __future__ import annotations

import numpy as np
import pandas as pd


ANOMALY_FEATURES = [
    "first_pass_success_rate",
    "failure_rate",
    "rework_rate",
    "maintenance_ratio",
    "execution_rate",
    "net_saved_hours",
]


def detect_anomalies_with_isolation_forest(
    kpis: pd.DataFrame,
    *,
    contamination: float = 0.05,
    minimum_rows: int = 30,
) -> pd.DataFrame:
    """Run Isolation Forest when enough history is available.

    This function is intentionally not called by the prototype pipeline. It is
    available for the later ML stage and requires packages from
    `requirements-ml.txt`.
    """
    if len(kpis) < minimum_rows:
        raise ValueError(
            f"At least {minimum_rows} automation-month rows are required; "
            f"only {len(kpis)} are available."
        )

    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise ImportError(
            "Install optional ML dependencies with: pip install -r requirements-ml.txt"
        ) from exc

    missing_features = [column for column in ANOMALY_FEATURES if column not in kpis]
    if missing_features:
        raise ValueError(f"Missing ML features: {', '.join(missing_features)}")

    result = kpis.copy()
    model_data = (
        result[ANOMALY_FEATURES]
        .replace([np.inf, -np.inf], np.nan)
        .fillna(result[ANOMALY_FEATURES].median(numeric_only=True))
        .fillna(0)
    )

    pipeline = make_pipeline(
        StandardScaler(),
        IsolationForest(
            contamination=contamination,
            random_state=42,
        ),
    )
    predictions = pipeline.fit_predict(model_data)
    scores = pipeline[-1].decision_function(pipeline[0].transform(model_data))

    result["ml_anomaly_flag"] = predictions == -1
    result["ml_anomaly_score"] = scores
    return result


def forecast_portfolio_net_savings(
    monthly_summary: pd.DataFrame,
    *,
    periods: int = 3,
    minimum_months: int = 6,
) -> pd.DataFrame:
    """Create a simple linear baseline forecast for portfolio net saved hours.

    The forecast should be compared with a naive baseline before publication.
    It is intentionally disabled when too little history exists.
    """
    history = monthly_summary.sort_values("reporting_month").copy()
    if len(history) < minimum_months:
        raise ValueError(
            f"At least {minimum_months} months are required; only {len(history)} are available."
        )

    try:
        from sklearn.linear_model import LinearRegression
    except ImportError as exc:
        raise ImportError(
            "Install optional ML dependencies with: pip install -r requirements-ml.txt"
        ) from exc

    history["time_index"] = np.arange(len(history))
    model = LinearRegression()
    model.fit(history[["time_index"]], history["net_saved_hours"])

    future_index = np.arange(len(history), len(history) + periods)
    predictions = model.predict(future_index.reshape(-1, 1))
    last_month = pd.Timestamp(history["reporting_month"].max())
    future_months = pd.date_range(
        start=last_month + pd.offsets.MonthBegin(1),
        periods=periods,
        freq="MS",
    )

    return pd.DataFrame(
        {
            "reporting_month": future_months,
            "forecast_net_saved_hours": predictions,
            "model": "LinearRegression baseline",
        }
    )
