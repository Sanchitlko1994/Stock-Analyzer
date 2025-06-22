import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import openai
import os

# -------------------------------
# Set OpenAI API Key (securely)
# -------------------------------
openai.api_key = st.secrets.get("openai_api_key") or os.getenv("OPENAI_API_KEY")

# -------------------------------
# Page Configuration
# -------------------------------
st.set_page_config(page_title="Stock Analyzer + AI", layout="wide")
st.title("📊 Stock Analyzer with GPT Chatbot")

# -------------------------------
# Sidebar - Stock Inputs
# -------------------------------
user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "TCS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

def format_ticker(ticker):
    if "." not in ticker:
        return ticker.strip().upper() + ".NS"
    return ticker.strip().upper()

ticker = format_ticker(user_input)

@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df = df.dropna()
    return df

# -------------------------------
# Stock Analyzer Logic
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
                sma_20 = ta.trend.SMAIndicator(close=close_prices, window=20).sma_indicator()
                rsi_14 = ta.momentum.RSIIndicator(close=close_prices, window=14).rsi()

                data['SMA_20'] = sma_20
                data['RSI'] = rsi_14

                st.subheader(f"📈 {user_input.upper()} Price Chart with SMA")
                fig, ax = plt.subplots(figsize=(12, 6))
                ax.plot(data.index, data['Close'], label='Close Price')
                ax.plot(data.index, data['SMA_20'], label='SMA 20', linestyle='--')
                ax.set_title(f"{user_input.upper()} - Price with SMA")
                ax.legend()
                st.pyplot(fig)

                st.subheader("📉 RSI Indicator")
                fig2, ax2 = plt.subplots(figsize=(12, 3))
                ax2.plot(data.index, data['RSI'], label='RSI', color='green')
                ax2.axhline(70, linestyle='--', color='red')
                ax2.axhline(30, linestyle='--', color='blue')
                ax2.set_title("RSI (14)")
                ax2.legend()
                st.pyplot(fig2)

                st.subheader("📄 Sample Data")
                st.dataframe(data.tail(10))

                st.download_button(
                    label="⬇️ Download CSV",
                    data=data.to_csv().encode(),
                    file_name=f"{user_input.upper()}_data.csv",
                    mime='text/csv'
                )
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# -------------------------------
# AI Chatbot Powered by GPT
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Ask AI Assistant")

# Chat history state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "system", "content": "You are a helpful financial assistant. Explain concepts like RSI, SMA, stock charts, etc. Be clear and concise."}
    ]

# User input
user_question = st.sidebar.text_input("Your question")

# Send question to GPT and get response
def ask_openai(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo"
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"Error: {str(e)}"

# Process user input
if user_question:
    st.session_state.chat_messages.append({"role": "user", "content": user_question})
    gpt_reply = ask_openai(st.session_state.chat_messages)
    st.session_state.chat_messages.append({"role": "assistant", "content": gpt_reply})

# Display chat history
for msg in st.session_state.chat_messages[1:]:  # skip system message
    speaker = "🧑 You" if msg["role"] == "user" else "🤖 GPT"
    st.sidebar.markdown(f"**{speaker}:** {msg['content']}")
