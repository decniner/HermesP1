//+------------------------------------------------------------------+
//|                          BTCJPY_Institutional_Sniper_V2.mq5      |
//|      Fixed: safe lot sizing, retracement entries, wider SL       |
//+------------------------------------------------------------------+
#property copyright "DEN Trading - BTCJPY Sniper"
#property version   "2.00"
#property strict
#include <Trade\Trade.mqh>

input group "=== Market Structure ==="
input ulong    MagicNumber        = 987661;
input int      ZoneBodyMinPct     = 50;
input int      ZoneExpiryHours    = 24;

input group "=== Entry ==="
input double   BaseLot            = 0.01;
input double   SL_ATR_Mult        = 0.5;     // SL buffer beyond zone edge
input double   MinRR              = 3.0;

input group "=== Trailing ==="
input double   TrailActivatePct   = 2.0;
input double   TrailDistPct       = 1.0;

input group "=== Protection ==="
input int      MaxSpread          = 15000;
input double   MaxDailyLossPct    = 5.0;
input int      MaxConsecLosses    = 2;

CTrade   trade;
int      hATR;
datetime g_lastBar = 0;
int      g_consecLoss = 0;
int      g_lastLossDir = 0;
datetime g_lockUntil = 0;
datetime g_dayCheck = 0;
double   g_dayStart = 0;
bool     g_dayHalt = false;

struct SZone { double hi, lo; bool ok; datetime ct; };
SZone g_dem, g_sup;
datetime g_zoneBar = 0;
int g_tc = 0;

int OnInit() {
   hATR = iATR(_Symbol, PERIOD_CURRENT, 14);
   if(hATR == INVALID_HANDLE) return INIT_FAILED;
   trade.SetExpertMagicNumber(MagicNumber);
   g_dayStart = AccountInfoDouble(ACCOUNT_EQUITY);
   EventSetTimer(1);
   return INIT_SUCCEEDED;
}
void OnDeinit(const int) { IndicatorRelease(hATR); }
void OnTimer() {
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   datetime td = dt.day_of_year + dt.year * 1000;
   if(td != g_dayCheck) { g_dayCheck = td; g_dayStart = AccountInfoDouble(ACCOUNT_EQUITY); g_dayHalt = false; }
   double lp = (g_dayStart - AccountInfoDouble(ACCOUNT_EQUITY)) / MathMax(g_dayStart,1) * 100;
   if(lp >= MaxDailyLossPct && !g_dayHalt) { g_dayHalt = true; CloseAll(); }
}

void OnTick() {
   if(g_dayHalt) return;
   if(g_lockUntil > 0 && TimeCurrent() < g_lockUntil) return;
   if(g_lockUntil > 0 && TimeCurrent() >= g_lockUntil) { g_consecLoss = 0; g_lastLossDir = 0; g_lockUntil = 0; }
   if((int)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD) > MaxSpread) return;

   // Only trade on new completed M15 bars
   datetime bt = iTime(_Symbol, PERIOD_CURRENT, 0);
   if(bt == g_lastBar) return;
   g_lastBar = bt;

   // Manage existing position
   if(PositionsTotal() > 0) { Trail(); return; }

   // Scan H4 zones
   ScanZones();

   // Get current ATR
   double atr[];
   if(CopyBuffer(hATR,0,0,1,atr)<1) return;
   double atrV = MathMax(atr[0], SymbolInfoDouble(_Symbol,SYMBOL_BID)*0.005);

   double bid = SymbolInfoDouble(_Symbol,SYMBOL_BID);
   double ask = SymbolInfoDouble(_Symbol,SYMBOL_ASK);

   // Get last 2 completed M15 candles
   MqlRates r15[];
   ArraySetAsSeries(r15, true);
   if(CopyRates(_Symbol, PERIOD_CURRENT, 0, 4, r15) < 4) return;

   // ═══ SHORT ═══
   if(g_lastLossDir != -1) {
      bool inSupply = g_sup.ok && ask >= g_sup.lo && ask <= g_sup.hi;
      bool bearCandle = r15[1].close < r15[1].open;   // Last completed bearish
      bool bearCandle2 = r15[2].close < r15[2].open;  // Second-last bearish (momentum)
      if(inSupply && bearCandle && bearCandle2) {
         double sl = g_sup.hi + atrV * SL_ATR_Mult;
         double risk = MathAbs(sl - ask);
         if(risk <= 0) return;
         double tp = ask - risk * MinRR;
         if(trade.Sell(BaseLot, _Symbol, bid, NormalizeDouble(sl,_Digits), NormalizeDouble(tp,_Digits))) {
            g_sup.ok = false; g_lastLossDir = 0;
            Print("SELL " + DoubleToString(BaseLot,2) + " @ " + DoubleToString(bid,0) +
                  " SL:" + DoubleToString(sl,0) + " TP:" + DoubleToString(tp,0));
         }
         return;
      }
   }

   // ═══ LONG ═══
   if(g_lastLossDir != 1) {
      bool inDemand = g_dem.ok && bid >= g_dem.lo && bid <= g_dem.hi;
      bool bullCandle = r15[1].close > r15[1].open;
      bool bullCandle2 = r15[2].close > r15[2].open;
      if(inDemand && bullCandle && bullCandle2) {
         double sl = g_dem.lo - atrV * SL_ATR_Mult;
         double risk = MathAbs(bid - sl);
         if(risk <= 0) return;
         double tp = bid + risk * MinRR;
         if(trade.Buy(BaseLot, _Symbol, ask, NormalizeDouble(sl,_Digits), NormalizeDouble(tp,_Digits))) {
            g_dem.ok = false; g_lastLossDir = 0;
            Print("BUY " + DoubleToString(BaseLot,2) + " @ " + DoubleToString(bid,0) +
                  " SL:" + DoubleToString(sl,0) + " TP:" + DoubleToString(tp,0));
         }
         return;
      }
   }
}

void ScanZones() {
   MqlRates h4[]; ArraySetAsSeries(h4, true);
   if(CopyRates(_Symbol, PERIOD_H4, 0, 3, h4) < 2) return;
   if(h4[1].time == g_zoneBar) return;
   g_zoneBar = h4[1].time;

   double body = MathAbs(h4[1].close - h4[1].open);
   double rg = h4[1].high - h4[1].low;
   if(rg <= 0) return;
   if(body / rg * 100 < ZoneBodyMinPct) return;

   double mid = (h4[1].high + h4[1].low) / 2;
   double half = rg * 0.3;  // 60% zone width
   if(h4[1].close > h4[1].open) {
      g_dem.lo = mid - half; g_dem.hi = mid + half;
      g_dem.ok = true; g_dem.ct = TimeCurrent();
   } else {
      g_sup.lo = mid - half; g_sup.hi = mid + half;
      g_sup.ok = true; g_sup.ct = TimeCurrent();
   }
   int sec = ZoneExpiryHours * 3600;
   if(g_dem.ok && TimeCurrent()-g_dem.ct > sec) g_dem.ok = false;
   if(g_sup.ok && TimeCurrent()-g_sup.ct > sec) g_sup.ok = false;
}

void Trail() {
   for(int i=PositionsTotal()-1; i>=0; i--) {
      ulong t = PositionGetTicket(i);
      if(!PositionSelectByTicket(t)||PositionGetString(POSITION_SYMBOL)!=_Symbol||PositionGetInteger(POSITION_MAGIC)!=MagicNumber) continue;
      double en=PositionGetDouble(POSITION_PRICE_OPEN),sl=PositionGetDouble(POSITION_SL),tp=PositionGetDouble(POSITION_TP);
      long ty=PositionGetInteger(POSITION_TYPE);
      double prc=(ty==POSITION_TYPE_BUY)?SymbolInfoDouble(_Symbol,SYMBOL_BID):SymbolInfoDouble(_Symbol,SYMBOL_ASK);
      double pct=MathAbs(prc-en)/en*100;
      if(pct<TrailActivatePct) continue;
      double ds=prc*(TrailDistPct/100);
      double ns=(ty==POSITION_TYPE_BUY)?prc-ds:prc+ds;
      if((ty==POSITION_TYPE_BUY&&(ns>sl||sl==0))||(ty==POSITION_TYPE_SELL&&(ns<sl||sl==0)))
         trade.PositionModify(t,NormalizeDouble(ns,_Digits),tp);
   }
}

void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &req, const MqlTradeResult &res) {
   if(trans.type!=TRADE_TRANSACTION_DEAL_ADD) return;
   ulong ticket=trans.deal;
   if(HistoryDealGetInteger(ticket,DEAL_MAGIC)!=(long)MagicNumber) return;
   if(HistoryDealGetInteger(ticket,DEAL_ENTRY)!=DEAL_ENTRY_OUT) return;
   double profit=HistoryDealGetDouble(ticket,DEAL_PROFIT)+HistoryDealGetDouble(ticket,DEAL_COMMISSION)+HistoryDealGetDouble(ticket,DEAL_SWAP);
   g_tc++;
   if(profit>=0) { g_consecLoss=0; g_lastLossDir=0; g_lockUntil=0; }
   else {
      g_consecLoss++;
      long dt=HistoryDealGetInteger(ticket,DEAL_TYPE);
      if(dt==DEAL_TYPE_SELL) g_lastLossDir=1;
      else g_lastLossDir=-1;
      if(g_consecLoss>=MaxConsecLosses) g_lockUntil=TimeCurrent()+7200; // 2 hour lock
   }
}

void CloseAll() {
   for(int i=PositionsTotal()-1; i>=0; i--) {
      ulong t=PositionGetTicket(i);
      if(PositionSelectByTicket(t)&&PositionGetInteger(POSITION_MAGIC)==MagicNumber)
         trade.PositionClose(t);
   }
}
