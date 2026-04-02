            # 原本可能只有這行
            # price = round(res['Close'].iloc[-1], 2)
            
            # ✨ 改成這樣：確保抓到的是最新的一個「有數字」的價格
            last_valid_row = res.dropna(subset=['Close']).iloc[-1]
            price = round(float(last_valid_row['Close']), 2)
