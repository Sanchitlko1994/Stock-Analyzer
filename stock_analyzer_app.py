# Import required libraries
import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime
import json

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Stock Analyzer Web App")

# -------------------------------
# NSE Index Selection
# -------------------------------
st.sidebar.subheader("📌 Select NIFTY Index")
index_options = [
    "NIFTY 50",
    "NIFTY BANK",
    "NIFTY AUTO",
    "NIFTY FINANCIAL SERVICES",
    "NIFTY 100",
    "NIFTY 200",
    "NIFTY 500"
]
selected_index = st.sidebar.selectbox("Choose an index:", index_options)

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# -------------------------------
# Fetch Stocks in Selected Index
# -------------------------------
@st.cache_data
def get_index_stocks(index_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9"
    }
    url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_name.upper().replace(' ', '%20')}"
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers=headers)
        response = session.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        stocks = [item['symbol'] for item in data['data'] if 'symbol' in item]
        return stocks
    except Exception as e:
        st.error(f"❌ Failed to load index data: {e}")
        return []

# -------------------------------
# Download Stock Data
# -------------------------------
@st.cache_data
def get_stock_data(ticker):
    df = yf.download(ticker + ".NS", start=start_date, end=end_date)
    if not df.empty:
        df.dropna(inplace=True)
    return df

# -------------------------------
# Bollinger Breakout Detection
# -------------------------------
def detect_bollinger_breakout(df):
    if df.empty or len(df) < 20:
        return False
    bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['bb_bbm'] = bb.bollinger_mavg()
    df['bb_bbh'] = bb.bollinger_hband()
    df['bb_bbl'] = bb.bollinger_lband()
    df['bb_width'] = df['bb_bbh'] - df['bb_bbl']
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    narrow = df['bb_width'].rolling(20).mean().iloc[-1] * 0.5
    if (
        last_row['Close'] > last_row['bb_bbh'] and
        prev_row['Close'] < prev_row['bb_bbh'] and
        last_row['bb_width'] < narrow
    ):
        return True
    return False

# -------------------------------
# Main Analysis Logic
# -------------------------------
breakout_stocks = []
all_stocks = get_index_stocks(selected_index)
stocks_data = {}

st.info(f"Scanning stocks in {selected_index} for Bollinger Breakout...")
for stock in all_stocks:
    df = get_stock_data(stock)
    if detect_bollinger_breakout(df):
        breakout_stocks.append(stock)
        stocks_data[stock] = df

selected_stock = st.selectbox("📌 Select breakout stock to visualize:", breakout_stocks) if breakout_stocks else None

if selected_stock:
    df = stocks_data[selected_stock]
    # Technical Indicators
    bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['bb_mavg'] = bb.bollinger_mavg()
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()

    # Chart
    st.subheader(f"📈 {selected_stock} Bollinger Bands & Candlestick")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df['Close'], label='Close Price', color='black')
    ax.plot(df.index, df['bb_high'], linestyle='--', color='red', label='Upper Band')
    ax.plot(df.index, df['bb_low'], linestyle='--', color='blue', label='Lower Band')
    ax.plot(df.index, df['bb_mavg'], linestyle='-', color='green', label='Middle Band')
    ax.set_title(f"{selected_stock} Bollinger Band")
    ax.legend()
    st.pyplot(fig)

    st.subheader("📉 RSI Indicator")
    fig2, ax2 = plt.subplots(figsize=(12, 3))
    ax2.plot(df.index, df['RSI'], color='green', label='RSI')
    ax2.axhline(70, color='red', linestyle='--')
    ax2.axhline(30, color='blue', linestyle='--')
    ax2.legend()
    st.pyplot(fig2)

    st.subheader("📄 Last 10 Rows")
    st.dataframe(df.tail(10))

    st.download_button(
        label="⬇️ Download CSV",
        data=df.to_csv().encode(),
        file_name=f"{selected_stock}_data.csv",
        mime='text/csv'
    )

# -------------------------------
# Hugging Face Chatbot Section
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Ask Shweta")

HF_API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
hf_token = st.secrets.get("huggingface", {}).get("api_key") or os.getenv("HF_API_KEY")
hf_headers = {"Authorization": f"Bearer {hf_token}"}

user_input_chat = st.sidebar.text_input("Your question")
if user_input_chat:
    try:
        response = requests.post(
            HF_API_URL,
            headers=hf_headers,
            json={"inputs": user_input_chat},
            timeout=30
        )
        response.raise_for_status()
        output = response.json()[0]['generated_text'].split('<|assistant|>')[-1].strip()
    except Exception as e:
        output = f"❌ Hugging Face API error: {str(e)}"

    st.sidebar.markdown(f"**🤖 Avyan:** {output}")
