"""Generate sample datasets for testing and demonstration."""

from pathlib import Path

import numpy as np
import pandas as pd


def make_population_monthly(n: int = 72, seed: int = 42) -> pd.DataFrame:
    """Monthly population indicator with trend, seasonality, and noise."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start="2018-01-01", periods=n, freq="MS")
    trend = 1_000_000 * (1.003 ** np.arange(n))
    seasonal = 5_000 * np.sin(2 * np.pi * np.arange(n) / 12)
    noise = rng.normal(0, 2_000, n)
    values = (trend + seasonal + noise).round(0)
    return pd.DataFrame({"date": dates.strftime("%Y-%m-%d"), "value": values})


def make_gdp_yearly(n: int = 20, seed: int = 42) -> pd.DataFrame:
    """Yearly GDP with external regressors (investment, exports)."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start="2004-01-01", periods=n, freq="YS")
    gdp = 100.0
    gdp_values = []
    for _ in range(n):
        gdp *= 1 + rng.normal(0.035, 0.015)
        gdp_values.append(round(gdp, 2))

    investment = [round(g * rng.uniform(0.18, 0.25), 2) for g in gdp_values]
    exports = [round(g * rng.uniform(0.25, 0.40), 2) for g in gdp_values]

    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "value": gdp_values,
        "investment": investment,
        "exports": exports,
    })


def main() -> None:
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    pop_path = data_dir / "population_monthly.csv"
    gdp_path = data_dir / "gdp_yearly.csv"

    make_population_monthly().to_csv(pop_path, index=False)
    print(f"Created {pop_path}")

    make_gdp_yearly().to_csv(gdp_path, index=False)
    print(f"Created {gdp_path}")


if __name__ == "__main__":
    main()
