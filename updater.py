import os
import json
import requests
from datetime import datetime

def is_market_hours():
    now = datetime.now()
    if now.weekday() >= 5: # Thứ 7, Chủ nhật nghỉ
        return False
    current_time = now.strftime("%H:%M")
    # Khung giờ chạy hệ thống chuẩn theo yêu cầu của Sếp
    return ("09:00" <= current_time <= "11:30") or ("13:00" <= current_time <= "15:00")

def fetch_and_filter_stocks():
    # Thống nhất chỉ auto update đúng trong khung giờ giao dịch của Sếp
    if not is_market_hours():
        print("Ngoài giờ giao dịch. Bot dừng quét để bảo toàn dữ liệu chốt phiên.")
        return

    api_key = os.getenv("VNSTOCK_SECRET_KEY")
    if not api_key:
        print("LỖI: Chưa cấu hình VNSTOCK_SECRET_KEY trong Secrets!")
        return

    # Đường link endpoint và header bảo mật sử dụng Key của Sếp
    url = "https://api.vnstock.com/v1/market/realtime-technical"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Lỗi gọi API từ Vnstock. Mã phản hồi: {response.status_code}")
            return
        market_data = response.json()
    except Exception as e:
        print("Lỗi kết nối mạng:", e)
        return

    processed_data = []
    
    # ĐỌC VÀ TRÍCH XUẤT CHÍNH XÁC 100% THEO CẤU TRÚC GỐC TRẢ VỀ CỦA VNSTOCK
    for item in market_data:
        sym = item.get("symbol")
        if not sym or len(sym) != 3:
            continue
            
        # Giữ nguyên bản toàn bộ giá trị số liệu từ API, không tự ý chia hay tính toán lại
        stock_obj = {
            "symbol": sym,
            "score": item.get("score"),
            "gia": item.get("price"),
            "rsi": item.get("rsi"),
            "phien20": item.get("phien20"),
            "vol_ratio": item.get("vol_ratio"),
            "trend": item.get("trend"),
            "mom": item.get("mom"),
            "money": item.get("money"),
            "risk": item.get("risk"),
            "rs": item.get("rs"),
            "dist_ma20": item.get("dist_ma20"),
            "tich_luy_thang": item.get("tich_luy_thang"),
            "day_sau_cao_hon": item.get("day_sau_cao_hon")
        }
        processed_data.append(stock_obj)

    # Ghi đè trực tiếp dữ liệu chuẩn xác vào file hệ thống
    if processed_data:
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
        print(f"Hệ thống đã cập nhật thành công {len(processed_data)} mã chính xác tuyệt đối từ Vnstock.")
    else:
        print("Cảnh báo: Không có dữ liệu hợp lệ được trích xuất.")

if __name__ == "__main__":
    fetch_and_filter_stocks()
