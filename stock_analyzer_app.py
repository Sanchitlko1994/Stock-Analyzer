import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt

# Page settings
st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Stock Analyzer Web App")

# Sidebar inputs
user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "TCS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Automatically append .NS for Indian stocks if no suffix is present
def format_ticker(ticker):
    if "." not in ticker:
        return ticker + ".NS"
    return ticker

ticker = format_ticker(user_input.strip().upper())

@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    df.dropna(inplace=True)
    return df

if st.sidebar.button("Analyze"):
    try:
        data = get_data(ticker, start_date, end_date)

        if data.empty:
            st.warning(f"No data found for ticker '{ticker}' between {start_date} and {end_date}.")
        else:
            # Ensure Close is numeric and drop NaNs
            data = data.copy()
            data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
            data.dropna(subset=['Close'], inplace=True)

            # Calculate indicators safely
            data['SMA_20'] = ta.trend.sma_indicator(close=data['Close'], window=20)
            data['RSI'] = ta.momentum.rsi(close=data['Close'], window=14)

            # --- Price Chart with SMA ---
            st.subheader(f"📈 {user_input.upper()} Price Chart with SMA")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(data.index, data['Close'], label='Close Price')
            ax.plot(data.index, data['SMA_20'], label='SMA 20', linestyle='--')
            ax.set_title(f"{user_input.upper()} - Price with SMA")
            ax.legend()
            st.pyplot(fig)

            # --- RSI Chart ---
            st.subheader(f"📉 RSI Indicator")
            fig2, ax2 = plt.subplots(figsize=(12, 3))
            ax2.plot(data.index, data['RSI'], label='RSI', color='green')
            ax2.axhline(70, linestyle='--', color='red')
            ax2.axhline(30, linestyle='--', color='blue')
            ax2.set_title("RSI")
            ax2.legend()
            st.pyplot(fig2)

            # --- Sample Data ---
            st.subheader("📄 Sample Data")
            st.dataframe(data.tail(10))

            # --- Download Button ---
            st.download_button(
                label="⬇️ Download CSV",
                data=data.to_csv().encode(),
                file_name=f"{user_input.upper()}_data.csv",
                mime='text/csv'
            )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
