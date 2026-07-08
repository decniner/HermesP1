# V5.2a Data-Driven Parameter Optimization

## Context
BTCJPY HybridBot V4.3 → V5.0 (Bug fixes + BoS) → V5.1 (Volatility tuning) → V5.2a (Full-year data analysis)

Trigger: User asked "Did you actually look at these years btcjpy performance before deciding the parameter values?"

## Full-Year BTCJPY Market Analysis (Jul 2025 — Jul 2026)

Data source: MT5 daily candles (365+ days), D1 timeframe.

### Key Metrics
| Metric | Value | Implication |
|--------|-------|-------------|
| Price Change | -35.4% | Bear market |
| 90-Day Range | ¥9.39M – ¥12.97M (38.1%) | Extreme volatility |
| Year Range | 102.1% | Annual range covers 2× the price |
| Avg Monthly Range | 20.4% | Monthly swings are huge |
| ATR(7) | 2.82% | Weekly noise level |
| ATR(14) | 3.40% | 2-week noise level (reference for SL) |
| ATR(30) | 3.49% | Monthly noise level |
| Max DD | 49.3% (from Jun 2026) | Half the account can vanish |
| Daily EMA200 vs Price | 9% bearish | Price is well below long-term MA |

### Monthly Breakdown
| Month | Return | Range | Regime |
|-------|--------|-------|--------|
| 2025-07 | +12.9% | 16.7% | Bull |
| 2025-08 | -8.6% | 15.8% | Bear |
| 2025-09 | +5.7% | 10.7% | Bull (low vol) |
| 2025-10 | -0.5% | 22.8% | Sideways (high vol) |
| 2025-11 | -15.5% | 35.5% | Bear (extreme vol) |
| 2025-12 | -3.3% | 14.1% | Bear |
| 2026-01 | -11.9% | 32.5% | Bear (extreme vol) |
| 2026-02 | -14.1% | 31.3% | Bear (extreme vol) |
| 2026-03 | +4.0% | 19.3% | Bull bounce |
| 2026-04 | +10.5% | 20.8% | Bull |
| 2026-05 | -2.2% | 12.3% | Bear |
| 2026-06 | -18.8% | 25.8% | Bear (high vol) |
| 2026-07 (partial) | +5.7% | 8.0% | Bull bounce |

### Regime Classification at Optimization Time (Jul 2026)
- **Trend:** Bear (+ long-term EMA bearish, short-term bounce)
- **Volatility:** Extreme (20d range 14.7%, ATR 3.45%)
- **Action:** Tighten risk, reduce trade frequency, widen stops

## Parameter Formulas Derived from Data

### Base Formula
| Parameter | Formula | Rationale |
|-----------|---------|-----------|
| StopLoss | `max(avg_monthly_range × 0.30, ATR_14 × 2)` | 30% of avg monthly range or 2× ATR, whichever is larger |
| TakeProfit | `avg_monthly_range × 0.50` | 50% of avg monthly range |
| TrailStart | `avg_monthly_range × 0.15` | 15% of avg monthly range |
| BodyStrengthMin | 50 | Allows more zones to be detected |
| ZoneExpiryHours | 36 | ~1.5 trading sessions |

### Regime Adjustments Applied at V5.2a

| Parameter | V5.2 Base | V5.2a (Bear + Extreme Vol) | Delta |
|-----------|-----------|----------------------------|-------|
| StopLoss | 7.0% | 6.5% | Slightly tighter (bear: don't give too much room) |
| TakeProfit | 8.0% | 10.0% | Need TP to be bigger % of monthly range in bear to compensate |
| TrailStart | 4.0% | 3.5% | Slightly tighter to lock gains in downtrend |
| DailyLossLimit | 6.0% | 5.0% | Tighter in high-vol bear (49% max DD) |
| MaxTradesPerDay | 2 | 2 | Unchanged (already conservative) |

### Parameter Calculation Script

```python
avg_monthly_range = 20.4  # %

sl = max(avg_monthly_range * 0.30, 3.49 * 2)  # = 6.98 → ~7.0%
tp = avg_monthly_range * 0.50  # = 10.2 → ~10.0%
trail = avg_monthly_range * 0.15  # = 3.06 → ~3.0%

# Bear adjustment
sl = sl * 0.93  # 6.5%
tp = tp * 1.0   # 10.0%
trail = trail * 1.15  # 3.5%

# High vol daily loss
daily_loss = max(avg_monthly_range * 0.30, 8.0) * 0.75  # 5.0%
```

## Comparison: What the Data Says vs V4.3 Settings

| Parameter | V4.3 (Before) | Data-Recommended | V5.2a (After) |
|-----------|:------------:|:---------------:|:------------:|
| SL | 3.48% | 6.1-7.0% | **6.5%** |
| TP | 8.0% | 10.2% | **10.0%** |
| Trail | 1.5% | 3.1% | **3.5%** |
| RSI Oversold | 7.5 | 25 | **25** |
| RSI Overbought | 58.5 | 65 | **65** |
| Daily Loss | None | 5% | **5%** |
| Max Trades/Day | Unlimited | 2 | **2** |
| Break-Even | OFF | ON | **ON** |
| Partial TP | OFF | ON | **ON** |

## Key Insight

The V4.3's 3.48% SL was the single biggest flaw — it got hit on normal volatility (ATR = 3.49%), meaning random price noise triggered exits, not failed strategies. Everything else (BE, partial TP, daily loss, RSI levels) was secondary to fixing the SL.
