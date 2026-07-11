# BTCJPY LowDDWithBoS V5.2 — Full Optimization Results

## Context

Session: Jul 10-11, 2026. Optimized BTCJPY_LowDDWithBoS EA across 4 versions (V4.3 original → V5 → V5_1 → V5_2) using MT5 Strategy Tester with 8,281 passes across 12 local cores over 2h 53m.

## EA Version History

| Version | Changes | Result |
|---------|---------|--------|
| V4.3 (original) | S/D zones, RSI(105) 7.5/58.5, EMA(579), SL 3.48%/TP 8% | 43 trades, +¥29K, 46% DD |
| V5 (Opt) | EMA(88), RSI(14) 40/60, Body 70, SL 1.5/TP 3.0 | 21 trades, -¥1,108, 11.5% DD |
| V5_1 | Body 55, RSI 30/60, SL 2.0/TP 3.5, dynamic bias, zone-on-new-bar-only | 0 trades (zone bug) → fixed → optimized |
| **V5_2** | **SL 3.6/TP 12.95 (optimized), Body 50, RSI 30/60** | **+¥10,248, PF 1.63, 8.8% DD, 35 trades** |

## Optimization Setup

- EA: BTCJPY_LowDDWithBoS_Opt_V5_1
- Symbol: BTCJPY, Period: M15
- Date: 2026.03.10 – 2026.07.10 (4 months)
- Mode: Real ticks (100% quality)
- Deposit: ¥50,000, Leverage: 1:1000
- Agents: 12 local cores
- Total passes: 8,281
- Duration: 2h 53m 52s
- Shortest pass: 8.8s, Longest: 20.7s, Average: 15.1s

## Optimized Parameters

| Parameter | Range Tested | Best Value |
|-----------|-------------|------------|
| StopLossATR | 1.0 – 5.0 (step 0.5) | **3.6** |
| TakeProfitATR | 2.0 – 20.0 (step 0.35) | **12.95** |

## Top 5 Passes

| Rank | Pass | SL | TP | Profit | PF | Sharpe | DD% | Trades |
|------|------|----|-----|--------|-----|--------|------|--------|
| 1 | 2465 | 3.6 | 12.95 | +¥10,248 | 1.633 | 5.52 | 8.8% | 35 |
| 2 | 2374 | 3.6 | 12.60 | +¥10,108 | 1.624 | 5.44 | 8.8% | 35 |
| 3 | 2283 | 3.6 | 12.25 | +¥9,996 | 1.618 | 5.39 | 8.8% | 35 |
| 4 | 2192 | 3.6 | 11.90 | +¥9,954 | 1.615 | 5.37 | 8.8% | 35 |
| 5 | 2557 | 3.8 | 13.30 | +¥9,560 | 1.565 | 4.82 | 8.0% | 35 |

## Key Finding: Trailing Does the Work

The optimal TakeProfitATR=12.95 is **extremely wide** — it's a safety net, not the exit mechanism. The trailing stop (activated at 1% profit, 0.6% offset) is what actually closes winning trades. The wide TP just prevents premature target-capping.

The optimization proved that:
- **Narrow SL/TP** (1.5/3.0) = stopped out by noise, negative PF
- **Medium SL/TP** (2.0/3.5) = still too tight for BTCJPY M15 volatility
- **Wide SL + extreme TP** (3.6/12.95) = trades breathe, trailing locks profits

This aligns with the "LowDD" design philosophy — wide stops prevent noise-induced losses, trailing protects gains.

## Optimizer XML Column Reference

When exporting optimization results from MT5 as XML format, the columns are:

| Column | XML Path | Type | Notes |
|--------|----------|------|-------|
| Pass | Cell[0] | Number | Pass ID |
| Result | Cell[1] | Number | Custom result metric |
| Profit | Cell[2] | Number | Net profit in JPY |
| Expected Payoff | Cell[3] | Float | Avg profit per trade |
| Profit Factor | Cell[4] | Float | Gross profit / gross loss |
| Recovery Factor | Cell[5] | Float | Net profit / max DD |
| Sharpe Ratio | Cell[6] | Float | Risk-adjusted return |
| Custom | Cell[7] | Number | Custom optimization metric |
| Equity DD % | Cell[8] | Float | Max equity drawdown % |
| Trades | Cell[9] | Number | Total trade count |
| StopLossATR | Cell[10] | Float | Optimized SL value |
| TakeProfitATR | Cell[11] | Float | Optimized TP value |

## .opt File Location

MT5 stores optimization results at:
```
%APPDATA%\MetaQuotes\Terminal\<INSTANCE>\tester\cache\<EA>.<SYMBOL>.<TF>.<FROM>.<TO>.<HASH>.opt
```

These are binary files in MT5 proprietary format. To read them:
- Export from MT5 Strategy Tester → Optimization Results tab → right-click → Export to XML
- The XML is Excel-compatible (Office XML Spreadsheet format)
- Parse columns using the reference above

## EA File Versioning Convention

**Rule: Every version MUST have a unique, numbered filename so the user knows which to test.**

Good: `BTCJPY_LowDDWithBoS_Opt_V5_2.mq5`
Bad: `BTCJPY_LowDDWithBoS_Opt.mq5` (ambiguous — which version?)

Version scheme:
- V5 → first optimized version
- V5_1 → bugfix/iteration
- V5_2 → optimized parameters applied

Each version also needs a unique MagicNumber (increment by 1) so they don't conflict when run simultaneously.

## File Locations

- Source: `C:\Users\decni\projects\POGIBOT\backend\btcjpy_optimized.mq5`
- Compiled EA: `%APPDATA%\MetaQuotes\Terminal\<INSTANCE>\MQL5\Experts\DEN_EA\BTCJPY_LowDDWithBoS_Opt_V5_2.ex5`
- Set file: `%APPDATA%\MetaQuotes\Terminal\<INSTANCE>\MQL5\Experts\DEN_EA\Sets\BTCJPY_LowDDWithBoS_Opt_V5_2.set`
- Tester results: `%APPDATA%\MetaQuotes\Terminal\<INSTANCE>\tester\cache\*.tst`
- Tester logs: `%APPDATA%\MetaQuotes\Terminal\<INSTANCE>\tester\logs\*.log`
- Agent logs: `%APPDATA%\MetaQuotes\Tester\<INSTANCE>\Agent-*\logs\*.log`
- Python tools: `C:\Users\decni\projects\POGIBOT\backend\backtest_runner.py`
- PowerShell runner: `C:\Users\decni\projects\POGIBOT\backend\run_backtest.ps1`
- Batch runner: `C:\Users\decni\projects\POGIBOT\backend\backtest_den_ea.bat`

## Fixing Zero-Trade EAs (Root Cause Checklist from this session)

1. BodyStrengthMin too high (70 → 55 → 50)
2. Zone detection loop overwriting (checking r[1] AND r[2]; fix: only r[1])
3. Patch corruption deleting ManageTrailing/ManagePartialTP function bodies (always compile-verify after patches)
4. Missing Print() → no diagnostics. Add zone/signal prints.
5. Daily loss stop stuck (reset logic below the halt guard)
6. Consecutive loss cooldown static variable blocking first trade
7. EMA slope too strict (> 0) → relax to > -0.5
8. RSI range too narrow (40-70) → widen to 30-75
