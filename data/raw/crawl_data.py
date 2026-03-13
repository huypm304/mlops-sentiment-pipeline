from google_play_scraper import Sort, reviews
import pandas as pd
from underthesea import word_tokenize
import re
import os

# --- 1. Cấu hình & Từ điển Teencode mở rộng ---
app_list = [
    'com.shopee.vn', 'com.lazada.android', 'vn.tiki.app.tikiandroid'
]

# Thêm một số từ phổ biến và rác
teencode_dict = {
    "cx": "cũng", "ko": "không", "k": "không", "ng": "người",
    "chs": "chơi", "dc": "được", "dell": "không", "dm": "tệ",
    "lagg": "lag", "r": "rồi", "acc": "tài khoản", "sv": "người chơi",
    "shop": "cửa hàng", "st": "số điện thoại", "rep": "phản hồi"
}

# --- 2. Các hàm tiền xử lý nâng cao ---

def advanced_clean(text):
    if not isinstance(text, str) or len(text.strip()) == 0:
        return None
    
    # a. Chuyển về chữ thường
    text = text.lower()
    
    # b. Xử lý ký tự lặp lại (ví dụ: ngonnnnn -> ngon, lagg -> lag)
    # Tìm bất kỳ ký tự nào lặp lại từ 3 lần trở lên và rút gọn còn 1
    text = re.sub(r'([a-z])\1{2,}', r'\1', text)
    
    # c. Xóa ký tự đặc biệt, chỉ giữ lại chữ cái và số
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # d. Sửa lỗi teencode từ dictionary
    words = text.split()
    words = [teencode_dict.get(w, w) for w in words]
    
    # e. BỎ QUA review quá ngắn (dưới 3 từ thường không mang ý nghĩa aspect)
    if len(words) < 3:
        return None
        
    # f. Lọc bỏ các review rác/quảng cáo thường gặp
    junk_keywords = ['tuyển', 'zalo', 'kiếm tiền', 'nhập mã']
    clean_text = " ".join(words)
    if any(keyword in clean_text for keyword in junk_keywords):
        return None
        
    return clean_text

def segment_text(text):
    if text is None: return None
    return word_tokenize(text, format="text")

def convert_sentiment(score):
    if score >= 4: return "positive"
    elif score == 3: return "neutral"
    else: return "negative"

# --- 3. Thu thập dữ liệu ---
final_df = pd.DataFrame()

for app_id in app_list:
    print(f"Đang crawl dữ liệu: {app_id}")
    try:
        result, _ = reviews(
            app_id, lang='vi', country='vn',
            sort=Sort.NEWEST, count=1000 # Tăng lên 1000 để sau khi lọc vẫn đủ 5000 câu
        )
        temp_df = pd.DataFrame(result)[['content', 'score']]
        temp_df['app_source'] = app_id
        final_df = pd.concat([final_df, temp_df], ignore_index=True)
    except Exception as e:
        print(f"Lỗi {app_id}: {e}")

# --- 4. Deep Preprocessing ---
print("Bắt đầu quy trình Deep Cleaning...")

# Bước 1: Loại bỏ hàng rỗng ban đầu
final_df = final_df.dropna(subset=["content"])

# Bước 2: Áp dụng hàm Clean nâng cao (Lọc ngắn, lọc rác, sửa lỗi lặp)
final_df["review_text_clean"] = final_df["content"].apply(advanced_clean)

# Bước 3: Loại bỏ những hàng bị hàm Clean đánh dấu None (review < 3 từ, rác...)
final_df = final_df.dropna(subset=["review_text_clean"])

# Bước 4: Loại bỏ trùng lặp sau khi đã clean (tránh trường hợp "tốt" và "tốt!!!!" giống nhau)
final_df = final_df.drop_duplicates(subset=["review_text_clean"])

# Bước 5: Gán nhãn Sentiment và Word Segmentation
final_df["sentiment"] = final_df["score"].apply(convert_sentiment)
final_df["review_text_segmented"] = final_df["review_text_clean"].apply(segment_text)

# --- 5. Xuất dữ liệu ---
output_dir = 'data/processed'
output_path = os.path.join(output_dir, 'reviews_vi_clean_v2.csv')

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

final_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"XONG! Giữ lại được {len(final_df)} review chất lượng.")
print(f"File sẵn sàng demo tại: {output_path}")