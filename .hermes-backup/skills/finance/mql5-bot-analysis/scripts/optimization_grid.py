#!/usr/bin/env python3
"""
MQL5 Bot Parameter Grid Optimizer (Python fallback)

Runs a grid search over SL, TP, and Trail parameters, simulating the
strategy on real BTC data. Results sorted by Profit Factor.

Usage:
    python3 optimization_grid.py

Output: optimization_results.txt (CSV) + top-15 results printed to stdout.

Limitations:
  - OHLC-only simulation (no intra-bar wicks — overestimates win rate)
  - No slippage modeling
  - Simplified P&L math (directional only, not accurate in yen value)

Interpretation:
  Focus on RELATIVE RANKING, not absolute P&L numbers. A top-3 combo
  of SL=5%, TP=12%, Trail=2% is probably strong — but the ¥38M profit
  figure is unreliable. Validate in MT5 Every Tick mode.
"""

import json, math
from datetime import datetime

# ── Load or fetch data ──
try:
    with open(r'C:\Users\decni\projects\mql-bots\btc_data.json') as f:
        data = json.load(f)
        candles = data['rates']
except FileNotFoundError:
    # Fall back to Binance fetch
    import urllib.request
    from datetime import datetime, timedelta
    end = datetime.utcnow()
    candles = []
    while len(candles) < 2000:
        url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&endTime={int(end.timestamp()*1000)}&limit=1000"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            batch = json.loads(resp.read().decode())
        if not batch: break
        candles = batch + candles
        if len(batch) < 1000: break
        end = datetime.fromtimestamp(batch[0][0]/1000) - timedelta(hours=1)
    # Convert format
    candles = [{'t': int(c[0]), 'o': float(c[1]), 'h': float(c[2]),
                'l': float(c[3]), 'c': float(c[4])} for c in candles]

print(f"Loaded {len(candles)} 1H candles")

prices = [c['c'] for c in candles]

def ema(prices, period, idx):
    if idx < period: return None
    pp = prices[idx-period:idx]
    m, e = 2/(period+1), pp[0]
    for p in pp[1:]: e = (p-e)*m+e
    return e

def rsi(prices, period, idx):
    if idx < period+1: return 50
    g = l = 0
    for i in range(idx-period, idx):
        ch = prices[i] - prices[i-1]
        if ch > 0: g += ch
        else: l -= ch
    if l == 0: return 100
    return 100 - 100/(1 + g/l)

GRID = {
    'sl_pct':  [4.0, 5.0, 6.0, 7.0, 8.0],
    'tp_pct':  [6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
    'trail_pct': [2.0, 3.0, 4.0, 5.0],
}

total_combos = len(GRID['sl_pct']) * len(GRID['tp_pct']) * len(GRID['trail_pct'])
print(f"Tuning {len(GRID)} params: {total_combos} combinations")
print()

results = []

for sl_pct in GRID['sl_pct']:
    for tp_pct in GRID['tp_pct']:
        for trail_pct in GRID['trail_pct']:
            balance = 1_000_000
            position = None
            trades = []
            winners = losers = 0
            max_dd = 0
            peak = balance

            for i in range(200, len(candles)):
                p = candles[i]['c']
                ema_v = ema(prices, 200, i)
                if ema_v is None: continue
                rsi_v = rsi(prices, 105, i)

                eq = balance
                if position:
                    fl = (p - position['entry']) / position['entry'] if position['dir'] == 'L' \
                         else (position['entry'] - p) / position['entry']
                    eq += fl * position['entry'] * 0.01 * 10000
                if eq > peak: peak = eq
                dd = (peak - eq) / peak * 100
                if dd > max_dd: max_dd = dd

                # Manage position
                if position:
                    entry = position['entry']
                    d = position['dir']
                    pnl_pct = ((p - entry) / entry if d == 'L' else (entry - p) / entry) * 100

                    if (d == 'L' and p <= entry * (1 - sl_pct/100)) or \
                       (d == 'S' and p >= entry * (1 + sl_pct/100)):
                        pnl = -entry * 0.01 * 10000 * (sl_pct/100) - 500
                        balance += pnl; losers += 1
                        position = None; trades.append(pnl); continue

                    if (d == 'L' and p >= entry * (1 + tp_pct/100)) or \
                       (d == 'S' and p <= entry * (1 - tp_pct/100)):
                        pnl = entry * 0.01 * 10000 * (tp_pct/100) - 500
                        balance += pnl; winners += 1
                        position = None; trades.append(pnl); continue

                    # Trailing
                    if pnl_pct > trail_pct:
                        ts = p * (1 - trail_pct/100) if d == 'L' else p * (1 + trail_pct/100)
                        prev = position.get('ts', 0 if d == 'L' else 999999)
                        if (d == 'L' and ts > prev) or (d == 'S' and ts < prev):
                            position['ts'] = ts

                    trail = position.get('ts', 0)
                    if trail > 0 and ((d == 'L' and p < trail) or (d == 'S' and p > trail)):
                        trail_profit = ((trail - entry) / entry if d == 'L' else (entry - trail) / entry) * 100
                        pnl = entry * 0.01 * 10000 * (trail_profit/100) - 500
                        balance += pnl; winners += 1
                        position = None; trades.append(pnl); continue

                # Entry
                elif position is None and i >= 4:
                    lo = min(candles[x]['l'] for x in range(i-4, i))
                    hi = max(candles[x]['h'] for x in range(i-4, i))
                    rng = hi - lo
                    if p <= lo + rng*0.25 and p > ema_v and rsi_v < 65:
                        position = {'dir': 'L', 'entry': p, 'ts': 0}
                    elif p >= hi - rng*0.25 and p < ema_v and rsi_v > 25:
                        position = {'dir': 'S', 'entry': p, 'ts': 0}

            total_trades = winners + losers
            gp = sum(t for t in trades if t > 0)
            gl = abs(sum(t for t in trades if t < 0))
            pf = gp / gl if gl > 0 else gp
            wr = (winners/total_trades*100) if total_trades > 0 else 0

            results.append({
                'sl': sl_pct, 'tp': tp_pct, 'trail': trail_pct,
                'trades': total_trades, 'wins': winners, 'losses': losers,
                'wr': wr, 'net': balance - 1_000_000, 'pf': pf, 'dd': max_dd
            })

results.sort(key=lambda r: -r['pf'])

# Print results
print(f"{'='*80}")
print(f"  OPTIMIZATION RESULTS — Sorted by Profit Factor")
print(f"{'='*80}")
print(f"  {'SL':>4} {'TP':>4} {'Trail':>5} {'Trades':>6} {'W/L':>7} {'WR':>5} {'P&L':>10} {'PF':>5} {'DD':>5}")
print(f"  {'-'*4} {'-'*4} {'-'*5} {'-'*6} {'-'*7} {'-'*5} {'-'*10} {'-'*5} {'-'*5}")

for r in results[:15]:
    print(f"  {r['sl']:>4.0f} {r['tp']:>4.0f} {r['trail']:>5.1f} {r['trades']:>6} {r['wins']}/{r['losses']:>3} {r['wr']:>3.0f}% {r['net']:>9,.0f}¥ {r['pf']:>4.1f} {r['dd']:>4.1f}%")

# Save to file
with open('optimization_results.txt', 'w') as f:
    f.write("sl,tp,trail,trades,wins,losses,wr,net,pf,dd\n")
    for r in results:
        f.write(f"{r['sl']},{r['tp']},{r['trail']},{r['trades']},{r['wins']},{r['losses']},{r['wr']:.1f},{r['net']:.0f},{r['pf']:.2f},{r['dd']:.1f}\n")

print(f"\nResults saved to optimization_results.txt ({len(results)} combos)")
