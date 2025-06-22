# Import required libraries
import streamlit as st  # Streamlit for creating the web interface
import yfinance as yf   # yfinance for downloading stock price data
import pandas as pd     # pandas for data manipulation
import ta               # technical analysis library for indicators like SMA and RSI
import matplotlib.pyplot as plt  # for plotting graphs

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
    """
    Formats the ticker by appending '.NS' if not already included
    Assumes Indian stocks need the NSE suffix.
    """
    if "." not in ticker:
        return ticker.strip().upper() + ".NS"
    return ticker.strip().upper()

ticker = format_ticker(user_input)

# -------------------------------
# Data Download Function (Cached)
# -------------------------------
@st.cache_data  # Caches the result to avoid re-fetching for same inputs
def get_data(ticker, start, end):
    """
    Downloads historical stock data from Yahoo Finance.
    Cleans up missing values if present.
    """
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df = df.dropna()
    return df

# -------------------------------
# Main Analysis Logic Triggered on Button Click
# -------------------------------
if st.sidebar.button("Analyze"):
    try:
        # Fetch data
        data = get_data(ticker, start_date, end_date)

        # Check for valid data
        if data.empty or 'Close' not in data.columns:
            st.warning(f"No valid 'Close' data found for {ticker}.")
        else:
            # Ensure close_prices is a 1D Series
            close_prices = data['Close']
            if isinstance(close_prices, pd.DataFrame):
                close_prices = close_prices.squeeze()  # Convert (n,1) dataframe to Series

            # Ensure we have enough data points
            if close_prices.empty or len(close_prices) < 20:
                st.error("Not enough data to calculate indicators.")
            else:
                # -------------------------------
                # Technical Indicator Calculations
                # -------------------------------
                sma_20 = ta.trend.SMAIndicator(close=close_prices, window=20).sma_indicator()
                rsi_14 = ta.momentum.RSIIndicator(close=close_prices, window=14).rsi()

                # Add indicators to the original dataframe
                data['SMA_20'] = sma_20
                data['RSI'] = rsi_14

                # -------------------------------
                # Plot Price with SMA
                # -------------------------------
                st.subheader(f"📈 {user_input.upper()} Price Chart with SMA")
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(data.index, data['Close'], label='Close Price')
                ax.plot(data.index, data['SMA_20'], label='SMA 20', linestyle='--')
                ax.set_title(f"{user_input.upper()} - Price with SMA")
                ax.legend()
                st.pyplot(fig)

                # -------------------------------
                # Plot RSI Indicator
                # -------------------------------
                st.subheader("📉 RSI Indicator")
                fig2, ax2 = plt.subplots(figsize=(12, 3))
                ax2.plot(data.index, data['RSI'], label='RSI', color='green')
                ax2.axhline(70, linestyle='--', color='red')  # Overbought line
                ax2.axhline(30, linestyle='--', color='blue')  # Oversold line
                ax2.set_title("RSI (14)")
                ax2.legend()
                st.pyplot(fig2)

                # -------------------------------
                # Display Sample of Processed Data
                # -------------------------------
                st.subheader("📄 Sample Data")
                st.dataframe(data.tail(10))  # Show last 10 rows for inspection

                # -------------------------------
                # Download CSV Option
                # -------------------------------
                st.download_button(
                    label="⬇️ Download CSV",
                    data=data.to_csv().encode(),  # Convert dataframe to CSV and encode for download
                    file_name=f"{user_input.upper()}_data.csv",
                    mime='text/csv'
                )

    except Exception as e:
        # Catch and show any error that occurs during the process
        st.error(f"❌ Error: {str(e)}")
