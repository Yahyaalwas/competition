# Time Series Forecasting System for Official Statistical Indicators

A reproducible pipeline for forecasting population and economic indicators with interpretable outputs and Arabic decision-support explanations.

## Features

- **Multiple Models**: Baseline (Naive, Seasonal Naive, Moving Average), ARIMA/SARIMAX, LightGBM
- **Robust Backtesting**: Expanding window cross-validation with multiple folds
- **Uncertainty Quantification**: Prediction intervals for all models
- **Explainability**: Trend/seasonality decomposition, feature importance, Arabic narrative reports
- **Flexible Data**: Supports monthly and yearly frequencies with optional external regressors

## Setup

### Using venv (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Using uv (faster alternative)

```bash
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt
```

## Quick Start

### Web GUI (Easiest)

After setup, launch the web interface:

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser. You can:
- Upload CSV files via drag & drop
- Configure frequency, horizon, and confidence level
- View interactive plots and download results

### Command Line

#### 1. Generate Sample Data

```bash
python scripts/make_sample_data.py
```

This creates sample datasets in `data/`:
- `population_monthly.csv` - Monthly population indicator
- `gdp_yearly.csv` - Yearly GDP with regressors

### 2. Train Models

```bash
# Monthly data, 12-month forecast horizon
python -m src.main train --data data/population_monthly.csv --freq M --horizon 12

# Yearly data, 5-year forecast horizon
python -m src.main train --data data/gdp_yearly.csv --freq Y --horizon 5
```

### 3. Generate Forecasts

```bash
python -m src.main forecast --data data/population_monthly.csv --freq M --horizon 12
```

### 4. Generate Full Report

```bash
python -m src.main report --data data/population_monthly.csv --freq M --horizon 12
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `train` | Train all models and perform backtesting to select the best |
| `forecast` | Generate forecasts using the best model |
| `report` | Full pipeline: train, forecast, and generate Arabic explanation report |

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `--data` | Path to CSV file | Required |
| `--freq` | Frequency: `M` (monthly) or `Y` (yearly) | `M` |
| `--horizon` | Number of periods to forecast | `12` |
| `--config` | Path to config file | `config.yaml` |
| `--output-dir` | Output directory | `outputs/` |

## Data Format

### Minimum Required Columns

| Column | Type | Description |
|--------|------|-------------|
| `date` | string/date | Date in ISO format (YYYY-MM-DD or YYYY-MM) |
| `value` | numeric | The indicator value |

### Optional Regressor Columns

Any additional numeric columns will be treated as external regressors (e.g., GDP, unemployment, inflation).

Example:
```csv
date,value,gdp_growth,unemployment
2020-01,1000,2.5,5.2
2020-02,1050,2.6,5.1
...
```

## Outputs

All outputs are saved to `outputs/` (or custom `--output-dir`):

| File | Description |
|------|-------------|
| `best_model.pkl` | Serialized best model |
| `forecast.csv` | Forecasts with prediction intervals |
| `backtest_results.csv` | Cross-validation metrics per fold |
| `model_comparison.csv` | Model performance comparison |
| `forecast_plot.png` | Visualization of historical data and forecasts |
| `residuals_plot.png` | Residual diagnostics |
| `decomposition_plot.png` | Trend/seasonality decomposition |
| `report_ar.txt` | Arabic decision-support report |

## Configuration

Edit `config.yaml` to customize:

```yaml
backtesting:
  min_train_size: 24  # Minimum training observations
  n_folds: 3          # Number of CV folds

metrics:
  primary: smape      # Primary selection metric
  secondary: rmse     # Secondary selection metric

models:
  arima:
    auto_order: true
    max_p: 5
    max_q: 5
  ml:
    n_lags: 12
    n_estimators: 100
```

## Model Details

### Baselines
- **Naive**: Last value repeated
- **Seasonal Naive**: Value from same season last year
- **Moving Average**: Rolling mean of last N periods

### ARIMA/SARIMAX
- Automatic order selection using AIC
- Supports external regressors (SARIMAX)
- Built-in prediction intervals

### LightGBM
- Lag features (configurable)
- Rolling statistics
- Quantile regression for prediction intervals
- Feature importance available

## Metrics

| Metric | Description |
|--------|-------------|
| MAE | Mean Absolute Error |
| RMSE | Root Mean Squared Error |
| MAPE | Mean Absolute Percentage Error |
| sMAPE | Symmetric MAPE (primary selection metric) |

## License

MIT License
