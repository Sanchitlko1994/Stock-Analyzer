# Import required libraries
import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import requests
import os

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Stock Analyzer Web App")

# -------------------------------
# NSE Helper Function to Fetch Index Stocks
# -------------------------------
def get_nse_index_symbols(index_name="NIFTY 50"):
    index_map = {
        "NIFTYBANK": "NIFTY BANK",
        "NIFTYAUTO": "NIFTY AUTO",
        "NIFTYFINANCIALS": "NIFTY FINANCIAL SERVICES",
        "NIFTY100": "NIFTY 100",
        "NIFTY200": "NIFTY 200",
        "NIFTY500": "NIFTY 500"
    }
    if index_name not in index_map:
        raise ValueError("Invalid index name")
    endpoint = index_map[index_name].replace(" ", "%20")
    url = f"https://www.nseindia.com/api/equity-stockIndices?index={endpoint}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers, timeout=5)
    resp = session.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    return [item["symbol"] + ".NS" for item in data]

# -------------------------------
# Detect Bollinger Band Breakouts
# -------------------------------
def detect_breakouts(symbols, start, end):
    breakout_stocks = []
    for symbol in symbols:
        try:
            df = yf.download(symbol, start=start, end=end)
            if df.empty or 'Close' not in df:
                continue
            df = df.dropna()
            close = df['Close']
            indicator_bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
            df['bb_bbm'] = indicator_bb.bollinger_mavg()
            df['bb_bbh'] = indicator_bb.bollinger_hband()
            df['bb_bbl'] = indicator_bb.bollinger_lband()
            df['bb_width'] = df['bb_bbh'] - df['bb_bbl']

            if df['bb_width'].iloc[-1] < df['bb_width'].quantile(0.1) and close.iloc[-1] > df['bb_bbh'].iloc[-1]:
                breakout_stocks.append(symbol)
        except Exception:
            continue
    return breakout_stocks

# -------------------------------
# Run Breakout Scan for All Indices
# -------------------------------
index_list = ["NIFTYBANK", "NIFTYAUTO", "NIFTYFINANCIALS", "NIFTY100", "NIFTY200", "NIFTY500"]
start_date = pd.to_datetime("2023-01-01")
end_date = pd.to_datetime("today")

all_breakouts = {}

with st.spinner("Scanning for breakout stocks..."):
    for index_name in index_list:
        try:
            symbols = get_nse_index_symbols(index_name)
            breakouts = detect_breakouts(symbols, start_date, end_date)
            if breakouts:
                all_breakouts[index_name] = breakouts
        except Exception as e:
            st.warning(f"⚠️ Failed to scan {index_name}: {e}")

# -------------------------------
# Display Breakouts
# -------------------------------
if all_breakouts:
    for index_name, stocks in all_breakouts.items():
        st.subheader(f"🚀 {index_name} Breakouts")
        st.write(", ".join(stocks))
else:
    st.info("No breakout stocks found.")

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
