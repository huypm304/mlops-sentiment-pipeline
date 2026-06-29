from google_play_scraper import Sort, reviews
import pandas as pd
from underthesea import text_normalize, word_tokenize
import re
import os
import random

# ==========================================
# 1. CONFIG
# ==========================================

APPS = {
    "Shopee": "com.shopee.vn",
    "Lazada": "com.lazada.android",
    "Tiki": "vn.tiki.app.tikiandroid",
}

REVIEWS_PER_APP = 6000

# ==========================================
# 2. TEENCODE DICTIONARY
# ==========================================

TEENCODE_DICT = {
    "ko":"không","k":"không","cx":"cũng","dc":"được","đc":"được",
    "sp":"sản phẩm","shop":"cửa hàng","rep":"trả lời",
    "ib":"nhắn tin","tks":"cảm ơn","thks":"cảm ơn",
    "đvvc":"đơn vị vận chuyển"
}

# ==========================================
# 3. SENTIMENT KEYWORDS
# ==========================================

POSITIVE_WORDS = [
    "tốt","nhanh","ok","ổn","tuyệt","hài lòng","đẹp",
    "chuẩn","uy tín","rất thích","giao nhanh"
]

NEGATIVE_WORDS = [
    "tệ","lag","lỗi","chậm","bực","không được",
    "lừa đảo","rởm","hỏng","thất vọng","kém",
    "không giao","không nhận","treo máy"
]

POSITIVE_EMOJI = ["😍","❤️","👍","😊","🔥","🥰"]
NEGATIVE_EMOJI = ["😡","😭","👎","🤬","😠"]

SPAM_KEYWORDS = [
    "nhận xu","tuyển ctv","link bio","zalo","telegram"
]

# ==========================================
# 4. CLEAN TEXT
# ==========================================

def clean_text(text):

    text = str(text).lower()

    # remove link
    text = re.sub(r"http\S+|www\S+", "", text)

    # normalize repeated chars (đẹpppp -> đẹp)
    text = re.sub(r"(.)\1{2,}", r"\1", text)

    # remove special chars
    text = re.sub(r"[^\w\s]", " ", text)

    # teencode convert
    words = [TEENCODE_DICT.get(w, w) for w in text.split()]

    return " ".join(words)

# ==========================================
# 5. GARBAGE FILTER
# ==========================================

def is_garbage(text):

    text = str(text).lower()

    if len(text.split()) < 2:
        return True

    if any(s in text for s in SPAM_KEYWORDS):
        return True

    return False

# ==========================================
# 6. HYBRID LABELING
# ==========================================

NEGATION_WORDS = ["không","ko","k","chẳng","chả"]

def hybrid_label(row):

    text = str(row["content"]).lower()
    star = row["score"]

    # NEGATION + positive word → negative
    for neg in NEGATION_WORDS:
        for pos in POSITIVE_WORDS:
            if f"{neg} {pos}" in text:
                return "negative"

    # negative emoji
    if any(e in text for e in NEGATIVE_EMOJI):
        return "negative"

    # positive emoji
    if any(e in text for e in POSITIVE_EMOJI):
        return "positive"

    # negative keywords
    if any(w in text for w in NEGATIVE_WORDS):
        return "negative"

    # positive keywords
    if any(w in text for w in POSITIVE_WORDS):
        return "positive"

    # fallback star rating
    if star >= 4:
        return "positive"
    elif star == 3:
        return "neutral"
    else:
        return "negative"

# ==========================================
# 7. CRAWL DATA
# ==========================================

print("🚀 Crawling reviews...")

all_reviews = []

for name, app in APPS.items():

    print(f"→ {name}")

    try:

        result, _ = reviews(
            app,
            lang="vi",
            country="vn",
            sort=Sort.NEWEST,
            count=REVIEWS_PER_APP
        )

        for r in result:

            all_reviews.append({
                "app": name,
                "content": r["content"],
                "score": r["score"]
            })

    except Exception as e:

        print("Error:", e)

print("Total raw:", len(all_reviews))

# ==========================================
# 8. DATAFRAME CLEANING
# ==========================================

df = pd.DataFrame(all_reviews)

df = df.dropna(subset=["content"])
df = df.drop_duplicates(subset=["content"])

df = df[~df["content"].apply(is_garbage)]

print("After cleaning:", len(df))

# ==========================================
# 9. LABELING
# ==========================================

print("Labeling sentiment...")

df["sentiment"] = df.apply(hybrid_label, axis=1)

print(df["sentiment"].value_counts())

# ==========================================
# 10. TEXT PROCESSING
# ==========================================

print("Cleaning text...")

df["review_clean"] = df["content"].apply(clean_text)

print("Word segmentation...")

df["review_segmented"] = df["review_clean"].apply(
    lambda x: word_tokenize(x, format="text")
)

df["language"] = "vi"

# ==========================================
# 11. BALANCE DATASET
# ==========================================

print("Balancing dataset...")

pos = df[df.sentiment == "positive"]
neg = df[df.sentiment == "negative"]

min_size = min(len(pos), len(neg))

pos = pos.sample(min_size, random_state=42)
neg = neg.sample(min_size, random_state=42)

balanced_df = pd.concat([pos, neg])

print("Balanced size:", len(balanced_df))

# ==========================================
# 12. TRAIN TEST SPLIT
# ==========================================

test_size = int(len(balanced_df) * 0.15)

test_df = balanced_df.sample(test_size, random_state=99)

train_df = balanced_df.drop(test_df.index)

# ==========================================
# 13. SAVE DATASET
# ==========================================


train_path = "data/raw/train_dataset.csv"

train_df.to_csv(train_path, index=False, encoding="utf-8-sig")

print("\n🎉 DATASET READY")

print("\nTrain distribution")
print(train_df.sentiment.value_counts())

print("\nTest distribution")
print(test_df.sentiment.value_counts())

print("\nSaved:")
print(train_path)