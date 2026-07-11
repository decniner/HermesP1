//+------------------------------------------------------------------+
//|                          BTCJPY_LowDDWithBoS_Opt_V6.mq5          |
//|      Pass 54 optimized: SlowMA=317, SL=10.09%, TP=71.2%, BoS    |
//+------------------------------------------------------------------+
#property copyright "DEN Trading - BTCJPY Optimized V6"
#property version   "6.00"
#property strict
#include <Trade\Trade.mqh>

input group "=== Strategy ==="
input long     MagicNumber        = 987662;
input int      SlowMAPeriod       = 317;
input bool     ShowDashboard      = false;
input bool     ShowFullDashboard  = false;
input bool     ShowMonthlySummaryOnly = false;

input group "=== RSI ==="
input bool     UseRSIFilter       = true;
input int      RSIPeriod          = 105;
input double   RSIOverbought      = 58.5;
input double   RSIOversold        = 7.5;

input group "=== Risk ==="
input double   StopLossPercent    = 10.09;
input double   TakeProfitPercent  = 71.2;
input double   FixedLotSize       = 0.01;

input group "=== Trailing ==="
input bool     UseTrailing        = true;
input bool     UseIntelligentTrail = true;
input double   TrailingStopPct    = 1.5;

input group "=== Partial TP ==="
input bool     UsePartialTP       = true;
input double   PartialTP_TriggerPct = 5.0;
input double   PartialClosePct    = 50.0;

input group "=== LTF Confirmation ==="
input bool     UseLTFConfirmation = true;
input ENUM_TIMEFRAMES LTF         = PERIOD_M15;
input int      BoSLookback        = 47;

input group "=== Zone Detection ==="
input ENUM_TIMEFRAMES ZoneTF      = PERIOD_H4;
input int      BodyStrengthMin    = 60;
input int      ZoneExpiryHours    = 24;

CTrade   trade;
int      slowMA, rsi;
datetime g_lastTradeTime = 0;
struct SZone { double hi, lo; bool ok; datetime ct; };
SZone g_dem, g_sup;
datetime g_zoneBar = 0;
bool     g_htfTouched = false;

int OnInit() {
   slowMA = iMA(_Symbol, PERIOD_CURRENT, SlowMAPeriod, 0, MODE_EMA, PRICE_CLOSE);
   rsi    = iRSI(_Symbol, PERIOD_CURRENT, RSIPeriod, PRICE_CLOSE);
   if(slowMA==INVALID_HANDLE||rsi==INVALID_HANDLE) return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);
   return INIT_SUCCEEDED;
}
void OnDeinit(const int) { IndicatorRelease(slowMA); IndicatorRelease(rsi); }

void OnTick() {
   if(PositionsTotal() > 0) { ManageTrailing(); return; }
   datetime bt = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(g_lastTradeTime >= bt) return;

   double bid = SymbolInfoDouble(_Symbol,SYMBOL_BID), ask = SymbolInfoDouble(_Symbol,SYMBOL_ASK);
   ScanZones();
   double ema[], rsiV[];
   if(CopyBuffer(slowMA,0,0,1,ema)<1||CopyBuffer(rsi,0,0,1,rsiV)<1) return;

   // Long setup
   bool inDemand = g_dem.ok && bid >= g_dem.lo && bid <= g_dem.hi;
   if(inDemand) g_htfTouched = true;

   if(UseLTFConfirmation && g_htfTouched) {
      MqlRates m15[]; ArraySetAsSeries(m15,true);
      if(CopyRates(_Symbol, LTF, 0, BoSLookback+2, m15) >= BoSLookback+2) {
         // Long
         if(inDemand && bid > ema[0] && rsiV[0] < RSIOverbought && CheckBoS(1)) {
            if(trade.Buy(FixedLotSize,_Symbol,ask,ask*(1-StopLossPercent/100),ask*(1+TakeProfitPercent/100))) {
               g_dem.ok=false; g_htfTouched=false; g_lastTradeTime=bt;
            }
            return;
         }
         // Short
         if(g_sup.ok && ask >= g_sup.lo && ask <= g_sup.hi && ask < ema[0] && rsiV[0] > RSIOversold && CheckBoS(-1)) {
            if(trade.Sell(FixedLotSize,_Symbol,bid,bid*(1+StopLossPercent/100),bid*(1-TakeProfitPercent/100))) {
               g_sup.ok=false; g_htfTouched=false; g_lastTradeTime=bt;
            }
            return;
         }
      }
   }
}

bool CheckBoS(int dir) {
   MqlRates m15[]; ArraySetAsSeries(m15,true);
   if(CopyRates(_Symbol, LTF, 0, BoSLookback+2, m15) < BoSLookback+2) return false;
   if(dir==1) {
      double swingHi = 0;
      for(int i=1; i<=BoSLookback; i++) if(m15[i].high > swingHi) swingHi = m15[i].high;
      return SymbolInfoDouble(_Symbol,SYMBOL_BID) > swingHi;
   } else {
      double swingLo = DBL_MAX;
      for(int i=1; i<=BoSLookback; i++) if(m15[i].low < swingLo) swingLo = m15[i].low;
      return SymbolInfoDouble(_Symbol,SYMBOL_ASK) < swingLo;
   }
}

void ScanZones() {
   MqlRates h4[]; ArraySetAsSeries(h4,true);
   if(CopyRates(_Symbol,ZoneTF,0,3,h4)<2) return;
   if(h4[1].time==g_zoneBar) return; g_zoneBar=h4[1].time;
   double body=MathAbs(h4[1].close-h4[1].open), rg=h4[1].high-h4[1].low;
   if(rg<=0||body/rg*100<BodyStrengthMin) return;
   if(h4[1].close>h4[1].open) {
      g_dem.lo=h4[1].low; g_dem.hi=h4[1].low+rg*0.25; g_dem.ok=true; g_dem.ct=TimeCurrent();
   } else {
      g_sup.lo=h4[1].high-rg*0.25; g_sup.hi=h4[1].high; g_sup.ok=true; g_sup.ct=TimeCurrent();
   }
   int sec=ZoneExpiryHours*3600;
   if(g_dem.ok&&TimeCurrent()-g_dem.ct>sec) g_dem.ok=false;
   if(g_sup.ok&&TimeCurrent()-g_sup.ct>sec) g_sup.ok=false;
}

void ManageTrailing() {
   for(int i=PositionsTotal()-1;i>=0;i--) {
      ulong t=PositionGetTicket(i);
      if(!PositionSelectByTicket(t)||PositionGetString(POSITION_SYMBOL)!=_Symbol||PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      double en=PositionGetDouble(POSITION_PRICE_OPEN),sl=PositionGetDouble(POSITION_SL),tp=PositionGetDouble(POSITION_TP);
      long ty=PositionGetInteger(POSITION_TYPE);
      double prc=(ty==POSITION_TYPE_BUY)?SymbolInfoDouble(_Symbol,SYMBOL_BID):SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      if(UseIntelligentTrail) {
         MqlRates h4[]; ArraySetAsSeries(h4,true);
         if(CopyRates(_Symbol,ZoneTF,0,21,h4)>=21) {
            int lb=20;
            double pp=MathAbs(prc-en)/en*100;
            if(pp>3) lb=10; if(pp>7) lb=5;
            if(ty==POSITION_TYPE_BUY) {
               int lb2=iLowest(_Symbol,ZoneTF,MODE_LOW,lb,1);
               double ns=h4[lb2].low-500*_Point;
               if(ns>sl||sl==0) trade.PositionModify(t,NormalizeDouble(ns,_Digits),tp);
            } else {
               int hb=iHighest(_Symbol,ZoneTF,MODE_HIGH,lb,1);
               double ns=h4[hb].high+500*_Point;
               if(ns<sl||sl==0) trade.PositionModify(t,NormalizeDouble(ns,_Digits),tp);
            }
         }
      }
   }
}
