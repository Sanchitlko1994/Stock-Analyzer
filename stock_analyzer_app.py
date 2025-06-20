import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt

st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Stock Analyzer Web App")

# Sidebar inputs
ticker = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "AAPL")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Automatically append .NS if needed
if "." not in ticker:
    ticker += ".NS"

@st.cache_data
def get_data(ticker, start, end):
    data = yf.download(ticker, start=start, end=end)
    data.dropna(inplace=True)
    return data

if st.sidebar.button("Analyze"):
    try:
        data = get_data(ticker, start_date, end_date)

        if data.empty:
            st.warning(f"No data found for ticker '{ticker}' in the selected date range.")
        else:
            # Add indicators
            data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
            data['RSI'] = ta.momentum.rsi(data['Close'], window=14)

            st.subheader(f"📈 {ticker} Price Chart with SMA")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(data['Close'], label='Close Price')
            ax.plot(data['SMA_20'], label='SMA 20', linestyle='--')
            ax.set_title(f"{ticker} - Price with SMA")
            ax.legend()
            st.pyplot(fig)

            st.subheader(f"📉 RSI Indicator")
            fig2, ax2 = plt.subplots(figsize=(12, 3))
            ax2.plot(data['RSI'], label='RSI', color='green')
            ax2.axhline(70, linestyle='--', color='red')
            ax2.axhline(30, linestyle='--', color='blue')
            ax2.set_title("RSI")
            ax2.legend()
            st.pyplot(fig2)

            st.subheader("📄 Sample Data")
            st.dataframe(data.tail(10))

            st.download_button(
                label="⬇️ Download CSV",
                data=data.to_csv().encode(),
                file_name=f"{ticker}_data.csv",
                mime='text/csv'
            )

    except Exception as e:
        st.error(f"❌ Error: {e}")
