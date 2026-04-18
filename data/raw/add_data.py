import pandas as pd
import random

# 1. Định nghĩa bộ từ điển từ khóa theo từng Aspect
data_pool = {
    "App": {
        "targets": ["ứng dụng", "app", "phần mềm", "giao diện", "tính năng"],
        "positive": ["rất mượt", "dễ dùng", "đẹp mắt", "tốc độ nhanh", "vượt trội"],
        "negative": ["hay lag", "khó dùng", "nặng máy", "nhiều lỗi", "rất tệ"],
        "neutral": ["bình thường", "tạm ổn", "cần cập nhật thêm", "vừa đủ dùng"]
    },
    "Ship": {
        "targets": ["giao hàng", "ship", "vận chuyển", "shipper", "thời gian giao"],
        "positive": ["nhanh chóng", "đúng hạn", "siêu tốc", "nhiệt tình", "cẩn thận"],
        "negative": ["quá lâu", "chậm trễ", "lâu kinh khủng", "thái độ kém", "không đúng hẹn"],
        "neutral": ["tạm được", "không nhanh không chậm", "bình thường", "như mọi khi"]
    },
    "Price": {
        "targets": ["giá", "giá tiền", "chi phí", "tầm giá", "số tiền bỏ ra"],
        "positive": ["rất rẻ", "hợp lý", "đáng đồng tiền", "quá hời", "phải chăng"],
        "negative": ["quá mắc", "đắt đỏ", "không xứng đáng", "hơi cao", "chát quá"],
        "neutral": ["tầm trung", "bình ổn", "chấp nhận được", "ổn so với thị trường"]
    }
}

# 2. Bộ khung câu (Templates) để tạo sự tự nhiên
sentence_templates = [
    "{target} {context}.",
    "Mình thấy {target} {context}, nên mua.",
    "Thực sự thì {target} {context} quá.",
    "Đánh giá 5 sao vì {target} {context}.",
    "Cá nhân mình cảm thấy {target} {context}.",
    "Dù mọi thứ ổn nhưng {target} {context}."
]

def generate_absa_data(num_samples=1000):
    generated_data = []
    
    # Chia đều số lượng cho các Aspect cần bù đắp
    aspects_to_gen = list(data_pool.keys())
    samples_per_aspect = num_samples // len(aspects_to_gen)
    
    for aspect in aspects_to_gen:
        for _ in range(samples_per_aspect):
            # Chọn ngẫu nhiên cảm xúc (ưu tiên Neutral và Positive nếu tập cũ đang thiếu)
            sentiment_choice = random.choice(["positive", "negative", "neutral"])
            sentiment_map = {"negative": 0, "positive": 1, "neutral": 2}
            
            target = random.choice(data_pool[aspect]["targets"])
            context = random.choice(data_pool[aspect][sentiment_choice])
            template = random.choice(sentence_templates)
            
            full_text = template.format(target=target, context=context)
            
            # Lưu cấu trúc giống như Dataset gốc để dễ dàng gộp vào
            generated_data.append({
                "text": full_text,
                "aspect": aspect,
                "target": target,
                "sentiment": sentiment_map[sentiment_choice]
            })
            
    return pd.DataFrame(generated_data)

# 3. Chạy và lưu kết quả
df_synthetic = generate_absa_data(1000)
df_synthetic.to_csv("synthetic_data.csv", index=False, encoding="utf-8-sig")

print(f"✅ Đã sinh xong {len(df_synthetic)} câu!")
print(df_synthetic.head())