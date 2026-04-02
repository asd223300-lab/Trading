import yfinance as yf
import pandas as pd
import requests
import os

# 1. 讀取金鑰
TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 2. 策略邏輯 (直接內建)
def my_logic(df, rsi_limit, vol_limit):
    df = df.copy()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    df['VolMA'] = df['Volume'].rolling(window=20).mean()
    df['Signal'] = 0
    pos = 0
    for i in range(20, len(df)):
        if pos == 0 and df['MA10'].iloc[i] > df['MA20'].iloc[i] and df['RSI'].iloc[i] > rsi_limit and df['Volume'].iloc[i] > df['VolMA'].iloc[i] * (vol_limit/10):
            pos = 1
        elif pos == 1 and df['Close'].iloc[i] < df['MA20'].iloc[i]:
            pos = 0
        df.iloc[i, df.columns.get_loc('Signal')] = pos
    return df

def send_tg(msg):
    if not TG_TOKEN: return
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"})

if __name__ == "__main__":
    send_tg("🚀 <b>重生測試：監控啟動！</b>")
    try:
        data = yf.Ticker("BTC-USD").history(period="1mo")
        res = my_logic(data, 60, 15)
        now_sig = int(res['Signal'].iloc[-1])
        status = "📈 持有中" if now_sig == 1 else "💤 空手中"
        send_tg(f"✅ BTC 檢查完畢\n價格: {round(res['Close'].iloc[-1], 2)}\n狀態: {status}")
    except Exception as e:
        send_tg(f"❌ 錯誤: {e}")
      
