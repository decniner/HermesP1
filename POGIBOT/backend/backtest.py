"""
BTCJPY_LowDDWithBoS Backtest Simulation
Approximates the EA's strategy logic using 4H BTC-USD data
"""
import yfinance as yf
import pandas as pd
import numpy as np

# Get 6 months of BTC-USD 4H data (proxy for BTCJPY)
df = yf.download("BTC-USD", period="6mo", interval="4h", progress=False)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
df.columns = [c.lower() for c in df.columns]

print(f"Data: {len(df)} candles, {df.index[0]} to {df.index[-1]}")
print(f"Price range: ${df['close'].min():.0f} - ${df['close'].max():.0f}")

# Strategy params from EA
SL_PCT = 0.0348
TP_PCT = 0.08
TRAIL_PCT = 0.015
RSI_PERIOD = 105
RSI_OB = 58.5
RSI_OS = 7.5
EMA_PERIOD = 579

# Indicators
df["ema"] = df["close"].ewm(span=EMA_PERIOD).mean()
delta = df["close"].diff()
gain = delta.where(delta > 0, 0).rolling(RSI_PERIOD).mean()
loss = (-delta.where(delta < 0, 0)).rolling(RSI_PERIOD).mean()
rs = gain / loss
df["rsi"] = 100 - (100 / (1 + rs))

# Swing points
df["swing_h"] = df["high"].rolling(3, center=True).apply(
    lambda x: 1 if x.iloc[1] == max(x) else 0, raw=False
)
df["swing_l"] = df["low"].rolling(3, center=True).apply(
    lambda x: 1 if x.iloc[1] == min(x) else 0, raw=False
)

# Backtest
position = None
trades = []
entry_price = 0
sl_price = 0
tp_price = 0
direction = 0
trail_activated = False

start_idx = max(EMA_PERIOD + RSI_PERIOD + 50, 0)
for i in range(start_idx, len(df)):
    price = df["close"].iloc[i]
    high = df["high"].iloc[i]
    low = df["low"].iloc[i]
    ema_val = df["ema"].iloc[i]
    rsi_val = df["rsi"].iloc[i]

    if position is None:
        # Long: price > EMA, RSI oversold, swing low formed
        if (price > ema_val and rsi_val < RSI_OS
                and df["swing_l"].iloc[i] == 1):
            direction = 1
            entry_price = price
            sl_price = price * (1 - SL_PCT)
            tp_price = price * (1 + TP_PCT)
            position = "long"
            trail_activated = False

        # Short: price < EMA, RSI overbought, swing high formed
        elif (price < ema_val and rsi_val > RSI_OB
              and df["swing_h"].iloc[i] == 1):
            direction = -1
            entry_price = price
            sl_price = price * (1 + SL_PCT)
            tp_price = price * (1 - TP_PCT)
            position = "short"
            trail_activated = False

    else:
        # Trailing stop
        if not trail_activated:
            if direction == 1 and price > entry_price * (1 + TRAIL_PCT):
                sl_price = price * (1 - TRAIL_PCT)
                trail_activated = True
            elif direction == -1 and price < entry_price * (1 - TRAIL_PCT):
                sl_price = price * (1 + TRAIL_PCT)
                trail_activated = True
        else:
            if direction == 1:
                new_sl = price * (1 - TRAIL_PCT)
                if new_sl > sl_price:
                    sl_price = new_sl
            elif direction == -1:
                new_sl = price * (1 + TRAIL_PCT)
                if new_sl < sl_price:
                    sl_price = new_sl

        # Exit checks
        exit_reason = None
        exit_price = None

        if direction == 1:
            if low <= sl_price:
                exit_price = sl_price
                exit_reason = "SL"
            elif high >= tp_price:
                exit_price = tp_price
                exit_reason = "TP"
        else:
            if high >= sl_price:
                exit_price = sl_price
                exit_reason = "SL"
            elif low <= tp_price:
                exit_price = tp_price
                exit_reason = "TP"

        if exit_reason:
            pnl = direction * (exit_price - entry_price) / entry_price * 100
            trades.append({
                "entry_date": df.index[entry_bar],
                "exit_date": df.index[i],
                "direction": "LONG" if direction == 1 else "SHORT",
                "entry": round(entry_price, 1),
                "exit": round(exit_price, 1),
                "pnl_pct": round(pnl, 2),
                "reason": exit_reason,
                "trailed": trail_activated,
            })
            position = None

    if position is not None and i == entry_bar if False else True:
        if position == "long" and i == entry_bar if "entry_bar" in dir() else True:
            pass
    if position is not None and i > 0:
        if "entry_bar" not in dir():
            entry_bar = i

# Results
if trades:
    wins = [t for t in trades if t["pnl_pct"] > 0]
    losses = [t for t in trades if t["pnl_pct"] <= 0]
    total_pnl = sum(t["pnl_pct"] for t in trades)
    win_rate = len(wins) / len(trades) * 100

    # Equity curve
    equity = 10000
    peak = 10000
    max_dd = 0
    for t in trades:
        pnl_pts = t["pnl_pct"] / 100 * 10000 * 0.01  # ~$ per 0.01 lot
        equity += pnl_pts
        if equity > peak:
            peak = equity
        dd = (peak - equity) / peak * 100
        if dd > max_dd:
            max_dd = dd

    avg_win = np.mean([t["pnl_pct"] for t in wins]) if wins else 0
    avg_loss = np.mean([t["pnl_pct"] for t in losses]) if losses else 0
    pf = abs(avg_win * len(wins) / (avg_loss * len(losses))) if losses and avg_loss != 0 else float("inf")

    print(f"\n{'='*60}")
    print(f"  BTCJPY_LowDDWithBoS — Backtest Simulation")
    print(f"  Data: BTC-USD 4H ({len(df)} candles)")
    print(f"  Period: {df.index[0]} to {df.index[-1]}")
    print(f"{'='*60}")
    print(f"  Total Trades:   {len(trades)}")
    print(f"  Win Rate:       {win_rate:.1f}% ({len(wins)}W / {len(losses)}L)")
    print(f"  Profit Factor:  {pf:.2f}")
    print(f"  Total Return:   {total_pnl:+.2f}%")
    print(f"  Avg Win:        {avg_wins:+.2f}%" if False else f"  Avg Win:        {avg_win:+.2f}%")
    print(f"  Avg Loss:       {avg_loss:.2f}%")
    print(f"  Max DD:         {max_dd:.2f}%")
    print(f"  SL Hit:         {len([t for t in trades if t['reason']=='SL'])}")
    print(f"  TP Hit:         {len([t for t in trades if t['reason']=='TP'])}")
    print(f"  Trailed:        {len([t for t in trades if t['trailed']])}")

    print(f"\n  Top 5 trades:")
    for t in sorted(trades, key=lambda x: abs(x["pnl_pct"]), reverse=True)[:5]:
        d = "L" if t["direction"] == "LONG" else "S"
        print(f"    {t['entry_date']} {d} ${t['entry']:.0f}→${t['exit']:.0f} {t['pnl_pct']:+.2f}% ({t['reason']})")

    print(f"\n  Worst 3:")
    for t in sorted(trades, key=lambda x: x["pnl_pct"])[:3]:
        d = "L" if t["direction"] == "LONG" else "S"
        print(f"    {t['entry_date']} {d} ${t['entry']:.0f}→${t['exit']:.0f} {t['pnl_pct']:+.2f}% ({t['reason']})")

    print(f"\n{'='*60}")
    print(f"  VERDICT: This is a BTC-USD proxy. Real BTCJPY results WILL differ.")
    print(f"  The EA uses Supply/Demand + BoS logic not fully replicated here.")
    print(f"  For accurate results, run in MT5 Strategy Tester with real ticks.")
else:
    print("No trades generated in this period.")
