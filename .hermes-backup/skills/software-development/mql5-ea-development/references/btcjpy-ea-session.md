# BTCJPY EA Development Session — Extended

## Session Overview
Extensive backtesting and optimization of BTCJPY Expert Advisors across multiple architectures. User runs EAs on XMTrading MT5, BTCJPY M15, ¥50K JPY, 1:1000 leverage. EAs stored in `DEN_EA/` folder.

## Reading Optimizer XML Reports

MT5 can export optimization results as XML (Excel-compatible format). Parse them to find best parameter combinations:

### XML Structure
```
Columns: Pass | Result | Profit | Expected Payoff | Profit Factor | Recovery Factor | Sharpe Ratio | Custom | Equity DD % | Trades | [params...]
```

Each `<Row>` has `<Cell>` elements in column order. Pass is the first cell, parameter values are after Trades.

### How to parse in conversation
1. Read the first 20-30 rows (sorted by best result)
2. Check column headers (Row 38-50 in the XML) to know parameter order
3. The parameter columns start after Trades — their order equals the `input` declaration order in the `.mq5` source file
4. Focus on **Profit Factor** as primary ranking metric, **Net Profit** as secondary
5. Trade off between PF, DD%, and Trade Count — PF 2.0 with only 3 trades is unreliable
6. Cross-check the parameter values against the EA's declared inputs

### Column Mapping for Optimization XMLs
The XML column order depends on how MT5 exports. Always read the header row to determine mapping:

```python
# First 10 columns are always fixed
headers = ["Pass","Result","Profit","Expected Payoff","Profit Factor",
           "Recovery Factor","Sharpe Ratio","Custom","Equity DD %","Trades"]
# Columns 10+ are EA input parameters in declaration order
```

**Example from this session — original EA optimization:**
Headers Row: `Pass | Result | Profit | Expected Payoff | Profit Factor | Recovery Factor | Sharpe Ratio | Custom | Equity DD % | Trades | SlowMAPeriod | StopLossPercent | TakeProfitPercent | UsePartialTP | PartialTP_TriggerPct | UseLTFConfirmation | BoSLookback`

### Example from this session
**8,281-pass optimization on V5_1 (SL/ATR + TP/ATR):**
- Best pass #2465: SL=3.6, TP=12.95 → +¥10,248, PF 1.633, DD 8.8%, 35 trades
- 12 local cores, 2h 53m runtime. Range: SL/ATR 1.0-5.0, TP/ATR 5.0-20.0

**19,000+ pass optimization on original EA (7 params):**
- Best pass #54: SlowMA=317, SL=10.09%, TP=71.2% → +¥13,055, PF 2.073, DD 13.3%, 8 trades
- PartialTP=true (trigger 8.5%), UseLTFConfirmation=true, BoSLookback=47
- Full top-10 table:
  | Pass | Profit | PF | SL% | TP% | SlowMA | PartialTP | BoS |
  |------|--------|-----|-----|------|--------|-----------|-----|
  | 54 | 13055 | 2.07 | 10.09 | 71.2 | 317 | true(8.5%) | 47 |
  | 834 | 12278 | 2.01 | 34.80 | 8.0 | 71 | false | 43 |
  | 821 | 12259 | 2.01 | 30.28 | 64.0 | 410 | true(8.0%) | 48 |
  | 319 | 11771 | 1.97 | 14.96 | 48.8 | 60 | true(6.0%) | 48 |

### Pass Viability Criteria
- PF ≥ 1.5, DD ≤ 15%, Trades ≥ 10, Sharpe ≥ 1.0
- Extreme-looking parameters that worked in one period likely won't generalize

## EAs Developed & Results

### V4.3 — Original BTCJPY_LowDDWithBoS
- BodyStrengthMin=60, EMAPeriod=579, RSI(105), fixed SL 3.48%/TP 8%
- 1yr result: 43 trades, +¥32,638 (+65%), Win 38.3%, PF 1.12, **DD 46%**

### V5 — First Attempt (dead code)
- BodyStrengthMin=70, EMAPeriod=88, RSI(14), ATR SL/TP 1.5/3.0, LongBias=true
- 0 trades — zone detection loop bug (loop checked r[1] AND r[2], second overwrote first)
- Fixed compile: 21 trades, -¥1,108, PF 0.89, DD 11.5%

### V5_1 — Dynamic Bias + Bugfixes
- BodyStrengthMin=55→50, RSILongMin=40→30, zone-once-per-bar, dynamic EMA slope bias
- 8,281-pass optimization (SL/ATR × TP/ATR): Pass #2465 — SL=3.6, TP=12.95 → +¥10,248 (20.5%), PF 1.633, DD 8.8%, 35 trades

### V5_2 — Applied Best Params
- SL=3.6, TP=12.95 (from V5_1 opt pass #2465)

### V6 — Original EA + Pass 54 Optimized Params
- 19,000+ passes across SlowMA, SL%, TP%, PartialTP, BoS
- Pass #54: SlowMA=317, SL=10.09%, TP=71.2%, PartialTP=true(trigger 8.5%), LTF=true, BoS=47
- Result: +¥13,055 (26.1%), PF 2.073, DD 13.3%, 8 trades
- This was on the ORIGINAL EA structure (not V5 series). The optimizer ran on `BTCJPY_LowDDWithBoS` (V4.3 base) with Spread/MA filters + zone + trailing.
- Original EA config used `input` parameters named SlowMAPeriod, StopLossPercent, TakeProfitPercent, etc. — NOT the ATR-based inputs of the V5 series. This is why reports showing SL=10.09% are valid for the original EA but not comparable to SL/ATR=3.6.
- **IMPORTANT TRIAGE LESSON:** When the user sent a test report showing `StopLossPercent=10.09` and `SlowMAPeriod=317`, it was easy to mistake this for the V5 series EA. Always check the **expert name at the top of the report** — `BTCJPY_LowDDWithBoS` means it's the original EA, NOT the Opt V5 series.

### Institutional Sniper Series — ALL FAILED
- V1: 1 trade only (forming bar bug — used m15[0] instead of m15[1])
- V1_1: -16.4% (reckless lot sizing formula, too many filters)
- V2: Losing (over-engineered: zone + BoS + RSI + candle confirm + spread + directional lock)
- Lesson: Too many gates = no trades or late entries. BTCJPY needs simple entry + wide risk + trailing.

## Key Bugs Discovered

1. **Forming bar vs completed bar**: Using m15[0] (forming bar) for candle confirmation means the condition changes every tick. Use m15[1] (last completed bar).
2. **Lot size blowup**: riskEq / riskPts * 100 produces reckless lots when SL is tight. Cap it or use fixed lot.
3. **H4 MA vs M15 price**: iMA(Symbol, ZoneTF, ...) creates H4 MA — comparing against M15 bid/ask is wrong scale.
4. **Zone detection loop overwrite**: A for(i=1; i<=2; i++) loop overwrites r[1] zone with r[2].
5. **38.2% fib zone width too tight**: Use 50-60% of candle range.
6. **Full C:\ paths required**: Always provide complete absolute paths when user asks for file locations.
7. **sdkmanager needs Java 17+**: The Android SDK manager requires Java 17 (class version 61). Java 8 gives "UnsupportedClassVersionError". Fix: install JDK 17 and set JAVA_HOME.
8. **GoRouter + Navigator.pushNamed → Silent No-Op**: When using GoRouter for navigation, `Navigator.pushNamed()` silently does nothing. Always use `context.push()` / `context.go()` from GoRouter, and ensure the file imports `package:go_router/go_router.dart`.

## Critical Lessons

### 0. GoRouter + Navigator.pushNamed → Silent No-Op
When using `GoRouter` for routing, `Navigator.pushNamed()` silently does nothing — GoRouter routes don't exist in the built-in Navigator's route table. The user taps a button, nothing happens, no error is thrown.

**Fix:** Always use GoRouter's extensions on `BuildContext`:
```dart
// ✅ Works with GoRouter
context.push('/player/movie/550/0/0');
context.go('/auth');

// ❌ Silent no-op (routes don't exist in old Navigator)
Navigator.pushNamed(context, '/player/movie/550/0/0');
Navigator.push(context, MaterialPageRoute(...));
```

**Symptoms:** "Nothing happens when I press the button" — no navigation, no error, no log. The button's `onPressed` fires but the route is never matched.

**Required imports:** Files using `context.push()` or `context.go()` must import `package:go_router/go_router.dart`.

**Checklist when a navigation button does nothing:**
1. Verify the route exists in the GoRouter config
2. Check the file imports `go_router.dart`
3. Confirm the call uses `context.push()`/`context.go()`, NOT `Navigator.pushNamed()`

### 1. User-Specified Architectures Underperform
The Sniper series (V1→V2) was built per the user's detailed architectural specs. Every version lost money. The simple zone+trail approach (V5.2) from automated optimization was the only profitable version.

### 2. Over-Filtering Kills
Each filter gates out trades independently. Stacking them means no signal survives. Rule of thumb for BTCJPY: entry condition with >4 boolean checks = over-filtered.

### 3. Wide SL/TP with Trailing > Tight SL
The optimization proved that SL/ATR=3.6 and TP/ATR=12.95 produced the best results. The wide SL avoids premature stop-outs. The trailing stop locks profits early.

### 4. Dynamic Bias > Hardcoded LongBias
LongBiasEnabled=true prevented shorts in the bearish 2025-2026 period. Fix: compute bias from EMA slope as percentage of price.

### 5. Always Tell the User the Exact Filename
When delivering for testing, state the filename in a clear standalone line.

### 6. Verify the Test Was Actually Run Correctly
When the user reports a bad test result, check the report's input parameters against what you intended — the user may have tested a different EA or stale parameters.
