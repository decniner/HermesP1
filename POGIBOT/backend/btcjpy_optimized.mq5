//+------------------------------------------------------------------+
//|                          BTCJPY_LowDDWithBoS_Opt_V5_1.mq5        |
//|      Dynamic long/short bias based on EMA trend + S/D zones      |
//|      V5.1: Fixes: dynamic bias, wider SL, zone-on-new-bar-only   |
//+------------------------------------------------------------------+
#property copyright "DEN Trading - BTCJPY Optimized Edition"
#property version   "5.10"
#property strict
#include <Trade\Trade.mqh>

input group "=== Strategy Settings ==="
input long     MagicNumber     = 987659;
input int      EMAPeriod       = 88;
input int      RSIPeriod       = 14;
input double   RSILongMin      = 30.0;    // RSI floor for longs
input double   RSIShortMax     = 60.0;    // RSI ceiling for shorts

input group "=== Zone Detection ==="
input ENUM_TIMEFRAMES ZoneTF    = PERIOD_H4;
input int      BodyStrengthMin  = 50;     // Lower = more zones
input int      ZoneExpiryHours  = 24;

input group "=== Risk Management ==="
input double   BaseLotSize      = 0.01;
input double   StopLossATR      = 3.6;    // Optimized: 3.6x ATR
input double   TakeProfitATR    = 12.95;  // Optimized: 12.95x ATR (trailing does the work)
input double   MaxDailyLossPct  = 5.0;
input int      MaxConsecutiveLosses = 3;

input group "=== Trailing ==="
input bool     UseTrailing      = true;
input double   TrailActivatePct = 1.0;
input double   TrailOffsetPct   = 0.6;

input group "=== Partial Profit ==="
input bool     UsePartialTP     = true;
input double   PartialTP1Pct    = 3.0;
input double   PartialClose1Pct = 50.0;
input double   PartialTP2Pct    = 6.0;
input double   PartialClose2Pct = 75.0;

CTrade      trade;
int         emaH, rsiH, atrH;
datetime    g_lastTradeTime = 0;
int         g_consecutiveLosses = 0;
double      g_dailyStart = 0;
bool        g_dailyStop = false;
datetime    g_lastDay = 0;
datetime    g_lastZoneBar = 0;

struct SZone { double ph, pl; bool ok; datetime ct; };
SZone g_demand, g_supply;
int tw=0, tl=0, tc=0;

//+------------------------------------------------------------------+
int OnInit() {
   emaH = iMA(_Symbol, PERIOD_CURRENT, EMAPeriod, 0, MODE_EMA, PRICE_CLOSE);
   rsiH = iRSI(_Symbol, PERIOD_CURRENT, RSIPeriod, PRICE_CLOSE);
   atrH = iATR(_Symbol, PERIOD_CURRENT, 14);
   if(emaH==INVALID_HANDLE||rsiH==INVALID_HANDLE||atrH==INVALID_HANDLE) return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);
   g_dailyStart = AccountInfoDouble(ACCOUNT_EQUITY);
   return INIT_SUCCEEDED;
}
void OnDeinit(const int) { IndicatorRelease(emaH); IndicatorRelease(rsiH); IndicatorRelease(atrH); }

//+------------------------------------------------------------------+
void OnTick() {
   // Daily reset
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   datetime td = dt.day_of_year + dt.year * 1000;
   if(td != g_lastDay) { g_lastDay = td; g_dailyStart = AccountInfoDouble(ACCOUNT_EQUITY); g_dailyStop = false; }
   double lossPct = (g_dailyStart - AccountInfoDouble(ACCOUNT_EQUITY)) / g_dailyStart * 100;
   if(lossPct >= MaxDailyLossPct && !g_dailyStop) { g_dailyStop = true; CloseAll(); return; }
   if(g_dailyStop) return;

   if(PositionsTotal() > 0) { Trailing(); PartialTP(); }
   CheckSignals();
}

//+------------------------------------------------------------------+
double CalcLot() {
   double b = BaseLotSize;
   if(tc > 0) { double wr = (double)tw/tc; b *= (wr > 0.45) ? 1.5 : (wr > 0.35) ? 1.0 : 0.7; }
   if(g_consecutiveLosses >= 2) b *= 0.6;
   return NormalizeDouble(MathMax(b, BaseLotSize*0.5), 2);
}

//+------------------------------------------------------------------+
void CheckSignals() {
   if(PositionsTotal() > 0 || g_dailyStop) return;
   datetime bt = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(g_lastTradeTime >= bt) return;

   if(g_consecutiveLosses >= MaxConsecutiveLosses) {
      static datetime cd = 0;
      if(cd == 0) cd = bt + 5*PeriodSeconds(PERIOD_CURRENT);
      if(bt < cd) return; if(bt >= cd) { g_consecutiveLosses = 0; cd = 0; }
   }

   double ema[], rsi[], atr[];
   if(CopyBuffer(emaH,0,0,2,ema)<2||CopyBuffer(rsiH,0,0,1,rsi)<1||CopyBuffer(atrH,0,0,1,atr)<1) return;
   double bid = SymbolInfoDouble(_Symbol,SYMBOL_BID), ask = SymbolInfoDouble(_Symbol,SYMBOL_ASK);
   double atrV = atr[0]; if(atrV <= 0) atrV = bid * 0.005;
   double slope = ema[0] - ema[1];
   // Normalize slope relative to price
   double slopePct = slope / ema[0] * 100;

   DetectZone();

   // Dynamic bias: EMA slope > 0.01% = bullish, < -0.01% = bearish
   bool trendUp = slopePct > 0.01;
   bool trendDn = slopePct < -0.01;
   bool canLong = trendUp || (!trendDn && g_consecutiveLosses == 0);
   bool canShort = trendDn;

   // LONG
   bool inD = g_demand.ok && bid <= g_demand.ph && bid >= g_demand.pl - atrV*0.3;
   if(canLong && g_demand.ok && inD && bid > ema[0] && rsi[0] >= RSILongMin && rsi[0] < 75) {
      double sl = bid - atrV*StopLossATR, tp = bid + atrV*TakeProfitATR;
      if(trade.Buy(CalcLot(),_Symbol,ask,sl,tp)) { g_demand.ok=false; g_lastTradeTime=bt; }
      return;
   }

   // SHORT
   bool inS = g_supply.ok && ask >= g_supply.pl && ask <= g_supply.ph + atrV*0.3;
   if(canShort && g_supply.ok && inS && ask < ema[0] && rsi[0] <= RSIShortMax && rsi[0] > 25) {
      double sl = ask + atrV*StopLossATR, tp = ask - atrV*TakeProfitATR;
      if(trade.Sell(CalcLot(),_Symbol,bid,sl,tp)) { g_supply.ok=false; g_lastTradeTime=bt; }
      return;
   }
}

//+------------------------------------------------------------------+
void DetectZone() {
   MqlRates r[]; ArraySetAsSeries(r,true);
   if(CopyRates(_Symbol,ZoneTF,0,3,r) < 2) return;

   // Only detect once per H4 bar
   if(r[1].time == g_lastZoneBar) return;
   g_lastZoneBar = r[1].time;

   double body = MathAbs(r[1].close - r[1].open), rg = r[1].high - r[1].low;
   if(rg <= 0) return;
   double pct = body/rg * 100;
   if(pct < BodyStrengthMin) return;

   if(r[1].close > r[1].open) {  // Bullish = Demand
      g_demand.pl = r[1].low; g_demand.ph = r[1].low + rg*0.25;
      g_demand.ok = true; g_demand.ct = TimeCurrent();
   } else if(r[1].close < r[1].open) {  // Bearish = Supply
      g_supply.pl = r[1].high - rg*0.25; g_supply.ph = r[1].high;
      g_supply.ok = true; g_supply.ct = TimeCurrent();
   }

   int exp = ZoneExpiryHours*3600;
   if(g_demand.ok && TimeCurrent()-g_demand.ct > exp) g_demand.ok=false;
   if(g_supply.ok && TimeCurrent()-g_supply.ct > exp) g_supply.ok=false;
}

//+------------------------------------------------------------------+
void Trailing() {
   if(!UseTrailing) return;
   for(int i=PositionsTotal()-1;i>=0;i--) {
      ulong t=PositionGetTicket(i);
      if(!PositionSelectByTicket(t)||PositionGetString(POSITION_SYMBOL)!=_Symbol||PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      double en=PositionGetDouble(POSITION_PRICE_OPEN),sl=PositionGetDouble(POSITION_SL),tp=PositionGetDouble(POSITION_TP);
      long ty=PositionGetInteger(POSITION_TYPE);
      double prc=ty==POSITION_TYPE_BUY?SymbolInfoDouble(_Symbol,SYMBOL_BID):SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      if(MathAbs(prc-en)/en*100<TrailActivatePct) continue;
      double ds=prc*(TrailOffsetPct/100);
      double ns=ty==POSITION_TYPE_BUY?prc-ds:prc+ds;
      if((ty==POSITION_TYPE_BUY&&(ns>sl||sl==0))||(ty==POSITION_TYPE_SELL&&(ns<sl||sl==0)))
         trade.PositionModify(t,NormalizeDouble(ns,_Digits),tp);
   }
}

//+------------------------------------------------------------------+
void PartialTP() {
   if(!UsePartialTP) return;
   for(int i=PositionsTotal()-1;i>=0;i--) {
      ulong t=PositionGetTicket(i);
      if(!PositionSelectByTicket(t)||PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      double iv=PositionGetDouble(POSITION_VOLUME),en=PositionGetDouble(POSITION_PRICE_OPEN);
      long ty=PositionGetInteger(POSITION_TYPE);
      double prc=ty==POSITION_TYPE_BUY?SymbolInfoDouble(_Symbol,SYMBOL_BID):SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      double pct=MathAbs(prc-en)/en*100;
      if(pct>=PartialTP1Pct&&iv>=BaseLotSize*0.8) {
         double cl=NormalizeDouble(iv*PartialClose1Pct/100,2);
         if(cl>0) trade.PositionClosePartial(t,cl); return;
      }
      if(pct>=PartialTP2Pct&&iv<BaseLotSize*0.8&&iv>BaseLotSize*0.1) {
         double cl=NormalizeDouble(iv*PartialClose2Pct/100,2);
         if(cl>0) trade.PositionClosePartial(t,cl);
      }
   }
}

//+------------------------------------------------------------------+
void CloseAll() {
   for(int i=PositionsTotal()-1;i>=0;i--) {
      ulong t=PositionGetTicket(i);
      if(PositionSelectByTicket(t)&&PositionGetInteger(POSITION_MAGIC)==MagicNumber) trade.PositionClose(t);
   }
}
