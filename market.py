import yfinance as yf
import pandas as pd
import numpy as np

def fetch_realtime_price(ticker):
    try: return yf.Ticker(ticker).fast_info['last_price']
    except: return 0.0

def fetch_history_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Fetch max history to find IPO price
        hist = stock.history(period="max", interval="1d")
        if not hist.empty:
            hist.index = hist.index.tz_localize(None)
            hist.reset_index(inplace=True)
        return hist, stock.info
    except: return pd.DataFrame(), {}

def fetch_latest_news(ticker):
    try:
        stock = yf.Ticker(ticker)
        news_list = stock.news
        if not news_list: return "NO LIVE NEWS AVAILABLE."
        headlines = [item['title'].upper() for item in news_list[:5]]
        return "  +++  ".join(headlines)
    except: return "NEWS FEED OFFLINE"

def get_listing_price(df):
    if not df.empty:
        return df.iloc[0]['Open']
    return 0.0

# --- THIS WAS MISSING ---
def add_technical_indicators(df):
    """
    Calculates technical indicators needed for prediction.py
    """
    data = df.copy()
    
    # Moving Averages
    data['MA_5'] = data['Close'].rolling(window=5).mean()
    data['MA_20'] = data['Close'].rolling(window=20).mean()
    
    # RSI
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    std_dev = data['Close'].rolling(20).std()
    data['BB_Upper'] = data['MA_20'] + (std_dev * 2)
    data['BB_Lower'] = data['MA_20'] - (std_dev * 2)
    
    # Lags for AI Features
    data['Lag_1'] = data['Close'].shift(1)
    data['Lag_2'] = data['Close'].shift(2)
    data['Lag_5'] = data['Close'].shift(5)
    
    return data.dropna()