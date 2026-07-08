# MetaTrader 5 Strategy Tester Setup

## Prerequisites

- MT5 terminal running with an active account (demo or real)
- EA `.ex5` compiled and present in `MQL5/Experts/` folder

## When the MT5 Python API Fails

The `MetaTrader5` Python module requires IPC with the running terminal. Common failure modes:

| Error | Likely Cause |
|-------|-------------|
| `Terminal: Authorization failed` | Python's IPC can't authenticate with the terminal process. Try installing MetaTrader5 into the same Python that Hermes uses, not the system Python. |
| `IPC initialize failed` | Terminal not running or path is wrong. Verify with `tasklist | grep terminal64`. |
| `Process create failed` | Running Python as a different user than the terminal. Run both as same user. |

**Fix:** run `pip install MetaTrader5` with the exact Python interpreter Hermes uses (check `which python`), then retry. If still failing, use the manual MT5 tester below.

## Manual MT5 Strategy Tester (Recommended)

Run the user's EA through MT5's built-in Strategy Tester for accurate results.

### Step 1: Open Strategy Tester

In MT5: **View → Strategy Tester** (or `Ctrl+R`)

### Step 2: Configure Parameters

| Field | Value |
|-------|-------|
| **Expert Advisor** | Select the `.ex5` from the dropdown |
| **Symbol** | The trading pair (e.g. BTCJPY) |
| **Timeframe** | H1 (or the EA's intended timeframe) |
| **Date range** | Custom → pick the backtest period |
| **Deposit** | ¥1,000,000 (or match the demo account) |
| **Mode** | **Every tick** — most accurate |

(... existing content preserved ...)

---

## Running an Optimization (Grid Search Over Parameters)

An **optimization** tests many parameter combinations to find robust settings, not just a single profitable one.

### Step 1: Enable Optimization

In the Strategy Tester window, check the **Optimization** checkbox, then click the **"..."** button next to it to select which parameters to tweak.

### Step 2: Choose Parameters to Optimize

The most impactful optimization parameters (in priority order):

| Priority | Parameter | Why | Typical Range |
|:--------:|-----------|-----|:-------------:|
| 🥇 | `StopLossPercent` | Most sensitive — too tight = stopped out on noise | 4-8% (BTCJPY) |
| 🥇 | `TakeProfitPercent` | Must be proportional to SL | SL × 1.0 to SL × 2.0 |
| 🥈 | `TrailingStopPct` | Affects how much profit is locked in | 2-5% |
| 🥉 | `RSIOverbought / RSIOversold` | Controls entry frequency | OB: 55-75 / OS: 15-35 |
| 🏅 | `ZoneExpiryHours` | How long zones stay alive | 24-72h |

### Step 3: Set Ranges

| Parameter | Start | Step | End |
|-----------|:-----:|:----:|:---:|
| `StopLossPercent` | 4.0 | 0.5 or 1.0 | 8.0 |
| `TakeProfitPercent` | 6.0 | 1.0 | 12.0 |

**Rule of thumb:** Keep total combinations under 500 (9 × 7 × 7 = 441 is fine). More than that takes too long.

### Step 4: Read the Optimization Results Grid

After completion, the **Optimization Result** tab shows all tested combinations. Sort by:

| Column | Target | Red Flags |
|--------|:------:|:----------:|
| **Profit Factor** | > 1.5 ✅ | > 5.0 = likely overfit |
| **Max Drawdown %** | < 20% ✅ | > 30% = too risky |
| **Net Profit** | Positive ✅ | Check it isn't driven by 1-2 outlier trades |
| **# Trades** | 30-150 ✅ | < 15 = not statistically meaningful |
| **Sharpe Ratio** | > 1.0 ✅ | < 0.5 = not enough reward for risk |

### Step 5: Load Results Back

When the best parameter set is found, MT5 automatically applies it to the tester. To save it for the user to apply to their live EA:

1. In the EA's input dialog, click **Save** and choose a location for the `.set` file
2. The user can later click **Load** to restore these settings

### Creating a .set File Programmatically

When the user wants a ready-to-load `.set` file (e.g., after market analysis), create it with the `[Tester]` and `[ExpertParameters]` sections:

```ini
[Tester]
Expert=C:\Path\To\Expert.ex5
Symbol=BTCJPY
Period=H1
Optimization=1
Model=0
FromDate=2026.04.01
ToDate=2026.07.01
Deposit=1000000
Leverage=500

[ExpertParameters]
StopLossPercent=4.0|8.0|0.5
TakeProfitPercent=6.0|12.0|1.0
TrailingStopPct=2.0|5.0|0.5
FixedLotSize=0.01
; ... all other parameters with fixed values ...
```

The optimization range format is `Start|End|Step`. Parameters not being optimized use a single value.

The `.set` file can also be loaded into MT5 via:
```
terminal64.exe /config:"path\to\file.set"
```
This launches the tester with those settings pre-loaded (useful when the MT5 Python API fails). Note: this only reliably works when no other MT5 instance is already running.

## Python Grid Search (Fallback When MT5 Fails)

When the MT5 Python API can't connect (`IPC initialize failed`, `Authorization failed`), use `scripts/optimization_grid.py` to run a parameter grid search on cached or Binance-fetched BTC data.

### When to Use

- `MetaTrader5.initialize()` fails repeatedly
- The terminal is not logged in or authorization keeps failing
- The user wants quick directional results before committing to a 15-minute MT5 optimization run

### What It Does

The script:

1. Loads cached BTCJPY data (or fetches from Binance)
2. Iterates over all SL × TP × Trail combinations (typically 140-200 runs)
3. Simulates the strategy for each combination
4. Sorts results by **Profit Factor**
5. Saves the top results to `optimization_results.txt`

### Limitations

| MT5 Every Tick | Python OHLC Sim |
|----------------|-----------------|
| Models every price tick | Only sees open/high/low/close |
| Includes spread and slippage | Rough estimate only |
| Broker-accurate contract specs | Simplified P&L math |
| **Use for real decisions** | **Directional ranking only** |

### Interpretation

Focus on **relative ranking** (which parameters rank 1st, 2nd, 3rd), not the absolute P&L numbers (which will be off by a factor of 10-100x). A top-3 result of `SL=5%, TP=12%, Trail=2%` means those parameters are likely strong — but the actual ¥38M profit number is unreliable.

Click **Start**. For first runs, enable **Visual mode** to watch trades execute in real-time — this helps spot:
- Entry timing relative to zones/indicators
- SL/TP placement relative to price action
- Trailing stop behavior in trending moves

### Step 4: Read the Report

After completion, the **Report** tab shows:

| Metric | What to Look For |
|--------|-----------------|
| **Net Profit** | Positive over 3+ months |
| **Total Trades** | At least 20-30 for statistical significance |
| **Win Rate** | 40-60% is healthy for most strategies |
| **Max Drawdown** | Should not exceed 20-30% |
| **Profit Factor** | > 1.5 is good; > 2.0 is excellent |
| **Sharpe Ratio** | > 1.0 is acceptable; > 1.5 is good |
| **Recovery Factor** | > 2.0 suggests the bot recovers well from DD |

### Step 5: Save Results

Use **Report → Save as HTML** to keep a record. Compare runs across different parameter sets.

## XM Demo Account

When the user is on an XM demo account:
- **Server:** `XMTrading-MT5 5` or `XMGlobal-MT5`
- Backtest data availability depends on the broker's server
- Some brokers restrict backtest data to the last few months
- If BTCJPY isn't visible, right-click Market Watch → Symbols → Show BTCJPY

## Common Issues

- **"No data"** — The broker doesn't provide historical data for that symbol. Try switching to a different server or downloading data through Tools → History Center.
- **"Expert stopped"** — Check the Experts tab in the Terminal window for error messages. Common causes: missing DLL permissions, disabled automated trading (Ctrl+E), or invalid parameters.
- **Different results from Python simulation** — Expected. MT5's Every Tick mode models every price change including intra-bar wicks that OHLC-based Python simulations miss.
