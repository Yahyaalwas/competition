#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
# GCC AI Intelligence Platform — One-Click Launcher (macOS / Linux)
# ──────────────────────────────────────────────────────────────────
set -e

echo ""
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║        GCC AI Intelligence Platform                  ║"
echo "  ║   AI-Powered GCC Youth Employment Intelligence       ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo ""

# ── Check Python ─────────────────────────────────────────────────
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "  ✗  Python not found. Install Python 3.10+ from https://python.org"
    exit 1
fi
PYTHON=$(command -v python3 || command -v python)
echo "  ✓  Python: $($PYTHON --version)"

# ── Check Streamlit ───────────────────────────────────────────────
if ! $PYTHON -c "import streamlit" &>/dev/null; then
    echo "  ⚙  Installing dependencies..."
    $PYTHON -m pip install -r requirements.txt --quiet
fi
echo "  ✓  Streamlit: ready"

# ── Validate data cache ───────────────────────────────────────────
if [ -f "data/processed/youth_unemployment_rate.csv" ]; then
    echo "  ✓  Data cache: available (offline mode supported)"
else
    echo "  ⚠  Data cache not found. Platform will prompt to fetch from World Bank API."
fi

echo ""
echo "  ► Launching platform at http://localhost:8501"
echo "  ► Press Ctrl+C to stop"
echo ""

# ── Launch ────────────────────────────────────────────────────────
$PYTHON -m streamlit run app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false
