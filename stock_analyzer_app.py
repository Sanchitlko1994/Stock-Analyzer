# Import required libraries
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import mplfinance as mpf
import ta
import requests
import os
from datetime import datetime

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer Web App", layout="wide")
st.title("📊 Stock Analyzer Web App")

# -------------------------------
# Helper Functions
# -------------------------------
@st.cache_data
def fetch_nse_index_stocks(index_name):
    url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_name}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    session = requests.Session()
    session.headers.update(headers)
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data['data'])
        return df['symbol'].tolist()
    except Exception as e:
        st.error(f"❌ Failed to load index data: {e}")
        return []

@st.cache_data
def download_data(ticker, start, end):
    df = yf.download(ticker + ".NS", start=start, end=end)
    if not df.empty:
        df.dropna(inplace=True)
    return df

def detect_breakout(df):
    if df.empty or len(df) < 20:
        return False
    indicator_bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['bb_bbm'] = indicator_bb.bollinger_mavg()
    df['bb_bbh'] = indicator_bb.bollinger_hband()
    df['bb_bbl'] = indicator_bb.bollinger_lband()
    df['bb_width'] = df['bb_bbh'] - df['bb_bbl']
    narrow_band = df['bb_width'].iloc[-1] < df['bb_width'].quantile(0.25)
    breakout = df['Close'].iloc[-1] > df['bb_bbh'].iloc[-1]
    return narrow_band and breakout

# -------------------------------
# Sidebar: User Inputs
# -------------------------------
st.sidebar.subheader("📌 Stock Data Analysis")
index_options = [
    "NIFTY 50", "NIFTY 100", "NIFTY 500",
    "NIFTY AUTO", "NIFTY FINANCIAL SERVICES"
]
selected_index = st.sidebar.selectbox("Select NSE Index", index_options)
start_date = st.sidebar.date_input("Start Date", datetime(2023, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.today())

# Format NSE Index URL format
index_url_map = {
    "NIFTY 50": "NIFTY%2050",
    "NIFTY 100": "NIFTY%20100",
    "NIFTY 500": "NIFTY%20500",
    "NIFTY AUTO": "NIFTY%20AUTO",
    "NIFTY FINANCIAL SERVICES": "NIFTY%20FINANCIAL%20SERVICES"
}

# -------------------------------
# Process and Detect Breakouts
# -------------------------------
st.sidebar.write("---")
stocks = fetch_nse_index_stocks(index_url_map[selected_index])
breakout_stocks = []

progress = st.sidebar.progress(0)
for i, symbol in enumerate(stocks):
    df = download_data(symbol, start_date, end_date)
    if detect_breakout(df):
        breakout_stocks.append(symbol)
    progress.progress((i+1)/len(stocks))

# -------------------------------
# Main Panel: Breakout Stock List
# -------------------------------
st.subheader("🚀 Stocks with Narrow Bollinger Band and Upper Breakout")
if breakout_stocks:
    selected_stock = st.selectbox("Select Stock to Analyze", breakout_stocks)
    df_selected = download_data(selected_stock, start_date, end_date)

    # Recalculate Bollinger Bands & RSI
    bb = ta.volatility.BollingerBands(close=df_selected['Close'], window=20)
    df_selected['bb_bbm'] = bb.bollinger_mavg()
    df_selected['bb_bbh'] = bb.bollinger_hband()
    df_selected['bb_bbl'] = bb.bollinger_lband()
    df_selected['RSI'] = ta.momentum.RSIIndicator(close=df_selected['Close'], window=14).rsi()

    # -------------------------------
    # Plot Bollinger Bands + Candlestick
    # -------------------------------
    st.subheader("📉 Bollinger Band with Candlestick")
    mpf.plot(df_selected, type='candle', style='yahoo', volume=False,
             addplot=[
                 mpf.make_addplot(df_selected['bb_bbh'], color='green'),
                 mpf.make_addplot(df_selected['bb_bbl'], color='red'),
                 mpf.make_addplot(df_selected['bb_bbm'], color='blue')
             ],
             figsize=(12, 6), title=selected_stock)

    # -------------------------------
    # Plot RSI
    # -------------------------------
    st.subheader("📊 RSI Chart")
    fig_rsi, ax_rsi = plt.subplots(figsize=(12, 3))
    ax_rsi.plot(df_selected.index, df_selected['RSI'], label='RSI', color='purple')
    ax_rsi.axhline(70, linestyle='--', color='red', label='Overbought')
    ax_rsi.axhline(30, linestyle='--', color='blue', label='Oversold')
    ax_rsi.set_title("RSI (14)")
    ax_rsi.legend()
    st.pyplot(fig_rsi)

    # -------------------------------
    # Show Last 10 Rows
    # -------------------------------
    st.subheader("📄 Recent Data Sample")
    st.dataframe(df_selected.tail(10))

    # -------------------------------
    # Download Button
    # -------------------------------
    st.download_button(
        label="⬇️ Download CSV",
        data=df_selected.to_csv().encode(),
        file_name=f"{selected_stock}_analysis.csv",
        mime='text/csv'
    )
else:
    st.warning("No breakout stocks found for the selected index and date range.")

# -------------------------------
# Sidebar Chatbot: Hugging Face
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Ask Shweta")
HF_API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
hf_token = st.secrets.get("huggingface", {}).get("api_key") or os.getenv("HF_API_KEY")
hf_headers = {"Authorization": f"Bearer {hf_token}"}
user_input_chat = st.sidebar.text_input("Your question")
if user_input_chat:
    prompt = user_input_chat
    try:
        response = requests.post(
            HF_API_URL,
            headers=hf_headers,
            json={"inputs": prompt},
            timeout=30
        )
        response.raise_for_status()
        output = response.json()[0]['generated_text'].split('<|assistant|>')[-1].strip()
    except Exception as e:
        output = f"❌ Hugging Face API error: {str(e)}"

    st.sidebar.markdown(f"**🤖 Avyan:** {output}")
