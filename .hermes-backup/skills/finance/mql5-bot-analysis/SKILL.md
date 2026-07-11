---
name: mql5-bot-analysis
description: "Use when the user wants MQL5 Expert Advisor (EA) code analyzed, compared across versions, critiqued for trading weaknesses, or improved with better parameter tuning — reading UTF-16 encoded .mq5 files, identifying strategy flaws, and creating optimized versions."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [mql5, metatrader, forex, trading, ea, expert-advisor, btcjpy]
    related_skills: [personal-finance-analysis, delegated-qa-workflow]
---

# MQL5 Trading Bot Analysis

Analyze, critique, and improve MQL5 Expert Advisors (EAs). Read UTF-16 encoded `.mq5` files, extract the strategy parameters, identify common trading bot weaknesses, and create improved versions.

Support files:
- [`scripts/backtest_simulator.py`](scripts/backtest_simulator.py) — Python simulator using Binance BTC data
- [`scripts/optimization_grid.py`](scripts/optimization_grid.py) — Python grid-search optimizer (runs 100+ parameter combinations and ranks by Profit Factor)
- [`references/metatrader-tester-setup.md`](references/metatrader-tester-setup.md) — MT5 Strategy Tester configuration + optimization + .set file guide
- [`references/session-hybridbot-analysis.md`](references/session-hybridbot-analysis.md) — Detailed BTCJPY HybridBot V4.3 → V5.0 session notes
- [`references/session-bos-integration.md`](references/session-bos-integration.md) — BoS confirmation technique from LowDDWithBoS, MT5 Python API troubleshooting, multi-bot comparison methodology, .set file format, version evolution protocol
- [`references/session-v5-data-driven-optimization.md`](references/session-v5-data-driven-optimization.md) — Full-year BTCJPY market analysis (365 days), monthly volatility breakdown, regime-based parameter formulas, and the V4.3→V5.2a evolution with data-backed justification for each tuning decision. Use when the user wants market-data-driven parameter tuning.
- [`references/session-lowdd-optimization.md`](references/session-lowdd-optimization.md) — LowDDWithBoS backtest analysis and V5.0 optimization: 46% DD reduction, zone detection fixes, BodyStrengthMin tuning, compile-verification-after-patch pattern, and zero-trade root cause checklist.
- [`references/session-v5_2-optimization.md`](references/session-v5_2-optimization.md) — Full 8,281-pass MT5 optimization results (SL/TP grid), optimizer XML parsing, EA versioning conventions (why V5_1→V5_2 naming matters), backtest_runner.py + .set file generation workflow, and the key finding that wide SL + extreme TP with trailing outperforms narrow parameters on BTCJPY.

## When to Use

- User asks you to review their MQL5 trading bots
- User wants to know which bot is most promising
- User wants you to critique and improve a bot's parameters (SL, TP, RSI, trailing stop, equity protection)
- Comparing multiple versions of the same EA to understand evolution
- User wants improvements pushed to their MetaTrader Experts folder and GitHub

## Step 1: Locate MQL5 Files

MetaTrader stores EAs under the user's AppData roaming folder:

```bash
# Find all .mq5 files
find /c/Users/<user>/AppData/Roaming/MetaQuotes/Terminal/*/MQL5/Experts/ -name "*.mq5"
```

The folder structure is typically:
```
AppData/Roaming/MetaQuotes/Terminal/<INSTANCE_ID>/MQL5/Experts/<YOUR_BOT_FOLDER>/*.mq5
```

## Step 2: Read UTF-16 Encoded Files

MQL5 files use UTF-16 LE encoding. Python's `open` with `'rb'` + `.decode('utf-16-le')` handles this:

```python
with open(path, 'rb') as f:
    raw = f.read()
text = raw.decode('utf-16-le')
lines = text.split('\r\n')
```

The `read_file` tool will report these as binary. Use a Python script via `write_file` + `terminal` instead.

## Step 3: Extract Key Parameters

Read the `input group` and `input` parameter sections. Every EA has common tuning points:

| Parameter | What to check | Typical BTCJPY Issues |
|-----------|--------------|----------------------|
| `StopLossPercent` | Too tight? BTCJPY has 3-5% wicks | < 4.0% gets stopped out on noise |
| `TakeProfitPercent` | Realistic reward:risk? | Should be 1.5-2x SL |
| `RSIOverbought / RSIOversold` | Extreme levels that never trigger? | Oversold < 10 is unrealistic for BTCJPY; 20-30 is practical |
| `TrailingStopPct` | Premature trailing? | < 2.0% triggers on BTCJPY normal volatility |
| `ActivationEquityGain` | Reachable goal? | ¥2,000,000 gain is unrealistic for 0.01 lot; > ¥50,000 |
| `ZoneExpiryHours` | Appropriate for timeframe? | 4H zones need 48h+; 24h expires too early |
| `BodyStrengthMin` | Zone detection sensitivity | > 60% misses valid zones; 45-50% is better |
| `MaxEquityDDPct` | Kill switch sanity | 40% is very aggressive; 20-30% safer |
| `FixedLotSize` | Position sizing | 0.01 is minimum; check if it matches account size |

## Step 4: Analyze Strategy Types

Common MQL5 bot strategies and their weaknesses:

### Grid / Martingale
- **Signs:** `GridStepPoints`, `BasketTP`, `MaxTrades`, grid spacing
- **Weaknesses:** Unbounded grid in trending markets, geometric loss multiplication
- **Fix:** Hard cap on trades, trend filter (200 EMA), emergency equity stop

### Mean Reversion (EMA-based)
- **Signs:** `DeviationPct`, `EMA_Period`, `basketDir`
- **Weaknesses:** Trades against strong trends, no volatility filter
- **Fix:** Add RSI filter, add ATR-based deviation for adaptive entry, require trend confirmation

### Supply/Demand + BoS (Break of Structure)
- **Signs:** `ZoneTF`, `SZone`, `BodyStrengthMin`, `DetectZones`
- **Weaknesses:** Zone expiry too short, body strength too high (misses zones), no multi-timeframe confirmation
- **Fix:** Extend expiry, lower body strength threshold, add BoS confirmation

### MA Crossover
- **Signs:** `FastMAPeriod`, `SlowMAPeriod`, `SignalConfirm`
- **Weaknesses:** Whipsaw in ranging markets, fixed percentages don't adapt to volatility
- **Fix:** Add ATR-based adaptive stops, volatility filter (skip trading during high ATR)

### Equity Trailing
- **Signs:** `EquityProtection`, `MinimumEquityStop`, `TrailingEquityPercent`, `peakEquity`
- **Weaknesses:** Trailing starts too late (requires unrealistic gains), hard floor too low
- **Fix:** Lower activation threshold, add proportional trailing that scales with account

## Step 5: Common MQL5 Code Smells

- **`#property strict` missing** — should be present
- **`IndicatorRelease` not called in `OnDeinit`** — handle leak
- **`ObjectsDeleteAll` without prefix** — can delete other EAs' objects
- **`ExpertRemove()` used as loss stop** — terminates the EA permanently; use `protectionHalt = true` instead
- **Hardcoded symbol names** — use `_Symbol` instead
- **Missing `ArraySetAsSeries` before `CopyBuffer`** — wrong array ordering
- **Break-even logic that can override a better structural trail** — always check `if(newSL improves currentSL)` before modifying
- **Partial TP closing logic without `initialLot >= FixedLotSize` guard** — can repeatedly close fractions

## Step 6: Rate and Rank Bots

When comparing multiple bots, rank by:

1. **Strategy sophistication** — Supply/Demand + BoS > MA Crossover > Simple Grid > Fixed grid
2. **Risk management completeness** — Equity protection + trailing + break-even + partial TP + max daily loss
3. **Parameter realism** — SL wide enough for pair volatility, RSI levels that actually trigger
4. **Code quality** — Proper cleanup, no memory leaks, correct MT5 API usage
5. **Evolution** — Multiple version numbers with progressive improvements suggest active refinement

## Step 7: Market-Condition-Based Parameter Tuning

After identifying weaknesses and before creating an improved version, **analyze current market conditions** to tune parameters. Static parameters fail when volatility regimes change.

### Fetch live market data

```python
import MetaTrader5 as mt5
from datetime import datetime

if mt5.initialize():
    rates_d1 = mt5.copy_rates_from('BTCJPY', mt5.TIMEFRAME_D1, datetime.now(), 90)
    rates_h1 = mt5.copy_rates_from('BTCJPY', mt5.TIMEFRAME_H1, datetime.now(), 200)
    bid = mt5.symbol_info('BTCJPY').bid

    # ATR (14-day)
    tr = []  # true range values
    for i in range(1, len(rates_d1)):
        hl = rates_d1[i][2] - rates_d1[i][3]
        hpc = abs(rates_d1[i][2] - rates_d1[i-1][4])
        lpc = abs(rates_d1[i][3] - rates_d1[i-1][4])
        tr.append(max(hl, hpc, lpc))
    atr14 = sum(tr[-14:]) / 14
    atr_pct = atr14 / bid * 100

    # EMA200 (daily)
    closes = [r[4] for r in rates_d1]
    m = 2/201; ema200 = closes[0]
    for p in closes[1:]: ema200 = (p - ema200) * m + ema200
    price_vs_ema = (bid - ema200) / ema200 * 100

    # 20-day volatility
    d_highs = [r[2] for r in rates_d1[-20:]]
    d_lows = [r[3] for r in rates_d1[-20:]]
    vol20 = (max(d_highs) / min(d_lows) - 1) * 100
```

### Apply parameter formulas

| Parameter | Formula | Notes |
|-----------|---------|-------|
| **StopLoss** | `max(ATRpct × 2, 5.0)` | Need 2× ATR to survive noise |
| **TakeProfit** | `SL × 1.5` (bull) / `SL × 1.15` (bear) | Reduce TP in bear trends |
| **Trail Start** | `max(ATRpct, 3.0)` | Match to ATR |
| **RSI Overbought** | `58.5` (base) or `65` during bullish bounces | Loosen when price fights trend |
| **Max Trades/Day** | `vol20 > 10% ? 2 : 3` | Fewer in high vol |
| **Daily Loss Limit** | `vol20 > 10% ? 6% : 8%` | Tighter in high vol |
| **Zone Expiry** | `ATRpct > 3% ? 36h : 48h` | Faster expiry in volatile mkts |
| **Partial TP Trigger** | `SL × 0.6` | Bank profits earlier with wide SL |

### Regime assessment

| Regime | Priority Adjustments |
|--------|---------------------|
| **Bull + Normal vol** | Default settings; widen TP; keep 3 trades/day |
| **Bull + High vol** | Widen SL (ATR×2.5), widen trail, keep 3/day |
| **Bear + High vol** | Narrow TP, reduce trades to 2, enable tighter daily loss limit, lower partial TP trigger |
| **Bear + Extreme vol** | Max trades = 1, widest SL, trail = ATR×1.5, daily loss = 5% |

**Example:** In July 2026 BTCJPY was 9% below EMA200 (bear) with 14.7% 20-day vol (extreme). V5.1 widened SL from 5%→7%, reduced TP 10%→8%, tightened daily loss 8%→6%, and cut max trades from 3→2.

## Step 8: Create Improved Version

After identifying weaknesses:

1. Create a new file with an incremented version number (e.g., V4.3 → V5.0)
2. Add a changelog comment block at the top listing all fixes
3. Fix the input parameters (widen SL, adjust RSI, extend expiry, etc.)
4. Add missing features (daily loss limit, max trades per day, dynamic lot sizing)
5. Fix any code bugs found in the logic
6. Enable features that were disabled but beneficial (break-even, partial TP)

Save the improved version to:
- The MetaTrader Experts folder
- The user's GitHub repo

## Common Pitfalls

1. **UTF-16 decoding** — MQL5 files are NOT UTF-8. Using `open(path)` in Python will produce garbled text with null bytes between characters. Always use `'rb'` + `.decode('utf-16-le')`.
2. **`ActivationEquityGain` being unreachable** — On small accounts with 0.01 lots, ¥2,000,000 gain would take years. Set to ¥10,000-50,000 instead (represents a reasonable first profit target).
3. **RSI oversold at 5-10 is unrealistic** — On BTCJPY, RSI rarely goes below 20. Setting `RSIOversold = 7.5` means a sell signal almost never triggers.
4. **Trailing stop too tight for volatile pairs** — BTCJPY moves 1-2% regularly. A 1.5% trailing stop triggers almost immediately after entry.
5. **Zone expiry tied to clock, not trading sessions** — 4H zones detected at 1 AM expire at 1 AM the next day, which may be mid-session. 48h gives at least 2 full trading sessions.
6. **Naming conflicts between EA versions** — Each version should have a unique `MagicNumber` so they don't interfere when running simultaneously in backtest.
8. **Copying to wrong MetaTrader instance** — The `Terminal` folder has a GUID subfolder. Always verify the correct path.
9. **Python backtest max drawdown bugs** — When simulating in Python, the max drawdown calculation using equity peaks produces absurd values (106,908%) when balance skyrockets. Use running drawdown from peak balance, not equity-based peaks, and always caveat Python results as "directional only."
10. **OHLC-only simulation can't model wick hits** — A backtest that closes at candle close times will NEVER hit a stop loss that triggers mid-candle. Real trades get stopped out on intra-bar wicks. Python simulations overestimate win rates by 2-5x for this reason alone.
11. **Always save to both DEN_EA AND GitHub** — After creating or updating an .mq5 file, ALWAYS run cp to the DEN_EA folder AND git push to the MQLNewStrat2 repo. The user needs the file in both places or they can't use it immediately.
12. **protectionHalt must reset on new day** — When daily loss limit triggers (protectionHalt = true), OnTick() returns immediately and never reaches ResetDailyCounters(). The halt becomes permanent. Fix: call ResetDailyCounters() BEFORE the if(protectionHalt) return guard, and reset protectionHalt = false when the new day is detected.
13. **MT5 Python API connection order** — Terminal must be running AND logged into an account BEFORE mt5.initialize() succeeds. If IPC timeout or authorization fails: terminal may be in portable mode (no account), or numpy is incompatible. Install MetaTrader5 into the hermes venv's Python (which uses Python 3.11), not the system Python 3.9.

## Zero-Trade Root Cause Checklist

When a backtest produces **0 trades** (final balance == initial deposit in tester log), check:

1. **BodyStrengthMin too high** — Values >60% on H4 BTCJPY produce 0-1 zones per week. Practical range: 45-55%.
2. **Zone detection loop overwrite** — If DetectZones() iterates over both `r[1]` AND `r[2]`, the older bar's zone overwrites the newer one. **Fix:** Only check `r[1]` (last completed bar), never loop.
3. **Compile corruption after patches** — Patch operations on .mq5 files can accidentally delete function bodies (ManageTrailing, ManagePartialTP, etc.). Always compile via MetaEditor64.exe CLI after each patch cycle and verify .ex5 file size is non-zero.
4. **Missing `Print()` debugging** — Add debug prints in DetectZones() (zone prices, timestamps) and CheckSignals() (RSI, EMA, slope, and why each condition failed). Check the agent log at `Tester/<GUID>/Agent-*/logs/`.
5. **Daily loss stop stuck permanently** — If `protectionHalt` or `g_dailyLossStop` is set `true` and the reset logic is below the `if(halt) return` guard, the EA never reaches the reset. Ensure daily reset runs BEFORE the halt check.
6. **Consecutive loss cooldown blocking first trade** — Static variables in CheckSignals() (like `cooldownEnd`) can persist across ticks. If `g_consecutiveLosses` is initialized >= threshold, the first trade never fires.
7. **Indicator warmup not met** — EMA(88) needs 88 bars, RSI(14) needs 15, ATR(14) needs 15 before producing values. If test period is too short or data starts mid-session, indicators return nothing.
8. **EMA slope too strict** — Requiring `emaSlope > 0` (strictly rising) means no trades during flat or slightly declining EMA periods. Relax to `emaSlope > -0.5` to allow near-flat trends.
9. **RSI range too narrow** — `RSI >= 40 AND RSI < 70` combined with EMA and zone filters can create an impossible entry condition. Widen the range: `RSI >= 30 AND RSI < 75` for more entry opportunities.

### Verification: Print "Demand zone" / "Supply zone" to confirm zones trigger
```python
Print("Demand zone: " + DoubleToString(g_demand.pl, 0) + " - " + DoubleToString(g_demand.ph, 0));
Print("Supply zone: " + DoubleToString(g_supply.pl, 0) + " - " + DoubleToString(g_supply.ph, 0));
```
If no zone prints appear in the agent log, zones are never being created — check CopyRates for the ZoneTF timeframe and BodyStrengthMin threshold.

## Full-Year Market Analysis for Parameter Tuning

Pull 365+ days of daily data to understand the complete volatility regime before setting parameters:

```python
rates_d1 = mt5.copy_rates_from('BTCJPY', mt5.TIMEFRAME_D1, datetime.now(), 365)
# Compute monthly open/high/low/close, avg monthly range, ATR over 7/14/30 days
```

From actual full-year BTCJPY data (2025-07 to 2026-07, range 102.1%):
- Average monthly range: 20.4%
- SL = 30% of avg monthly range (~6%)
- TP = 50% of avg monthly range (~10%)
- Trail start = 15% of avg monthly range (~3%)
- Daily loss = tighter in bear markets (5% vs 8%)
- Max trades/day = reduced in high volatility (2 vs 3)

## Optimization: Run 8K+ Passes Across All Cores

When the user asks for parameter optimization:

1. **Prepare the .set file** — Use the `backtest_runner.py` pattern (or manual UTF-16LE .set file) with optimization ranges for SL, TP, RSI, etc.
2. **Set up the tester** — Select the EA, symbol (BTCJPY), period (M15), mode (real ticks), date range (at least 4 months)
3. **Enable all cores** — MT5 automatically uses multiple local agents (12 in this session). The optimization log shows `Core 01` through `Core 12`.
4. **Run optimization** — Wait for completion. Log shows: `optimization finished, total passes XXXX` and `Statistics: optimization done in X hours`
5. **Export results** — In MT5 Strategy Tester → Optimization Results tab → right-click → **Export to XML**
6. **Parse the XML** — It's Office XML Spreadsheet format. Columns: Pass, Result, Profit, Expected Payoff, Profit Factor, Recovery Factor, Sharpe Ratio, Custom, Equity DD %, Trades, StopLossATR, TakeProfitATR (or whatever params were optimized).
7. **Identify the best combo** — Sort by Profit Factor > 1.5, then by highest Profit. Check that DD% and trade count are reasonable.

### Key Optimization Finding (BTCJPY M15)

The optimization of 8,281 passes proved that **wide SL + extreme TP with trailing** beats narrow parameters:

| Setup | SL | TP | PF | Profit | DD% |
|-------|-----|----|-----|--------|-----|
| Narrow (V5 default) | 2.0 | 3.5 | 0.89 | -¥1,108 | 11.5% |
| Medium | 2.5-3.0 | 6-9 | ~1.2 | +¥4-6K | ~9% |
| **Best (V5_2)** | **3.6** | **12.95** | **1.63** | **+¥10,248** | **8.8%** |

The extreme TP (12.95x ATR) is NOT the exit mechanism — the **trailing stop** closes winning trades. The wide TP just acts as a safety net so trades aren't artificially capped. Wide SL prevents noise-induced stop-outs.

This pattern likely generalizes to other volatile JPY pairs. Always optimize SL/TP before touching entry filters.

## EA Versioning Convention

**USER PREFERENCE (Den Sanchez):** Every EA version MUST have a unique, numbered filename. The filename is how Den decides which one to test.

✅ Correct: `BTCJPY_LowDDWithBoS_Opt_V5_2.mq5`
❌ Wrong: `BTCJPY_LowDDWithBoS_Opt.mq5` (ambiguous)

Naming scheme:
```
<EANAME>_V<major>_<minor>.mq5
```
- Increment minor for parameter tweaks and bugfixes
- Increment major for strategy rewrites
- Each version needs a unique `MagicNumber` (increment by 1)

## Automating .set File Generation

Use the `backtest_runner.py` pattern to generate UTF-16LE .set files:

1. Define parameters as a list of tuples: `(name, default, start, step, stop, optimize?)`
2. Set `optimize=True` when generating for optimization runs
3. Write to UTF-16LE with `content.encode('utf-16-le')`
4. Save to: `%APPDATA%\MetaQuotes\Terminal\<INSTANCE>\MQL5\Experts\<FOLDER>\Sets\<EA_NAME>.set`

The .set file format:
```
; name=value||start||step||stop||selected
StopLossATR=3.6||1.0||0.5||5.0||Y
TakeProfitATR=12.95||5.0||1.0||20.0||Y
```

The `selected` column controls optimization checkboxes. `Y` = enabled, blank = disabled.
PowerShell runner example: see `run_backtest.ps1` in the session reference.

## Compile-Verify After Every Patch

MQL5 patch operations via `skill_manage(action='patch')` or `patch()` can accidentally delete function bodies. The ManageTrailing and ManagePartialTP functions are especially vulnerable because they use braces at similar indentation.

**Always** after patching an .mq5 file:
1. Convert to UTF-16LE: `iconv -f UTF-8 -t UTF-16LE source.mq5 > output.mq5`
2. Compile via MetaEditor64 CLI: `"MetaEditor64.exe" /compile:"<path>\<EA>.mq5"`
3. Verify .ex5 exists and has non-zero file size
4. If compile fails, check for: orphaned closing braces, missing function bodies, unclosed strings

The real MT5 Strategy Tester is the authoritative backtesting tool, but it may be unavailable if:
- The Python MetaTrader5 module can't connect (`IPC initialize failed`)
- Terminal authorization fails (`Terminal: Authorization failed`)
- The account isn't logged in or the terminal isn't running

**When this happens, build a simplified Python backtest** using exchange data (Binance API for BTC):

```python
# Fetch BTCUSDT 1H data via Binance API with pagination
import json, urllib.request
from datetime import datetime, timedelta

end = datetime.utcnow()
url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&endTime={int(end.timestamp()*1000)}&limit=1000"
# Paginate by chaining endTime backward to get 2000+ candles
```

### Backtest simulation guidelines

| Real MT5 Tester | Python Simulation Limitation |
|----------------|------------------------------|
| Every tick execution | OHLC only — can't model intra-bar wick hits |
| Spread + commission | Estimate as a fixed percentage |
| Slippage on market orders | Not modeled — results are optimistic |
| Overnight gap risk | Not modeled |
| Order queue priority | Not modeled |

**Therefore: treat Python simulation results as directional indicators only.** A simulation showing 100% win rate + 883% return likely overestimates by 2-5x. Use the real MT5 backtester for production decisions.

### Building a realistic simulation

Key features to include for a credible backtest:

```python
class Backtest:
    def __init__(self, candles):
        self.ema_period = 200
        self.sl_pct = 5.0
        self.tp_pct = 10.0
        self.trail_pct = 3.0
        self.partial_tp_pct = 5.0
        self.max_trades_per_day = 3
        self.max_daily_loss_pct = 8.0
        
        # Realistic costs
        self.spread_cost_pct = 0.02
        self.commission_per_trade = 500
```

Include:
- ✅ Spread + commission costs
- ✅ Daily loss limit (halts trading after X% daily loss)
- ✅ Max trades per day
- ✅ Trailing stop logic
- ✅ Partial TP logic
- ✅ Monthly profit tracking
- ❌ **Not included:** slippage, gap risk, partial fills

### Presenting simulation results

Always include a **caveat section** explaining why real results will differ:

```
⚠️ Important Caveat

The [X]% win rate and [Y]% return above are from a simplified Python
simulation, not the real MT5 Strategy Tester. The actual bot would face:
- Slippage — price can gap past your SL/TP during volatile moves
- Spread widening — BTCJPY spread can spike to 50,000+ points
- Execution delays — MT5 doesn't fill every trade at the exact price
- Overnight gaps — daily gaps can skip stops entirely

For real results, run the backtest inside MetaTrader 5 with:
- Mode: Every tick
- Symbol: BTCJPY, Timeframe: H1
- Initial deposit: ¥1,000,000
- Visual mode to watch trades execute
```

## Verification Checklist

- [ ] All `.mq5` files found and catalogued
- [ ] UTF-16 decoding successful (no null-byte artifacts)
- [ ] Key parameters extracted and analyzed
- [ ] Strategy type identified (grid, mean-reversion, S&D, MA crossover, etc.)
- [ ] Weaknesses itemized with specific parameter values
- [ ] Bots ranked by sophistication, risk management, and parameter realism
- [ ] Improved version created with changelog comment
- [ ] New version copied to MetaTrader Experts folder
- [ ] New version pushed to GitHub repo
