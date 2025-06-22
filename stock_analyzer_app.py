# (Import section remains unchanged)
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

st.set_page_config(page_title="Stock Analyzer Web App", layout="wide")

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

st.title("📊 Stock Analyzer Web App")

# CSV Load Function
@st.cache_data
def get_nse_index_stocks(index_name="NIFTY 50"):
    csv_url = "https://raw.githubusercontent.com/Sanchitlko1994/Stock-Analyzer/main/NSE%20INDEX%20STOCKS.csv"
    df = pd.read_csv(csv_url)
    return df[df["index"] == index_name]["stock"].tolist()

# Sidebar Inputs
index_options = ["NIFTY 50", "NIFTY 100", "NIFTY 500", "NIFTY AUTO", "NIFTY BANK", "NIFTY FINANCIAL SERVICES", "NIFTY HEALTHCARE", "NIFTY PHARMA", "NIFTY IT", "NIFTY OIL & GAS"]
selected_index = st.sidebar.selectbox("Select NSE Index", index_options)
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

analyze_button = st.sidebar.button("🔍 Analyze")
clear_button = st.sidebar.button("🧹 Clear Analysis")

# Add chatbot toggle button to main interface
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False

if st.button("💬 Show Chatbot"):
    st.session_state.show_chat = not st.session_state.show_chat

# Session Management
if clear_button:
    st.session_state.clear()
    st.rerun()

if analyze_button:
    st.session_state["start_analysis"] = True
    st.session_state["selected_stock"] = None

# Breakout Detection Logic
def detect_bollinger_breakout(df):
    if len(df) < 21:
        return False
    close_series = df['Close'].squeeze()
    bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    bb_width = bb.bollinger_hband() - bb.bollinger_lband()
    df['bb_width'] = bb_width
    return (bb_width < bb_width.quantile(0.2)).iloc[-1] and (close_series > bb.bollinger_hband()).iloc[-1]

@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df.dropna(inplace=True)
    return df

# Analyze logic
if st.session_state.get("start_analysis"):
    start_timer = time.time()
    with st.spinner("Analyzing breakout stocks. Please wait..."):
        breakout_stocks, stocks = [], []
        error_occurred = False
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
            error_occurred = True

        if error_occurred:
            st.error("❌ Error during analysis.")
        elif not stocks:
            st.error("❌ No stocks found.")
        elif not breakout_stocks:
            st.warning("⚠️ No breakout stocks found.")
        else:
            st.session_state["breakout_stocks"] = breakout_stocks
            st.success(f"✅ {len(breakout_stocks)} breakout stocks found.")

# Stock analysis UI
breakout_stocks = st.session_state.get("breakout_stocks", [])
if breakout_stocks:
    selected_stock = st.sidebar.selectbox("Select Stock for Analysis", breakout_stocks, index=breakout_stocks.index(st.session_state.get("selected_stock", breakout_stocks[0])) if st.session_state.get("selected_stock") in breakout_stocks else 0)
    st.session_state["selected_stock"] = selected_stock

    df = get_data(selected_stock, start_date, end_date)
    close_series = df['Close'].squeeze()
    bb = ta.volatility.BollingerBands(close=close_series, window=20, window_dev=2)
    df['bb_mavg'] = bb.bollinger_mavg()
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['RSI'] = ta.momentum.RSIIndicator(close=close_series, window=14).rsi()

    st.subheader(f"📈 {selected_stock} - Bollinger Band with Close Price")
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df.index, df['Close'], label='Close')
    ax.plot(df.index, df['bb_mavg'], label='Middle Band', linestyle='--')
    ax.plot(df.index, df['bb_high'], label='Upper Band', linestyle='--')
    ax.plot(df.index, df['bb_low'], label='Lower Band', linestyle='--')
    ax.set_title("Bollinger Bands")
    ax.legend()
    st.pyplot(fig)

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

    st.download_button("⬇️ Download CSV", data=df.to_csv().encode(), file_name=f"{selected_stock}_data.csv", mime='text/csv')

    b64_audio = base64.b64encode(requests.get("https://www.soundjay.com/buttons/sounds/button-29.mp3").content).decode()
    st.markdown(f"""
    <audio autoplay>
        <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
    </audio>
    """, unsafe_allow_html=True)

    elapsed = time.time() - start_timer
    st.info(f"✅ Analysis completed in {elapsed:.2f} seconds.")

# -------------------------------
# Chatbot Section (Toggle-Based)
# -------------------------------
if st.session_state.show_chat:
    st.markdown("---")
    st.markdown("### 💬 Ask Shweta")

    HF_API_URL = "https://api-inference.huggingface.co/models/bigscience/bloom-560m"
    hf_token = st.secrets.get("huggingface", {}).get("api_key") or os.getenv("HF_API_KEY")
    hf_headers = {"Authorization": f"Bearer {hf_token}"}

    with st.form("chat_form"):
        user_input_chat = st.text_input("Your question", key="chat_input")
        submit_chat = st.form_submit_button("Send")

    if submit_chat and user_input_chat:
        if not hf_token:
            st.warning("⚠️ Hugging Face API token is missing or invalid.")
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
            st.markdown(f"**🤖 Avyan:** {output}")
