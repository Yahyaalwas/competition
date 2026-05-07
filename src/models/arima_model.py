"""ARIMA / SARIMAX model wrapper with automatic order selection via AIC."""

import logging
from typing import Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Candidate non-seasonal orders to try during auto-selection
_CANDIDATE_ORDERS = [
    (1, 1, 0), (0, 1, 1), (1, 1, 1),
    (2, 1, 0), (0, 1, 2), (2, 1, 1),
    (1, 1, 2), (0, 2, 1), (1, 2, 1),
    (1, 0, 0), (0, 0, 1), (1, 0, 1),
]

# Candidate seasonal orders (P, D, Q) — period is added at fit time
_CANDIDATE_SEASONAL = [
    (1, 1, 0), (0, 1, 1), (1, 1, 1), (0, 0, 1), (1, 0, 0),
]


class ARIMAModel:
    """SARIMAX wrapper with AIC-based automatic order selection."""

    name = "ARIMA"

    def __init__(
        self,
        auto_order: bool = True,
        max_p: int = 3,
        max_d: int = 2,
        max_q: int = 3,
        max_P: int = 1,
        max_D: int = 1,
        max_Q: int = 1,
        seasonal_period: int = 12,
        use_seasonal: bool = True,
        freq: str = "M",
    ) -> None:
        self.auto_order = auto_order
        self.max_p = max_p
        self.max_d = max_d
        self.max_q = max_q
        self.max_P = max_P
        self.max_D = max_D
        self.max_Q = max_Q
        self.seasonal_period = seasonal_period
        self.use_seasonal = use_seasonal
        self.freq = freq
        self._result = None

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "ARIMAModel":
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        self._y = y.copy()

        if self.auto_order:
            order, seasonal_order = self._select_order(y, X)
        else:
            order = (1, 1, 1)
            seasonal_order = (
                (1, 1, 1, self.seasonal_period) if self.use_seasonal else (0, 0, 0, 0)
            )

        try:
            self._result = SARIMAX(
                y,
                exog=X,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False, method="lbfgs", maxiter=200)
        except Exception:
            # Fall back to simple (1,1,1)
            logger.warning("ARIMAModel fit failed with order %s; falling back to (1,1,1)", order)
            self._result = SARIMAX(
                y,
                exog=X,
                order=(1, 1, 1),
                seasonal_order=(0, 0, 0, 0),
                enforce_stationarity=False,
                enforce_invertibility=False,
            ).fit(disp=False, method="lbfgs", maxiter=200)

        return self

    # ------------------------------------------------------------------
    def _select_order(
        self, y: pd.Series, X: Optional[pd.DataFrame]
    ) -> Tuple[Tuple, Tuple]:
        from statsmodels.tsa.statespace.sarimax import SARIMAX

        best_aic = np.inf
        best_order = (1, 1, 1)
        best_seasonal = (0, 0, 0, 0)

        # Filter candidates by max bounds
        candidates = [
            (p, d, q)
            for p, d, q in _CANDIDATE_ORDERS
            if p <= self.max_p and d <= self.max_d and q <= self.max_q
        ]

        for order in candidates:
            try:
                res = SARIMAX(
                    y,
                    exog=X,
                    order=order,
                    seasonal_order=(0, 0, 0, 0),
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                ).fit(disp=False, method="lbfgs", maxiter=100)
                if res.aic < best_aic:
                    best_aic = res.aic
                    best_order = order
            except Exception:
                pass

        if self.use_seasonal and self.seasonal_period > 1:
            seasonal_candidates = [
                (P, D, Q)
                for P, D, Q in _CANDIDATE_SEASONAL
                if P <= self.max_P and D <= self.max_D and Q <= self.max_Q
            ]
            for P, D, Q in seasonal_candidates:
                try:
                    res = SARIMAX(
                        y,
                        exog=X,
                        order=best_order,
                        seasonal_order=(P, D, Q, self.seasonal_period),
                        enforce_stationarity=False,
                        enforce_invertibility=False,
                    ).fit(disp=False, method="lbfgs", maxiter=100)
                    if res.aic < best_aic:
                        best_aic = res.aic
                        best_seasonal = (P, D, Q, self.seasonal_period)
                except Exception:
                    pass

        return best_order, best_seasonal

    # ------------------------------------------------------------------
    def predict(self, horizon: int, X_future: Optional[pd.DataFrame] = None) -> pd.Series:
        return self._result.forecast(steps=horizon, exog=X_future)

    def predict_interval(
        self,
        horizon: int,
        alpha: float = 0.2,
        X_future: Optional[pd.DataFrame] = None,
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        pred = self._result.get_forecast(steps=horizon, exog=X_future)
        forecast = pred.predicted_mean
        ci = pred.conf_int(alpha=alpha)
        lower = ci.iloc[:, 0]
        upper = ci.iloc[:, 1]
        # Rename to avoid statsmodels column name leakage
        lower.name = None
        upper.name = None
        return forecast, lower, upper
