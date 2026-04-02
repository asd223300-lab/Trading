import yfinance as yf
import pandas as pd
import requests
import os

# 1. 讀取金鑰
TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# 2. 策略邏輯 (不變)
def my_logic(df, rsi_limit, vol_limit):
    df = df.copy()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss + 0.0001))) # 加微量避免除以0
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

# ================= 3. 複數監控執行區 =================
if __name__ == "__main__":
    # 📝 在這裡加入你想追蹤的所有標的
    # 台股記得加 .TW，美股直接打代號，幣圈加 -USD
       # 📝 複數監控清單
    watch_list = [
        {"name": "比特幣", "id": "BTC-USD", "p1": 60, "p2": 15},
        {"name": "以太幣", "id": "ETH-USD", "p1": 60, "p2": 15},
        {"name": "0050 (台灣50)", "id": "0050.TW", "p1": 55, "p2": 11},  # 台股波動較小，RSI 門檻降低一點
        {"name": "S&P 500 (SPY)", "id": "SPY", "p1": 58, "p2": 12},     # 美股大盤通常走長多，參數不宜過嚴
        {"name": "輝達 (NVDA)", "id": "NVDA", "p1": 65, "p2": 13}
    ]

    send_tg(f"🔍 <b>開始多標的掃描... (共 {len(watch_list)} 檔)</b>")

    for item in watch_list:
        try:
            print(f"正在檢查 {item['name']}...")
            data = yf.Ticker(item['id']).history(period="1mo")
            if data.empty:
                continue
            
            data.index = data.index.tz_localize(None)
            res = my_logic(data, item['p1'], item['p2'])
            
            now_sig = int(res['Signal'].iloc[-1])
            pre_sig = int(res['Signal'].iloc[-2])
            price = round(res['Close'].iloc[-1], 2)
            
            # 基本報時
            status = "📈 持有中" if now_sig == 1 else "💤 空手中"
            
            # 如果發生訊號交叉，給予強烈通知
            if now_sig == 1 and pre_sig == 0:
                send_tg(f"🚀 <b>【買進訊號】</b>\n標的：{item['name']} ({item['id']})\n價格：{price}")
            elif now_sig == 0 and pre_sig == 1:
                send_tg(f"🩸 <b>【賣出訊號】</b>\n標的：{item['name']} ({item['id']})\n價格：{price}")
            else:
                # 平常只傳簡單狀態
                send_tg(f"✅ {item['name']}：{price} ({status})")

        except Exception as e:
            send_tg(f"❌ {item['name']} 檢查失敗: {e}")
