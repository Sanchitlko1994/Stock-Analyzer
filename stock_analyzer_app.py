# ==============================================
# 📦 Import Required Libraries
# ==============================================

import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime
import time
import base64

# ==============================================
# ⚙️ Page Configuration
# ==============================================

st.set_page_config(
    page_title="Stock Analyzer Web App",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Report a bug': "mailto:Sanchitbkt@gmail.com",
        'About': (
            "📈 This app provides advanced stock analysis for NSE indices. "
            "Built in 2025 by Sanchit and Shweta Singh. Use it to identify Bollinger Band breakouts."
        )
    }
)

# ==============================================
# 🌈 Custom Styling
# ==============================================

st.markdown("""
    <style>
    .element-container:nth-child(n+4) div[data-testid="stVerticalBlock"] {
        animation: fadeIn 0.6s ease-in-out;
    }
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    </style>
""", unsafe_allow_html=True)

# ==============================================
# 📜 Title
# ==============================================

st.markdown(
    """
    <h1 style='text-align: center; margin-top: 10px; font-size: 3rem;'>📊 Stock Analyzer Web App</h1>
    """,
    unsafe_allow_html=True
)

# ==============================================
# 📂 Load Stock List
# ==============================================

@st.cache_data
def get_nse_index_stocks(index_name="NIFTY 50"):
    csv_url = "https://raw.githubusercontent.com/Sanchitlko1994/Stock-Analyzer/main/NSE%20INDEX%20STOCKS.csv"
    df = pd.read_csv(csv_url)
    return df[df["index"] == index_name]["stock"].tolist()

# ==============================================
# 🗘️ Sidebar Inputs
# ==============================================

index_options = [
    "NIFTY 50", "NIFTY 100", "NIFTY 500", "NIFTY AUTO", "NIFTY BANK",
    "NIFTY FINANCIAL SERVICES", "NIFTY HEALTHCARE", "NIFTY PHARMA",
    "NIFTY IT", "NIFTY OIL & GAS"
]
selected_index = st.sidebar.selectbox("Select NSE Index", index_options)
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

analyze_button = st.sidebar.button("🔍 Analyze")
clear_button = st.sidebar.button("🗾 Clear Analysis")

indicator_choice = st.sidebar.radio(
    "📊 Select Technical Indicator",
    options=["None", "RSI", "MACD"],
    index=0
)

st.sidebar.markdown("### 🎛️ Customize Indicators")
rsi_period = int(st.sidebar.number_input("RSI Period", min_value=2, max_value=50, value=14))
macd_fast = int(st.sidebar.number_input("MACD Fast Period", min_value=2, max_value=50, value=12))
macd_slow = int(st.sidebar.number_input("MACD Slow Period", min_value=macd_fast + 1, max_value=100, value=26))
macd_signal = int(st.sidebar.number_input("MACD Signal Period", min_value=1, max_value=30, value=9))

if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

if st.sidebar.button("💬 Show/Hide Chatbot"):
    st.session_state.show_chat = not st.session_state.show_chat

# ==============================================
# 🧳 State Management
# ==============================================

if clear_button:
    st.session_state.clear()
    st.rerun()

if analyze_button:
    st.session_state["start_analysis"] = True
    st.session_state["selected_stock"] = None

# ==============================================
# 📈 Bollinger Breakout Detection
# ==============================================

def detect_bollinger_breakout(df):
    if len(df) < 21:
        return False
    close_series = df['Close'].squeeze()
    bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    bb_bbh = bb.bollinger_hband()
    bb_bbl = bb.bollinger_lband()
    bb_width = bb_bbh - bb_bbl
    df['bb_width'] = bb_width
    narrow = bb_width < bb_width.quantile(0.2)
    breakout = close_series > bb_bbh
    return narrow.iloc[-1] and breakout.iloc[-1]

# ==============================================
# 🗅️ Get Stock Data
# ==============================================

@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df.dropna(inplace=True)
    return df

# ==============================================
# 🚀 Main Analysis Logic
# ==============================================

if st.session_state.get("start_analysis"):
    start_timer = time.time()
    with st.spinner("Analyzing breakout stocks. Please wait..."):
        breakout_stocks = []
        stocks = []
        try:
            stocks = get_nse_index_stocks(selected_index)
            progress_bar = st.progress(0, text="Scanning stocks...")
            for i, stock in enumerate(stocks):
                df = get_data(stock, start_date, end_date)
                if not df.empty and detect_bollinger_breakout(df):
                    breakout_stocks.append(stock)
                progress_bar.progress((i + 1) / len(stocks), text=f"Analyzing {stock} ({i + 1}/{len(stocks)})")
            progress_bar.empty()
        except Exception as e:
            st.error(f"❌ Failed to load index data: {str(e)}")

        if not stocks:
            st.error("❌ No stocks found for selected index.")
        elif not breakout_stocks:
            st.warning("⚠️ No breakout stocks found for the selected period.")
        else:
            st.session_state["breakout_stocks"] = breakout_stocks
            st.success(f"✅ {len(breakout_stocks)} breakout stocks found.")

# ==============================================
# 📊 Visualization Section
# ==============================================

breakout_stocks = st.session_state.get("breakout_stocks", [])
if breakout_stocks:
    selected_stock = st.sidebar.selectbox(
        "Select Stock for Analysis",
        breakout_stocks,
        index=breakout_stocks.index(
            st.session_state.get("selected_stock", breakout_stocks[0])
        ) if st.session_state.get("selected_stock") in breakout_stocks else 0
    )
    st.session_state["selected_stock"] = selected_stock

    df = get_data(selected_stock, start_date, end_date)
    df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
    df['Volume'].fillna(0, inplace=True)

    close_series = df['Close'].squeeze()
    bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    df['bb_mavg'] = bb.bollinger_mavg()
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['RSI'] = ta.momentum.RSIIndicator(close=close_series, window=rsi_period).rsi()
    macd = ta.trend.MACD(close=close_series, window_slow=macd_slow, window_fast=macd_fast, window_sign=macd_signal)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()

    st.subheader(f"📈 {selected_stock} - Price Chart with Bollinger Bands & Volume")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax1.plot(df.index, df['Close'], label='Close Price')
    ax1.plot(df.index, df['bb_mavg'], label='Middle Band', linestyle='--')
    ax1.plot(df.index, df['bb_high'], label='Upper Band', linestyle='--')
    ax1.plot(df.index, df['bb_low'], label='Lower Band', linestyle='--')
    ax1.set_ylabel("Price")
    ax1.legend()
    ax2.bar(df.index, df['Volume'], color='lightblue')
    ax2.set_ylabel("Volume")
    st.pyplot(fig)

    if indicator_choice == "RSI":
        st.subheader("📉 RSI Indicator with Volume")
        fig2, (ax2a, ax2b) = plt.subplots(2, 1, figsize=(12, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
        ax2a.plot(df.index, df['RSI'], label=f'RSI ({rsi_period})', color='green')
        ax2a.axhline(70, linestyle='--', color='red')
        ax2a.axhline(30, linestyle='--', color='blue')
        ax2a.legend()
        ax2b.bar(df.index, df['Volume'], color='gray')
        ax2b.set_ylabel("Volume")
        st.pyplot(fig2)

    elif indicator_choice == "MACD":
        st.subheader("📉 MACD Indicator with Volume")
        fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(12, 6), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
        ax3a.plot(df.index, df['MACD'], label='MACD', color='purple')
        ax3a.plot(df.index, df['MACD_signal'], label='Signal Line', color='orange')
        ax3a.axhline(0, linestyle='--', color='gray')
        ax3a.legend()
        ax3b.bar(df.index, df['Volume'], color='gray')
        ax3b.set_ylabel("Volume")
        st.pyplot(fig3)

    st.download_button(
        label="⬇️ Download CSV",
        data=df.to_csv().encode(),
        file_name=f"{selected_stock}_data.csv",
        mime='text/csv'
    )

    audio_file = "https://www.soundjay.com/buttons/sounds/button-29.mp3"
    b64_audio = base64.b64encode(requests.get(audio_file).content).decode()
    audio_html = f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
    elapsed = time.time() - start_timer
    st.info(f"✅ Analysis completed in {elapsed:.2f} seconds.")
