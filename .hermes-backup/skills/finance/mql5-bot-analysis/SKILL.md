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

## Step 8: Backtest Simulation (when MT5 terminal is inaccessible)

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
