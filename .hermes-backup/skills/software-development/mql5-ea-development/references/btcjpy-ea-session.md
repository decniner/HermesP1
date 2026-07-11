# BTCJPY EA Optimization Sessions — Jul 2026

## Session Overview
Extensive backtesting and optimization of BTCJPY Expert Advisors across multiple architectures. User runs EAs on XMTrading MT5, BTCJPY M15, ¥50K JPY, 1:1000 leverage. EAs stored in `DEN_EA/` folder.

## EAs Developed & Results

### V4.3 — Original BTCJPY_LowDDWithBoS
- BodyStrengthMin=60, EMAPeriod=579, RSI(105), fixed SL 3.48%/TP 8%
- 1yr result: 43 trades, +¥32,638 (+65%), Win 38.3%, PF 1.12, **DD 46%**

### V5 — First Attempt (dead code)
- BodyStrengthMin=70, EMAPeriod=88, RSI(14), ATR SL/TP 1.5/3.0, LongBias=true
- **0 trades** — zone detection loop bug (loop checked r[1] AND r[2], second overwrote first)
- Fixed compile: 21 trades, **-¥1,108**, PF 0.89, DD 11.5%

### V5_1 — Dynamic Bias + Bugfixes
- BodyStrengthMin=55→50, RSILongMin=40→30, zone-once-per-bar, dynamic EMA slope bias
- First compile: 21 trades, **-¥7,429**, DD 14.86% — worse than V5 (LongBias still too restrictive)
- **8,281-pass optimization** (SL/ATR × TP/ATR): **Pass #2465** — SL=3.6, TP=12.95 → **+¥10,248 (20.5%), PF 1.633, DD 8.8%, 35 trades** ✅
- 12 local cores, 2h 53m runtime. Range: SL/ATR 1.0-5.0, TP/ATR 5.0-20.0

### V5_2 — Applied Best Params
- SL=3.6, TP=12.95 (from V5_1 opt pass #2465)
- Full-year confirmation test produced 130KB result file
- All other params same as V5_1

### V6 — Original EA + Pass 54 Optimized Params
- Optimized on the ORIGINAL BTCJPY_LowDDWithBoS (percentage-based SL/TP, not ATR)
- **19,000+ passes** across SlowMA, SL%, TP%, PartialTP, BoS
- **Pass #54**: SlowMA=317, SL=10.09%, TP=71.2%, PartialTP=true(trigger 8.5%), LTF=true, BoS=47
- Result: +¥13,055 (26.1%), PF 2.073, DD 13.3%, **only 8 trades**

### Institutional Sniper Series — ALL FAILED
- V1: 1 trade only (forming bar bug — used m15[0] instead of m15[1])
- V1_1: -16.4% (reckless lot sizing formula, too many filters)
- V2: Losing (over-engineered: zone + BoS + RSI + candle confirm + spread + directional lock)
- Lesson: Too many gates = no trades or late entries. BTCJPY needs simple entry + wide risk + trailing.

## Key Bugs Discovered

1. **Forming bar vs completed bar**: Using `m15[0]` (forming bar) for candle confirmation means the condition changes every tick. Use `m15[1]` (last completed bar).

2. **Lot size blowup**: `riskEq / riskPts * 100` produces reckless lots when SL is tight. Use fixed lots or properly tick-value-corrected calculation.

3. **H4 MA vs M15 price**: `iMA(_Symbol, ZoneTF, ...)` creates H4 MA — comparing against M15 bid/ask is wrong scale.

4. **Zone detection loop overwrite**: A `for(i=1; i<=2; i++)` loop overwrites r[1] zone with r[2]. Only check r[1].

5. **38.2% fib zone width too tight**: Use 50-60% of candle range for wider retracement zone.

## Critical Lessons

### 1. User-Specified Architectures Underperform
The Sniper series (V1→V2) was built per the user's detailed architectural specs ("elite MQL5 Quantitative Developer", "Institutional Sniper"). Every version lost money. The simple zone+trail approach (V5.2) from automated optimization was the only profitable version.

**Don't** build from scratch based on user specs unless there's a clear, simple winning path. **Do** take an existing working EA and optimize its parameters — this reliably outperforms ground-up redesigns.

### 2. Over-Filtering Kills
Each filter (zone + BoS + RSI + candle confirm + spread + directional lock + MA) gates out trades independently. Stacking them means no signal survives. The winning V5.2 had exactly: zone detected, price in zone, trailing active. No RSI, no BoS, no candle confirm, no directional flip.

Rule of thumb for BTCJPY: entry condition with >4 boolean checks = over-filtered.

### 3. Wide SL/TP with Trailing > Tight SL
The optimization proved that SL/ATR=3.6 and TP/ATR=12.95 produced the best results. The wide SL avoids premature stop-outs. The trailing stop locks profits early. The huge TP is just a backstop.

### 4. Dynamic Bias > Hardcoded LongBias
`LongBiasEnabled=true` prevented shorts in the bearish 2025-2026 period. Fix: compute bias from EMA slope as percentage of price.

## Tooling Created

- `backtest_runner.py` — generates UTF-16LE .set files with optimization ranges
- `run_backtest.ps1` — PowerShell script that generates .set and launches MT5
- `backtest_den_ea.bat` — simple batch version

## File Locations

.set files go to:
```
C:\Users\decni\AppData\Roaming\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Experts\DEN_EA\Sets\
```

Always provide the **full absolute path** starting from `C:\` when the user asks about file locations.

## File Naming Convention

```
DEN_EA/
├── BTCJPY_LowDDWithBoS.ex5              ← Original V4.3
├── BTCJPY_LowDDWithBoS_Opt_V5.ex5       ← First ATR-based attempt
├── BTCJPY_LowDDWithBoS_Opt_V5_1.ex5     ← Fixed zone detection
├── BTCJPY_LowDDWithBoS_Opt_V5_2.ex5     ← Optimized SL=3.6/TP=12.95
├── BTCJPY_Institutional_Sniper_V1.ex5   ← User-spec architecture (failed)
├── BTCJPY_Institutional_Sniper_V1_1.ex5 ← Bugfix (still failed)
├── BTCJPY_Institutional_Sniper_V2.ex5   ← Retracement (still failed)
├── BTCJPY_LowDDWithBoS_Opt_V6.ex5       ← Pass 54 params
└── Sets/*.set                           ← Input parameter presets
```

## Session Data Files
- `doc_2018e726469f_ReportOptimizer-755742362.xml` — V5_1 optimization (8,281 passes, SL/TP)
- `doc_0f2fac872e38_ReportOptimizer-755742362.xml` — Original EA optimization (19K+ passes, SL%/TP%/SlowMA)

## POGIBOT Chat Feature Added

The POGIBOT VR boxing coach was updated with a conversational AI chat feature. Pattern:
1. Backend: `POST /chat` endpoint accepting `{message, conversation[], last_analysis{}}`
2. Frontend: Chat box with input field, message history, loading indicators
3. Uses DeepSeek with system prompt instructing brutal-honesty boxing coach persona
4. Injects last analysis context (events, ratings, score, verdict) + training history into chat context
5. Maintains conversation continuity via `chatConversation[]` array (last 10 exchanges)
