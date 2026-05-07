"""LightGBM-based forecasting model with quantile regression for prediction intervals."""

import logging
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_LOWER_Q = 0.1
_MEDIAN_Q = 0.5
_UPPER_Q = 0.9


class LightGBMModel:
    """Recursive multi-quantile LightGBM forecaster."""

    name = "LightGBM"

    def __init__(
        self,
        n_lags: int = 12,
        rolling_windows: Optional[List[int]] = None,
        n_estimators: int = 100,
        freq: str = "M",
    ) -> None:
        self.n_lags = n_lags
        self.rolling_windows = rolling_windows or [3, 6, 12]
        self.n_estimators = n_estimators
        self.freq = freq
        self._models: dict = {}
        self._feature_names: List[str] = []

    # ------------------------------------------------------------------
    def _make_feature_names(self) -> List[str]:
        names = [f"lag_{i}" for i in range(1, self.n_lags + 1)]
        for w in self.rolling_windows:
            names += [f"roll_mean_{w}", f"roll_std_{w}"]
        if self.freq == "M":
            names += ["month", "quarter"]
        names += ["year_idx"]
        return names

    def _build_training_matrix(self, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
        """Build supervised learning matrix from a time series."""
        n = len(y)
        min_row = max(self.n_lags, max(self.rolling_windows, default=0))
        rows = []
        targets = []

        for t in range(min_row, n):
            row = self._build_feature_row(y.values, t, y.index[t])
            if row is not None:
                rows.append(row)
                targets.append(float(y.iloc[t]))

        if not rows:
            return pd.DataFrame(columns=self._feature_names), pd.Series(dtype=float)

        X = pd.DataFrame(rows, columns=self._feature_names)
        return X, pd.Series(targets)

    def _build_feature_row(
        self, values: np.ndarray, t: int, date: pd.Timestamp
    ) -> Optional[List[float]]:
        """Build a single feature row for position t."""
        if t < self.n_lags:
            return None

        row: List[float] = []

        # Lag features
        for lag in range(1, self.n_lags + 1):
            row.append(float(values[t - lag]))

        # Rolling statistics (computed over values BEFORE t)
        for w in self.rolling_windows:
            window_vals = values[max(0, t - w): t]
            row.append(float(np.mean(window_vals)) if len(window_vals) > 0 else 0.0)
            row.append(float(np.std(window_vals)) if len(window_vals) > 1 else 0.0)

        # Calendar features
        if self.freq == "M":
            row.append(float(date.month))
            row.append(float(date.quarter))

        # Trend proxy: position relative to start
        row.append(float(t))

        return row

    def _build_future_row(
        self, history: np.ndarray, future_date: pd.Timestamp, t: int
    ) -> List[float]:
        """Build a feature row for a future prediction step."""
        row: List[float] = []

        n = len(history)
        for lag in range(1, self.n_lags + 1):
            idx = n - lag
            row.append(float(history[idx]) if idx >= 0 else 0.0)

        for w in self.rolling_windows:
            window_vals = history[max(0, n - w):]
            row.append(float(np.mean(window_vals)) if len(window_vals) > 0 else 0.0)
            row.append(float(np.std(window_vals)) if len(window_vals) > 1 else 0.0)

        if self.freq == "M":
            row.append(float(future_date.month))
            row.append(float(future_date.quarter))

        row.append(float(self._train_n + t))

        return row

    # ------------------------------------------------------------------
    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "LightGBMModel":
        import lightgbm as lgb

        self._y = y.copy()
        self._train_n = len(y)
        self._feature_names = self._make_feature_names()

        X_train, y_train = self._build_training_matrix(y)

        if len(y_train) < 5:
            raise ValueError(
                f"Not enough observations to build LightGBM features (got {len(y_train)}). "
                "Need at least n_lags + max(rolling_windows) + 5 observations."
            )

        for q in (_LOWER_Q, _MEDIAN_Q, _UPPER_Q):
            model = lgb.LGBMRegressor(
                objective="quantile",
                alpha=q,
                n_estimators=self.n_estimators,
                learning_rate=0.05,
                max_depth=4,
                num_leaves=15,
                min_child_samples=max(5, len(y_train) // 10),
                subsample=0.8,
                colsample_bytree=0.8,
                verbose=-1,
            )
            model.fit(X_train, y_train)
            self._models[q] = model

        return self

    # ------------------------------------------------------------------
    def predict(self, horizon: int) -> pd.Series:
        forecast, _, _ = self.predict_interval(horizon, alpha=0.2)
        return forecast

    def predict_interval(
        self, horizon: int, alpha: float = 0.2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        # Map alpha to trained quantiles
        # We always trained [0.1, 0.5, 0.9]; use them regardless of alpha
        # (interval will be approximate for alpha != 0.2)
        future_index = self._make_future_index(horizon)
        history = list(self._y.values)

        medians, lowers, uppers = [], [], []

        for step, future_date in enumerate(future_index):
            row = self._build_future_row(np.array(history), future_date, step)
            X_pred = pd.DataFrame([row], columns=self._feature_names)

            med = float(self._models[_MEDIAN_Q].predict(X_pred)[0])
            lo = float(self._models[_LOWER_Q].predict(X_pred)[0])
            hi = float(self._models[_UPPER_Q].predict(X_pred)[0])

            # Ensure monotonicity
            lo = min(lo, med)
            hi = max(hi, med)

            medians.append(med)
            lowers.append(lo)
            uppers.append(hi)

            history.append(med)

        return (
            pd.Series(medians, index=future_index),
            pd.Series(lowers, index=future_index),
            pd.Series(uppers, index=future_index),
        )

    # ------------------------------------------------------------------
    def get_feature_importance(self) -> pd.Series:
        model = self._models[_MEDIAN_Q]
        importance = model.feature_importances_
        return pd.Series(importance, index=self._feature_names).sort_values(ascending=False)

    def _make_future_index(self, horizon: int) -> pd.DatetimeIndex:
        freq = self._y.index.freq
        if freq is None:
            freq = pd.infer_freq(self._y.index)
        return pd.date_range(start=self._y.index[-1], periods=horizon + 1, freq=freq)[1:]
