# Import required libraries
import streamlit as st  # Streamlit for creating the web interface
import yfinance as yf   # yfinance for downloading stock price data
import pandas as pd     # pandas for data manipulation
import ta               # technical analysis library for indicators like SMA and RSI
import matplotlib.pyplot as plt  # for plotting graphs
import requests
import os
from datetime import datetime

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer Web App", layout="wide")  # Set page title and layout
st.title("📊 Stock Analyzer Web App")  # Title displayed on the app

# -------------------------------
# NSE Index Stock Fetch Function from GitHub CSV
# -------------------------------
@st.cache_data
def get_nse_index_stocks(index_name="NIFTY 50"):
    csv_url = "https://raw.githubusercontent.com/Sanchitlko1994/Stock-Analyzer/main/NSE%20INDEX%20STOCKS.csv"
    df = pd.read_csv(csv_url)
    return df[df["index"] == index_name]["stock"].tolist()

# -------------------------------
# Sidebar Inputs
# -------------------------------
index_options = ["NIFTY 50", "NIFTY 100", "NIFTY 500", "NIFTY AUTO", "NIFTY BANK", "NIFTY FINANCIAL SERVICES","NIFTY HEALTHCARE","NIFTY PHARMA","NIFTY IT","NIFTY OIL & GAS"]
selected_index = st.sidebar.selectbox("Select NSE Index", index_options)
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# -------------------------------
# Bollinger Band Breakout Check
# -------------------------------
def detect_bollinger_breakout(df):
    if len(df) < 21:
        return False
    bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    bb_bbm = bb.bollinger_mavg()
    bb_bbh = bb.bollinger_hband()
    bb_bbl = bb.bollinger_lband()
    bb_width = bb_bbh - bb_bbl
    df['bb_width'] = bb_width
    narrow = bb_width < bb_width.quantile(0.2)
    breakout = df['Close'] > bb_bbh
    return narrow.iloc[-1] and breakout.iloc[-1]

# -------------------------------
# Cached Data Download Function
# -------------------------------
@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df.dropna(inplace=True)
    return df

# -------------------------------
# Identify Breakout Stocks
# -------------------------------
breakout_stocks = []
stocks = []
try:
    stocks = get_nse_index_stocks(selected_index)
    for stock in stocks:
        df = get_data(stock, start_date, end_date)
        if not df.empty and detect_bollinger_breakout(df):
            breakout_stocks.append(stock)
except Exception as e:
    st.error(f"❌ Failed to load index data: {str(e)}")

# -------------------------------
# UI: Display List of Breakout Stocks
# -------------------------------
if breakout_stocks:
    st.sidebar.success(f"{len(breakout_stocks)} breakout stocks found")
    selected_stock = st.sidebar.selectbox("Select Stock for Analysis", breakout_stocks)

    df = get_data(selected_stock, start_date, end_date)

    # Calculate indicators
    bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['bb_mavg'] = bb.bollinger_mavg()
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()

    # Bollinger + Candlestick
    st.subheader(f"📈 {selected_stock} - Bollinger Band with Close Price")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df['Close'], label='Close')
    ax.plot(df.index, df['bb_mavg'], label='Middle Band', linestyle='--')
    ax.plot(df.index, df['bb_high'], label='Upper Band', linestyle='--')
    ax.plot(df.index, df['bb_low'], label='Lower Band', linestyle='--')
    ax.set_title("Bollinger Bands")
    ax.legend()
    st.pyplot(fig)

    # RSI
    st.subheader("📉 RSI Indicator")
    fig2, ax2 = plt.subplots(figsize=(12, 3))
    ax2.plot(df.index, df['RSI'], label='RSI', color='green')
    ax2.axhline(70, linestyle='--', color='red')
    ax2.axhline(30, linestyle='--', color='blue')
    ax2.set_title("RSI (14)")
    ax2.legend()
    st.pyplot(fig2)

    st.subheader("📄 Sample Data")
    st.dataframe(df.tail(10))

    st.download_button(
        label="⬇️ Download CSV",
        data=df.to_csv().encode(),
        file_name=f"{selected_stock}_data.csv",
        mime='text/csv'
    )
else:
    st.warning("No breakout stocks found or failed to fetch index data.")

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
