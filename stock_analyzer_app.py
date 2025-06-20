import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
from datetime import datetime

# --- Streamlit App Config ---
st.set_page_config(page_title="Stock Analyzer & RSI Comparator", layout="wide")
st.title("📊 Stock Analyzer & Top 5 RSI Picks")

# --- Index and Ticker Selection ---
index_options = {
    "NIFTY 50": ["RELIANCE", "TCS", "INFY", "HDFCBANK", "LT", "WIPRO", "HCLTECH", "ITC", "MARUTI", "TATAMOTORS"],
    "NIFTY 100": ["ASIANPAINT", "BAJFINANCE", "BHARTIARTL", "CIPLA", "DIVISLAB"],
    "NIFTY BANK": ["AXISBANK", "ICICIBANK", "KOTAKBANK", "PNB", "SBIN"]
}

selected_index = st.sidebar.selectbox("Select Index", list(index_options.keys()))
selected_stocks = index_options[selected_index]

custom_ticker = st.sidebar.text_input("Or Enter Custom Stock Ticker (e.g., AAPL, TCS)", "")

if custom_ticker:
    if "." not in custom_ticker:
        ticker_list = [custom_ticker + ".NS"]
    else:
        ticker_list = [custom_ticker]
else:
    ticker_list = [ticker + ".NS" if "." not in ticker else ticker for ticker in selected_stocks]

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

@st.cache_data
def fetch_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    df.dropna(inplace=True)
    return df

def calculate_indicators(df):
    df['EMA_12'] = ta.trend.EMAIndicator(close=df['Close'], window=12).ema_indicator()
    df['EMA_26'] = ta.trend.EMAIndicator(close=df['Close'], window=26).ema_indicator()
    df['RSI'] = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
    return df

def generate_signals(df):
    df['Buy_EMA'] = (df['EMA_12'] > df['EMA_26']) & (df['EMA_12'].shift(1) <= df['EMA_26'].shift(1))
    df['Sell_EMA'] = (df['EMA_12'] < df['EMA_26']) & (df['EMA_12'].shift(1) >= df['EMA_26'].shift(1))
    df['Buy_RSI'] = df['RSI'] < 30
    df['Sell_RSI'] = df['RSI'] > 70
    return df

def plot_price_with_signals(df, ticker):
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(df.index, df['Close'], label='Close Price', color='black')
    ax.plot(df.index, df['EMA_12'], label='EMA 12', linestyle='--')
    ax.plot(df.index, df['EMA_26'], label='EMA 26', linestyle=':')

    buy_points = df[df['Buy_EMA']]
    sell_points = df[df['Sell_EMA']]
    ax.plot(buy_points.index, buy_points['Close'], '^', markersize=10, color='green', label='Buy Signal')
    ax.plot(sell_points.index, sell_points['Close'], 'v', markersize=10, color='red', label='Sell Signal')

    ax.set_title(f"{ticker} Price with EMA and Buy/Sell Signals")
    ax.legend()
    ax.grid()
    st.pyplot(fig)

def plot_rsi(df):
    fig, ax = plt.subplots(figsize=(14, 3))
    ax.plot(df.index, df['RSI'], label='RSI', color='blue')
    ax.axhline(70, linestyle='--', color='red')
    ax.axhline(30, linestyle='--', color='green')

    rsi_buy = df[df['Buy_RSI']]
    rsi_sell = df[df['Sell_RSI']]
    ax.plot(rsi_buy.index, rsi_buy['RSI'], '^', markersize=8, color='green', label='RSI Buy')
    ax.plot(rsi_sell.index, rsi_sell['RSI'], 'v', markersize=8, color='red', label='RSI Sell')

    ax.set_title("RSI Indicator with Buy/Sell Thresholds")
    ax.legend()
    ax.grid()
    st.pyplot(fig)

# --- Main Logic ---
if st.sidebar.button("Analyze & Compare"):
    rsi_list = []
    result_data = {}

    for ticker in ticker_list:
        try:
            df = fetch_data(ticker, start_date, end_date)
            df = calculate_indicators(df)
            df = generate_signals(df)
            if not df.empty and 'RSI' in df.columns:
                rsi_list.append((ticker, df['RSI'].iloc[-1]))
                result_data[ticker] = df
        except Exception as e:
            st.warning(f"Failed to process {ticker}: {e}")

    top5 = sorted(rsi_list, key=lambda x: x[1])[:5]  # lowest RSI

    for ticker, rsi_val in top5:
        st.subheader(f"📈 {ticker} (RSI: {rsi_val:.2f})")
        df = result_data[ticker]
        plot_price_with_signals(df, ticker)
        plot_rsi(df)

        st.subheader("📄 Latest 20 Rows of Data with Signals")
        st.dataframe(df.tail(20))

        st.download_button(
            label="⬇️ Download CSV",
            data=df.to_csv().encode(),
            file_name=f"{ticker}_analysis.csv",
            mime='text/csv'
        )
