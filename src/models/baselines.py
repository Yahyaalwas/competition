"""Baseline forecasting models: Naive, Seasonal Naive, Moving Average, Drift."""

from typing import Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import norm


def _future_index(y: pd.Series, horizon: int) -> pd.DatetimeIndex:
    freq = y.index.freq
    if freq is None:
        freq = pd.infer_freq(y.index)
    return pd.date_range(start=y.index[-1], periods=horizon + 1, freq=freq)[1:]


def _z(alpha: float) -> float:
    return float(norm.ppf(1 - alpha / 2))


class NaiveModel:
    """Forecast = last observed value."""

    name = "Naive"

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "NaiveModel":
        self._y = y.copy()
        diffs = y.diff().dropna()
        self._sigma = float(diffs.std()) if len(diffs) > 1 else float(y.std() * 0.1 + 1e-6)
        return self

    def predict(self, horizon: int) -> pd.Series:
        idx = _future_index(self._y, horizon)
        return pd.Series(np.full(horizon, self._y.iloc[-1]), index=idx)

    def predict_interval(
        self, horizon: int, alpha: float = 0.2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        forecast = self.predict(horizon)
        z = _z(alpha)
        margin = z * self._sigma * np.sqrt(np.arange(1, horizon + 1))
        lower = pd.Series(forecast.values - margin, index=forecast.index)
        upper = pd.Series(forecast.values + margin, index=forecast.index)
        return forecast, lower, upper


class SeasonalNaiveModel:
    """Forecast = value from the same season one cycle ago."""

    name = "Seasonal Naive"

    def __init__(self, period: int = 12) -> None:
        self.period = period

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "SeasonalNaiveModel":
        self._y = y.copy()
        if len(y) > self.period:
            seasonal_diffs = y.diff(self.period).dropna()
            self._sigma = float(seasonal_diffs.std()) if len(seasonal_diffs) > 1 else float(y.std() * 0.1 + 1e-6)
        else:
            self._sigma = float(y.std() * 0.1 + 1e-6)
        return self

    def predict(self, horizon: int) -> pd.Series:
        idx = _future_index(self._y, horizon)
        values = []
        n = len(self._y)
        for h in range(1, horizon + 1):
            # Find corresponding season in history
            lookback = h
            while lookback <= horizon:
                src = n - self.period + ((lookback - 1) % self.period)
                if 0 <= src < n:
                    values.append(float(self._y.iloc[src]))
                    break
                lookback += self.period
            else:
                values.append(float(self._y.iloc[-(self.period - ((h - 1) % self.period))]))
        return pd.Series(values, index=idx)

    def predict_interval(
        self, horizon: int, alpha: float = 0.2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        forecast = self.predict(horizon)
        z = _z(alpha)
        k = np.floor((np.arange(1, horizon + 1) - 1) / self.period) + 1
        margin = z * self._sigma * np.sqrt(k)
        lower = pd.Series(forecast.values - margin, index=forecast.index)
        upper = pd.Series(forecast.values + margin, index=forecast.index)
        return forecast, lower, upper


class MovingAverageModel:
    """Forecast = rolling mean of the last `window` observations."""

    name = "Moving Average"

    def __init__(self, window: int = 3) -> None:
        self.window = window

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "MovingAverageModel":
        self._y = y.copy()
        w = min(self.window, len(y))
        self._mean = float(y.iloc[-w:].mean())
        residuals = y - y.rolling(w, min_periods=1).mean().shift(1)
        self._sigma = float(residuals.dropna().std()) if len(residuals.dropna()) > 1 else float(y.std() * 0.1 + 1e-6)
        return self

    def predict(self, horizon: int) -> pd.Series:
        idx = _future_index(self._y, horizon)
        return pd.Series(np.full(horizon, self._mean), index=idx)

    def predict_interval(
        self, horizon: int, alpha: float = 0.2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        forecast = self.predict(horizon)
        z = _z(alpha)
        margin = z * self._sigma * np.sqrt(np.arange(1, horizon + 1))
        lower = pd.Series(forecast.values - margin, index=forecast.index)
        upper = pd.Series(forecast.values + margin, index=forecast.index)
        return forecast, lower, upper


class DriftModel:
    """Forecast extrapolates the linear trend between first and last observed values."""

    name = "Drift"

    def fit(self, y: pd.Series, X: Optional[pd.DataFrame] = None) -> "DriftModel":
        self._y = y.copy()
        n = len(y)
        if n < 2:
            self._slope = 0.0
        else:
            self._slope = float((y.iloc[-1] - y.iloc[0]) / (n - 1))
        self._last = float(y.iloc[-1])
        # Residuals from the linear trend
        x = np.arange(n)
        trend_vals = y.iloc[0] + self._slope * x
        residuals = y.values - trend_vals
        self._sigma = float(np.std(residuals)) if n > 2 else float(abs(self._slope) * 0.1 + 1e-6)
        return self

    def predict(self, horizon: int) -> pd.Series:
        idx = _future_index(self._y, horizon)
        steps = np.arange(1, horizon + 1)
        values = self._last + self._slope * steps
        return pd.Series(values, index=idx)

    def predict_interval(
        self, horizon: int, alpha: float = 0.2
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        forecast = self.predict(horizon)
        z = _z(alpha)
        n = len(self._y)
        # Variance grows with horizon and depends on training length
        margin = z * self._sigma * np.sqrt(np.arange(1, horizon + 1) * (1 + 1 / n))
        lower = pd.Series(forecast.values - margin, index=forecast.index)
        upper = pd.Series(forecast.values + margin, index=forecast.index)
        return forecast, lower, upper
