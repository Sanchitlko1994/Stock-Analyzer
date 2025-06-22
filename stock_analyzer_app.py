# Import required libraries
import streamlit as st  # Streamlit for creating the web interface
import yfinance as yf   # yfinance for downloading stock price data
import pandas as pd     # pandas for data manipulation
import ta               # technical analysis library for indicators like SMA and RSI
import matplotlib.pyplot as plt  # for plotting graphs
import requests
import os

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer", layout="wide")  # Set page title and layout
st.title("📊 Stock Analyzer Web App")  # Title displayed on the app

# -------------------------------
# Sidebar Input Fields
# -------------------------------
user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "TCS")  # User input for stock symbol
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))  # Start date for data download
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))  # End date for data download

# -------------------------------
# Helper Function to Format Ticker
# -------------------------------
def format_ticker(ticker):
    if "." not in ticker:
        return ticker.strip().upper() + ".NS"
    return ticker.strip().upper()

ticker = format_ticker(user_input)

# -------------------------------
# Data Download Function (Cached)
# -------------------------------
@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df = df.dropna()
    return df

# -------------------------------
# Main Analysis Logic Triggered on Button Click
# -------------------------------
if st.sidebar.button("Analyze"):
    try:
        data = get_data(ticker, start_date, end_date)

        if data.empty or 'Close' not in data.columns:
            st.warning(f"No valid 'Close' data found for {ticker}.")
        else:
            close_prices = data['Close']
            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.squeeze()

            if close_prices.empty or len(close_prices) < 20:
                st.error("Not enough data to calculate indicators.")
            else:
                sma_20 = ta.trend.SMAIndicator(close=close_prices, window=20).sma_indicator()
                rsi_14 = ta.momentum.RSIIndicator(close=close_prices, window=14).rsi()

                data['SMA_20'] = sma_20
                data['RSI'] = rsi_14

                st.subheader(f"📈 {user_input.upper()} Price Chart with SMA")
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(data.index, data['Close'], label='Close Price')
                ax.plot(data.index, data['SMA_20'], label='SMA 20', linestyle='--')
                ax.set_title(f"{user_input.upper()} - Price with SMA")
                ax.legend()
                st.pyplot(fig)

                st.subheader("📉 RSI Indicator")
                fig2, ax2 = plt.subplots(figsize=(12, 3))
                ax2.plot(data.index, data['RSI'], label='RSI', color='green')
                ax2.axhline(70, linestyle='--', color='red')
                ax2.axhline(30, linestyle='--', color='blue')
                ax2.set_title("RSI (14)")
                ax2.legend()
                st.pyplot(fig2)

                st.subheader("📄 Sample Data")
                st.dataframe(data.tail(10))

                st.download_button(
                    label="⬇️ Download CSV",
                    data=data.to_csv().encode(),
                    file_name=f"{user_input.upper()}_data.csv",
                    mime='text/csv'
                )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# -------------------------------
# Hugging Face Chatbot Section
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Ask Hugging Face Assistant")

HF_API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
hf_token = st.secrets.get("huggingface", {}).get("api_key") or os.getenv("HF_API_KEY")
hf_headers = {"Authorization": f"Bearer {hf_token}"}

if "hf_chat_history" not in st.session_state:
    st.session_state.hf_chat_history = []

user_input_chat = st.sidebar.text_input("Your question")

if user_input_chat:
    st.session_state.hf_chat_history.append(("👤 You", user_input_chat))
    prompt = f"<|system|>\nYou are a helpful financial assistant.\n<|user|>\n{user_input_chat}\n<|assistant|>"

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

    st.session_state.hf_chat_history.append(("🤖 HuggingFace", output))

st.sidebar.markdown("🧠 **Chat History**")
for role, msg in st.session_state.hf_chat_history:
    st.sidebar.markdown(f"**{role}:** {msg}")
