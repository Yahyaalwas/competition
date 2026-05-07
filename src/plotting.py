"""Reusable plotting helpers (used by the CLI pipeline)."""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd


def plot_forecast(
    history: pd.Series,
    forecast: pd.Series,
    lower: pd.Series,
    upper: pd.Series,
    confidence_level: float = 0.80,
    title: str = "Time Series Forecast",
    output_path: Optional[Path] = None,
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(history.index, history.values, color="#2ca02c", linewidth=2,
            label="Historical", marker="o", markersize=3)
    ax.plot(forecast.index, forecast.values, color="#1f77b4", linewidth=2,
            linestyle="--", label="Forecast", marker="s", markersize=4)
    ax.fill_between(forecast.index, lower.values, upper.values,
                    color="#1f77b4", alpha=0.2,
                    label=f"{confidence_level * 100:.0f}% Interval")
    ax.axvline(x=history.index[-1], color="gray", linestyle=":", alpha=0.7)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Value")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig


def plot_residuals(
    residuals: pd.Series,
    title: str = "Residual Diagnostics",
    output_path: Optional[Path] = None,
) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(residuals.index, residuals.values, color="#d62728", alpha=0.8)
    axes[0].axhline(0, color="gray", linestyle="--", linewidth=0.8)
    axes[0].set_title("Residuals over Time")
    axes[0].set_xlabel("Date")
    axes[0].set_ylabel("Residual")
    axes[0].grid(True, alpha=0.3)

    axes[1].hist(residuals.dropna().values, bins=20, color="#1f77b4", edgecolor="white", alpha=0.8)
    axes[1].set_title("Residual Distribution")
    axes[1].set_xlabel("Residual")
    axes[1].set_ylabel("Frequency")
    axes[1].grid(True, alpha=0.3)

    plt.suptitle(title, fontsize=13, fontweight="bold")
    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig


def plot_decomposition(
    observed: pd.Series,
    trend: pd.Series,
    seasonal: pd.Series,
    residual: pd.Series,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

    components = [
        (observed, "Observed", "#2ca02c"),
        (trend, "Trend", "#1f77b4"),
        (seasonal, "Seasonal", "#ff7f0e"),
        (residual, "Residual", "#d62728"),
    ]

    for ax, (series, label, color) in zip(axes, components):
        ax.plot(series.index, series.values, color=color, linewidth=1.2)
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)
        if label in ("Seasonal", "Residual"):
            ax.axhline(0, color="gray", linestyle="--", linewidth=0.5)

    axes[0].set_title("Time Series Decomposition", fontsize=14, fontweight="bold")
    axes[-1].set_xlabel("Date")

    plt.tight_layout()

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")

    return fig
