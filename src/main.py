"""CLI entry point: train, forecast, report commands."""

import logging
import sys
from pathlib import Path

import click
import joblib
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import data as data_module
from src import evaluate as eval_module
from src import explain as explain_module
from src import plotting as plot_module
from src.models.baselines import NaiveModel, SeasonalNaiveModel, MovingAverageModel, DriftModel
from src.models.arima_model import ARIMAModel
from src.models.ml_model import LightGBMModel


def _setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _load_config(config_path: str) -> dict:
    p = Path(config_path)
    if p.exists():
        with open(p) as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_models(freq: str, config: dict) -> list:
    bc = config.get("models", {}).get("baselines", {})
    ac = config.get("models", {}).get("arima", {})
    mc = config.get("models", {}).get("ml", {})
    seasonal_period = 12 if freq == "M" else 1

    return [
        NaiveModel(),
        SeasonalNaiveModel(period=seasonal_period),
        MovingAverageModel(window=bc.get("moving_average_window", 3)),
        DriftModel(),
        ARIMAModel(
            auto_order=ac.get("auto_order", True),
            max_p=ac.get("max_p", 3),
            max_d=ac.get("max_d", 2),
            max_q=ac.get("max_q", 3),
            max_P=ac.get("max_P", 1),
            max_D=ac.get("max_D", 1),
            max_Q=ac.get("max_Q", 1),
            seasonal_period=seasonal_period,
            use_seasonal=(seasonal_period > 1),
            freq=freq,
        ),
        LightGBMModel(
            n_lags=mc.get("n_lags", 12) if freq == "M" else mc.get("n_lags_yearly", 3),
            rolling_windows=mc.get("rolling_windows", [3, 6, 12]) if freq == "M" else mc.get("rolling_windows_yearly", [2, 3]),
            n_estimators=mc.get("n_estimators", 100),
            freq=freq,
        ),
    ]


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

@click.group()
def cli() -> None:
    """Time Series Forecasting CLI for Official Statistical Indicators."""


_common_options = [
    click.option("--data", required=True, type=click.Path(exists=True), help="Path to CSV file"),
    click.option("--freq", default="M", show_default=True, type=click.Choice(["M", "Y"]), help="Data frequency"),
    click.option("--horizon", default=12, show_default=True, type=int, help="Forecast horizon"),
    click.option("--config", default="config.yaml", show_default=True, help="Config file path"),
    click.option("--output-dir", default="outputs", show_default=True, help="Output directory"),
    click.option("--confidence", default=0.80, show_default=True, type=float, help="Confidence level"),
]


def add_options(options):
    def decorator(f):
        for opt in reversed(options):
            f = opt(f)
        return f
    return decorator


def _prepare_data(data_path: str, freq: str, config: dict):
    cfg_data = config.get("data", {})
    date_col = cfg_data.get("date_column", "date")
    value_col = cfg_data.get("value_column", "value")
    missing_strat = cfg_data.get("missing_value_strategy", "interpolate")

    df = data_module.load_csv(data_path, date_column=date_col, value_column=value_col, freq=freq)
    regressors = [c for c in df.columns if c != value_col and pd.api.types.is_numeric_dtype(df[c])]
    df = data_module.clean_data(df, value_col, missing_strat)
    quality = data_module.validate_data(df, value_col, freq)
    return df, value_col, regressors, quality


@cli.command()
@add_options(_common_options)
def train(data, freq, horizon, config, output_dir, confidence):
    """Train all models via backtesting and save the best one."""
    cfg = _load_config(config)
    _setup_logging(cfg.get("logging", {}).get("level", "INFO"))
    log = logging.getLogger("train")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df, value_col, regressors, quality = _prepare_data(data, freq, cfg)
    if quality.has_issues():
        for issue in quality.issues:
            log.warning("Data quality: %s", issue)

    alpha = 1 - confidence
    min_train = 24 if freq == "M" else 10
    n_folds = max(1, min(3, (len(df) - min_train) // horizon))

    models = _get_models(freq, cfg)
    log.info("Running backtesting with %d folds over %d models...", n_folds, len(models))

    backtest = eval_module.backtest_all_models(
        models=models,
        df=df,
        value_column=value_col,
        horizon=horizon,
        n_folds=n_folds,
        min_train_size=min_train,
        regressors=regressors or None,
        alpha=alpha,
    )

    log.info("Best model: %s  sMAPE=%.2f%%", backtest.best_model_name, backtest.best_model_smape)

    best_model = next(m for m in models if m.name == backtest.best_model_name)
    y = df[value_col]
    X = df[regressors] if regressors else None
    best_model.fit(y, X)

    joblib.dump(best_model, out / "best_model.pkl")
    backtest.comparison_df.to_csv(out / "model_comparison.csv", index=False)
    backtest.comparison_df.to_csv(out / "backtest_results.csv", index=False)

    log.info("Saved model and results to %s", out)
    click.echo(f"Best model: {backtest.best_model_name}  sMAPE={backtest.best_model_smape:.2f}%")


@cli.command()
@add_options(_common_options)
def forecast(data, freq, horizon, config, output_dir, confidence):
    """Load the best model and generate a forecast."""
    cfg = _load_config(config)
    _setup_logging(cfg.get("logging", {}).get("level", "INFO"))
    log = logging.getLogger("forecast")

    out = Path(output_dir)
    model_path = out / "best_model.pkl"

    if not model_path.exists():
        click.echo("No trained model found. Run 'train' first.", err=True)
        sys.exit(1)

    best_model = joblib.load(model_path)
    df, value_col, regressors, _ = _prepare_data(data, freq, cfg)

    alpha = 1 - confidence
    fc, lower, upper = best_model.predict_interval(horizon=horizon, alpha=alpha)

    forecast_df = pd.DataFrame({
        "date": fc.index.strftime("%Y-%m-%d"),
        "forecast": fc.values.round(cfg.get("output", {}).get("decimal_places", 2)),
        "lower": lower.values.round(2),
        "upper": upper.values.round(2),
    })

    out.mkdir(parents=True, exist_ok=True)
    forecast_df.to_csv(out / "forecast.csv", index=False)

    y = df[value_col]
    fig = plot_module.plot_forecast(y, fc, lower, upper, confidence_level=confidence)
    fig.savefig(out / "forecast_plot.png", dpi=150, bbox_inches="tight")

    log.info("Forecast saved to %s", out / "forecast.csv")
    click.echo(forecast_df.to_string(index=False))


@cli.command()
@add_options(_common_options)
@click.option("--indicator-name", default="المؤشر", help="Indicator name for Arabic report")
def report(data, freq, horizon, config, output_dir, confidence, indicator_name):
    """Full pipeline: train, forecast, decompose, and generate Arabic report."""
    cfg = _load_config(config)
    _setup_logging(cfg.get("logging", {}).get("level", "INFO"))
    log = logging.getLogger("report")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    df, value_col, regressors, quality = _prepare_data(data, freq, cfg)
    alpha = 1 - confidence
    min_train = 24 if freq == "M" else 10
    n_folds = max(1, min(3, (len(df) - min_train) // horizon))

    models = _get_models(freq, cfg)
    log.info("Backtesting...")
    backtest = eval_module.backtest_all_models(
        models=models,
        df=df,
        value_column=value_col,
        horizon=horizon,
        n_folds=n_folds,
        min_train_size=min_train,
        regressors=regressors or None,
        alpha=alpha,
    )

    best_model = next(m for m in models if m.name == backtest.best_model_name)
    y = df[value_col]
    X = df[regressors] if regressors else None
    best_model.fit(y, X)

    fc, lower, upper = best_model.predict_interval(horizon=horizon, alpha=alpha)

    feature_importance = None
    if hasattr(best_model, "get_feature_importance"):
        try:
            feature_importance = best_model.get_feature_importance()
        except Exception:
            pass

    decomp = explain_module.decompose_series(y, freq=freq)
    explanation = explain_module.generate_explanation(
        series=y,
        forecast=fc,
        lower=lower,
        upper=upper,
        model_name=best_model.name,
        model_smape=backtest.best_model_smape,
        freq=freq,
        data_quality_issues=quality.issues,
        feature_importance=feature_importance,
        confidence_level=confidence,
    )
    arabic_report = explain_module.generate_arabic_report(explanation, indicator_name)

    # Save outputs
    forecast_df = pd.DataFrame({
        "date": fc.index.strftime("%Y-%m-%d"),
        "forecast": fc.values.round(2),
        "lower": lower.values.round(2),
        "upper": upper.values.round(2),
    })
    forecast_df.to_csv(out / "forecast.csv", index=False)
    backtest.comparison_df.to_csv(out / "model_comparison.csv", index=False)
    (out / "report_ar.txt").write_text(arabic_report, encoding="utf-8")
    joblib.dump(best_model, out / "best_model.pkl")

    plot_module.plot_forecast(y, fc, lower, upper, confidence_level=confidence,
                               output_path=out / "forecast_plot.png")
    plot_module.plot_decomposition(y, decomp.trend, decomp.seasonal, decomp.residual,
                                    output_path=out / "decomposition_plot.png")

    log.info("Report saved to %s", out)
    click.echo(arabic_report)


if __name__ == "__main__":
    cli()
