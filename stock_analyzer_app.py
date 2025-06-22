import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt

# -------------------------------
# Streamlit Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Stock Analyzer Web App")

# -------------------------------
# Sidebar Input Fields
# -------------------------------
user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "TCS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# -------------------------------
# Format ticker (for NSE stocks)
# -------------------------------
def format_ticker(ticker):
    if "." not in ticker:
        return ticker.strip().upper() + ".NS"
    return ticker.strip().upper()

ticker = format_ticker(user_input)

# -------------------------------
# Data download function
# -------------------------------
@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df = df.dropna()
    return df

# -------------------------------
# Stock Analysis Logic
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
                # Calculate indicators
                sma_20 = ta.trend.SMAIndicator(close=close_prices, window=20).sma_indicator()
                rsi_14 = ta.momentum.RSIIndicator(close=close_prices, window=14).rsi()

                data['SMA_20'] = sma_20
                data['RSI'] = rsi_14

                # Plot Price Chart
                st.subheader(f"📈 {user_input.upper()} Price Chart with SMA")
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(data.index, data['Close'], label='Close Price')
                ax.plot(data.index, data['SMA_20'], label='SMA 20', linestyle='--')
                ax.set_title(f"{user_input.upper()} - Price with SMA")
                ax.legend()
                st.pyplot(fig)

                # Plot RSI Chart
                st.subheader("📉 RSI Indicator")
                fig2, ax2 = plt.subplots(figsize=(12, 3))
                ax2.plot(data.index, data['RSI'], label='RSI', color='green')
                ax2.axhline(70, linestyle='--', color='red')
                ax2.axhline(30, linestyle='--', color='blue')
                ax2.set_title("RSI (14)")
                ax2.legend()
                st.pyplot(fig2)

                # Show Recent Data
                st.subheader("📄 Sample Data")
                st.dataframe(data.tail(10))

                # CSV Download Button
                st.download_button(
                    label="⬇️ Download CSV",
                    data=data.to_csv().encode(),
                    file_name=f"{user_input.upper()}_data.csv",
                    mime='text/csv'
                )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


# -------------------------------
# AI Chatbot Assistant Section
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Ask AI Assistant")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Simple rule-based AI response
def ai_response(user_msg):
    msg = user_msg.lower()
    if "rsi" in msg:
        return "RSI (Relative Strength Index) measures the speed and change of price movements. RSI >70 is overbought, <30 is oversold."
    elif "sma" in msg or "moving average" in msg:
        return "SMA (Simple Moving Average) smooths price data over a period. It helps identify trend direction."
    elif "download" in msg:
        return "Click the 'Download CSV' button to get the processed stock data."
    elif "price chart" in msg:
        return "The price chart shows the historical stock closing prices along with the 20-day SMA."
    else:
        return "I'm here to help with RSI, SMA, and charts. Try asking about those!"

# Input box for user chat
user_question = st.sidebar.text_input("Ask a question", key="chat_input")

if user_question:
    response = ai_response(user_question)
    st.session_state.chat_history.append(("You", user_question))
    st.session_state.chat_history.append(("AI", response))

# Display chat history
for speaker, msg in st.session_state.chat_history[-6:]:  # show last 6 messages
    st.sidebar.markdown(f"**{speaker}:** {msg}")
