# BTCJPY EA Development Session — Part 2 (Jul 2026)

## EA Performance Data

### BTCJPY_LowDDWithBoS_Opt_V5_2 (Proven Winner)
SL=3.6/TP=12.95 — from 8,281-pass optimization

| Metric | Value |
|--------|-------|
| Net Profit | +¥10,248 (20.5%) |
| Profit Factor | 1.633 |
| Max DD | 8.8% |
| Trades | 35 |
| Sharpe | 5.52 |
| Recovery Factor | 2.11 |
| Period | Mar-Jul 2026 (4mo) |

### Original BTCJPY_LowDDWithBoS (V4.3)
Default parameters, 1yr backtest

| Metric | Value |
|--------|-------|
| Net Profit | +¥32,638 |
| Profit Factor | 1.12 |
| Max DD | 46% |
| Trades | 43 |
| Win Rate | 38.3% |

### Pass 54 (from 19,000+ pass optimization on V4.3)
SlowMA=317, SL=10.09%, TP=71.2%, BoSLookback=47, PartialTP=true (8.5%)

| Metric | Value |
|--------|-------|
| Net Profit | +¥13,055 (26.1%) |
| Profit Factor | 2.073 |
| Max DD | 13.3% |
| Trades | 8 |
| Sharpe | 0.32 |

## Key Architecture Lessons

1. **Simple wins:** V5_2 (zone + trail + loss protection only, no RSI/BoS/candle confirm) outperformed all Sniper variants
2. **Wide SL/TP works:** SL=3.6x ATR and TP=12.95x ATR — the TP is a backstop, trailing stop does the real work
3. **Parameter optimization beats architecture redesign:** 8,281 passes on existing parameters found a profitable combo; 3 ground-up builds (Sniper V1/V1.1/V2) all lost
4. **Dynamic bias > hardcoded:** Use EMA slope with deadband instead of LongBiasEnabled toggle
5. **Verify what was tested:** User ran a different EA (BTCJPY_LowDDWithBoS_v6) and sent me its report — wasted one iteration

## Reference Optimization XML Column Order

When reading optimizer XML reports, the column order is:
1. Pass (int)
2. Result (custom metric)
3. Profit (net profit ¥)
4. Expected Payoff (avg per trade)
5. Profit Factor
6. Recovery Factor
7. Sharpe Ratio
8. Custom
9. Equity DD %
10. Trades
11+ EA input parameters (in declaration order from the .mq5 file)
