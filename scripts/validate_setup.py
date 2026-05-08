"""
GCC AI Intelligence Platform — Setup Validation Script
Run before demo to confirm all dependencies and data are in place.

Usage:
    python scripts/validate_setup.py
"""
import sys
import importlib
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
PASS = "  ✓"
FAIL = "  ✗"
WARN = "  ⚠"


def check(label: str, ok: bool, detail: str = "", critical: bool = True) -> bool:
    icon = PASS if ok else (FAIL if critical else WARN)
    line = f"{icon}  {label}"
    if detail:
        line += f" — {detail}"
    print(line)
    return ok


def main():
    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║      GCC AI Intelligence Platform — Setup Check      ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()

    errors = 0
    warnings = 0

    # ── Python version ────────────────────────────────────────────
    py = sys.version_info
    ok = py >= (3, 10)
    if not check(f"Python {py.major}.{py.minor}.{py.micro}", ok,
                 "3.10+ required" if not ok else ""):
        errors += 1

    print()
    print("  Dependencies:")

    # ── Required packages ─────────────────────────────────────────
    packages = [
        ("streamlit",    "1.30", True),
        ("pandas",       "2.0",  True),
        ("numpy",        "1.24", True),
        ("plotly",       "5.18", True),
        ("statsmodels",  "0.14", True),
        ("lightgbm",     "4.0",  True),
        ("sklearn",      "1.3",  True),
        ("scipy",        "1.10", True),
        ("requests",     "2.30", False),
        ("yaml",         "6.0",  False),
    ]

    for pkg, min_ver, critical in packages:
        try:
            mod = importlib.import_module(pkg)
            ver = getattr(mod, "__version__", "unknown")
            ok = check(f"{pkg} ({ver})", True)
        except ImportError:
            ok = check(pkg, False, f"missing — pip install {pkg}", critical)
            if critical:
                errors += 1
            else:
                warnings += 1

    print()
    print("  Data:")

    # ── Data cache ────────────────────────────────────────────────
    data_dir = ROOT / "data" / "processed"
    expected_files = [
        "youth_unemployment_rate.csv",
        "gdp_growth.csv",
        "inflation.csv",
        "population_growth.csv",
        "internet_usage.csv",
        "metadata.json",
    ]
    all_data_ok = True
    for fname in expected_files:
        fpath = data_dir / fname
        ok = fpath.exists() and fpath.stat().st_size > 100
        if not check(f"data/processed/{fname}", ok,
                     "" if ok else "missing — run 'Refresh Data' in the app"):
            warnings += 1
            all_data_ok = False

    if all_data_ok:
        print(f"{PASS}  All data files present — platform runs fully offline")
    else:
        print(f"{WARN}  Some data files missing — use 'Refresh Data' button in app")

    print()
    print("  Application:")

    # ── App file ─────────────────────────────────────────────────
    app_ok = (ROOT / "app.py").exists()
    if not check("app.py", app_ok, "main application file"):
        errors += 1

    # ── Syntax check ─────────────────────────────────────────────
    if app_ok:
        try:
            import ast
            code = (ROOT / "app.py").read_text()
            ast.parse(code)
            check("app.py syntax", True)
        except SyntaxError as e:
            check("app.py syntax", False, str(e))
            errors += 1

    # ── Src modules ───────────────────────────────────────────────
    src_modules = ["gcc_data", "intelligence", "scenario", "evaluate", "explain"]
    for mod in src_modules:
        try:
            sys.path.insert(0, str(ROOT))
            importlib.import_module(f"src.{mod}")
            check(f"src/{mod}.py", True)
        except Exception as e:
            check(f"src/{mod}.py", False, str(e))
            errors += 1

    print()
    print("  Offline resilience:")

    # ── Full import test ──────────────────────────────────────────
    try:
        sys.path.insert(0, str(ROOT))
        from src import gcc_data
        from src import intelligence as intel_module
        from src import scenario as scenario_module

        countries = list(gcc_data.COUNTRIES.keys())
        check(f"gcc_data ({len(countries)} countries)", len(countries) == 6)

        indicators = list(gcc_data.INDICATORS.keys())
        check(f"indicators ({len(indicators)} loaded)", len(indicators) == 5)

        series = gcc_data.get_series("Saudi Arabia", "youth_unemployment_rate")
        check(f"data series (Saudi Arabia, {len(series)} points)", len(series) > 5)

        presets = scenario_module.SCENARIO_PRESETS
        check(f"scenario presets ({len(presets)} loaded)", len(presets) == 8)

        cc = intel_module.compute_confidence_classification(8.5, 2.0, 12.0, 3)
        check(f"confidence classification ({cc.label})", bool(cc.label))

    except Exception as e:
        check("Full system import", False, str(e))
        errors += 1

    # ── Summary ──────────────────────────────────────────────────
    print()
    print("  " + "─" * 52)
    if errors == 0 and warnings == 0:
        print(f"  ✓  ALL CHECKS PASSED — platform is demo-ready")
    elif errors == 0:
        print(f"  ⚠  {warnings} warning(s) — platform is functional but check warnings above")
    else:
        print(f"  ✗  {errors} error(s), {warnings} warning(s) — resolve errors before demo")
    print()

    if errors == 0:
        print("  Launch the platform:")
        print("    macOS/Linux:  ./run_app.sh")
        print("    Windows:      run_app.bat")
        print("    Direct:       streamlit run app.py")
    print()

    return errors


if __name__ == "__main__":
    sys.exit(main())
