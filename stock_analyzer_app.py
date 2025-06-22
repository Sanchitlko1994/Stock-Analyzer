# Import required libraries
import streamlit as st  # For creating the web application interface
import yfinance as yf   # For fetching historical stock data from Yahoo Finance
import pandas as pd     # For data manipulation and handling
import ta               # For technical analysis indicators like SMA and RSI
import matplotlib.pyplot as plt  # For plotting charts and visualizations
import requests         # For making HTTP requests (used for chatbot API call)
import os               # For accessing environment variables (API keys)

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer", layout="wide")  # Set app title and make layout wide
st.title("📊 Stock Analyzer Web App")  # Display title at the top of the app

# -------------------------------
# Sidebar Input Fields
# -------------------------------
# User inputs for stock symbol and date range from the sidebar
user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "TCS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# -------------------------------
# Helper Function to Format Ticker
# -------------------------------
# Ensures that Indian stocks get ".NS" suffix if not already present
def format_ticker(ticker):
    if "." not in ticker:
        return ticker.strip().upper() + ".NS"
    return ticker.strip().upper()

ticker = format_ticker(user_input)

# -------------------------------
# Data Download Function (Cached)
# -------------------------------
# Downloads and caches stock data to avoid redundant API calls
@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df = df.dropna()  # Clean missing rows if any
    return df

# -------------------------------
# Main Analysis Logic Triggered on Button Click
# -------------------------------
if st.sidebar.button("Analyze"):
    try:
        data = get_data(ticker, start_date, end_date)  # Fetch historical data

        if data.empty or 'Close' not in data.columns:
            st.warning(f"No valid 'Close' data found for {ticker}.")
        else:
            close_prices = data['Close']
            if isinstance(close_prices, pd.DataFrame):  # Just in case it's 2D
                close_prices = close_prices.squeeze()

            if close_prices.empty or len(close_prices) < 20:
                st.error("Not enough data to calculate indicators.")
            else:
                # Calculate 20-day Simple Moving Average (SMA)
                sma_20 = ta.trend.SMAIndicator(close=close_prices, window=20).sma_indicator()
                # Calculate 14-day Relative Strength Index (RSI)
                rsi_14 = ta.momentum.RSIIndicator(close=close_prices, window=14).rsi()

                # Add calculated indicators to the original dataframe
                data['SMA_20'] = sma_20
                data['RSI'] = rsi_14

                # -------------------------------
                # Plot Closing Price with SMA
                # -------------------------------
                st.subheader(f"📈 {user_input.upper()} Price Chart with SMA")
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(data.index, data['Close'], label='Close Price')
                ax.plot(data.index, data['SMA_20'], label='SMA 20', linestyle='--')
                ax.set_title(f"{user_input.upper()} - Price with SMA")
                ax.legend()
                st.pyplot(fig)

                # -------------------------------
                # Plot RSI
                # -------------------------------
                st.subheader("📉 RSI Indicator")
                fig2, ax2 = plt.subplots(figsize=(12, 3))
                ax2.plot(data.index, data['RSI'], label='RSI', color='green')
                ax2.axhline(70, linestyle='--', color='red')   # Overbought level
                ax2.axhline(30, linestyle='--', color='blue')  # Oversold level
                ax2.set_title("RSI (14)")
                ax2.legend()
                st.pyplot(fig2)

                # -------------------------------
                # Display Processed Data
                # -------------------------------
                st.subheader("📄 Sample Data")
                st.dataframe(data.tail(10))  # Show last 10 rows

                # -------------------------------
                # CSV Download Option
                # -------------------------------
                st.download_button(
                    label="⬇️ Download CSV",
                    data=data.to_csv().encode(),
                    file_name=f"{user_input.upper()}_data.csv",
                    mime='text/csv'
                )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")  # Display any processing error

# -------------------------------
# Hugging Face Chatbot Section (Compact Bottom-Right Box)
# -------------------------------
# Creates a floating container in the bottom-right corner for the chatbot
with st.container():
    spacer1, chat_col = st.columns([8, 2])  # Layout spacing

    with chat_col:
        # Styling for fixed-position chat box
        st.markdown("<div style='position:fixed; bottom:10px; right:10px; width:300px; padding:10px; border:1px solid #ccc; border-radius:10px; background-color:#f9f9f9;'>", unsafe_allow_html=True)
        st.markdown("### 💬 Ask Shweta")  # Chatbot title

        # Setup Hugging Face inference endpoint
        HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"
        hf_token = st.secrets.get("huggingface", {}).get("api_key") or os.getenv("HF_API_KEY")
        hf_headers = {"Authorization": f"Bearer {hf_token}"}

        # Chat input field
        user_input_chat = st.text_input("Type your question:", key="chat_input")

        if user_input_chat:
            prompt = user_input_chat
            try:
                # Send POST request to Hugging Face API
                response = requests.post(
                    HF_API_URL,
                    headers=hf_headers,
                    json={"inputs": prompt},
                    timeout=60
                )
                response.raise_for_status()
                output = response.json()[0]['generated_text']  # Extract generated text
            except Exception as e:
                output = f"❌ Hugging Face API error: {str(e)}"

            # Display chatbot's response
            st.markdown(f"**🤖 Avyan:** {output}")

        # Close floating chat box
        st.markdown("</div>", unsafe_allow_html=True)
