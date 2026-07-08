# V5.0 → V5.2a Evolution & Bug Fixes

## Version History

### V5.0 (Structural Fixes)
- SL: 3.48% → 5.0%
- RSI Oversold: 7.5 → 25.0
- Trail: 1.5% → 3.0%
- Equity Activation: ¥2,000,000 → ¥50,000
- Zone Expiry: 24h → 48h
- Body Strength: 60 → 50
- Break-Even: OFF → ON (2% trigger, 0.5% buffer)
- Partial TP: OFF → ON (30% at 5%)
- Daily Loss Limit: NEW (8%)
- Max Trades/Day: NEW (3)
- Trail cushion: 500pts → 300pts

### V5.1 (Market-Tuned for Jul 2026 Bear Market)
Market conditions: Price ¥10,013,683, 9% below EMA200, ATR 3.45%, 20d vol 14.7%
- SL: 5.0% → 7.0%
- TP: 10.0% → 8.0%
- Trail: 3.0% → 4.0%
- RSI Overbought: 58.5 → 65.0
- BE Trigger: 2.0% → 3.0%
- Partial TP Trigger: 5.0% → 4.0%
- Partial Close: 30% → 40%
- Max Trades/Day: 3 → 2
- Daily Loss: 8% → 6%
- Zone Expiry: 48h → 36h

### V5.2 (BoS Integration)
Added Break of Structure confirmation from LowDDWithBoS:
- `CheckLTFBreakOfStructure()` function
- `UseLTFConfirmation`, `LTF`, `BoSLookback` inputs
- BoS waits for 15M structure break AFTER 4H zone touch
- Dashboards shows BoS status

### V5.2a (Data-Driven Params)
Based on full-year BTCJPY analysis (365 days, range 102.1%, avg monthly range 20.4%):
- SL: 7.0% → 6.5%
- TP: 8.0% → 10.0%
- Trail: 4.0% → 3.5%
- Daily Loss: 6.0% → 5.0%

## Daily Loss Limit Bug Fix

### The Bug
When `MaxDailyLossPercent` triggered, `protectionHalt = true` was set. `OnTick()` started with `if(protectionHalt) return;` which meant `ResetDailyCounters()` was NEVER called again — even on the next day. The halt was permanent.

### The Fix (2 changes)
1. Moved `ResetDailyCounters()` BEFORE the `if(protectionHalt) return` guard in `OnTick()`
2. Inside `ResetDailyCounters()`, when a new day is detected (`currentDay != g_currentDay`), reset `protectionHalt = false` and log "Daily loss limit reset - new trading day"

```cpp
void OnTick() {
   ResetDailyCounters();  // Must run first
   if(protectionHalt) return;
   ...
}

void ResetDailyCounters() {
   datetime currentDay = iTime(_Symbol, PERIOD_D1, 0);
   if(currentDay != g_currentDay) {
      g_currentDay = currentDay;
      g_tradesToday = 0; g_dailyPNL = 0;
      g_dailyStartingEquity = AccountInfoDouble(ACCOUNT_EQUITY);
      if(protectionHalt) {
         protectionHalt = false;
         Print("Daily loss limit reset - new trading day");
      }
   }
   ...
}
```
