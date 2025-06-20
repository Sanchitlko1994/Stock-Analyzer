import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt

# Streamlit layout
st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Stock Analyzer Web App")

# Sidebar input
user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "TCS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Append .NS for Indian stocks if no suffix
def format_ticker(ticker):
    if "." not in ticker:
        return ticker.strip().upper() + ".NS"
    return ticker.strip().upper()

ticker = format_ticker(user_input)

# Get data with fallback for column mismatch
@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    expected_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    df = df[[col for col in expected_columns if col in df.columns]]
    df.dropna(inplace=True)
    return df

# Button triggers analysis
if st.sidebar.button("Analyze"):
    try:
        data = get_data(ticker, start_date, end_date)

        if data.empty or 'Close' not in data.columns:
            st.warning(f"No usable 'Close' price data found for '{ticker}'. Try another ticker.")
        else:
            close_prices = data['Close']

            # Only compute indicators if enough data
            if close_prices.isnull().all() or len(close_prices) < 20:
                st.error("Not enough data to compute indicators.")
            else:
                # Indicators
                data['SMA_20'] = ta.trend.sma_indicator(close=close_prices, window=20)
                data['RSI'] = ta.momentum.rsi(close=close_prices, window=14)

                # Plot SMA chart
                st.subheader(f"📈 {user_input.upper()} Price Chart with SMA")
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(data.index, close_prices, label='Close Price')
                ax.plot(data.index, data['SMA_20'], label='SMA 20', linestyle='--')
                ax.set_title(f"{user_input.upper()} - Price with SMA")
                ax.legend()
                st.pyplot(fig)

                # Plot RSI
                st.subheader("📉 RSI Indicator")
                fig2, ax2 = plt.subplots(figsize=(12, 3))
                ax2.plot(data.index, data['RSI'], label='RSI', color='green')
                ax2.axhline(70, linestyle='--', color='red')
                ax2.axhline(30, linestyle='--', color='blue')
                ax2.set_title("RSI (14)")
                ax2.legend()
                st.pyplot(fig2)

                # Show sample data
                st.subheader("📄 Sample Data")
                st.dataframe(data.tail(10))

                # Download CSV
                st.download_button(
                    label="⬇️ Download CSV",
                    data=data.to_csv().encode(),
                    file_name=f"{user_input.upper()}_data.csv",
                    mime='text/csv'
                )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
