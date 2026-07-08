# Session Notes: BoS Integration + MT5 Troubleshooting

## Break of Structure (BoS) Confirmation

### What it does
Waits for price to break a recent structure high/low on a **lower timeframe** (e.g., 15M) before entering a trade, even if price is already inside a 4H Supply/Demand zone. This filters out "fake touches" where price briefly dips into a zone then keeps going.

### The Code

```mq5
// Input parameters
input bool     UseLTFConfirmation = true;     // Enable BoS confirmation
input ENUM_TIMEFRAMES  LTF          = PERIOD_M15; // Entry timeframe (15M)
input int              BoSLookback  = 5;         // Candles to check for structure break

// Global tracker
bool g_htfZoneTouched = false;  // Set to true when price enters a 4H zone

// The BoS function
bool CheckLTFBreakOfStructure(int direction) {
   if(direction == 1) {  // Long: break ABOVE recent resistance
      int highBar = iHighest(_Symbol, LTF, MODE_HIGH, BoSLookback, 1);
      double resistance = iHigh(_Symbol, LTF, highBar);
      if(SymbolInfoDouble(_Symbol, SYMBOL_BID) > resistance) return true;
   } else if(direction == -1) {  // Short: break BELOW recent support
      int lowBar = iLowest(_Symbol, LTF, MODE_LOW, BoSLookback, 1);
      double support = iLow(_Symbol, LTF, lowBar);
      if(SymbolInfoDouble(_Symbol, SYMBOL_ASK) < support) return true;
   }
   return false;
}
```

### Integration in CheckSignals()
The BoS path runs BEFORE the original momentum confirmation path. When enabled, it short-circuits the regular entry logic:

```mq5
// Track when price touches the 4H zone
if(inDemand || inSupply) g_htfZoneTouched = true;

// BoS path
if(UseLTFConfirmation && g_htfZoneTouched) {
   if(allowLong && inDemand && CheckLTFBreakOfStructure(1)) {
      // Enter long — structure just broke up on 15M
   } else if(allowShort && inSupply && CheckLTFBreakOfStructure(-1)) {
      // Enter short — structure just broke down on 15M
   }
   return;  // Skip original entry logic entirely
}

// Original path (no BoS)
if(!UseLTFConfirmation) { ... }
```

### When BoS helps vs hurts
| Market | Effect |
|--------|--------|
| **Strong trend** | ✅ Confirms entries in trend direction |
| **Range / Choppy** | ✅ Reduces false breakouts |
| **Quick reversal from zone** | ❌ May miss entry if structure hasn't formed yet |
| **Low volatility / narrow range** | ❌ BoS may never trigger, resulting in 0 trades |

---

## MT5 Python API Connection Troubleshooting

### The problem
`MetaTrader5.initialize()` frequently fails with:
- `(-6, 'Terminal: Authorization failed')`
- `(-10001, 'IPC send failed')`
- `(-10003, 'IPC initialize failed')`
- `(-10005, 'IPC timeout')`

### Root causes
1. **Multiple terminal instances** — Each MT5 instance binds to the IPC port. If you launch a new terminal while one is already running, the Python API can't tell which to connect to.
2. **Portable mode** — `terminal64.exe /portable` starts without an account logged in. The Python API requires an authenticated session.
3. **Architecture mismatch** — 32-bit Python with 64-bit MT5 (or vice versa) breaks the named pipe IPC.
4. **Permission elevation** — If MT5 is under `Program Files`, the Python process may not have the same access rights to create IPC pipes.

### The fix sequence
1. Kill all existing terminals first: `taskkill /F /IM terminal64.exe`
2. Start a fresh terminal normally (NOT `/portable`): double-click the desktop icon or run `terminal64.exe` without flags
3. Wait for it to fully load and auto-login (15-20 seconds)
4. Call `mt5.initialize()` WITHOUT arguments — it auto-discovers the running terminal

### When the API still won't connect
**Cache the data and work offline:**
```python
import MetaTrader5 as mt5, json
from datetime import datetime

# Connect once, get the data, save it
if mt5.initialize():
    rates = mt5.copy_rates_from('BTCJPY', mt5.TIMEFRAME_H1, datetime.now(), 100*24)
    data = [{'t': int(r[0]), 'o': float(r[1]), 'h': float(r[2]), 'l': float(r[3]), 'c': float(r[4])} for r in rates]
    with open('btc_data.json', 'w') as f:
        json.dump({'rates': data}, f)
    mt5.shutdown()

# All future analysis uses the cached file
with open('btc_data.json') as f:
    data = json.load(f)
candles = data['rates']
```

**Never hardcode the belief that "MT5 API is broken."** The connection works when the terminal is freshly started and logged in. If it fails, the environment state changed (terminal was killed, portable mode was used, etc.). Fix the environment, then retry.

---

## Multi-Bot Comparison Methodology

When the user has several MQL5 bots and asks "which is best," compare them on these axes:

| Criteria | How to evaluate |
|----------|----------------|
| **Strategy sophistication** | Supply/Demand + BoS > S&D only > MA Crossover > Grid |
| **Risk management** | Count: equity protection + trail + BE + partial TP + daily loss limit |
| **Parameter realism** | Check SL vs ATR, RSI levels vs real data, equity activation vs account size |
| **Code quality** | Proper cleanup, MT5 API correctness, no memory leaks |
| **Evolution** | Multiple versions with actual improvements (not just number bumps) |

### The comparison table format

| Feature | Bot A (V4.x) | Bot B (V5.x) | Winner |
|---------|:-----------:|:-----------:|:------:|
| Strategy type | Supply/Demand | Supply/Demand | Tie |
| SL | 3.48% (too tight) | 6.5% (ATR-based) | Bot B |
| RSI Oversold | 7.5 (never hits) | 25 (practical) | Bot B |
| Break-even | OFF | ON | Bot B |
| Daily loss limit | Missing | 5% | Bot B |
| Max Drawdown (backtest) | 26.5% | Lower | Bot B (expected) |

---

## Multi-Bot Version Evolution Protocol

### Naming convention
When creating a new version that merges features from two different bots:
```
ORIGINAL_BOT_NAME + FEATURE_SOURCE → VERSION
  
Example: V5.1 + LowDDWithBoS (BoS) → V5.2
```

### Changelog format
Every evolved version MUST have a changelog comment block at the top:
```mq5
// V5.2 CHANGES from V5.1:
//   1. SL 7% → 6.5%    (Full-year data: avg monthly range 20.4%)
//   2. TP 8% → 10%     (50% of avg monthly range)
//   3. Trail 4% → 3.5% (15% of avg monthly range)
//   4. Daily loss 6% → 5% (49% max DD = brutal bear market)
//   5. NEW: BoS confirmation from LowDDWithBoS
```

### File organization
Keep each distinct version as its own `.mq5` file:
```
DEN_EA/
├── BTCJPY_QuantumKingv1.2.mq5
├── BTCJPY_HybridBot.mq5          (V4.3 original)
├── BTCJPY_LowDDWithBoS.mq5       (V4.3 + BoS)
├── BTCJPY_Hybrid_Pro_V5_0.mq5    (Parameter fixes)
├── BTCJPY_Hybrid_Pro_V5_1.mq5    (Market-tuned)
├── BTCJPY_Hybrid_Pro_V5_2.mq5    (V5.1 + BoS)
```

---

## MetaTrader Strategy Tester .set File Format

The `.set` file used by MT5's Strategy Tester follows this format:

```ini
[Tester]
Expert=C:\path\to\Expert.ex5
Symbol=BTCJPY
Period=H1
Optimization=1               # 1 = enable, 0 = disable
Model=0                      # 0 = every tick, 1 = OHLC
FromDate=2026.04.01
ToDate=2026.07.01
Deposit=1000000
Leverage=500
[Optimizer]
Criterion=6                  # 6 = Profit Factor, 0 = Balance, etc.
[ExpertParameters]
StopLossPercent=4.0|8.0|0.5  # min|max|step (triggers optimization)
TakeProfitPercent=6.0|12.0|1.0
```

### How to run from CLI (unreliable — use MT5 GUI instead)
```
"C:\Program Files\MetaTrader 5\terminal64.exe" /config:"path\to\file.set"
```
This often fails when another MT5 instance is already running. The MT5 GUI method (Ctrl+R → Load .set file → Start) is more reliable.
