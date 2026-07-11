"""
DEN EA Backtest Automation Tool
Generates .set files for MT5 Strategy Tester (UTF-16LE format)
Usage:  python backtest_runner.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────
EA_NAME = "BTCJPY_LowDDWithBoS_Opt_V5_1"
SYMBOL = "BTCJPY"
TIMEFRAME = "M15"
FROM_DATE = "2025.07.01"
TO_DATE = "2026.07.10"
TEST_MODE = 0  # 0=real ticks, 1=1M OHLC, 2=open prices
DEPOSIT = 50000
LEVERAGE = 1000

# ── EA Input Parameters (name, value, start, step, stop, optimize?) ──
PARAMS = [
    ("MagicNumber",         987659, 987659, 1,      987659,  True),
    ("EMAPeriod",           88,     30,     5,      150,     True),
    ("UseRSIFilter",        True,   True,   None,   None,    False),
    ("RSIPeriod",           14,     14,     1,      14,      False),
    ("RSILongMin",          30.0,   20.0,   5.0,    50.0,    True),
    ("RSIShortMax",         60.0,   50.0,   5.0,    80.0,    True),
    ("ZoneTF",              16388,  16388,  None,   None,    False),
    ("BodyStrengthMin",     50,     30,     5,      70,      True),
    ("ZoneExpiryHours",     24,     12,     4,      48,      True),
    ("BaseLotSize",         0.01,   0.01,   0.01,   0.05,    True),
    ("StopLossATR",         2.0,    1.0,    0.5,    4.0,     True),
    ("TakeProfitATR",       3.5,    2.0,    0.5,    6.0,     True),
    ("MaxDailyLossPct",     5.0,    3.0,    1.0,    10.0,    True),
    ("MaxConsecutiveLosses", 3,     2,      1,      5,       True),
    ("UseTrailing",         True,   True,   None,   None,    False),
    ("TrailActivatePct",    1.0,    0.5,    0.2,    3.0,     True),
    ("TrailOffsetPct",      0.6,    0.3,    0.1,    1.5,     True),
    ("UsePartialTP",        True,   True,   None,   None,    False),
    ("PartialTP1Pct",       3.0,    2.0,    0.5,    6.0,     True),
    ("PartialClose1Pct",    50.0,   25.0,   10.0,   75.0,    True),
    ("PartialTP2Pct",       6.0,    4.0,    1.0,    10.0,    True),
    ("PartialClose2Pct",    75.0,   50.0,   10.0,   90.0,    True),
]


def find_terminal_instance():
    """Locate the active MT5 terminal instance folder."""
    terminal_data = Path(os.environ.get("APPDATA", "")) / "MetaQuotes" / "Terminal"
    if not terminal_data.exists():
        return None
    for d in terminal_data.iterdir():
        if d.is_dir() and d.name not in ("Common", "Community"):
            return d
    return None


def generate_set_file(path: Path, params: list, optimize: bool = False):
    """Generate a .set file in UTF-16LE format for MT5."""
    lines = [
        "; DEN EA Backtest Parameters - Auto-generated",
        f"; Expert: {EA_NAME}",
        f"; Symbol: {SYMBOL}  Period: {TIMEFRAME}",
        f"; Date: {FROM_DATE} - {TO_DATE}",
        f"; Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "; name=value||start||step||stop||selected",
    ]

    for name, value, start, step, stop, optimize_flag in params:
        # Format value
        if isinstance(value, bool):
            val_str = str(value).lower()
        elif isinstance(value, float):
            val_str = f"{value:.1f}"
        else:
            val_str = str(value)

        # Start/step/stop for optimization
        if optimize and optimize_flag:
            # Use the optimization range
            if isinstance(start, float):
                s = f"{start:.1f}"
                st = f"{step:.1f}" if step else ""
                so = f"{stop:.1f}" if stop else ""
            else:
                s = str(start) if start is not None else val_str
                st = str(step) if step else ""
                so = str(stop) if stop else ""
        else:
            s, st, so = val_str, "", ""

        sel = "Y" if optimize_flag else ""
        line = f"{name}={val_str}||{s}||{st}||{so}||{sel}"
        lines.append(line)

    # Write as UTF-16LE
    content = "\r\n".join(lines) + "\r\n"
    path.write_bytes(content.encode("utf-16-le"))
    return path


def generate_batch_runner(instance: Path):
    """Generate a PowerShell script to run the test."""
    script = f"""# DEN EA Backtest Runner
# Run this script in PowerShell to execute the backtest

$eaName = "{EA_NAME}"
$symbol = "{SYMBOL}"
$timeframe = "{TIMEFRAME}"
$fromDate = "{FROM_DATE}"
$toDate = "{TO_DATE}"
$setFile = "{instance}\\MQL5\\Experts\\DEN_EA\\Sets\\{EA_NAME}.set"

Write-Host "=== DEN EA Backtest ===" -ForegroundColor Cyan
Write-Host "Expert: $eaName"
Write-Host "Symbol: $symbol  Period: $timeframe"
Write-Host "Date: $fromDate - $toDate"
Write-Host ""
Write-Host "Project: C:\\Users\\decni\\projects\\POGIBOT\\backend"
Write-Host "Set file: $setFile" -ForegroundColor Green
Write-Host ""
Write-Host "=== MANUAL STEPS ===" -ForegroundColor Yellow
Write-Host "1. Open MetaTrader 5"
Write-Host "2. View -> Strategy Tester"
Write-Host "3. Expert: $eaName"
Write-Host "4. Symbol: $symbol / Period: $timeframe"
Write-Host "5. Date: $fromDate - $toDate"
Write-Host "6. Mode: Real ticks (recommended)"
Write-Host "7. Inputs tab -> Load -> Select $eaName.set"
Write-Host "8. Check boxes for parameters to optimize"
Write-Host "9. Click Start"
Write-Host ""

# Optional: Launch MT5
$mt5 = "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
if (Test-Path $mt5) {{
    Write-Host "Launching MetaTrader 5..." -ForegroundColor Cyan
    Start-Process $mt5
}} else {{
    Write-Host "MT5 not found at $mt5" -ForegroundColor Red
    Write-Host "Launch it manually."
}}

Read-Host "Press Enter to exit"
"""
    return script


def main():
    print("=" * 55)
    print("  DEN EA Backtest Automation Tool")
    print("=" * 55)

    # Find MT5 instance
    instance = find_terminal_instance()
    if not instance:
        print("ERROR: Cannot find MetaTrader 5 terminal instance.")
        print(f"      Looked in: {os.environ.get('APPDATA', '')}\\MetaQuotes\\Terminal\\")
        return

    print(f"\nFound MT5 instance: {instance.name}")

    # Generate .set file
    sets_dir = instance / "MQL5" / "Experts" / "DEN_EA" / "Sets"
    sets_dir.mkdir(parents=True, exist_ok=True)
    set_path = sets_dir / f"{EA_NAME}.set"

    generate_set_file(set_path, PARAMS, optimize=True)
    print(f"  ✅ .set file: {set_path}")

    # Generate PowerShell runner
    runner_path = Path(__file__).parent / "run_backtest.ps1"
    runner_path.write_text(generate_batch_runner(instance))
    print(f"  ✅ Runner script: {runner_path}")

    print(f"\n{'=' * 55}")
    print(f"  Ready! Run:  powershell -ExecutionPolicy Bypass -File")
    print(f"               {runner_path}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
