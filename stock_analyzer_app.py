import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import streamlit_authenticator as stauth
st.write(stauth.Hasher(['123']).generate())

# ---------- Authentication Setup ----------
credentials = {
    "usernames": {
        "sanchit1994": {
            "name": "Sanchit",
            "password": "$2b$12$moZ43RYXHDV4L0CV8xuWkOKLoOa2bUefKji5mwKWaGbx1Hj6YTK1y"
        },
        "shweta1995": {
            "name": "Shweta",
            "password": "$2b$12$tEgfH7RAmspS95T4wqsoQO9nt0oSPiAuYTrpSC6uUtJczzgT3MQIm"
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    "stock_dashboard",          # cookie name
    "abcdef1234567890",         # signature key
    cookie_expiry_days=1
)

# Corrected login call using keyword arguments
name, authentication_status, username = authenticator.login("Login", location="main")

# ---------- If Authenticated ----------
if authentication_status:
    st.set_page_config(page_title="Stock Analyzer", layout="wide")
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome, {name} 👋")

    st.title("📊 EMA-Based Stock Analyzer Dashboard")

    # Sidebar Inputs
    user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS)", "TCS")
    start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
    end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

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
                st.warning("No valid data found.")
            else:
                close = data['Close']

                if close.empty or len(close) < 50:
                    st.error("Not enough data for analysis.")
                else:
                    # Technical Indicators
                    data['EMA_12'] = ta.trend.EMAIndicator(close=close, window=12).ema_indicator()
                    data['EMA_26'] = ta.trend.EMAIndicator(close=close, window=26).ema_indicator()
                    data['RSI'] = ta.momentum.RSIIndicator(close=close, window=14).rsi()

                    # Buy/Sell Signals
                    data['EMA_Signal'] = ''
                    crossover_up = (data['EMA_12'] > data['EMA_26']) & (data['EMA_12'].shift(1) <= data['EMA_26'].shift(1))
                    crossover_down = (data['EMA_12'] < data['EMA_26']) & (data['EMA_12'].shift(1) >= data['EMA_26'].shift(1))
                    data.loc[crossover_up, 'EMA_Signal'] = 'Buy'
                    data.loc[crossover_down, 'EMA_Signal'] = 'Sell'

                    data['RSI_Signal'] = data['RSI'].apply(
                        lambda x: 'Buy' if x < 30 else ('Sell' if x > 70 else '')
                    )

                    # EMA Chart
                    st.subheader(f"📈 {user_input.upper()} Price with EMA Buy/Sell Signals")
                    fig, ax = plt.subplots(figsize=(14, 6))
                    ax.plot(data.index, data['Close'], label='Close')
                    ax.plot(data.index, data['EMA_12'], label='EMA 12', linestyle='--')
                    ax.plot(data.index, data['EMA_26'], label='EMA 26', linestyle=':')
                    ax.plot(data.index[data['EMA_Signal'] == 'Buy'], data['Close'][data['EMA_Signal'] == 'Buy'], '^', color='green', label='Buy', markersize=10)
                    ax.plot(data.index[data['EMA_Signal'] == 'Sell'], data['Close'][data['EMA_Signal'] == 'Sell'], 'v', color='red', label='Sell', markersize=10)
                    ax.set_title(f"{user_input.upper()} - EMA Crossover Signals")
                    ax.legend()
                    st.pyplot(fig)

                    # RSI Chart
                    st.subheader("📉 RSI Indicator with Buy/Sell Signals")
                    fig2, ax2 = plt.subplots(figsize=(12, 3))
                    ax2.plot(data.index, data['RSI'], label='RSI', color='green')
                    ax2.axhline(70, linestyle='--', color='red')
                    ax2.axhline(30, linestyle='--', color='blue')
                    ax2.plot(data.index[data['RSI_Signal'] == 'Buy'], data['RSI'][data['RSI_Signal'] == 'Buy'], '^', color='blue', markersize=8)
                    ax2.plot(data.index[data['RSI_Signal'] == 'Sell'], data['RSI'][data['RSI_Signal'] == 'Sell'], 'v', color='orange', markersize=8)
                    ax2.set_title("RSI (14)")
                    ax2.legend()
                    st.pyplot(fig2)

                    # Data Table and Export
                    st.subheader("📄 Latest Signal Table")
                    st.dataframe(data[['Close', 'EMA_12', 'EMA_26', 'RSI', 'EMA_Signal', 'RSI_Signal']].tail(20))

                    st.download_button(
                        label="⬇️ Download CSV",
                        data=data.to_csv().encode(),
                        file_name=f"{user_input.upper()}_signals.csv",
                        mime='text/csv'
                    )
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ---------- If Login Failed ----------
elif authentication_status is False:
    st.error("❌ Incorrect username or password")

# ---------- If Login Not Attempted ----------
elif authentication_status is None:
    st.info("Please log in to access the dashboard.")
