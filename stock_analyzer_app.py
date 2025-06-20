import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt

# Set up Streamlit
st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Stock Analyzer Web App")

# --- Sidebar inputs ---
user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "TCS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Format ticker to use .NS if needed
def format_ticker(ticker):
    if "." not in ticker:
        return ticker.strip().upper() + ".NS"
    return ticker.strip().upper()

ticker = format_ticker(user_input)

# --- Fetch stock data ---
@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    df = df[['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']].dropna()
    return df

# --- Button triggers analysis ---
if st.sidebar.button("Analyze"):
    try:
        data = get_data(ticker, start_date, end_date)

        if data.empty:
            st.warning(f"No data found for '{ticker}' between {start_date} and {end_date}.")
        else:
            # Calculate indicators safely
            close_prices = data['Close']

            # Check if Close is valid
            if close_prices.isnull().all() or len(close_prices) < 20:
                st.error("Not enough valid 'Close' price data to compute indicators.")
            else:
                sma_20 = ta.trend.sma_indicator(close=close_prices, window=20)
                rsi_14 = ta.momentum.rsi(close=close_prices, window=14)

                data['SMA_20'] = sma_20
                data['RSI'] = rsi_14

                # --- Plot Close + SMA ---
                st.subheader(f"📈 {user_input.upper()} Price Chart with SMA")
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(data.index, close_prices, label='Close Price')
                ax.plot(data.index, data['SMA_20'], label='SMA 20', linestyle='--')
                ax.set_title(f"{user_input.upper()} - Price with SMA")
                ax.legend()
                st.pyplot(fig)

                # --- Plot RSI ---
                st.subheader("📉 RSI Indicator")
                fig2, ax2 = plt.subplots(figsize=(12, 3))
                ax2.plot(data.index, data['RSI'], label='RSI', color='green')
                ax2.axhline(70, linestyle='--', color='red')
                ax2.axhline(30, linestyle='--', color='blue')
                ax2.set_title("RSI (14)")
                ax2.legend()
                st.pyplot(fig2)

                # --- Data Table ---
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
