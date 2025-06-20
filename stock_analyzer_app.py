import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt

# Streamlit UI
st.set_page_config(page_title="Stock Analyzer", layout="wide")
st.title("📊 Stock Analyzer Web App")

# Sidebar input
user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "TCS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

# Add .NS if needed
def format_ticker(ticker):
    return ticker.strip().upper() if "." in ticker else ticker.strip().upper() + ".NS"

ticker = format_ticker(user_input)

@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    return df.dropna()

if st.sidebar.button("Analyze"):
    try:
        data = get_data(ticker, start_date, end_date)

        if data.empty or 'Close' not in data.columns:
            st.warning(f"No valid data for {ticker}.")
        else:
            close = data['Close'].squeeze()

            if close.empty or len(close) < 50:
                st.error("Not enough data to compute indicators.")
            else:
                # EMA Indicators
                ema_12 = ta.trend.EMAIndicator(close=close, window=12).ema_indicator()
                ema_26 = ta.trend.EMAIndicator(close=close, window=26).ema_indicator()
                rsi_14 = ta.momentum.RSIIndicator(close=close, window=14).rsi()

                # Assign to dataframe
                data['EMA_12'] = ema_12
                data['EMA_26'] = ema_26
                data['RSI'] = rsi_14

                # EMA crossover Buy/Sell
                data['EMA_Signal'] = ''
                crossover_up = (data['EMA_12'] > data['EMA_26']) & (data['EMA_12'].shift(1) <= data['EMA_26'].shift(1))
                crossover_down = (data['EMA_12'] < data['EMA_26']) & (data['EMA_12'].shift(1) >= data['EMA_26'].shift(1))
                data.loc[crossover_up, 'EMA_Signal'] = 'Buy'
                data.loc[crossover_down, 'EMA_Signal'] = 'Sell'

                # RSI Buy/Sell
                data['RSI_Signal'] = data['RSI'].apply(
                    lambda x: 'Buy' if x < 30 else ('Sell' if x > 70 else '')
                )

                # Plot price + EMA
                st.subheader(f"📈 {user_input.upper()} Price & EMA Crossover Signals")
                fig, ax = plt.subplots(figsize=(14, 6))
                ax.plot(data.index, data['Close'], label='Close')
                ax.plot(data.index, data['EMA_12'], label='EMA 12', linestyle='--')
                ax.plot(data.index, data['EMA_26'], label='EMA 26', linestyle=':')
                ax.plot(data.index[data['EMA_Signal'] == 'Buy'], data['Close'][data['EMA_Signal'] == 'Buy'], '^', color='green', label='Buy Signal', markersize=10)
                ax.plot(data.index[data['EMA_Signal'] == 'Sell'], data['Close'][data['EMA_Signal'] == 'Sell'], 'v', color='red', label='Sell Signal', markersize=10)
                ax.set_title(f"{user_input.upper()} - EMA Crossover")
                ax.legend()
                st.pyplot(fig)

                # Plot RSI
                st.subheader("📉 RSI Indicator with Buy/Sell")
                fig2, ax2 = plt.subplots(figsize=(12, 3))
                ax2.plot(data.index, data['RSI'], label='RSI', color='green')
                ax2.axhline(70, linestyle='--', color='red')
                ax2.axhline(30, linestyle='--', color='blue')
                ax2.plot(data.index[data['RSI_Signal'] == 'Buy'], data['RSI'][data['RSI_Signal'] == 'Buy'], '^', color='blue', markersize=8)
                ax2.plot(data.index[data['RSI_Signal'] == 'Sell'], data['RSI'][data['RSI_Signal'] == 'Sell'], 'v', color='orange', markersize=8)
                ax2.set_title("RSI (14)")
                ax2.legend()
                st.pyplot(fig2)

                # Table & download
                st.subheader("📄 Signal Table")
                st.dataframe(data[['Close', 'EMA_12', 'EMA_26', 'RSI', 'EMA_Signal', 'RSI_Signal']].tail(20))

                st.download_button(
                    label="⬇️ Download CSV with EMA/RSI Signals",
                    data=data.to_csv().encode(),
                    file_name=f"{user_input.upper()}_ema_signals.csv",
                    mime='text/csv'
                )

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
