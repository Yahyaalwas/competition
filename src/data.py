"""Data loading, cleaning, and validation utilities."""

from dataclasses import dataclass, field
from typing import List

import numpy as np
import pandas as pd


@dataclass
class DataQuality:
    issues: List[str] = field(default_factory=list)

    def has_issues(self) -> bool:
        return len(self.issues) > 0


def clean_data(df: pd.DataFrame, value_column: str, strategy: str = "interpolate") -> pd.DataFrame:
    """Fill missing values using the specified strategy."""
    df = df.copy()
    if strategy == "interpolate":
        df[value_column] = df[value_column].interpolate(method="time")
    elif strategy == "ffill":
        df[value_column] = df[value_column].ffill()
    elif strategy == "drop":
        df = df.dropna(subset=[value_column])
    # Remaining NaNs at edges
    df[value_column] = df[value_column].ffill().bfill()
    return df


def validate_data(df: pd.DataFrame, value_column: str, freq: str) -> DataQuality:
    """Run data quality checks and return a DataQuality report."""
    issues: List[str] = []
    n = len(df)
    min_obs = 24 if freq == "M" else 10

    if n < min_obs:
        issues.append(
            f"Short series: {n} observations (recommended minimum: {min_obs})"
        )

    missing = int(df[value_column].isna().sum())
    if missing > 0:
        issues.append(f"{missing} missing value(s) detected and will be imputed")

    non_positive = int((df[value_column] <= 0).sum())
    if non_positive > 0:
        issues.append(
            f"{non_positive} non-positive value(s) found — percentage metrics may be unreliable"
        )

    q1 = df[value_column].quantile(0.25)
    q3 = df[value_column].quantile(0.75)
    iqr = q3 - q1
    if iqr > 0:
        outliers = int(
            ((df[value_column] < q1 - 3 * iqr) | (df[value_column] > q3 + 3 * iqr)).sum()
        )
        if outliers > 0:
            issues.append(f"{outliers} potential outlier(s) detected (3×IQR rule)")

    return DataQuality(issues=issues)


def load_csv(path: str, date_column: str = "date", value_column: str = "value",
             freq: str = "M") -> pd.DataFrame:
    """Load a CSV file, parse dates, set frequency, and return a DataFrame."""
    df = pd.read_csv(path)
    df[date_column] = pd.to_datetime(df[date_column])
    df = df.sort_values(date_column).set_index(date_column)
    df = df.asfreq("MS" if freq == "M" else "YS")
    return df
