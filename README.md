# Stock-Analyzer
# 📊 Stock Analyzer Web App

A simple web-based stock analyzer built with Streamlit and Python. Enter a stock ticker to view price charts, technical indicators like RSI and SMA, and download historical data.

## 🚀 Features
- Fetch historical data with `yfinance`
- Display price chart + 20-day SMA
- Plot RSI indicator
- Download CSV report
- Ready to deploy on Streamlit Cloud or Render

## 🔧 Install Locally

```bash
pip install -r requirements.txt
streamlit run stock_analyzer_app.py
```

## 🌐 Deploy on Streamlit Cloud
1. Fork this repo
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect to GitHub and deploy

## 📦 Deploy on Render
1. Create a new web service at [render.com](https://render.com)
2. Use this repo and `render.yaml`

## ✅ Example Tickers
- US: `AAPL`, `MSFT`, `TSLA`
- India: `TCS.NS`, `RELIANCE.NS`, `INFY.NS`
