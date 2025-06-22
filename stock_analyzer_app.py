import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import requests
import os
import time
import base64

# Page Configuration
st.set_page_config(page_title="📈 NSE Stock Analyzer", layout="wide")

# Custom CSS
st.markdown("""
<style>
section.main > div {padding-top: 1.5rem;}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 style='text-align: center;'>📊 NSE Stock Analyzer Web App</h1>", unsafe_allow_html=True)

# Sidebar: Index and Date Selection
with st.sidebar:
    st.header("🔍 Filter Options")
    index_options = [
        "NIFTY 50", "NIFTY 100", "NIFTY 500", "NIFTY AUTO", "NIFTY BANK",
        "NIFTY FINANCIAL SERVICES", "NIFTY HEALTHCARE", "NIFTY PHARMA",
        "NIFTY IT", "NIFTY OIL & GAS"
    ]
    selected_index = st.selectbox("Index", index_options)
    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime("today"))

    if "show_chat" not in st.session_state:
        st.session_state.show_chat = False
    if st.button("💬 Toggle Chatbot"):
        st.session_state.show_chat = not st.session_state.show_chat

# Cache stock list
@st.cache_data
def get_nse_index_stocks(index_name="NIFTY 50"):
    url = "https://raw.githubusercontent.com/Sanchitlko1994/Stock-Analyzer/main/NSE%20INDEX%20STOCKS.csv"
    df = pd.read_csv(url)
    return df[df["index"] == index_name]["stock"].tolist()

@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    return df.dropna() if not df.empty else df

def detect_bollinger_breakout(df):
    if len(df) < 21:
        return False
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    bb_width = bb.bollinger_hband() - bb.bollinger_lband()
    narrow = bb_width < bb_width.quantile(0.2)
    breakout = df['Close'] > bb.bollinger_hband()
    return narrow.iloc[-1] and breakout.iloc[-1]

# Main Content
st.divider()
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("⚙️ Run Analysis")
    analyze_button = st.button("🔍 Analyze")
    clear_button = st.button("♻️ Clear")
    
    if "start_analysis" not in st.session_state:
        st.session_state.start_analysis = False
    if "breakout_stocks" not in st.session_state:
        st.session_state.breakout_stocks = []

    if clear_button:
        st.session_state.clear()
        st.rerun()
    if analyze_button:
        st.session_state.start_analysis = True
        st.session_state.selected_stock = None

with col2:
    with st.expander("📃 Customized Options"):
        rsi_period = st.number_input("RSI Period", 2, 50, 14)
        macd_fast = st.number_input("MACD Fast", 2, 50, 12)
        macd_slow = st.number_input("MACD Slow", macd_fast+1, 100, 26)
        macd_signal = st.number_input("MACD Signal", 1, 30, 9)

    with st.expander("📊 Technical Chart"):
        indicator_choice = st.radio("Select Indicator", ["None", "RSI", "MACD"])

# Run Analysis
if st.session_state.start_analysis:
    stocks = get_nse_index_stocks(selected_index)
    breakout_stocks = []
    with st.spinner("🔎 Scanning stocks..."):
        progress = st.progress(0)
        for i, stock in enumerate(stocks):
            df = get_data(stock, start_date, end_date)
            if not df.empty and detect_bollinger_breakout(df):
                breakout_stocks.append(stock)
            progress.progress((i+1)/len(stocks))
        st.session_state.breakout_stocks = breakout_stocks

# Show Breakouts and Visuals
if st.session_state.breakout_stocks:
    st.success(f"✅ Found {len(st.session_state.breakout_stocks)} breakout stocks.")
    selected_stock = st.selectbox("📌 Select a Stock", st.session_state.breakout_stocks)

    df = get_data(selected_stock, start_date, end_date)

    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['bb_mavg'] = bb.bollinger_mavg()
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=rsi_period).rsi()
    macd = ta.trend.MACD(df['Close'], macd_fast, macd_slow, macd_signal)
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()

    st.subheader(f"📈 {selected_stock} Price + Bollinger Bands")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df['Close'], label='Close')
    ax.plot(df.index, df['bb_mavg'], label='Middle Band', linestyle='--')
    ax.plot(df.index, df['bb_high'], label='Upper Band', linestyle='--')
    ax.plot(df.index, df['bb_low'], label='Lower Band', linestyle='--')
    ax.legend()
    st.pyplot(fig)

    if indicator_choice == "RSI":
        st.subheader("📉 RSI Chart")
        fig2, ax2 = plt.subplots(figsize=(12, 3))
        ax2.plot(df.index, df['RSI'], color='green')
        ax2.axhline(70, color='red', linestyle='--')
        ax2.axhline(30, color='blue', linestyle='--')
        st.pyplot(fig2)

    elif indicator_choice == "MACD":
        st.subheader("📉 MACD Chart")
        fig3, ax3 = plt.subplots(figsize=(12, 3))
        ax3.plot(df.index, df['MACD'], label="MACD", color="purple")
        ax3.plot(df.index, df['MACD_signal'], label="Signal", color="orange")
        ax3.axhline(0, color='gray', linestyle='--')
        ax3.legend()
        st.pyplot(fig3)

    st.download_button("⬇️ Download Data", df.to_csv().encode(), file_name=f"{selected_stock}_data.csv")

# Chatbot Section
if st.session_state.show_chat:
    st.markdown("---")
    st.subheader("💬 Ask Shweta")
    user_input = st.text_input("Type your question:")
    if user_input:
        with st.spinner("Thinking..."):
            HF_API_URL = "https://api-inference.huggingface.co/models/bigscience/bloom-560m"
            hf_token = st.secrets.get("huggingface", {}).get("api_key") or os.getenv("HF_API_KEY")
            headers = {"Authorization": f"Bearer {hf_token}"}
            try:
                res = requests.post(HF_API_URL, headers=headers, json={"inputs": user_input}, timeout=30)
                output = res.json()[0]['generated_text']
            except Exception as e:
                output = f"❌ Error: {e}"
            st.markdown(f"**🤖 Shweta:** {output}")
