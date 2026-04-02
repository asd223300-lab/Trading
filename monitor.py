if __name__ == "__main__":
    # 📝 監控清單 (想增加標的，就照格式加在括號內)
    watch_list = [
        {"name": "比特幣", "id": "BTC-USD", "p1": 60, "p2": 15},
        {"name": "以太幣", "id": "ETH-USD", "p1": 60, "p2": 15},
        {"name": "0050 (台灣50)", "id": "0050.TW", "p1": 55, "p2": 11},
        {"name": "S&P 500 (SPY)", "id": "SPY", "p1": 58, "p2": 12},
    ]

    send_tg(f"🔍 <b>開始多標的行情掃描...</b>")
    
    for item in watch_list:
        try:
            print(f"📡 正在檢查 {item['name']}...")
            # 1. 抓取資料 (yf 會自動處理美股、台股與加密貨幣)
            data = yf.Ticker(item['id']).history(period="1mo")
            if data.empty:
                print(f"⚠️ 找不到 {item['name']} 的資料")
                continue
            
            data.index = data.index.tz_localize(None)
            
            # 2. 跑策略 (請確認你的函式名稱是 my_logic 或 run_mmp_logic)
            # 這裡統一使用 my_logic，請對照你之前的函式名稱
            res = my_logic(data, item['p1'], item['p2'])
            
            # 3. 取得訊號與價格
            now_sig = int(res['Signal'].iloc[-1])
            pre_sig = int(res['Signal'].iloc[-2])
                        # 原本可能只有這行
            # price = round(res['Close'].iloc[-1], 2)
            
            # ✨ 改成這樣：確保抓到的是最新的一個「有數字」的價格
            last_valid_row = res.dropna(subset=['Close']).iloc[-1]
            price = round(float(last_valid_row['Close']), 2)

            
            status = "📈 持有中" if now_sig == 1 else "💤 空手中"
            
            # 4. 判斷是否發送訊號
            if now_sig == 1 and pre_sig == 0:
                send_tg(f"🚀 <b>【買進訊號】</b>\n標的: {item['name']}\n價格: {price}")
            elif now_sig == 0 and pre_sig == 1:
                send_tg(f"🩸 <b>【賣出訊號】</b>\n標的: {item['name']}\n價格: {price}")
            else:
                # 平常只回報狀態，確認機器人還活著
                send_tg(f"✅ {item['name']}: {price} ({status})")
                
        except Exception as e:
            send_tg(f"❌ {item['name']} 執行錯誤: {str(e)}")
