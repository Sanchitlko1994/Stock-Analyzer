# Import required libraries
import streamlit as st  # Streamlit for creating the web interface
import yfinance as yf   # yfinance for downloading stock price data
import pandas as pd     # pandas for data manipulation
import ta               # technical analysis library for indicators like SMA and RSI
import matplotlib.pyplot as plt  # for plotting graphs
import requests
import os
from datetime import datetime
import time
import base64  # for audio feedback

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer Web App", layout="wide")

# Optional CSS for Fade-In Animation and Draggable Chatbox
st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        order: 0;
        border-right: 1px solid #ccc;
        border-left: none;
    }
    .element-container:nth-child(n+4) div[data-testid="stVerticalBlock"] {
        animation: fadeIn 0.6s ease-in-out;
    }
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    #chatbox {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 300px;
        padding: 15px;
        background-color: white;
        border: 1px solid #ccc;
        border-radius: 8px;
        z-index: 1000;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        cursor: move;
    }
    </style>
    <script>
    // Drag logic for chatbot
    window.onload = function() {
        const el = window.parent.document.querySelector('#chatbox')
        if (el) {
            let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
            el.onmousedown = dragMouseDown;
            function dragMouseDown(e) {
                e = e || window.event;
                e.preventDefault();
                pos3 = e.clientX;
                pos4 = e.clientY;
                document.onmouseup = closeDragElement;
                document.onmousemove = elementDrag;
            }
            function elementDrag(e) {
                e = e || window.event;
                e.preventDefault();
                pos1 = pos3 - e.clientX;
                pos2 = pos4 - e.clientY;
                pos3 = e.clientX;
                pos4 = e.clientY;
                el.style.top = (el.offsetTop - pos2) + "px";
                el.style.left = (el.offsetLeft - pos1) + "px";
            }
            function closeDragElement() {
                document.onmouseup = null;
                document.onmousemove = null;
            }
        }
    }
    </script>
""", unsafe_allow_html=True)

st.title("📊 Stock Analyzer Web App")

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
with st.sidebar:
    index_options = ["NIFTY 50", "NIFTY 100", "NIFTY 500", "NIFTY AUTO", "NIFTY BANK", "NIFTY FINANCIAL SERVICES","NIFTY HEALTHCARE","NIFTY PHARMA","NIFTY IT","NIFTY OIL & GAS"]
    selected_index = st.selectbox("Select NSE Index", index_options)
    start_date = st.date_input("Start Date", pd.to_datetime("2023-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime("today"))
    analyze_button = st.button("🔍 Analyze")
    clear_button = st.button("🧹 Clear Analysis")
    toggle_chatbot = st.checkbox("Show Chatbot 💬", value=False)

# -------------------------------
# State Management
# -------------------------------
if clear_button:
    st.session_state.clear()
    st.rerun()

if analyze_button:
    st.session_state["start_analysis"] = True
    st.session_state["selected_stock"] = None

# -------------------------------
# Detect Bollinger Breakout Function
# -------------------------------
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

# -------------------------------
# Data Fetching
# -------------------------------
@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df.dropna(inplace=True)
    return df

# -------------------------------
# Analyze Button Logic
# -------------------------------
if st.session_state.get("start_analysis"):
    start_timer = time.time()
    with st.spinner("Analyzing breakout stocks. Please wait..."):
        breakout_stocks = []
        stocks = []
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
            error_occurred = True
            st.error(f"❌ Failed to load index data: {str(e)}")

        if error_occurred:
            st.error("❌ Error occurred during index or stock data fetch.")
        elif not stocks:
            st.error("❌ No stocks found for selected index.")
        elif not breakout_stocks:
            st.warning("⚠️ No breakout stocks found for the selected period.")
        else:
            st.session_state["breakout_stocks"] = breakout_stocks
            st.success(f"✅ {len(breakout_stocks)} breakout stocks found.")

# -------------------------------
# Stock Analysis UI
# -------------------------------
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

# -------------------------------
# Hugging Face Chatbot Section
# -------------------------------
if toggle_chatbot:
    st.markdown("""
        <div id="chatbox">
        <h4>💬 Ask Shweta</h4>
    """, unsafe_allow_html=True)

    HF_API_URL = "https://api-inference.huggingface.co/models/bigscience/bloom-560m"
    hf_token = st.secrets.get("huggingface", {}).get("api_key") or os.getenv("HF_API_KEY")
    hf_headers = {"Authorization": f"Bearer {hf_token}"}

    with st.form("chat_form"):
        user_input_chat = st.text_input("Your question", key="chat_input")
        submit_chat = st.form_submit_button("Send")

    if submit_chat and user_input_chat:
        prompt = user_input_chat

        if not hf_token:
            st.warning("⚠️ Hugging Face API token is missing or invalid.")
        else:
            try:
                response = requests.post(
                    HF_API_URL,
                    headers=hf_headers,
                    json={"inputs": prompt},
                    timeout=30
                )
                response.raise_for_status()
                output = response.json()[0]['generated_text'] if isinstance(response.json(), list) else response.json()['generated_text']
            except Exception as e:
                output = f"❌ Hugging Face API error: {str(e)}"

            st.markdown(f"**🤖 Avyan:** {output}")

    st.markdown("</div>", unsafe_allow_html=True)
