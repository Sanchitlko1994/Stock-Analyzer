# Stock Analyzer Web App

import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import mplfinance as mpf
import requests
import os
from bs4 import BeautifulSoup

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Stock Analyzer Web App")

# ----------------------------
# NSE Index Options
# ----------------------------
index_options = {
    "NIFTY 50": "NIFTY 50",
    "NIFTY 100": "NIFTY 100",
    "NIFTY 500": "NIFTY 500",
    "NIFTY AUTO": "NIFTY AUTO"
}

index_selected = st.sidebar.selectbox("Select NSE Index", list(index_options.keys()))
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# ----------------------------
# NSE Ticker Fetching
# ----------------------------
@st.cache_data
def get_nse_index_stocks(index_name):
    url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_name.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    session = requests.Session()
    session.headers.update(headers)
    response = session.get("https://www.nseindia.com")  # Necessary to establish session
    r = session.get(url)
    r.raise_for_status()
    data = r.json()
    return [stock["symbol"] + ".NS" for stock in data["data"]]

# ----------------------------
# Data Fetch & Indicator Calc
# ----------------------------
@st.cache_data
def get_stock_data(ticker):
    df = yf.download(ticker, start=start_date, end=end_date)
    if not df.empty:
        df = df.dropna()
    return df

def detect_bollinger_breakout(df):
    close = df['Close']
    bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
    df['bb_bbm'] = bb.bollinger_mavg()
    df['bb_bbh'] = bb.bollinger_hband()
    df['bb_bbl'] = bb.bollinger_lband()
    df['bb_width'] = df['bb_bbh'] - df['bb_bbl']
    
    recent = df.iloc[-1]
    narrow = df['bb_width'].rolling(20).mean().iloc[-1] * 0.75
    is_narrow = recent['bb_width'] < narrow
    is_breakout = recent['Close'] > recent['bb_bbh']
    return is_narrow and is_breakout

# ----------------------------
# Process Index Stocks
# ----------------------------
qualified_stocks = []
stocks_list = []
try:
    stocks_list = get_nse_index_stocks(index_options[index_selected])
    for stock in stocks_list:
        df = get_stock_data(stock)
        if not df.empty and detect_bollinger_breakout(df):
            qualified_stocks.append(stock)
except Exception as e:
    st.error(f"❌ Failed to load index data: {e}")

# ----------------------------
# UI Output
# ----------------------------
if qualified_stocks:
    selected_stock = st.selectbox("Select Breakout Stock", qualified_stocks)
    df = get_stock_data(selected_stock)

    # Indicators
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['bb_mavg'] = bb.bollinger_mavg()
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()

    # Candlestick + Bollinger
    st.subheader("📈 Candlestick with Bollinger Bands")
    mpf_data = df[['Open', 'High', 'Low', 'Close']]
    addplots = [
        mpf.make_addplot(df['bb_high'], color='g'),
        mpf.make_addplot(df['bb_low'], color='r'),
        mpf.make_addplot(df['bb_mavg'], color='b')
    ]
    fig, _ = mpf.plot(mpf_data, type='candle', style='yahoo', addplot=addplots, returnfig=True)
    st.pyplot(fig)

    # RSI Plot
    st.subheader("📉 RSI Indicator")
    fig2, ax2 = plt.subplots(figsize=(12, 3))
    ax2.plot(df.index, df['RSI'], label='RSI', color='green')
    ax2.axhline(70, linestyle='--', color='red')
    ax2.axhline(30, linestyle='--', color='blue')
    ax2.set_title("RSI (14)")
    ax2.legend()
    st.pyplot(fig2)

    # Dataframe
    st.subheader("📄 Sample Data")
    st.dataframe(df.tail(10))

    # Download
    st.download_button(
        label="⬇️ Download CSV",
        data=df.to_csv().encode(),
        file_name=f"{selected_stock}_data.csv",
        mime='text/csv'
    )
else:
    st.info("No stocks found with strong breakout setup.")

# ----------------------------
# Hugging Face Chatbot
# ----------------------------
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
