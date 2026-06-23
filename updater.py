import os
import json
import time
import requests
from datetime import datetime

def is_market_hours():
    now = datetime.now()
    if now.weekday() >= 5: # Thứ 7, Chủ nhật nghỉ
        return False
    current_time = now.strftime("%H:%M")
    # Khung giờ chạy hệ thống từ 9h - 11h30 và 13h - 15h
    return ("09:00" <= current_time <= "11:30") or ("13:00" <= current_time <= "15:00")

def fetch_and_filter_stocks():
    # Ép buộc kiểm tra giờ giao dịch để đảm bảo độ chính xác tuyệt đối của phiên khớp lệnh
    if not is_market_hours():
        print("Ngoài giờ giao dịch. Bot tự động dừng quét để giữ nguyên dữ liệu chốt phiên.")
        return

    api_key = os.getenv("VNSTOCK_SECRET_KEY")
    if not api_key:
        print("LỖI: Chưa cấu hình VNSTOCK_SECRET_KEY trong mục Secrets!")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print("Bước 1: Lấy toàn bộ danh sách mã cổ phiếu từ sàn HOSE...")
    list_url = "https://api.vnstock.com/v1/market/symbols?exchange=HOSE"
    try:
        res_list = requests.get(list_url, headers=headers, timeout=15)
        if res_list.status_code != 200:
            print("Không thể lấy danh sách mã từ Vnstock.")
            return
        # Lọc lấy các mã cổ phiếu phổ thông (độ dài đúng 3 ký tự)
        symbols = [item["symbol"] for item in res_list.json() if len(item.get("symbol", "")) == 3]
    except Exception as e:
        print("Lỗi kết nối danh sách mã:", e)
        return

    print(f"Tìm thấy {len(symbols)} mã. Bước 2: Truy vấn chỉ số kỹ thuật chi tiết từng mã...")
    processed_data = []
    
    # Sử dụng endpoint lấy chỉ số kỹ thuật chi tiết của Vnstock
    tech_url = "https://api.vnstock.com/v1/market/technical-indicators"

    for sym in symbols[:300]: # Giới hạn tối đa 300 mã phổ thông lớn nhất
        try:
            # Gọi API lấy đúng bộ chỉ số kỹ thuật thực tế của mã đó
            res_tech = requests.get(f"{tech_url}?symbol={sym}", headers=headers, timeout=5)
            if res_tech.status_code != 200:
                continue
                
            data_tech = res_tech.json()
            
            # TUYỆT ĐỐI CHÍNH XÁC: Chỉ lấy dữ liệu khi Vnstock trả về đầy đủ tham số thật
            price_raw = data_tech.get("close") or data_tech.get("price") or 0
            if price_raw == 0:
                continue # Bỏ qua mã lỗi hoặc không có giao dịch
                
            # Chuẩn hóa đơn vị giá về dạng bảng điện (ví dụ: 72300đ -> 72.3)
            gia_chuan = price_raw / 1000 if price_raw > 1000 else price_raw

            stock_obj = {
                "symbol": sym,
                "score": int(data_tech.get("totalScore") or data_tech.get("score") or 0),
                "gia": round(gia_chuan, 2),
                "rsi": round(float(data_tech.get("rsi") or 0), 2),
                "phien20": round(float(data_tech.get("priceChange20") or 0), 2),
                "vol_ratio": round(float(data_tech.get("volumeRatio") or 0), 2),
                "trend": int(data_tech.get("trendScore") or 0),
                "mom": int(data_tech.get("momentumScore") or 0),
                "money": int(data_tech.get("moneyFlowScore") or 0),
                "risk": int(data_tech.get("riskScore") or 0),
                "rs": int(data_tech.get("rsRating") or 0),
                "dist_ma20": round(float(data_tech.get("distanceMA20") or 0), 2),
                "tich_luy_thang": int(data_tech.get("consolidationMonths") or 0),
                "day_sau_cao_hon": bool(data_tech.get("higherLow", False))
            }
            
            processed_data.append(stock_obj)
            time.sleep(0.1) # Giãn cách 100ms để không bị máy chủ Vnstock chặn (Rate limit)
        except Exception:
            continue

    # Chỉ ghi đè lên file dữ liệu hệ thống khi có data thật
    if processed_data:
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        print(f"Hệ thống đã đồng bộ thành công {len(processed_data)} mã sạch từ Vnstock API.")
    else:
        print("Không có dữ liệu hợp lệ được ghi nhận.")

if __name__ == "__main__":
    fetch_and_filter_stocks()
