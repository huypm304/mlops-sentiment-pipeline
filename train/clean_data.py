import pandas as pd
import re
from tqdm import tqdm

# 1. LOAD DATA
print("Đang nạp dữ liệu...")
train_df = pd.read_csv(r".\data\raw\train_dataset.csv")

# --- THÊM DÒNG NÀY ĐỂ FIX LỖI 'float' object has no attribute 'lower' ---
train_df['review_segmented'] = train_df['review_segmented'].fillna("").astype(str)
# -----------------------------------------------------------------------

label_map = {"negative": 0, "positive": 1}
train_df["original_label"] = train_df["sentiment"].map(label_map)


def detect_irrelevant(text):
    """
    Phát hiện review không liên quan đến sản phẩm
    """
    if pd.isna(text) or len(text.strip()) < 5:
        return True, "Too short"
    
    text_lower = text.lower()
    
    # 1. Spam patterns
    spam_patterns = [
        r'^\s*\.\s*$',  # Chỉ có dấu chấm
        r'^\s*ok\s*$',  # Chỉ có "ok"
        r'^\s*tốt\s*$', # Chỉ có "tốt"
        r'^\s*good\s*$',
        r'^\.+$',       # Chỉ có dấu chấm
    ]
    
    for pattern in spam_patterns:
        if re.match(pattern, text_lower):
            return True, "Spam/too simple"
    
    # 2. Off-topic (nói về platform, không về sản phẩm)
    offtopic_keywords = [
        r'shopee.*lazada',
        r'lazada.*shopee',
        r'tiki.*shopee',
        r'nên.*mua.*(\w+)\s+(shopee|lazada|tiki)',  # "nên qua lazada"
        r'chuyển.*sang.*(shopee|lazada|tiki)',
        r'không.*mua.*(shopee|lazada|tiki).*nữa',
    ]
    
    for pattern in offtopic_keywords:
        if re.search(pattern, text_lower):
            return True, "Off-topic (platform comparison)"
    
    # 3. Chỉ nói về giao hàng/admin (không về sản phẩm)
    delivery_only = [
        r'^(giao|ship|vận chuyển|admin|người bán)',
    ]
    
    has_product_mention = bool(re.search(
        r'(sản phẩm|hàng|chất lượng|đẹp|xấu|tốt|dở|kém)', 
        text_lower
    ))
    
    for pattern in delivery_only:
        if re.match(pattern, text_lower) and not has_product_mention:
            return True, "Only about delivery/admin"
    
    return False, "Valid"

def should_be_neutral(text, score):
    """
    Xác định review có nên được gán NEUTRAL không
    """
    text_lower = text.lower()
    
    # 1. Score = 3 + text mơ hồ
    if score == 3:
        vague_patterns = [
            r'^\s*(bình thường|tạm|ok|ổn)\s*$',
            r'không.*đặc biệt',
            r'cũng.*được',
            r'tạm.*được',
        ]
        for pattern in vague_patterns:
            if re.search(pattern, text_lower):
                return True, "Score 3 + vague text"
    
    # 2. Có cả positive VÀ negative mạnh
    has_strong_pos = bool(re.search(
        r'(tuyệt vời|xuất sắc|rất tốt|hoàn hảo|yêu thích)', 
        text_lower
    ))
    has_strong_neg = bool(re.search(
        r'(tệ|dở|kém|thất vọng|hỏng|lỗi)', 
        text_lower
    ))
    
    if has_strong_pos and has_strong_neg:
        return True, "Mixed strong sentiments"
    
    # 3. Neutral expressions
    neutral_patterns = [
        r'không.*tốt.*không.*xấu',
        r'cũng.*được.*thôi',
        r'bình.*thường',
        r'tạm.*ổn',
    ]
    
    for pattern in neutral_patterns:
        if re.search(pattern, text_lower):
            return True, "Neutral expression"
    
    return False, "Not neutral"

# ==============================
# 3. ÁP DỤNG PHÁT HIỆN
# ==============================
print("\n🔍 Đang phân tích các mẫu...")

results = []
for idx, row in tqdm(train_df.iterrows(), total=len(train_df)):
    text = row['review_segmented']
    score = row['score']
    
    is_irrelevant, irr_reason = detect_irrelevant(text)
    is_neutral, neu_reason = should_be_neutral(text, score)
    
    results.append({
        'is_irrelevant': is_irrelevant,
        'irrelevant_reason': irr_reason,
        'is_neutral': is_neutral,
        'neutral_reason': neu_reason
    })

result_df = pd.DataFrame(results)
train_df = pd.concat([train_df, result_df], axis=1)

# ==============================
# 4. THỐNG KÊ
# ==============================
print("\n" + "="*80)
print("📊 KẾT QUẢ PHÂN TÍCH")
print("="*80)

n_irrelevant = train_df['is_irrelevant'].sum()
n_neutral = train_df['is_neutral'].sum()
n_clean = len(train_df) - n_irrelevant - n_neutral

print(f"\n✅ Clean (Pos/Neg rõ ràng): {n_clean} ({n_clean/len(train_df)*100:.1f}%)")
print(f"⚠️  Neutral: {n_neutral} ({n_neutral/len(train_df)*100:.1f}%)")
print(f"❌ Irrelevant: {n_irrelevant} ({n_irrelevant/len(train_df)*100:.1f}%)")

# ==============================
# 5. TẠO 3 DATASETS
# ==============================

# OPTION 1: 2 classes (loại bỏ neutral & irrelevant)
df_binary = train_df[
    ~train_df['is_irrelevant'] & 
    ~train_df['is_neutral']
].copy()
df_binary['label'] = df_binary['sentiment'].map({'negative': 0, 'positive': 1})
df_binary.to_csv(r".\data\processed\train_binary_clean.csv", index=False)
print(f"\nBinary (2 classes): {len(df_binary)} mẫu → train_binary_clean.csv")

# OPTION 2: 3 classes
df_3class = train_df.copy()
def assign_3class_label(row):
    if row['is_irrelevant']:
        return None  # Sẽ bỏ sau
    if row['is_neutral']:
        return 1  # Neutral
    if row['sentiment'] == 'negative':
        return 0  # Negative
    if row['sentiment'] == 'positive':
        return 2  # Positive

df_3class['label_3class'] = df_3class.apply(assign_3class_label, axis=1)
df_3class = df_3class[df_3class['label_3class'].notna()].copy()
df_3class['label'] = df_3class['label_3class'].astype(int)
df_3class['sentiment_3class'] = df_3class['label'].map({
    0: 'negative',
    1: 'neutral', 
    2: 'positive'
})
df_3class.to_csv(r".\data\processed\train_3class.csv", index=False)
print(f"3-class: {len(df_3class)} mẫu → train_3class.csv")
print(f"   Phân bố: {df_3class['sentiment_3class'].value_counts().to_dict()}")

# Files riêng
irrelevant_df = train_df[train_df['is_irrelevant']].copy()
irrelevant_df.to_csv(r".\data\processed\irrelevant_samples.csv", index=False)

neutral_df = train_df[train_df['is_neutral'] & ~train_df['is_irrelevant']].copy()
neutral_df.to_csv(r".\data\processed\neutral_samples.csv", index=False)

# ==============================
# 6. HIỂN THỊ VÍ DỤ
# ==============================
print("\n" + "="*80)
print("VÍ DỤ IRRELEVANT:")
print("="*80)
for idx, row in irrelevant_df.head(5).iterrows():
    print(f"\n'{row['review_segmented'][:100]}'")
    print(f"   Score: {row['score']} | Lý do: {row['irrelevant_reason']}")

print("\n" + "="*80)
print("VÍ DỤ NEUTRAL:")
print("="*80)
for idx, row in neutral_df.head(5).iterrows():
    print(f"\n'{row['review_segmented'][:100]}'")
    print(f"   Score: {row['score']} | Lý do: {row['neutral_reason']}")

# ==============================
# 7. XỬ LÝ CASE ĐẶC BIỆT
# ==============================
print("\n" + "="*80)
print("="*80)

special_case = train_df[
    train_df['review_segmented'].str.contains('shopee.*lazada|lazada.*shopee', 
                                               case=False, 
                                               regex=True, 
                                               na=False)
].head(10)

print(f"\nTìm thấy {len(special_case)} mẫu tương tự:")
for idx, row in special_case.iterrows():
    print(f"\n'{row['review_segmented'][:100]}'")
    print(f"   Score: {row['score']} | Original: {row['sentiment']}")
    print(f"   → Irrelevant: {row['is_irrelevant']} ({row['irrelevant_reason']})")

# ==============================
# 8. KHUYẾN NGHỊ
# ==============================
print("\n" + "="*80)
print("KHUYẾN NGHỊ:")
print("="*80)

irrelevant_ratio = n_irrelevant / len(train_df)
neutral_ratio = n_neutral / len(train_df)

if irrelevant_ratio > 0.05:
    print(f"Có {irrelevant_ratio*100:.1f}% mẫu irrelevant (>5%)")
    print("   → NÊN loại bỏ để tránh nhiễu")

if neutral_ratio > 0.15:
    print(f"\nCó {neutral_ratio*100:.1f}% mẫu neutral (>15%)")
    print("   → CÂN NHẮC dùng 3-class model")
    print("   → HOẶC loại bỏ nếu muốn binary classification rõ ràng")
else:
    print(f"\nTỷ lệ neutral thấp ({neutral_ratio*100:.1f}%)")
    print("   → Có thể dùng 2-class model")

print("\nQUYẾT ĐỊNH:")
print("1. Nếu mục tiêu: Phân loại tích cực/tiêu cực RÕ RÀNG")
print("   → Dùng train_binary_clean.csv (đã loại neutral)")
print("\n2. Nếu muốn: Xử lý cả trường hợp mơ hồ")
print("   → Dùng train_3class.csv (3 classes)")
print("\n3. Case 'cay cú shopee... lazada...':")
print("   → Đã được đánh dấu IRRELEVANT")
print("   → KHÔNG nên dùng vì không review sản phẩm")