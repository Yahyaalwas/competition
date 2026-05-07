"""Backtesting and model evaluation utilities."""

import copy
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BacktestResults:
    comparison_df: pd.DataFrame
    best_model_name: str
    best_model_smape: float
    best_model_rmse: float


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Compute MAE, RMSE, MAPE, and sMAPE."""
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    mask = np.abs(y_true) > 1e-8
    if mask.any():
        mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)
    else:
        mape = float("inf")

    denom = (np.abs(y_true) + np.abs(y_pred)) / 2
    mask2 = denom > 1e-8
    if mask2.any():
        smape = float(np.mean(np.abs(y_true[mask2] - y_pred[mask2]) / denom[mask2]) * 100)
    else:
        smape = float("inf")

    return {"mae": mae, "rmse": rmse, "mape": mape, "smape": smape}


def backtest_all_models(
    models: list,
    df: pd.DataFrame,
    value_column: str,
    horizon: int,
    n_folds: int,
    min_train_size: int,
    regressors: Optional[List[str]] = None,
    alpha: float = 0.2,
) -> BacktestResults:
    """
    Expanding-window cross-validation for all models.

    Fold k trains on [0, n - (n_folds - k) * horizon) and tests on
    [n - (n_folds - k) * horizon, n - (n_folds - k - 1) * horizon).
    """
    n = len(df)
    all_results: List[Dict] = []

    for model in models:
        fold_metrics: List[Dict] = []

        for fold in range(n_folds):
            train_end = n - (n_folds - fold) * horizon
            test_end = train_end + horizon

            if train_end < min_train_size:
                logger.debug("Skipping fold %d for %s: not enough training data", fold, model.name)
                continue

            train_df = df.iloc[:train_end]
            test_df = df.iloc[train_end:test_end]

            if len(test_df) == 0:
                continue

            y_train = train_df[value_column]
            y_test = test_df[value_column].values
            X_train = train_df[regressors] if regressors else None

            try:
                m = copy.deepcopy(model)
                m.fit(y_train, X_train)
                test_horizon = len(test_df)
                forecast, _, _ = m.predict_interval(horizon=test_horizon, alpha=alpha)
                y_pred = np.array(forecast.values[:len(y_test)], dtype=float)
                fold_metrics.append(compute_metrics(y_test, y_pred))
            except Exception as exc:
                logger.warning("Model %s failed on fold %d: %s", model.name, fold, exc)

        if fold_metrics:
            avg = {k: float(np.mean([m[k] for m in fold_metrics])) for k in fold_metrics[0]}
        else:
            avg = {"mae": np.inf, "rmse": np.inf, "mape": np.inf, "smape": np.inf}

        all_results.append({"model": model.name, **avg})

    comparison_df = pd.DataFrame(all_results)

    # Guard against all-inf results
    finite_mask = np.isfinite(comparison_df["smape"])
    if finite_mask.any():
        best_idx = comparison_df.loc[finite_mask, "smape"].idxmin()
    else:
        best_idx = 0

    best_row = comparison_df.iloc[best_idx]

    return BacktestResults(
        comparison_df=comparison_df,
        best_model_name=str(best_row["model"]),
        best_model_smape=float(best_row["smape"]),
        best_model_rmse=float(best_row["rmse"]),
    )
