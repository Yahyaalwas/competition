"""
Streamlit GUI for Time Series Forecasting System.

Run with: streamlit run app.py
"""

import io
import sys
import logging
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import yaml
import joblib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import data as data_module
from src import evaluate as eval_module
from src import explain as explain_module
from src import plotting as plot_module
from src.models.baselines import NaiveModel, SeasonalNaiveModel, MovingAverageModel, DriftModel
from src.models.arima_model import ARIMAModel
from src.models.ml_model import LightGBMModel

# Configure logging
logging.basicConfig(level=logging.WARNING)

# Page config
st.set_page_config(
    page_title="Time Series Forecasting",
    page_icon="📈",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .rtl {
        direction: rtl;
        text-align: right;
        font-family: 'Arial', sans-serif;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .best-model {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)


def load_config():
    """Load default configuration."""
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


def get_models(freq: str, config: dict):
    """Initialize all models."""
    models_config = config.get("models", {})
    baselines_config = models_config.get("baselines", {})
    arima_config = models_config.get("arima", {})
    ml_config = models_config.get("ml", {})

    seasonal_period = 12 if freq == "M" else 1

    return [
        NaiveModel(),
        SeasonalNaiveModel(period=seasonal_period),
        MovingAverageModel(window=baselines_config.get("moving_average_window", 3)),
        DriftModel(),
        ARIMAModel(
            auto_order=True,
            max_p=3, max_d=2, max_q=3,
            max_P=1, max_D=1, max_Q=1,
            seasonal_period=seasonal_period,
            use_seasonal=(seasonal_period > 1),
            freq=freq
        ),
        LightGBMModel(
            n_lags=12 if freq == "M" else 3,
            rolling_windows=[3, 6, 12] if freq == "M" else [2, 3],
            n_estimators=100,
            freq=freq
        ),
    ]


def main():
    # Header
    st.title("📈 Time Series Forecasting System")
    st.markdown("*For Official Statistical Indicators (Population & Economic)*")

    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    # File upload
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV Data",
        type=["csv"],
        help="CSV with columns: date, value (and optional regressors)"
    )

    # Settings
    freq = st.sidebar.selectbox(
        "Data Frequency",
        options=["M", "Y"],
        format_func=lambda x: "Monthly" if x == "M" else "Yearly",
        help="M = Monthly, Y = Yearly"
    )

    horizon = st.sidebar.slider(
        "Forecast Horizon",
        min_value=1,
        max_value=36 if freq == "M" else 10,
        value=12 if freq == "M" else 5,
        help="Number of periods to forecast"
    )

    indicator_name = st.sidebar.text_input(
        "Indicator Name (Arabic)",
        value="المؤشر",
        help="Name for Arabic report"
    )

    confidence_level = st.sidebar.slider(
        "Confidence Level",
        min_value=0.5,
        max_value=0.99,
        value=0.80,
        help="For prediction intervals"
    )

    # Load config
    config = load_config()

    # Main content
    if uploaded_file is None:
        # Show instructions
        st.info("👆 Upload a CSV file to get started")

        st.markdown("### 📋 Data Format Requirements")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Minimum required columns:**")
            st.code("date,value\n2020-01-01,1000\n2020-02-01,1050\n...", language="csv")

        with col2:
            st.markdown("**With optional regressors:**")
            st.code("date,value,gdp,unemployment\n2020-01-01,1000,2.5,5.2\n...", language="csv")

        st.markdown("### 📊 Sample Data")
        if st.button("Generate & Download Sample Data"):
            # Generate sample
            np.random.seed(42)
            dates = pd.date_range(start="2018-01-01", periods=60, freq="MS")
            trend = 1000 * (1.003 ** np.arange(60))
            seasonal = 50 * np.sin(2 * np.pi * np.arange(60) / 12)
            noise = np.random.normal(0, 20, 60)
            values = trend + seasonal + noise

            sample_df = pd.DataFrame({
                "date": dates.strftime("%Y-%m-%d"),
                "value": values.round(2)
            })

            csv = sample_df.to_csv(index=False)
            st.download_button(
                "📥 Download Sample CSV",
                csv,
                "sample_data.csv",
                "text/csv"
            )

        return

    # Load uploaded data
    try:
        df = pd.read_csv(uploaded_file)
        st.success(f"✅ Loaded {len(df)} rows")
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return

    # Data preview
    with st.expander("📋 Data Preview", expanded=True):
        st.dataframe(df.head(10), use_container_width=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Rows", len(df))
        col2.metric("Columns", len(df.columns))
        col3.metric("Date Range", f"{df['date'].min()} → {df['date'].max()}")

    # Process data
    try:
        # Parse dates and set index
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").set_index("date")

        if freq == "M":
            df = df.asfreq("MS")
        else:
            df = df.asfreq("YS")

        # Identify regressors
        regressors = [c for c in df.columns if c != "value" and pd.api.types.is_numeric_dtype(df[c])]

        if regressors:
            st.info(f"📊 Found regressors: {', '.join(regressors)}")

        # Clean data
        df = data_module.clean_data(df, "value", "interpolate")

    except Exception as e:
        st.error(f"Error processing data: {e}")
        return

    # Validate data
    quality = data_module.validate_data(df, "value", freq)

    if quality.has_issues():
        with st.expander("⚠️ Data Quality Warnings"):
            for issue in quality.issues:
                st.warning(issue)

    # Run forecast button
    st.markdown("---")

    if st.button("🚀 Run Forecast", type="primary", use_container_width=True):

        alpha = 1 - confidence_level

        # Progress tracking
        progress = st.progress(0, text="Initializing models...")

        try:
            # Initialize models
            models = get_models(freq, config)
            progress.progress(10, text="Running backtesting...")

            # Backtest
            min_train = 24 if freq == "M" else 10
            n_folds = min(3, (len(df) - min_train) // horizon)

            if n_folds < 1:
                st.warning("Limited data - using simplified evaluation")
                n_folds = 1

            backtest_results = eval_module.backtest_all_models(
                models=models,
                df=df,
                value_column="value",
                horizon=horizon,
                n_folds=n_folds,
                min_train_size=min_train,
                regressors=regressors if regressors else None,
                alpha=alpha
            )

            progress.progress(60, text="Training best model on full data...")

            # Train best model on full data
            best_idx = [i for i, m in enumerate(models) if m.name == backtest_results.best_model_name][0]
            best_model = models[best_idx]

            y = df["value"]
            X = df[regressors] if regressors else None
            best_model.fit(y, X)

            progress.progress(80, text="Generating forecast...")

            # Generate forecast
            forecast, lower, upper = best_model.predict_interval(horizon=horizon, alpha=alpha)

            progress.progress(90, text="Creating visualizations...")

            # Decomposition
            decomp = explain_module.decompose_series(y, freq=freq)

            # Feature importance
            feature_importance = None
            if hasattr(best_model, "get_feature_importance"):
                try:
                    feature_importance = best_model.get_feature_importance()
                except:
                    pass

            # Generate explanation
            explanation = explain_module.generate_explanation(
                series=y,
                forecast=forecast,
                lower=lower,
                upper=upper,
                model_name=best_model.name,
                model_smape=backtest_results.best_model_smape,
                freq=freq,
                data_quality_issues=quality.issues,
                feature_importance=feature_importance,
                confidence_level=confidence_level
            )

            # Arabic report
            arabic_report = explain_module.generate_arabic_report(explanation, indicator_name)

            progress.progress(100, text="Complete!")

            # Store results in session state
            st.session_state["results"] = {
                "backtest": backtest_results,
                "forecast": forecast,
                "lower": lower,
                "upper": upper,
                "history": y,
                "decomp": decomp,
                "explanation": explanation,
                "arabic_report": arabic_report,
                "best_model": best_model,
                "feature_importance": feature_importance
            }

        except Exception as e:
            st.error(f"Error during forecasting: {e}")
            import traceback
            st.code(traceback.format_exc())
            return

    # Display results
    if "results" in st.session_state:
        results = st.session_state["results"]

        st.markdown("---")
        st.header("📊 Results")

        # Best model card
        st.markdown(f"""
        <div class="best-model">
            <h3>🏆 Best Model: {results['backtest'].best_model_name}</h3>
            <p>sMAPE: <b>{results['backtest'].best_model_smape:.2f}%</b> |
               RMSE: <b>{results['backtest'].best_model_rmse:,.2f}</b></p>
        </div>
        """, unsafe_allow_html=True)

        # Tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 Forecast",
            "🔬 Model Comparison",
            "📉 Decomposition",
            "📝 Arabic Report",
            "📥 Downloads"
        ])

        with tab1:
            # Forecast plot
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(12, 6))

            ax.plot(results["history"].index, results["history"].values,
                   color="#2ca02c", linewidth=2, label="Historical", marker="o", markersize=3)
            ax.plot(results["forecast"].index, results["forecast"].values,
                   color="#1f77b4", linewidth=2, linestyle="--", label="Forecast", marker="s", markersize=4)
            ax.fill_between(results["forecast"].index, results["lower"].values, results["upper"].values,
                           color="#1f77b4", alpha=0.2, label=f"{confidence_level*100:.0f}% Interval")
            ax.axvline(x=results["history"].index[-1], color="gray", linestyle=":", alpha=0.7)

            ax.set_title("Time Series Forecast", fontsize=14, fontweight="bold")
            ax.set_xlabel("Date")
            ax.set_ylabel("Value")
            ax.legend()
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()

            st.pyplot(fig)
            plt.close()

            # Forecast table
            forecast_df = pd.DataFrame({
                "Date": results["forecast"].index.strftime("%Y-%m-%d"),
                "Forecast": results["forecast"].values.round(2),
                "Lower": results["lower"].values.round(2),
                "Upper": results["upper"].values.round(2)
            })
            st.dataframe(forecast_df, use_container_width=True)

        with tab2:
            # Model comparison
            st.subheader("Model Performance Comparison")

            comparison_df = results["backtest"].comparison_df.copy()
            comparison_df = comparison_df.round(2)

            # Highlight best
            st.dataframe(
                comparison_df.style.highlight_min(subset=["smape", "rmse"], color="lightgreen"),
                use_container_width=True
            )

            # Bar chart
            fig, axes = plt.subplots(1, 2, figsize=(12, 5))

            colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(comparison_df)))

            axes[0].bar(comparison_df["model"], comparison_df["smape"], color=colors)
            axes[0].set_title("sMAPE (%) - Lower is Better")
            axes[0].set_ylabel("sMAPE (%)")
            plt.setp(axes[0].xaxis.get_majorticklabels(), rotation=45, ha="right")

            axes[1].bar(comparison_df["model"], comparison_df["rmse"], color=colors)
            axes[1].set_title("RMSE - Lower is Better")
            axes[1].set_ylabel("RMSE")
            plt.setp(axes[1].xaxis.get_majorticklabels(), rotation=45, ha="right")

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with tab3:
            # Decomposition
            st.subheader("Time Series Decomposition")

            decomp = results["decomp"]

            col1, col2 = st.columns(2)
            col1.metric("Trend Direction", decomp.trend_direction.capitalize())
            col2.metric("Seasonality Strength", f"{decomp.seasonality_strength:.0%}")

            fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

            axes[0].plot(results["history"].index, results["history"].values, color="#2ca02c")
            axes[0].set_ylabel("Observed")
            axes[0].set_title("Time Series Decomposition", fontsize=14, fontweight="bold")

            axes[1].plot(decomp.trend.index, decomp.trend.values, color="#1f77b4")
            axes[1].set_ylabel("Trend")

            axes[2].plot(decomp.seasonal.index, decomp.seasonal.values, color="#ff7f0e")
            axes[2].set_ylabel("Seasonal")
            axes[2].axhline(y=0, color="gray", linestyle="--", linewidth=0.5)

            axes[3].plot(decomp.residual.index, decomp.residual.values, color="#d62728", alpha=0.7)
            axes[3].set_ylabel("Residual")
            axes[3].axhline(y=0, color="gray", linestyle="--", linewidth=0.5)
            axes[3].set_xlabel("Date")

            for ax in axes:
                ax.grid(True, alpha=0.3)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

        with tab4:
            # Arabic report
            st.subheader("التقرير العربي")
            st.markdown(f'<div class="rtl"><pre>{results["arabic_report"]}</pre></div>',
                       unsafe_allow_html=True)

        with tab5:
            # Downloads
            st.subheader("📥 Download Results")

            col1, col2, col3 = st.columns(3)

            # Forecast CSV
            forecast_csv = forecast_df.to_csv(index=False)
            col1.download_button(
                "📊 Forecast CSV",
                forecast_csv,
                "forecast.csv",
                "text/csv",
                use_container_width=True
            )

            # Arabic report
            col2.download_button(
                "📝 Arabic Report",
                results["arabic_report"],
                "report_ar.txt",
                "text/plain",
                use_container_width=True
            )

            # Model comparison
            comparison_csv = results["backtest"].comparison_df.to_csv(index=False)
            col3.download_button(
                "📈 Model Comparison",
                comparison_csv,
                "model_comparison.csv",
                "text/csv",
                use_container_width=True
            )


if __name__ == "__main__":
    main()
