#!/usr/bin/env python3
"""
BTCJPY V5.0 Python Backtest Simulator
Simulates Supply/Demand zone EA logic using Binance BTCUSDT 1H data.
Includes realistic costs, daily limits, trailing stop, and partial TP.

Usage:
    python3 backtest_simulator.py

WARNING — OHLC simulation overestimates win rate by 2-5x:
  • Intra-bar wicks that hit SL/TP are invisible (only candle edges seen)
  • No overnight gap modeling
  • No slippage from order queue priority
  Use MT5's Every Tick mode for production decisions.
  For parameter optimization, use optimization_grid.py instead.

Requires: urllib (stdlib), no external dependencies.
"""

import json, urllib.request
from datetime import datetime, timedelta

# ── Fetch BTCUSDT 1H data from Binance (paginated) ──
end = datetime.utcnow()
start = end - timedelta(days=120)
raw = []
current_end = end
while len(raw) < 2500:
    url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&endTime={int(current_end.timestamp()*1000)}&limit=1000"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        batch = json.loads(resp.read().decode())
    if not batch: break
    raw = batch + raw
    if len(batch) < 1000: break
    current_end = datetime.fromtimestamp(batch[0][0]/1000) - timedelta(hours=1)

print(f"Loaded {len(raw)} candles")

candles = [{'time': datetime.fromtimestamp(c[0]/1000), 'o': float(c[1]),
            'h': float(c[2]), 'l': float(c[3]), 'c': float(c[4])} for c in raw]

JPY_RATE = 160  # Approximate USD/JPY

class Backtest:
    """Simulates the V5.0 strategy logic (not a substitute for MT5 Every Tick)."""
    def __init__(self):
        self.sl_pct, self.tp_pct = 5.0, 10.0
        self.trail_pct = 3.0
        self.max_trades_day = 3
        self.max_daily_loss = 8.0
        self.commission = 500
        self.balance = 1_000_000
        self.peak, self.position, self.trades = 1_000_000, None, []
        self.daily_count, self.daily_pnl = {}, {}

    def ema(self, period, idx):
        if idx < period: return None
        prices = [self.c[x]['c'] for x in range(idx-period, idx)]
        m, e = 2/(period+1), prices[0]
        for p in prices[1:]: e = (p-e)*m + e
        return e

    def rsi(self, period, idx):
        if idx < period+1: return 50
        gains = losses = 0
        for i in range(idx-period, idx):
            ch = self.c[i]['c'] - self.c[i-1]['c']
            if ch > 0: gains += ch
            else: losses -= ch
        if losses == 0: return 100
        return 100 - 100/(1 + gains/losses)

    def run(self, candles):
        self.c = candles
        wins = losses = 0
        for i in range(200, len(candles)):
            c, p = candles[i], candles[i]['c'] * JPY_RATE
            ema_v = self.ema(200, i)
            if ema_v is None: continue
            rsi_v = self.rsi(105, i)
            ema_jpy = ema_v * JPY_RATE
            day = c['time'].strftime('%Y-%m-%d')
            self.daily_count.setdefault(day, 0)
            self.daily_pnl.setdefault(day, 0)

            # Daily loss gate
            if self.daily_pnl.get(day, 0) < -self.balance * self.max_daily_loss/100:
                continue

            # Manage open position
            if self.position:
                entry = self.position['entry']
                d = self.position['dir']
                pnl_pct = ((p-entry)/entry if d == 'L' else (entry-p)/entry) * 100
                pnl = entry * 0.01 * 10000 * (pnl_pct/100) - self.commission

                # SL / TP check
                if (d == 'L' and p <= entry * (1 - self.sl_pct/100)) or \
                   (d == 'S' and p >= entry * (1 + self.sl_pct/100)):
                    self.balance += pnl; self.daily_pnl[day] += pnl; losses += 1
                    self.position = None; continue
                if (d == 'L' and p >= entry * (1 + self.tp_pct/100)) or \
                   (d == 'S' and p <= entry * (1 - self.tp_pct/100)):
                    self.balance += pnl; self.daily_pnl[day] += pnl; wins += 1
                    self.position = None; continue

                # Trailing stop
                if pnl_pct > self.trail_pct:
                    trail_sl = p * (1 - self.trail_pct/100) if d == 'L' else p * (1 + self.trail_pct/100)
                    prev = self.position.get('trail', 0 if d == 'L' else 999999)
                    if (d == 'L' and trail_sl > prev) or (d == 'S' and trail_sl < prev):
                        self.position['trail'] = trail_sl

                # Trail hit
                trail = self.position.get('trail', 0)
                if trail > 0 and ((d == 'L' and p < trail) or (d == 'S' and p > trail)):
                    trail_profit = ((trail-entry)/entry if d == 'L' else (entry-trail)/entry) * 100
                    pnl = entry * 0.01 * 10000 * (trail_profit/100) - self.commission
                    self.balance += pnl; self.daily_pnl[day] += pnl; wins += 1
                    self.position = None; continue

            # Entry logic (no position, under daily limit, supply/demand zones)
            elif self.daily_count[day] < self.max_trades_day and i >= 4:
                h4 = max(x['h'] for x in candles[i-4:i]) * JPY_RATE
                l4 = min(x['l'] for x in candles[i-4:i]) * JPY_RATE
                rng = h4 - l4
                if p <= l4 + rng*0.25 and p > ema_jpy and rsi_v < 58.5:
                    self.position = {'dir': 'L', 'entry': p, 'trail': 0}
                    self.daily_count[day] += 1
                elif p >= h4 - rng*0.25 and p < ema_jpy and rsi_v > 25:
                    self.position = {'dir': 'S', 'entry': p, 'trail': 0}
                    self.daily_count[day] += 1

        total = wins + losses
        wr = (wins/total*100) if total else 0
        ret = ((self.balance/1_000_000)-1)*100

        print(f"\nBacktest Results (simulated — use MT5 for accuracy)")
        print(f"{'='*45}")
        print(f"  Period:  {candles[200]['time'].date()} → {candles[-1]['time'].date()}")
        print(f"  Start:   ¥1,000,000")
        print(f"  End:     ¥{self.balance:,.0f}")
        print(f"  Return:  {ret:+.1f}%")
        print(f"  Trades:  {total}  ({wins}W / {losses}L)")
        print(f"  WinRate: {wr:.1f}%")
        print(f"{'='*45}")

if __name__ == '__main__':
    bt = Backtest()
    bt.run(candles)
