# BTCJPY EA Development Session — Extended

## Session Overview
Extensive backtesting and optimization of BTCJPY Expert Advisors across multiple architectures. User runs EAs on XMTrading MT5, BTCJPY M15, ¥50K JPY, 1:1000 leverage. EAs stored in `DEN_EA/` folder.

## Reading Optimizer XML Reports

MT5 can export optimization results as XML. Parse them to find best parameter combinations:

### XML Structure
Columns: Pass | Result | Profit | Expected Payoff | Profit Factor | Recovery Factor | Sharpe Ratio | Custom | Equity DD % | Trades | [params...]

Pass is the first cell, parameter values are after Trades.

### How to parse
1. Read the first 20-30 rows (sorted by best result)
2. Check column headers (Row 38-50 in the XML) to know parameter order
3. First 10 columns are fixed, then parameter columns match `input` declaration order in `.mq5`
4. Focus on **Profit Factor** as primary ranking, **Net Profit** as secondary
5. Trade off between PF, DD%, and Trade Count — PF 2.0 with 3 trades is unreliable
6. Cross-check parameter values against EA's declared inputs

### Example from this session — original EA headers:
Pass | Result | Profit | Expected Payoff | Profit Factor | Recovery Factor | Sharpe Ratio | Custom | Equity DD % | Trades | SlowMAPeriod | StopLossPercent | TakeProfitPercent | UsePartialTP | PartialTP_TriggerPct | UseLTFConfirmation | BoSLookback

### Top passes from 19,000+ optimization on original EA:
| Pass | Profit | PF | SL% | TP% | SlowMA | PartialTP | BoS |
|------|--------|-----|------|------|--------|-----------|-----|
| 54 | 13055 | 2.07 | 10.09 | 71.2 | 317 | true(8.5%) | 47 |
| 834 | 12278 | 2.01 | 34.80 | 8.0 | 71 | false | 43 |

### Pass Viability Criteria
- PF ≥ 1.5, DD ≤ 15%, Trades ≥ 10, Sharpe ≥ 1.0

## EAs Developed & Results

### V4.3 — Original BTCJPY_LowDDWithBoS
- BodyStrengthMin=60, EMAPeriod=579, RSI(105), fixed SL 3.48%/TP 8%
- 1yr: 43 trades, +¥32,638 (+65%), Win 38.3%, PF 1.12, DD 46%

### V5 — First Attempt
- BodyStrengthMin=70, EMAPeriod=88, RSI(14), ATR SL/TP 1.5/3.0, LongBias=true
- 0 trades (zone loop bug). Fixed: 21 trades, -¥1,108, PF 0.89, DD 11.5%

### V5_1 — Dynamic Bias + Bugfixes
- 8,281-pass opt (SL/ATR × TP/ATR): Pass #2465 — SL=3.6, TP=12.95 → +¥10,248 (20.5%), PF 1.633, DD 8.8%, 35 trades

### V5_2 — Applied Best Params
- SL=3.6, TP=12.95 (from V5_1 opt)

### V6 — Original EA + Pass 54 Optimized Params
- SlowMA=317, SL=10.09%, TP=71.2%, PartialTP=true(8.5%), LTF=true, BoS=47
- +¥13,055 (26.1%), PF 2.073, DD 13.3%, 8 trades

### Post-MT5-Reinstall Restore
Backup `.mq5` from `~/projects/POGIBOT/backend/`. Recreate `DEN_EA/` + `Sets/`. Convert UTF-8→UTF-16LE. Regenerate `.set` files. Compile in MetaEditor GUI — CLI compile timeouts.

**Restored:** V5_2, V6, Sniper V1_1. **Lost:** Original `BTCJPY_LowDDWithBoS.mq5`.

### Institutional Sniper Series — ALL FAILED
- V1: 1 trade (forming bar bug — used m15[0] instead of m15[1])
- V1_1: -16.4% (reckless lot sizing, too many filters)
- V2: Losing (over-engineered: zone + BoS + RSI + candle confirm + spread + directional lock)

## Key Bugs Discovered

1. **Forming bar vs completed bar** — Use `m15[1]` (completed), not `m15[0]` (forming)
2. **Lot size blowup** — `riskEq / riskPts * 100` produces reckless lots
3. **H4 MA vs M15 price** — wrong scale comparison
4. **Zone detection loop** — for(i=1; i<=2; i++) overwrites r[1] with r[2]
5. **38.2% fib zone width** — too tight, use 50-60%
6. **Full C:\ paths required** — don't abbreviate
7. **sdkmanager needs Java 17+** — Java 8 gives UnsupportedClassVersionError
8. **GoRouter + Navigator.pushNamed** — silent no-op, use `context.push()`

## Critical Lessons for Next Session

1. **User-Specified Architectures Underperform** — Start from working EA, optimize params, don't build from scratch per specs
2. **Over-Filtering Kills** — >4 boolean checks = over-filtered for BTCJPY
3. **Wide SL/TP with Trailing** — SL/ATR=3.6, TP/ATR=12.95 best
4. **Dynamic Bias** — EMA slope % of price, not hardcoded LongBias
5. **Tell exact filename** — standalone line for each test deliverable
6. **Verify what was tested** — Check report's EA name and params before debugging
7. **Android 11+ queries** — Add `<data android:scheme="magnet"/>` to manifest
8. **Embed sites don't work in WebView** — Use system browser
9. **TPB API: apibay.org** — Reliable torrent search, no auth
10. **TMDb API key** — `8f056e7aba498426cd3e99e20ca63892` already embedded
