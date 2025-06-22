import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import matplotlib.pyplot as plt
import os
from openai import OpenAI

# -------------------------------
# Load OpenAI API Key
# -------------------------------
openai_api_key = st.secrets.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(page_title="📊 Stock Analyzer + GPT Chatbot", layout="wide")
st.title("📊 Stock Analyzer with GPT-4 Chatbot")

# -------------------------------
# Sidebar: Inputs
# -------------------------------
user_input = st.sidebar.text_input("Stock Ticker (e.g., AAPL, TCS.NS)", "TCS")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

def format_ticker(ticker):
    if "." not in ticker:
        return ticker.strip().upper() + ".NS"
    return ticker.strip().upper()

ticker = format_ticker(user_input)

# -------------------------------
# Cache data download
# -------------------------------
@st.cache_data
def get_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    if not df.empty:
        df = df.dropna()
    return df

# -------------------------------
# Analyze button logic
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
# GPT-4 Chatbot Section (with token-saving)
# -------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("💬 Ask AI Assistant")

# Chat history memory
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "system", "content": "You are a helpful financial assistant. Answer clearly about stock indicators like RSI, SMA, and stock chart interpretation."}
    ]

MAX_CHAT_TURNS = 3  # Number of user-assistant exchanges to keep

# Function to call OpenAI API
def ask_gpt(messages):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # use gpt-3.5-turbo for lower cost
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Chat input
user_msg = st.sidebar.text_input("Your question")

if user_msg:
    # Add user message to full session history
    st.session_state.chat_messages.append({"role": "user", "content": user_msg})

    # Trim chat history to save tokens
    system_msg = st.session_state.chat_messages[0]
    chat_history = st.session_state.chat_messages[1:]
    trimmed_history = chat_history[-MAX_CHAT_TURNS * 2:]  # 2 messages per turn (user + assistant)

    messages_to_send = [system_msg] + trimmed_history

    # Get GPT response
    gpt_output = ask_gpt(messages_to_send)
    st.session_state.chat_messages.append({"role": "assistant", "content": gpt_output})

# Display chat history
st.sidebar.markdown("🧠 **Chat History**")
for msg in st.session_state.chat_messages[1:]:  # Skip system message
    role = "🧑 You" if msg["role"] == "user" else "🤖 GPT"
    st.sidebar.markdown(f"**{role}:** {msg['content']}")
