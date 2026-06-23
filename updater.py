import os
import json
import requests
from datetime import datetime

def is_market_hours():
    now = datetime.now()
    # Kiểm tra nếu là Thứ 7 (5) hoặc Chủ Nhật (6) thì nghỉ
    if now.weekday() >= 5:
        return False
        
    current_time = now.strftime("%H:%M")
    morning_start = "09:00"
    morning_end = "11:30"
    afternoon_start = "13:00"
    afternoon_end = "15:00"
    
    # Kiểm tra nằm trong 2 khung giờ giao dịch chuẩn của Sếp
    if (morning_start <= current_time <= morning_end) or (afternoon_start <= current_time <= afternoon_end):
        return True
    return False

def fetch_and_filter_stocks():
    # Chỉ chạy khi trong giờ giao dịch
    if not is_market_hours():
        print("Ngoài giờ giao dịch hoặc ngày nghỉ. Bot tự động bỏ qua quét dữ liệu.")
        return

    api_key = os.getenv("VNSTOCK_SECRET_KEY")
    if not api_key:
        print("LỖI: Không tìm thấy VNSTOCK_SECRET_KEY trong Secrets!")
        return

    url = "https://api.vnstock.com/v1/market/realtime-technical"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"LỖI API: Vnstock trả về mã lỗi {response.status_code}")
            return
        market_data = response.json()
    except Exception as e:
        print("LỖI KẾT NỐI: Không thể kết nối tới API Vnstock:", e)
        return

    # Chỉ xử lý dữ liệu thật từ Vnstock, không thêm thắt ngẫu nhiên
    processed_data = []
    for item in market_data:
        sym = item.get("symbol")
        if not sym or len(sym) != 3:
            continue
            
        # Ánh xạ chuẩn xác tên trường dữ liệu từ Vnstock API của Sếp
        # Chia 1000 nếu API trả về đơn vị Đồng để hiển thị dạng 72.3 (72.300đ) đúng chuẩn bảng giá gốc
        price_raw = item.get("price") or item.get("closePrice") or item.get("matchPrice") or 0
        gia_hien_tai = float(price_raw) / 1000 if price_raw > 1000 else float(price_raw)
        
        stock_obj = {
            "symbol": sym,
            "score": int(item.get("score") or item.get("totalScore") or 0),
            "gia": round(gia_hien_tai, 2),
            "rsi": round(float(item.get("rsi") or 0), 2),
            "phien20": round(float(item.get("change20") or item.get("priceChange20") or 0), 2),
            "vol_ratio": round(float(item.get("volumeRatio") or item.get("volRatio") or 0), 2),
            "trend": int(item.get("trend") or item.get("trendScore") or 0),
            "mom": int(item.get("momentum") or item.get("momScore") or 0),
            "money": int(item.get("moneyFlow") or item.get("moneyScore") or 0),
            "risk": int(item.get("risk") or item.get("riskScore") or 0),
            "rs": int(item.get("rs") or item.get("rsRating") or 0),
            "dist_ma20": round(float(item.get("distanceMA20") or item.get("distMA20") or 0), 2),
            "tich_luy_thang": int(item.get("consolidationMonths") or item.get("baseWeeks", 0) // 4 or 0),
            "day_sau_cao_hon": bool(item.get("higherLow", False))
        }
        processed_data.append(stock_obj)

    # Chỉ ghi đè file khi có dữ liệu thật đổ về thành công
    if processed_data:
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        print(f"Đã cập nhật thành công {len(processed_data)} mã từ Vnstock API.")
    else:
        print("Cảnh báo: Dữ liệu API trả về trống hoặc lỗi cấu trúc trường thông tin.")

if __name__ == "__main__":
    fetch_and_filter_stocks()
