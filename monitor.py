import yfinance as yf
import pandas as pd
import requests
import os

# ================= 1. 設定區 (從 GitHub Secrets 讀取) =================
TG_TOKEN = os.environ.get("TG_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

# ================= 2. 功能定義區 (必須放在最前面) =================

def send_tg(msg):
    """發送 Telegram 訊息的功能"""
    if not TG_TOKEN or not TG_CHAT_ID:
        print(f"⚠️ 金鑰缺失，無法發送訊息: {msg}")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"❌ TG 發送失敗: {e}")

def my_logic(df, rsi_limit, vol_limit):
    """策略邏輯功能"""
    df = df.copy()
    # 均線
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / (loss + 0.0001))))
    # 成交量均線
    df['VolMA'] = df['Volume'].rolling(window=20).mean()
    
    df['Signal'] = 0
    pos = 0
    for i in range(20, len(df)):
        # 買入條件
        cond = (df['MA10'].iloc[i] > df['MA20'].iloc[i]) and \
               (df['RSI'].iloc[i] > rsi_limit) and \
               (df['Volume'].iloc[i] > df['VolMA'].iloc[i] * (vol_limit/10))
        
        if pos == 0 and cond:
            pos = 1
        elif pos == 1 and df['Close'].iloc[i] < df['MA20'].iloc[i]:
            pos = 0
        df.iloc[i, df.columns.get_loc('Signal')] = pos
    return df

# ================= 3. 主執行程序 (最後才執行) =================

if __name__ == "__main__":
    # 📝 監控清單
    watch_list = [
        {"name": "比特幣", "id": "BTC-USD", "p1": 60, "p2": 15},
        {"name": "以太幣", "id": "ETH-USD", "p1": 60, "p2": 15},
        {"name": "0050 (台灣50)", "id": "0050.TW", "p1": 55, "p2": 11},
        {"name": "S&P 500 (SPY)", "id": "SPY", "p1": 58, "p2": 12},
        {"name": "輝達 (NVDA)", "id": "NVDA", "p1": 65, "p2": 13}
    ]

    send_tg("🔍 <b>多標的行情監控系統啟動...</b>")
    
    for item in watch_list:
        try:
            print(f"📡 正在檢查 {item['name']}...")
            data = yf.Ticker(item['id']).history(period="1mo")
            if data.empty:
                continue
            
            data.index = data.index.tz_localize(None)
            res = my_logic(data, item['p1'], item['p2'])
            
            # ✨ 修正 nan 價格的問題
            last_valid = res.dropna(subset=['Close']).iloc[-1]
            price = round(float(last_valid['Close']), 2)
            now_sig = int(last_valid['Signal'])
            
            # 取得前一天的訊號判斷交叉
            pre_sig = int(res['Signal'].iloc[-2]) if len(res) > 1 else now_sig
            
            status = "📈 持有中" if now_sig == 1 else "💤 空手中"
            
            # 訊號發送
            if now_sig == 1 and pre_sig == 0:
                send_tg(f"🚀 <b>【買進訊號】</b>\n標的: {item['name']}\n價格: {price}")
            elif now_sig == 0 and pre_sig == 1:
                send_tg(f"🩸 <b>【賣出訊號】</b>\n標的: {item['name']}\n價格: {price}")
            else:
                send_tg(f"✅ {item['name']}: {price} ({status})")
                
        except Exception as e:
            print(f"❌ {item['name']} 錯誤: {e}")
