# Import required libraries
import streamlit as st  # Streamlit for creating the web interface
import yfinance as yf   # yfinance for downloading stock price data
import pandas as pd     # pandas for data manipulation
import ta               # technical analysis library for indicators like SMA and RSI
import matplotlib.pyplot as plt  # for plotting graphs
import requests
import os
import numpy as np
import time

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer", layout="wide")  # Set page title and layout
st.title("📊 Stock Analyzer Web App")  # Title displayed on the app

# -------------------------------
# Helper Functions
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

    index_param = index_map[index_name]
    url = f"https://www.nseindia.com/api/equity-stockIndices?index={index_param.replace(' ', '%20')}"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/"
    }

    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers, timeout=5)
    response = session.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()["data"]
    return [item["symbol"] + ".NS" for item in data]

def scan_breakouts(symbols, index_name):
    results = []
    for symbol in symbols:
        try:
            df = yf.download(symbol, period="6mo", interval="1d", progress=False)
            df.dropna(inplace=True)
            if len(df) < 20:
                continue

            df["SMA20"] = df["Close"].rolling(20).mean()
            df["STD"] = df["Close"].rolling(20).std()
            df["Upper"] = df["SMA20"] + 2 * df["STD"]
            df["Lower"] = df["SMA20"] - 2 * df["STD"]
            df["Width"] = df["Upper"] - df["Lower"]

            latest = df.iloc[-1]
            width_percentile_20 = np.percentile(df["Width"].dropna(), 20)

            if latest["Width"] <= width_percentile_20 and latest["Close"] > latest["Upper"]:
                results.append({
                    "Index": index_name,
                    "Symbol": symbol,
                    "Date": latest.name.strftime("%Y-%m-%d"),
                    "Close": round(latest["Close"], 2),
                    "Upper Band": round(latest["Upper"], 2),
                    "Band Width": round(latest["Width"], 2)
                })

            time.sleep(0.5)
        except Exception as e:
            print(f"[{symbol}] Error: {e}")
    return pd.DataFrame(results)

# -------------------------------
# Main Analysis Logic Triggered on Button Click
# -------------------------------
if st.sidebar.button("Scan Breakouts"):
    index_list = ["NIFTYBANK", "NIFTYAUTO", "NIFTYFINANCIALS", "NIFTY100", "NIFTY200", "NIFTY500"]
    all_results = pd.DataFrame()

    for index in index_list:
        st.write(f"🔍 Scanning {index}...")
        try:
            symbols = get_nse_index_symbols(index)
            df = scan_breakouts(symbols, index)
            if not df.empty:
                all_results = pd.concat([all_results, df], ignore_index=True)
        except Exception as err:
            st.warning(f"⚠️ Failed to process {index}: {err}")

    if not all_results.empty:
        st.success("✅ Breakout Stocks Found")
        st.dataframe(all_results)
        st.download_button(
            label="⬇️ Download Breakout Stocks CSV",
            data=all_results.to_csv(index=False).encode(),
            file_name="nse_breakouts.csv",
            mime='text/csv'
        )
    else:
        st.info("📭 No breakouts found across selected indices.")

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
