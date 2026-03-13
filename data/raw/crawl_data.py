from google_play_scraper import Sort, reviews
import pandas as pd
from underthesea import text_normalize, word_tokenize
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

def clean_data(text):
    if not isinstance(text, str) or len(text.strip()) == 0:
        return None
    
    # 1. Chuẩn hóa tiếng Việt (Xử lý dấu, chính tả, một số teencode phổ biến)
    # Đây là chỗ "ăn tiền" nhất của underthesea
    text = text_normalize(text)
    
    # 2. Hạ chữ thường & Xử lý lặp ký tự (ngonnnnn -> ngon)
    text = text.lower()
    text = re.sub(r'([a-z])\1{2,}', r'\1', text)
    
    # 3. Xóa ký tự đặc biệt (trừ khoảng trắng)
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # 4. Áp dụng Dictionary của Huy (để fix những từ underthesea chưa cover)
    words = text.split()
    words = [teencode_dict.get(w, w) for w in words]
    
    # 5. Lọc độ dài
    if len(words) < 3:
        return None
        
    return " ".join(words)

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