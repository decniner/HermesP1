---
name: mql5-ea-development
description: Build, backtest, analyze, and optimize MetaTrader 5 Expert Advisors — reading MQL5 source, interpreting Strategy Tester reports, identifying performance issues, and iterating on parameters.
category: software-development
triggers:
  - "build / rewrite an MQL5 Expert Advisor"
  - "debug / fix / optimize an EA"
  - "analyze MetaTrader Strategy Tester report"
  - "backtest a forex/crypto EA on real ticks"
  - "improve EA performance metrics (profit factor, drawdown, win rate)"
version: 1.0.0
---

# MQL5 EA Development — Analysis & Optimization

## Overview

Class-level guide for working with MetaTrader 5 Expert Advisors: reading source code, running backtests, interpreting reports, and iterating on strategy logic.

## ⚠️ Mandatory: QA Protocol (User Expectation)

**QA your own work before reporting.** The user will say: *"Not working, qa it yourself to make sure it works before asking me."* Do not skip.

1. **After compilation** — verify `.ex5` file exists and has nonzero size
2. **After strategy changes** — run one backtest to confirm trades fire
3. **Check tester logs** — look for `final balance` line, verify trades occurred
4. **Verify inputs** — confirm the report shows the intended parameters, not stale ones
5. **Report** — only after all above pass

Diagnose and fix silently. Never ask the user to check if a version works.

## Key Skills Required

1. **Reading MQL5 source** — MQL5 files are UTF-16 LE encoded. Use `iconv -f UTF-16 -t UTF-8 file.mq5` to read them in terminal, or open in MetaEditor.
2. **Running backtests** — MT5 Strategy Tester with real ticks for accuracy. Visual mode is slower but lets you watch.
3. **Interpreting reports** — Focus on: Profit Factor, Sharpe Ratio, Max Drawdown, Recovery Factor, Consecutive Losses, Avg Win/Avg Loss ratio.
4. **Identifying issues** — Common problems and their symptoms.
5. **Iterative optimization** — One parameter change at a time, track results in versioned filenames.

## Compilation

MQL5 source must be compiled via MetaEditor64.exe:

```bash
# Convert from UTF-8 source to UTF-16 LE for MT5
iconv -f UTF-8 -t UTF-16LE source.mq5 > "path/to/MQL5/Experts/DEN_EA/FILENAME.mq5"

# Compile via MetaEditor CLI
"/c/Program Files/MetaTrader 5/MetaEditor64.exe" /compile:"C:\full\path\to\FILENAME.mq5"
```

The `.ex5` binary is generated in the same directory. Check file timestamp after compile to confirm.

## Reading an EA's Strategy

Focus on these sections when analyzing MQL5 source:

### Input Parameters
Look at the `input` variables — these are the tunable knobs:
- `MagicNumber` — unique ID per EA (must differ between versions)
- Indicator periods (EMA, RSI, MACD)
- Risk settings (lot size, SL/TP, trailing)
- Filter toggles (RSI filter, spread filter, long bias)

### Indicator Handles
```mql5
emaHandle = iMA(_Symbol, PERIOD_CURRENT, EMAPeriod, 0, MODE_EMA, PRICE_CLOSE);
rsiHandle = iRSI(_Symbol, PERIOD_CURRENT, RSIPeriod, PRICE_CLOSE);
atrHandle = iATR(_Symbol, PERIOD_CURRENT, 14);
```

### Entry Logic (`CheckSignals()` or `OnTick()`)
Identify the exact conditions for long and short entries:
- Price vs EMA (above/below)
- RSI thresholds
- Supply/Demand zone proximity
- EMA slope (bullish/bearish)
- Candlestick confirmation patterns

### Exit Logic
- Fixed SL/TP percentages
- ATR-based trailing
- Partial profit taking
- Break-even logic
- Time-based expiry

## CRITICAL: User-Specified Architectures Underperform

When a user provides detailed architectural specifications for a ground-up EA build, the result **almost always underperforms** compared to iterative optimization of an existing working EA.

This session's evidence:
- Sniper V1, V1_1, V2: built per user's "elite MQL5 Quantitative Developer" specs — **all lost money**
- V5.2: built by taking the original EA and running automated parameter optimization — **profitable**

**Rule:** Never build from scratch based on user specs unless there's a clear, simple winning path. Start from the closest working EA, optimize its parameters, then iterate. A new architecture is a multi-session commitment, not a quick fix.

## Delivery: Always Tell the User the Exact Filename

When delivering a new EA for testing, state the **exact filename** in a standalone line — do not bury it in a paragraph. The user said: *"You need to tell me each time what is the EA filename i should test."*

```
Test BTCJPY_LowDDWithBoS_Opt_V5_2 in the Strategy Tester.
```

Every version bump gets its filename called out explicitly at delivery time.

## Providing File Paths

When the user asks for a file location, always provide the **full absolute path starting from `C:\`**, not a relative or shortened path. Example:

```
C:\Users\decni\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\DEN_EA\Sets\BTCJPY_LowDDWithBoS_Opt_V6.set
```

Not `...\DEN_EA\Sets\...` or `~/AppData/...`

## Versioned Filenames (CRITICAL preference)

**Each iteration MUST have a unique, sequential version in the filename.** This user tracks EAs by filename — `_V5`, `_V5_1`, `_V5_2`, etc.

```mql5
// BAD — user can't tell which is which
BTCJPY_LowDDWithBoS_Opt.mq5
BTCJPY_LowDDWithBoS_Opt.mq5  (overwritten!)

// GOOD — clear progression
BTCJPY_LowDDWithBoS_Opt_V5.mq5
BTCJPY_LowDDWithBoS_Opt_V5_1.mq5
BTCJPY_LowDDWithBoS_Opt_V5_2.mq5
```

Also update the `#property version` directive inside the source file to match:
```mql5
#property version   "5.10"
```

## Interpreting Strategy Tester Reports

### Key Metrics (ranked by importance)

| Metric | What It Measures | Good | Warning | Bad |
|--------|-----------------|------|---------|-----|
| **Profit Factor** | Gross Profit / Gross Loss | > 1.5 | 1.0–1.5 | < 1.0 |
| **Max Drawdown %** | Peak-to-trough equity drop | < 15% | 15–30% | > 30% |
| **Sharpe Ratio** | Risk-adjusted return | > 1.0 | 0–1.0 | < 0 |
| **Win Rate** | % of profitable trades | > 50% | 35–50% | < 35% |
| **Avg Win / Avg Loss** | Reward-to-risk ratio | > 2:1 | 1.2–2:1 | < 1.2 |
| **Recovery Factor** | Net Profit / Max DD | > 1.0 | 0.5–1.0 | < 0.5 |
| **Consecutive Losses** | Worst losing streak | < 3 | 3–5 | > 5 |

### Report Sections to Check

1. **Settings** — Verify the input parameters match what you intended. MT5 logs all inputs at the top of the report.
2. **Results** — History Quality must be 100% real ticks for any meaningful conclusion. Lower quality = unreliable.
3. **Orders** — Check that both long AND short trades fired if the strategy should trade both directions. If only one side trades, check the bias/filter.
4. **Deals** — Look at the balance curve: steady climb vs sharp drops. Check swap/commission costs.

### Common Issues & Their Symptoms

**Issue: Zero trades**
- Check if `PositionsTotal() > 0` guard is blocking re-entry
- Check if EMA/RSI need warmup period (indicator handles need N bars)
- Check if BodyStrengthMin is too high for zone detection
- Check if RSI oversold threshold is unreachable (e.g., oversold = 7.5 on RSI 105)
- Check if long bias is blocking shorts in a downtrend

**Issue: Only one direction trades**
- `LongBiasEnabled = true` but EMA slope is bearish — no shorts allowed
- Dynamic bias: if EMA slope threshold is too tight (> 0), flat EMA blocks all trades
- **Fix:** Use a small deadband (e.g., `slope > -0.5` for longs, `slope < 0.5` for shorts) instead of strict zero

**Issue: High drawdown (> 30%)**
- SL too tight → getting stopped out, re-entering in worse position
- Consecutive losses stacking → no cooldown mechanism
- **Fix:** Widen SL (increase StopLossATR), add max-consecutive-loss cooldown, add daily loss limit

**Issue: Profit Factor < 1.0**
- Winners not big enough relative to losers
- Too many small SL hits eating into gains
- **Fix:** Increase TakeProfitATR relative to StopLossATR (target 2:1 or better), use partial profit taking to lock gains

**Issue: Single trade only (confirm-bar uses forming bar, not completed bar)**

- EA placed 1 trade in a 1-year backtest then stopped firing
- **Root cause:** The confirm-bar check used `m15[0]` (the **current forming bar**) instead of `m15[1]` (the **last completed bar**). Index 0 changes every tick because the bar is still forming:
  ```mql5
  // WRONG — m15[0] is the forming bar; close/open flip on every tick
  for(int i=0; i<ShortConfirmBars; i++) {
      if(m15[i].close < m15[i].open) confirm++;  // unreliable
  }

  // RIGHT — m15[1] is the last COMPLETED candle (fixed)
  bool bearCandle = m15[1].close < m15[1].open;
  bool bullCandle = m15[1].close > m15[1].open;
  ```
- After the first trade closed (via SL), the forming bar's close/open ratio may never satisfy the confirm condition again, so no new trades ever fire
- **Fix:** Always use index `1` for the last completed bar's close/open. Use index `2` for the bar before that. Never use index `0` for candle pattern confirmation.

**Issue: Zone spam in tester logs**
- `DetectZone()` called on every tick prints the same zone repeatedly
- **Fix:** Track `g_lastZoneBar` and only detect when a new H4 bar completes

**Issue: Over-filtering (too many gates → no trades OR late entries)**

Layering multiple independent filters (H4 zones AND M15 BoS AND RSI AND candle confirm AND spread check AND directional lock) creates an architecture where each filter gates out trades. When all stack up, the EA either:
- Fires zero trades (no combination satisfies all gates)
- Enters so late that the move is exhausted (by the time zone + BoS + confirm all align)

This was the root cause of the Sniper V1→V2 series failures on BTCJPY. Each version added more filters ("institutional grade") and each version traded worse.

**Fix:** Prune filters ruthlessly. Run the EA with ONE filter, verify it trades, then add ONE more at a time. The V5_2 succeeded because it had exactly: zone detection + trailing stop + loss protection. That's it — no RSI, no BoS, no candle confirm, no directional flip.

**Rule of thumb for BTCJPY:** If the entry condition has more than 4 boolean checks, you're over-filtering. Strip it down and let the trailing stop do the work.



## Common Bugs in EA Code

### Code-Path Splitting Bug

When refactoring to support two input modes (e.g., URL vs file upload), a variable set inside one branch may be referenced outside it:

```mql5
// BUG: normalized_url only set in the "else" branch
if(source_type == "file_uri") {
   contents = [user_text, file_part];
} else {
   normalized_url = Normalize(url);
   contents = [user_text, url_part];
}
// Later uses normalized_url — CRASH when source_type is "file_uri"
```

**Fix:** Assign a single result variable in both branches.

### Window Port 5000

Port **5000** is reserved by `Universal.Server` on Windows 10/11. Always use port **5001+** for Flask/MT5 tester agents.

### Lazy API Client Init

Never init indicator handles or API clients at global scope in `OnInit()` — but in MQL5 this IS the pattern. For Python backends, use lazy init with error messages.

## Parameter Optimization Heuristics

### From this session's data:

**Original EA (V4.3)**: 43 trades, +¥32,638, Win Rate 38.3%, DD 46%
- BodyStrengthMin=60, EMAPeriod=579, RSI(105) 7.5/58.5

**Opt V5 (first attempt)**: 21 trades, -¥1,108, Win Rate 42.86%, DD 11.5%
- BodyStrengthMin=70, EMAPeriod=88, RSI(14) 40/60, LongBias=true
- Lower drawdown but less profitable. LongBias prevented shorts in downtrend.

**Opt V5_1 (8281-pass optimization)**: SL=3.6/TP=12.95 → **+¥10,248 (20.5%), PF 1.63, DD 8.8%, 35 trades**
- 12 local cores, 2h 53m, 8281 combinations of SL/ATR and TP/ATR
- **Best found:** StopLossATR=3.6, TakeProfitATR=12.95
- Key insight: the wide TP is a backstop — the trailing stop (activated at 1%) actually locks profits much earlier. The wide SL prevents premature stop-outs.
- Sharpe 5.52, Recovery Factor 2.11 — excellent risk-adjusted metrics

### Typical improvement strategies:

1. **Widen SL/TP** — Reduces SL hits, improves RR ratio
2. **Dynamic bias** — Let the market direction decide, don't hardcode
3. **Add loss cooldown** — Pause after N consecutive losses
4. **Add daily loss limit** — Stop trading after X% daily drawdown
5. **Reduce zone strength requirements** — More zones = more trades
6. **Switch to shorter RSI** — 14-period responds faster than 105-period
7. **Track one change per iteration** — Otherwise you can't attribute results

## Reference Files

See `references/btcjpy-ea-session.md` for the complete session transcript: all backtest results, parameter changes, and result analysis from the BTCJPY_LowDDWithBoS optimization cycle.

## Reading Optimizer XML Reports

MT5 can export optimization results as XML (Excel-compatible format). Parse them to find the best parameter combinations:

### XML Structure

```xml
<Row>
  <Cell><Data ss:Type="Number">54</Data></Cell>              <!-- Pass -->
  <Cell><Data ss:Type="Number">-13</Data></Cell>             <!-- Result (custom) -->
  <Cell><Data ss:Type="Number">13055</Data></Cell>           <!-- Profit -->
  <Cell><Data ss:Type="Number">1631.875</Data></Cell>        <!-- Expected Payoff -->
  <Cell><Data ss:Type="Number">2.073249</Data></Cell>        <!-- Profit Factor -->
  <Cell><Data ss:Type="Number">0.324831</Data></Cell>        <!-- Sharpe Ratio -->
  <Cell ss:StyleID="ce11"><Data ss:Type="Number">13.3125</Data></Cell>  <!-- Equity DD % -->
  <Cell><Data ss:Type="Number">8</Data></Cell>               <!-- Trades -->
  <!-- Then parameter columns in order -->
  <Cell><Data ss:Type="Number">317</Data></Cell>             <!-- SlowMAPeriod -->
  <Cell><Data ss:Type="Number">10.092</Data></Cell>          <!-- StopLossPercent -->
  <Cell><Data ss:Type="Number">71.2</Data></Cell>            <!-- TakeProfitPercent -->
</Row>
```

### How to parse in conversation

1. Read the first 20-30 rows from the XML (sorted by best result)
2. Check column headers above data rows to know parameter order
3. Focus on **Profit Factor** as primary ranking, **Net Profit** as secondary
4. Trade off between PF, DD%, and Trade Count — PF 2.0 with 3 trades is unreliable
5. Cross-check parameters against the EA's declared inputs

### Example: This Session's Optimizations

**8,281-pass optimization on V5_1 (SL/ATR + TP/ATR):**
- Best pass #2465: SL=3.6, TP=12.95 → +¥10,248, PF 1.633, DD 8.8%, 35 trades

**19,000+ pass optimization on original EA (SL% + TP%):**
- Best pass #54: SlowMA=317, SL=10.09%, TP=71.2% → +¥13,055, PF 2.073, DD 13.3%, 8 trades
- PartialTP=true (trigger 8.5%), UseLTFConfirmation=true, BoSLookback=47

### Pass Viability Criteria

- PF ≥ 1.5, DD ≤ 15%, Trades ≥ 10, Sharpe ≥ 1.0
- Extreme parameters that worked in one period likely won't generalize

## See Also

- `self-hosted-python-web-apps` — For Python-based trading dashboards (Streamlit/yfinance)
- `python-web-tunnel` — For tunneling local servers to mobile access

## Backtest Automation (.set Files & Runner Scripts)

MT5 stores EA input parameters in `.set` files (UTF-16LE format). These can be auto-generated and loaded in the Strategy Tester.

### .set File Format

```
; comments start with semicolons
; name=value||start||step||stop||selected
MagicNumber=987659||987659||1||987659||Y
BodyStrengthMin=50||30||5||70||Y
```

- `||` delimiters separate value, optimization-start, optimization-step, optimization-stop
- Checkbox with `Y` marks a parameter for optimization
- Files must be **UTF-16LE encoded**

### Generation Script

Use a Python script to generate .set files with proper encoding:

```python
path.write_bytes(content.encode("utf-16-le"))
```

### Runner Script

A PowerShell script automates the workflow:

```powershell
# Detect MT5 terminal instance
$terminalData = "$env:APPDATA\MetaQuotes\Terminal"
$instance = Get-ChildItem $terminalData | Where-Object { $_.Name -notin @("Common","Community") } | Select-Object -First 1

# .set file goes under the Sets directory
$setDir = "$terminalData\$instance\MQL5\Experts\DEN_EA\Sets"
```

### metatester64.exe Limitations

`metatester64.exe` requires the full MT5 terminal GUI. CLI flags (`/help`, `/?`) hang without a desktop session. The Strategy Tester must be launched from the terminal GUI:
1. Open MT5
2. View → Strategy Tester
3. Select EA, symbol, timeframe, date, mode
4. Inputs tab → Load → .set file
5. Start

### Optimization Workflow

1. Generate .set with optimization ranges (start/step/stop for each parameter)
2. In Strategy Tester Inputs tab, click Load → select the .set
3. Check boxes next to parameters to optimize
4. Click Start — MT5 runs all combinations
5. Analyze the optimization results table for best parameter sets

## Dynamic Long/Short Bias Design Pattern

A common EA problem is getting stuck in one direction during trend changes. Use a **dynamic bias** instead of hardcoded `LongBiasEnabled`:

```mql5
// Slope as percentage of price for normalization
double slopePct = (ema[0] - ema[1]) / ema[0] * 100;

// Dynamic bias: EMA slope > 0.01% = bullish, < -0.01% = bearish
bool trendUp  = slopePct >  0.01;
bool trendDn  = slopePct < -0.01;
bool canLong  = trendUp || (!trendDn && consecutiveLosses == 0);
bool canShort = trendDn;
```

**Design rules:**
- Use a small deadband instead of strict zero — flat EMA should still allow the default bias
- Normalize slope as percentage of price so it works across different price levels
- Reset bias after consecutive losses to prevent revenge trading
- Prefer longs for bull-biased assets unless EMA clearly signals otherwise
