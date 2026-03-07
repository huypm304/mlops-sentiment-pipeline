from google_play_scraper import Sort, reviews
import pandas as pd
from underthesea import word_tokenize
import re
import os

# --- 1. Cấu hình & Từ điển Teencode ---
app_list = [
    'com.shopee.vn', 'com.lazada.android', 'vn.tiki.app.tikiandroid',
    'com.garena.game.kgvn', 'com.dts.freefireth'
]

teencode_dict = {
    "cx": "cũng", "ko": "không", "k": "không", "ng": "người",
    "chs": "chơi", "dc": "được", "dell": "không", "dm": "tệ",
    "lagg": "lag", "r": "rồi", "acc": "tài khoản", "sv": "người chơi"
}

# --- 2. Các hàm bổ trợ ---
def clean_teencode(text):
    text = text.lower()
    # Xóa ký tự đặc biệt & Emoji
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()
    words = [teencode_dict.get(w, w) for w in words]
    return " ".join(words)

def segment_text(text):
    # PhoBERT cần format word_tokenize (máy_tính, giao_hàng)
    return word_tokenize(text, format="text")

def convert_sentiment(score):
    if score >= 4: return "positive"
    elif score == 3: return "neutral"
    else: return "negative"

# --- 3. Thu thập dữ liệu (Scraping) ---
final_df = pd.DataFrame()

for app_id in app_list:
    print(f"Đang lấy dữ liệu từ: {app_id}")
    try:
        result, _ = reviews(
            app_id, lang='vi', country='vn',
            sort=Sort.NEWEST, count=500
        )
        temp_df = pd.DataFrame(result)[['content', 'score']]
        temp_df['app_source'] = app_id
        final_df = pd.concat([final_df, temp_df], ignore_index=True)
    except Exception as e:
        print(f"Lỗi khi crawl {app_id}: {e}")

# --- 4. Tiền xử lý dữ liệu (Preprocessing) ---
print("🧹 Đang thực hiện tiền xử lý dữ liệu...")

# Loại bỏ hàng rỗng và trùng
final_df = final_df.dropna(subset=["content"]).drop_duplicates(subset=["content"])

# Gán nhãn Sentiment và Language
final_df["sentiment"] = final_df["score"].apply(convert_sentiment)
final_df["language"] = "vi"

# Clean teencode và Segment 
final_df["review_text_clean"] = final_df["content"].apply(lambda x: clean_teencode(str(x)))
final_df["review_text_segmented"] = final_df["review_text_clean"].apply(segment_text)

# --- 5. Lưu trữ ---
output_dir = 'data/processed'
output_path = os.path.join(output_dir, 'reviews_vi_final.csv')

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"📁 Đã tạo thư mục mới: {output_dir}")

final_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"HOÀN THÀNH! Tổng cộng: {len(final_df)} review.")
print(f"File lưu tại: {output_path}")