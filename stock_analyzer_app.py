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
# ☘️ Sidebar Inputs
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

if "show_indicator_settings" not in st.session_state:
    st.session_state.show_indicator_settings = False
if "show_indicator_chart" not in st.session_state:
    st.session_state.show_indicator_chart = False

if st.sidebar.button("📜 Customized Options"):
    st.session_state.show_indicator_settings = not st.session_state.show_indicator_settings

if st.sidebar.button("📊 Technical Chart"):
    st.session_state.show_indicator_chart = not st.session_state.show_indicator_chart

if st.session_state.show_indicator_chart:
    indicator_choice = st.sidebar.radio(
        "📊 Technical Indicator",
        options=["RSI", "MACD"],
        index=0
    )
else:
    indicator_choice = "None"

if st.session_state.show_indicator_settings:
    st.sidebar.markdown("### 🎛️ Customize Indicators")
    rsi_period = int(st.sidebar.number_input("RSI Period", min_value=2, max_value=50, value=14))
    macd_fast = int(st.sidebar.number_input("MACD Fast Period", min_value=2, max_value=50, value=12))
    macd_slow = int(st.sidebar.number_input("MACD Slow Period", min_value=13, max_value=100, value=26))
    macd_signal = int(st.sidebar.number_input("MACD Signal Period", min_value=1, max_value=30, value=9))
else:
    rsi_period = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9

if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

if st.sidebar.button("💬 Show/Hide Chatbot"):
    st.session_state.show_chat = not st.session_state.show_chat

# ==============================================
# 🚓 State Management
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

    bb_bbh = pd.Series(bb.bollinger_hband().squeeze(), index=close_series.index)
    bb_bbl = pd.Series(bb.bollinger_lband().squeeze(), index=close_series.index)

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

    close_series = df['Close'].squeeze()
    bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    df['bb_mavg'] = bb.bollinger_mavg().squeeze()
    df['bb_high'] = bb.bollinger_hband().squeeze()
    df['bb_low'] = bb.bollinger_lband().squeeze()
    df['RSI'] = ta.momentum.RSIIndicator(close=close_series, window=rsi_period).rsi().squeeze()
    macd = ta.trend.MACD(close=close_series, window_slow=macd_slow, window_fast=macd_fast, window_sign=macd_signal)
    df['MACD'] = macd.macd().squeeze()
    df['MACD_signal'] = macd.macd_signal().squeeze()

    st.subheader(f"📈 {selected_stock} - Price Chart with Bollinger Bands")
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(df.index, df['Close'], label='Close Price')
    ax1.plot(df.index, df['bb_mavg'], label='Middle Band', linestyle='--')
    ax1.plot(df.index, df['bb_high'], label='Upper Band', linestyle='--')
    ax1.plot(df.index, df['bb_low'], label='Lower Band', linestyle='--')
    ax1.set_ylabel("Price")
    ax1.legend()
    st.pyplot(fig)

    if indicator_choice == "RSI":
        st.subheader("📉 RSI Indicator")
        fig2, ax2 = plt.subplots(figsize=(12, 4))
        ax2.plot(df.index, df['RSI'], label=f'RSI ({rsi_period})', color='green')
        ax2.axhline(70, linestyle='--', color='red')
        ax2.axhline(30, linestyle='--', color='blue')
        ax2.legend()
        st.pyplot(fig2)

    elif indicator_choice == "MACD":
        st.subheader("📉 MACD Indicator")
        fig3, ax3 = plt.subplots(figsize=(12, 4))
        ax3.plot(df.index, df['MACD'], label='MACD', color='purple')
        ax3.plot(df.index, df['MACD_signal'], label='Signal Line', color='orange')
        ax3.axhline(0, linestyle='--', color='gray')
        ax3.legend()
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

# ==============================================
# 🤖 Chatbot: Ask Shweta
# ==============================================

if st.session_state.show_chat:
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Ask Shweta")

    HF_API_URL = "https://api-inference.huggingface.co/models/bigscience/bloom-560m"
    hf_token = st.secrets.get("huggingface", {}).get("api_key") or os.getenv("HF_API_KEY")
    hf_headers = {"Authorization": f"Bearer {hf_token}"}

    with st.sidebar.form("chat_form"):
        user_input_chat = st.text_input("Your question", key="chat_input")
        submit_chat = st.form_submit_button("Send")

    if submit_chat and user_input_chat:
        if not hf_token:
            st.sidebar.warning("⚠️ Hugging Face API token is missing or invalid.")
        else:
            try:
                response = requests.post(
                    HF_API_URL,
                    headers=hf_headers,
                    json={"inputs": user_input_chat},
                    timeout=30
                )
                response.raise_for_status()
                output = response.json()[0]['generated_text'] if isinstance(response.json(), list) else response.json()['generated_text']
            except Exception as e:
                output = f"❌ Hugging Face API error: {str(e)}"

            st.sidebar.markdown(f"**🤖 Avyan:** {output}")
