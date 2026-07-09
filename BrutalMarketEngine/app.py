"""
app.py — BrutalMarketEngine Web UI

Streamlit app that:
  - Lets you pick assets (stocks / crypto)
  - Fetches + calculates indicators live via analysis.py
  - Renders interactive charts
  - Pipes the indicator summary into DeepSeek (OpenAI-compatible API)
  - Auto-refreshes every N seconds

Usage:
    DEEPSEEK_API_KEY=sk-... DEEPSEEK_BASE_URL=https://api.deepseek.com/v1 \
        streamlit run app.py --server.port 8501 --server.address 0.0.0.0
"""

import os
import time
import threading
from typing import Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from analysis import (
    fetch_data,
    calculate_indicators,
    format_indicator_summary,
)

load_dotenv()  # read .env if present

# ---------------------------------------------------------------------------
# Streamlit page config — must be the very first streamlit command
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BrutalMarketEngine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Constants & session state
# ---------------------------------------------------------------------------

DEFAULT_SYMBOLS = ["8604.T", "BTC-JPY", "^N225", "ETH-JPY", "9984.T"]
PERIOD = "1mo"
INTERVAL = "4h"
REFRESH_SECONDS = 10  # how often to auto-poll

if "symbols" not in st.session_state:
    st.session_state.symbols = ["8604.T", "BTC-JPY"]
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()


# ---------------------------------------------------------------------------
# Sidebar — controls
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## ⚙️ Controls")

    asset_type = st.selectbox("Asset class", ["auto", "stocks", "crypto"], index=0)

    # Symbol management
    new_sym = st.text_input(
        "Add symbol",
        placeholder="8604.T or BTC/JPY or ETH-JPY",
        key="new_sym_input",
    )
    if st.button("➕ Add") and new_sym.strip():
        sym = new_sym.strip().upper()
        # Normalise separators for display
        sym_display = sym.replace(":", "/").replace("-", "/") if "/" in sym or ":" in sym else sym
        if sym not in st.session_state.symbols:
            st.session_state.symbols.append(sym)
            st.rerun()

    if st.session_state.symbols:
        st.markdown("**Tracked assets**")
        for s in list(st.session_state.symbols):
            col1, col2 = st.columns([4, 1])
            col1.write(s)
            if col2.button("✕", key=f"rm_{s}"):
                st.session_state.symbols.remove(s)
                st.rerun()

    st.divider()
    st.markdown(f"🔄 Auto-refresh every **{REFRESH_SECONDS}s**")
    if st.button("🔄 Refresh now"):
        st.session_state.last_refresh = time.time()
        st.rerun()

    st.divider()
    st.markdown("### 🤖 AI Analysis")
    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=os.getenv("DEEPSEEK_API_KEY", ""),
        help="Leave blank to use DEEPSEEK_API_KEY from .env",
    )
    base_url = st.text_input(
        "Base URL",
        value=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
    )
    model_name = st.text_input(
        "Model",
        value=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    )

    do_ai = st.button("🔥 Run DeepSeek Analysis", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Data management helpers (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=REFRESH_SECONDS, show_spinner="Fetching market data…")
def load_data(symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
    """Cached data fetch — auto-expires every REFRESH_SECONDS."""
    df = fetch_data(symbol, period=period, interval=interval)
    if df is not None and not df.empty:
        df = calculate_indicators(df)
        df.attrs["symbol"] = symbol
    return df


# ---------------------------------------------------------------------------
# AI analysis (DeepSeek)
# ---------------------------------------------------------------------------

BRUTAL_SYSTEM_PROMPT = """You are a Principal Staff institutional risk manager at a major Tokyo-based hedge fund. You have zero tolerance for hopium, retail-grade analysis, or sugarcoating.

Your ONLY job is to look at the technical data provided and deliver a brutally honest, evidence-based market reality check. You do not predict the future — you assess the CURRENT regime and tell the reader exactly what the data says, no matter how uncomfortable.

RULES — never violate:
1. Every claim MUST cite a specific indicator value from the data provided. No hand-waving.
2. Call out conflicting signals explicitly — the data is not always clean.
3. If the data is inconclusive, SAY SO. Forcing a view is worse than admitting uncertainty.
4. Use direct, confrontational language — "You need to accept that…", "Here is the truth…", "This is not working…"
5. End with exactly ONE actionable tactical statement: a clear entry/exit, a stop-loss level, or "Do nothing — wait for confirmation."
6. Maximum 4 paragraphs. Every word must carry weight. No fluff, no disclaimers, no "in my opinion."
7. Attach a single numeric RISK SCORE from 1 (dead calm) to 10 (full-blown crisis).

Your output is read by a professional trader. Talk to them like a peer who respects them enough to be honest."""  # noqa: E501


def run_deepseek_analysis(api_key: str, base_url: str, model: str, summary: str) -> str:
    """Call DeepSeek (OpenAI-compatible) with the indicator summary."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": BRUTAL_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Here is the current technical state of the market. "
                        "Give me the brutal reality check. No mercy.\n\n"
                        f"{summary}"
                    ),
                },
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[DEEPSEEK ERROR] {e}"


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------

st.title("📊 BrutalMarketEngine")
st.caption(
    f"Self-hosted · {INTERVAL} candles · {PERIOD} · "
    f"auto-refresh every {REFRESH_SECONDS}s"
)

# Trigger rerun on timer (client-side polling via st.empty + sleep loop below)
if time.time() - st.session_state.last_refresh > REFRESH_SECONDS:
    st.session_state.last_refresh = time.time()
    st.cache_data.clear()
    st.rerun()

symbols = st.session_state.symbols
data_frames: dict[str, Optional[pd.DataFrame]] = {}

for sym in symbols:
    df = load_data(sym, PERIOD, INTERVAL)
    data_frames[sym] = df

    with st.container(border=True):
        if df is None or df.empty:
            st.error(f"❌ **{sym}** — No data. Check symbol or network.")
            continue

        col1, col2, col3, col4, col5 = st.columns(5)
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        chg = last["close"] - prev["close"]
        chg_pct = (chg / prev["close"]) * 100
        col1.metric(sym, f"{last['close']:.2f}", f"{chg:+.2f} ({chg_pct:+.2f}%)")
        col2.metric("RSI(14)", f"{last.get('rsi_14', 0):.1f}")
        col3.metric("MACD", f"{last.get('macd', 0):.4f}")
        col4.metric("ATR(14)", f"{last.get('atr_14', 0):.4f}")
        col5.metric("Volume", f"{last['volume']:.0f}")

        # --- Price chart ---
        chart_tab, indicator_tab, raw_tab = st.tabs(
            ["📈 Price + EMA", "📉 Indicators", "📄 Raw Summary"]
        )

        with chart_tab:
            chart_data = df[["close"]].copy()
            for ma in ("ema_9", "ema_21", "ema_50"):
                if ma in df.columns:
                    chart_data[ma] = df[ma]
            st.line_chart(chart_data, height=320)

        with indicator_tab:
            col_a, col_b = st.columns(2)
            with col_a:
                if "rsi_14" in df.columns:
                    st.subheader("RSI(14)")
                    st.line_chart(df[["rsi_14"]], height=180)
            with col_b:
                if "macd" in df.columns and "macd_signal" in df.columns:
                    st.subheader("MACD")
                    st.line_chart(
                        df[["macd", "macd_signal"]], height=180
                    )
            if "bb_upper" in df.columns:
                st.subheader("Bollinger Bands")
                bb_df = df[["close", "bb_upper", "bb_mid", "bb_lower"]].dropna()
                st.line_chart(bb_df, height=240)

        with raw_tab:
            st.code(format_indicator_summary(df), language="text")

# ---------------------------------------------------------------------------
# AI analysis section (below all charts)
# ---------------------------------------------------------------------------

if do_ai:
    st.divider()
    st.header("🔥 AI Market Reality Check")

    if not api_key:
        st.error(
            "No API key. Set DEEPSEEK_API_KEY in .env or paste it in the sidebar."
        )
    else:
        # Collect summaries for ALL tracked assets
        combined_parts = []
        for sym in symbols:
            df = data_frames.get(sym)
            if df is not None and not df.empty:
                combined_parts.append(
                    format_indicator_summary(df)
                )
        combined_summary = "\n\n==========\n\n".join(combined_parts)

        with st.spinner("Running DeepSeek analysis… this takes a few seconds."):
            result = run_deepseek_analysis(
                api_key, base_url, model_name, combined_summary
            )

        st.markdown("### 🎯 Brutal Assessment")
        st.markdown(result)

        with st.expander("📦 Data sent to DeepSeek"):
            st.code(combined_summary, language="text")

# ---------------------------------------------------------------------------
# Auto-refresh loop — stays open so the page polls
# ---------------------------------------------------------------------------

if not do_ai:
    # This empty placeholder forces Streamlit to re-execute the script.
    # The cache TTL + the time-check rerun above drive the live refresh.
    time.sleep(0.1)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.divider()
st.caption(
    "BrutalMarketEngine · "
    "Data from Yahoo Finance · "
    "Indicators via pandas-ta · "
    f"Last refresh: {time.strftime('%H:%M:%S')}"
)
