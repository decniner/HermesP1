# Session: BTCJPY Hybrid Bot V4.3 → V5.0 → V5.1 Analysis (July 3, 2026)

## Bots Found

12 MQL5 bots under `AppData/Roaming/MetaQuotes/Terminal/<ID>/MQL5/Experts/DEN_EA/`.

## Bots Analyzed

### 1. BTCJPY_QuantumKingv1.2.mq5
- **Strategy:** Mean-Reversion Grid (200 EMA + 1.5% deviation)
- **Size:** 21KB, 345 lines
- **Strengths:** Clean code, dashboard, emergency equity stop
- **Weaknesses:** Too simple, no trend filter, no dynamic sizing, no partial TP, no trailing stop
- **Verdict:** Basic; outperformed by HybridBot

### 2. BTCJPY_HybridBot.mq5 & BTCJPY_LowDDWithBoS.mq5
- **Strategy:** Structural Supply/Demand + Break of Structure (V4.30)
- **Size:** 67-71KB, 764-817 lines
- **Strengths:** Institutional-grade S&D zones, multi-filter (RSI, MA trend, spread), intelligent trailing with dynamic lookback, partial TP, equity trailing, directional flip loss filter, full dashboard with monthly P&L grid
- **Weaknesses (fixed in V5.0):**
  - SL 3.48% too tight for BTCJPY (regular wicks 3-5%)
  - RSI Oversold = 7.5 (virtually never triggers on BTCJPY)
  - Trail start 1.5% (triggers on normal volatility)
  - ActivationEquityGain = ¥2,000,000 (unreachable for 0.01 lot)
  - Zone expiry 24h (too short for 4H)
  - BodyStrengthMin = 60 (misses valid zones)
  - Break-Even OFF, Partial TP OFF
  - No daily loss limit
  - No max trades per day

### 3. BTCJPY_BotEQTrailProximityArrow.mq5
- **Strategy:** MA Crossover (10/98) + Proximity Signal
- **Size:** 70KB, 807 lines
- **Strengths:** Percentage-based stops, ATR volatility filter, spread filter, equity protection
- **Weaknesses:** MA crossovers whip in ranging markets, fixed percentages don't adapt
- **Verdict:** Solid but conservative; S&D strategy preferred

## V5.0 Improvements Applied

| Parameter | V4.3 | V5.0 | Rationale |
|-----------|------|------|-----------|
| StopLossPercent | 3.48% | 5.0% | BTCJPY wick tolerance |
| TakeProfitPercent | 8.0% | 10.0% | Maintain 1:2 RR with wider SL |
| RSIOversold | 7.5 | 25.0 | Realistic trigger level |
| TrailingStopPct | 1.5% | 3.0% | Avoid noise-triggered trailing |
| UseBreakEven | false | true | Capital protection |
| UsePartialTP | false | true (30%) | Bank early profits |
| ActivationEquityGain | ¥2,000,000 | ¥50,000 | Reachable target |
| ZoneExpiryHours | 24 | 48 | Full 2-session lifespan |
| BodyStrengthMin | 60 | 50 | Capture more valid zones |
| MaxTradesPerDay | N/A | 3 | Prevent overtrading |
| MaxDailyLossPercent | N/A | 8.0% | Account protection |
| UseDailyLossLimit | N/A | true | New feature |
| BE_BufferPct | 0.2% | 0.5% | Safer buffer |
| PartialClosePct | 50% | 30% | Keep more position |
| Structural trail buffer | 500pts | 300pts | Tighter lock-in |

## V5.1: Market-Tuned for Current Conditions (July 2026)

After analyzing real-time market data via MT5 on account 75574235, V5.1 adjusts all parameters for the current BTCJPY regime:

### Market Snapshot (July 3, 2026)
| Metric | Value |
|--------|-------|
| Price | ¥10,013,683 |
| 90-Day Range | ¥9.39M–¥12.97M (38.1%!!) |
| Daily EMA200 | ¥11,006,428 (price **9% below** → bearish) |
| Hourly EMA50/200 | Bullish (short-term bounce) |
| 14d ATR | ¥345,914 (3.45%) |
| 20d Volatility | 14.7% |
| Hourly RSI | 62.2 |
| Support | ¥9,393,627 |
| Resistance | ¥10,774,523 |

**Regime assessment:** Bearish long-term (below EMA200) with a short-term bullish bounce inside extreme volatility (38.1% range). Classic bear market rally environment where tight stops get killed and profits need to be taken earlier.

### V5.1 Parameter Changes

| Parameter | V5.0 | V5.1 | Rationale |
|-----------|------|------|-----------|
| **StopLossPercent** | 5.0% | **7.0%** | ATR 3.45% × 2 = need 7% to survive wicks in 14.7% volatility regime |
| **TakeProfitPercent** | 10.0% | **8.0%** | Bear market: rallies fail. Take profit faster (still maintain positive RR at 7% SL / 8% TP = 1.14:1) |
| **TrailingStopPct** | 3.0% | **4.0%** | Widen trail to avoid being shaken out during 3.45% daily swings |
| **RSIOverbought** | 58.5 | **65.0** | Current bounce pushes RSI to 62 — 58.5 was blocking valid long entries |
| **BE_TriggerPct** | 2.0% | **3.0%** | Higher bar before break-even in high-vol market (2% profit can vanish in 1 candle) |
| **PartialTP_TriggerPct** | 5.0% | **4.0%** | Bank profits earlier in bear market rallies |
| **PartialClosePct** | 30% | **40%** | Take more off the table in a downtrend |
| **MaxTradesPerDay** | 3 | **2** | Reduce exposure in extreme volatility |
| **MaxDailyLossPercent** | 8.0% | **6.0%** | Tighter risk control when markets swing 14.7% |
| **ZoneExpiryHours** | 48h | **36h** | Zones expire faster in fast-moving market |
| **MagicNumber** | 987113 | 987114 | Unique ID for parallel backtest comparison |
| **Structural trail tighten** | 4%/8% | 5%/9% | Slightly later tightening to avoid trailing on intra-volatility |

### Formula for Market-Tuning Parameters
```
SL = max(ATR_pct × 2, base_SL)
TP = max(SL × 0.85, base_TP × 0.85)   // reduced in bear, maintained in bull
Trail = max(ATR_pct, base_trail)
RSI_OB = base_OB + (current_RSI - 50) × 0.3  // adaptive to current market
MaxTrades = volatility > 10% ? 2 : 3
DailyLoss = volatility > 10% ? 6% : 8%
```

### MetaTrader5 Python API Issues Encountered

The `MetaTrader5` Python module had persistent connection issues on this system:

| Error | Cause | Resolution |
|-------|-------|------------|
| `Terminal: Authorization failed` | IPC handshake fails between Python and running terminal | Try `mt5.initialize()` (no args) first; fall back to `mt5.initialize(path=exe_path)`; if both fail, user must run Strategy Tester manually |
| `IPC initialize failed` | Terminal process not shareable from Python | Kill terminal, restart, retry. Or use system Python (not venv) |
| `IPC send failed` | Terminal killed during prior attempt | Clean restart needed |
| numpy incompatibility | Hermes venv had numpy compiled for Python 3.11, but Hermes ran Python 3.9 | `pip install numpy==1.26.0 MetaTrader5 --force-reinstall` |

**Bottom line:** The MT5 Python module is unreliable for automation on Windows. When possible, guide the user to run the Strategy Tester manually in the MT5 GUI.

### Python Backtest Simulation Pitfalls

The Binance API + Python simulation backtest showed wildly unrealistic results:
- V5.0 simulation: 180–883% return, 100% win rate, 0% max DD
- V5.1 simulation: 4018% return, 50% win rate (buggy)

Root causes of simulation inaccuracy:
1. **OHLC-only data** — Can't model intra-candle wick hits (SL/TP triggers during the candle, not at close)
2. **Wrong lot/contract math** — BTCJPY contract specs (1 lot = 100,000 JPY per point) are hard to replicate correctly
3. **Max drawdown calc bug** — Using simple equity peaks causes absurd DD values (106,908%) when balance skyrockets
4. **No slippage model** — Market orders fill at worse prices in reality
5. **Gap risk** — Weekend / overnight gaps skip SL entirely

**Lesson:** Never present Python simulation results as factual. Always caveat with "directional only, verify in MT5 Strategy Tester on Every tick mode."

## Key Insight

The HybridBot V4.30 was the clear winner because it combines Supply/Demand zone detection (institutional-grade concept) with multi-timeframe confirmation, multiple filters, and a comprehensive safety suite. Earlier bots were progressively testing simpler approaches (grid, MA crossover) that the user outgrew.

The V5.1 refinement showed that **parameter tuning must be market-regime aware** — static parameters that work in one volatility environment fail in another. The ATR-based SL formula (ATR × 2) is a more robust approach than fixed percentages.
