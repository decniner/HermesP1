"""
analysis.py — BrutalMarketEngine Data Layer

Raw data fetching, indicator calculation, and AI-prompt formatting.
No UI, no API keys. Pure technical math with `ta` library.
"""

import pandas as pd
import yfinance as yf
from typing import Optional

from ta.trend import EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange, BollingerBands


# ---------------------------------------------------------------------------
# 1. Data fetching
# ---------------------------------------------------------------------------

def normalize_symbol(raw: str) -> str:
    """
    Normalise a user-supplied symbol into a yfinance-recognised ticker.

    Rules:
      - ':' or '/'  →  '-'   (e.g. TYO:8604 → 8604.T,  BTC/JPY → BTC-JPY)
      - If parts[0] is all digits (JP stock code) append exchange suffix.
      - Pure alpha pairs (BTC/JPY, ETH/USDT) → BTC-JPY (yahoo crypto format).
    """
    s = raw.strip().upper()

    for sep in (":", "/"):
        if sep in s:
            parts = [p.strip() for p in s.split(sep, maxsplit=1)]
            # Stock code like 8604:T → 8604.T
            if parts[0].isdigit():
                return f"{parts[0]}.{parts[1]}"
            # Crypto pair like BTC/JPY → BTC-JPY
            return f"{parts[0]}-{parts[1]}"

    return s


def fetch_data(
    symbol: str,
    period: str = "1mo",
    interval: str = "4h",
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data from Yahoo Finance.

    Returns
    -------
    DataFrame with columns [open, high, low, close, volume] + datetime index,
    or None if the ticker is unreachable.
    """
    ticker = normalize_symbol(symbol)
    try:
        data = yf.download(
            tickers=ticker,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
        )
    except Exception as e:
        print(f"[error] yfinance failed for {symbol} ({ticker}): {e}")
        return None

    if data is None or data.empty:
        return None

    # Flatten MultiIndex columns that yfinance sometimes returns
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Ensure column names are lowercase
    data.columns = [str(c).lower() for c in data.columns]

    needed = {"open", "high", "low", "close", "volume"}
    have = set(data.columns)
    if not needed.issubset(have):
        missing = needed - have
        print(f"[warn] {symbol}: missing columns {missing}")
        return None

    return data


def fetch_multiple(symbols: list[str], **kwargs) -> dict[str, Optional[pd.DataFrame]]:
    """Fetch several symbols at once.  Returns {label: DataFrame}."""
    return {s: fetch_data(s, **kwargs) for s in symbols}


# ---------------------------------------------------------------------------
# 2. Indicator calculation  (using `ta` library)
# ---------------------------------------------------------------------------

def _sma(series: pd.Series, length: int) -> pd.Series:
    return SMAIndicator(series, window=length).sma_indicator()


def _ema(series: pd.Series, length: int) -> pd.Series:
    return EMAIndicator(series, window=length).ema_indicator()


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical-indicator columns to the DataFrame (in-place + return).

    Core set mandated by the blueprint:
      - Trend   : EMA(9, 21, 50), SMA(20, 50)
      - Momentum: RSI(14), MACD (12, 26, 9)
      - Volatility: ATR(14), Bollinger Bands (20, 2)
      - Volume  : SMA(20) on volume
    """
    if df is None or df.empty:
        return df

    close = df["close"]
    high = df["high"]
    low = df["low"]

    # --- Trend ---
    df["ema_9"] = _ema(close, 9)
    df["ema_21"] = _ema(close, 21)
    df["ema_50"] = _ema(close, 50)
    df["sma_20"] = _sma(close, 20)
    df["sma_50"] = _sma(close, 50)

    # --- Momentum ---
    df["rsi_14"] = RSIIndicator(close, window=14).rsi()

    macd = MACD(close, window_slow=26, window_fast=12, window_sign=9)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()

    # --- Volatility ---
    df["atr_14"] = AverageTrueRange(high, low, close, window=14).average_true_range()

    bb = BollingerBands(close, window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_mid"] = bb.bollinger_mavg()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_width"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_mid"]

    # --- Volume ---
    df["volume_sma_20"] = _sma(df["volume"], 20)

    return df


# ---------------------------------------------------------------------------
# 3. Text summary for the AI prompt
# ---------------------------------------------------------------------------

def format_indicator_summary(df: pd.DataFrame) -> str:
    """
    Produce a concise, number-heavy text block of the current indicator state.

    This is what gets piped into the DeepSeek system prompt so the AI can
    produce the "brutal market reality check" without seeing raw JSON.
    """
    if df is None or df.empty:
        return "[NO DATA]"

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last

    symbol = df.attrs.get("symbol", "?")
    lines = []
    lines.append(f"Symbol (last candle): {symbol}")
    lines.append(f"Timestamp: {df.index[-1]}")
    lines.append(f"Close: {last['close']:.4f}  |  Prev: {prev['close']:.4f}")
    lines.append(f"Change: {(last['close'] - prev['close']):.4f}  "
                 f"({((last['close']/prev['close'] - 1)*100):.2f}%)")
    lines.append(f"High: {last['high']:.4f}  Low: {last['low']:.4f}  "
                 f"Volume: {last['volume']:.0f}")
    lines.append("")

    # Trend
    lines.append("── TREND ──")
    for ma in ("ema_9", "ema_21", "ema_50", "sma_20", "sma_50"):
        if ma in last and pd.notna(last[ma]):
            dist = ((last["close"] / last[ma]) - 1) * 100
            lines.append(f"  {ma.upper():<10} {last[ma]:>10.4f}  "
                         f"(price is {dist:+.2f}% relative)")
    lines.append("")

    # Momentum
    lines.append("── MOMENTUM ──")
    if "rsi_14" in last and pd.notna(last["rsi_14"]):
        rsi = float(last["rsi_14"])
        label = "OVERBOUGHT" if rsi > 70 else "OVERSOLD" if rsi < 30 else "neutral"
        lines.append(f"  RSI(14):       {rsi:>8.2f}  → {label}")
    if "macd" in last and pd.notna(last["macd"]):
        macd_val = last["macd"]
        sig = last.get("macd_signal", 0)
        hist = last.get("macd_hist", 0)
        cross = "BULLISH CROSS" if macd_val > sig else "BEARISH CROSS"
        lines.append(f"  MACD:          {macd_val:>8.4f}")
        lines.append(f"  SIGNAL:        {sig:>8.4f}")
        lines.append(f"  HISTOGRAM:     {hist:>8.4f}  → {cross}")
    lines.append("")

    # Volatility
    lines.append("── VOLATILITY ──")
    if "atr_14" in last and pd.notna(last["atr_14"]):
        atr_pct = (float(last["atr_14"]) / float(last["close"])) * 100
        lines.append(f"  ATR(14):       {float(last['atr_14']):.4f}  ({atr_pct:.2f}% of price)")
    if "bb_upper" in last and pd.notna(last["bb_upper"]):
        bb_range = float(last["bb_upper"]) - float(last["bb_lower"])
        price = float(last["close"])
        if price > float(last["bb_upper"]):
            pos = "ABOVE upper band"
        elif price < float(last["bb_lower"]):
            pos = "BELOW lower band"
        else:
            pos = "inside bands"
        lines.append(f"  BOLLINGER:     Upper {float(last['bb_upper']):.4f}  "
                     f"Mid {float(last['bb_mid']):.4f}  "
                     f"Lower {float(last['bb_lower']):.4f}")
        lines.append(f"  BAND WIDTH:    {bb_range:.4f}  → price is {pos}")
    lines.append("")

    # Volume
    lines.append("── VOLUME ──")
    if "volume_sma_20" in last and pd.notna(last["volume_sma_20"]):
        vol_ratio = float(last["volume"]) / float(last["volume_sma_20"])
        avg_label = "ABOVE" if vol_ratio > 1.1 else "BELOW" if vol_ratio < 0.9 else "AT"
        lines.append(f"  VOL / SMA(20): {vol_ratio:.2f}x  → {avg_label} average")
    lines.append("")

    # Last 3 candles as a mini table
    lines.append("── LAST 3 CANDLES ──")
    lines.append(f"{'TIME':<20} {'OPEN':>10} {'HIGH':>10} {'LOW':>10} "
                 f"{'CLOSE':>10} {'VOL':>10}")
    for i in range(max(0, len(df) - 3), len(df)):
        r = df.iloc[i]
        t = str(df.index[i])[:19]
        lines.append(f"{t:<20} {float(r['open']):>10.4f} {float(r['high']):>10.4f} "
                     f"{float(r['low']):>10.4f} {float(r['close']):>10.4f} "
                     f"{float(r['volume']):>10.0f}")

    return "\n".join(lines)
