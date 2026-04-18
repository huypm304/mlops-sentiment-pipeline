"""
Vietnamese Review Cleaning Pipeline for PhoBERT Sentiment Training
==================================================================
Fixes vs old script:
  - ViTokenizer runs FIRST, teencode replace runs on token list (fixes \b Unicode bug)
  - Dedup on raw comment BEFORE cleaning (avoid false dedup)
  - ok/oke removed from map (wrong semantic)
  - Repeated-sentence detection added
  - cmt, vl, vkl etc. fixed to not corrupt compound tokens
  - char-level repeated-word collapser (aaaaa -> a) applied before tokenize
  - Clean order: normalize → dedup_raw → tokenize → replace_teencode → finalize
"""

import pandas as pd
import re
import csv
import os
from tqdm import tqdm

try:
    from pyvi import ViTokenizer
    HAS_PYVI = True
except ImportError:
    HAS_PYVI = False
    print("⚠️  pyvi không tìm thấy — bỏ qua bước word segmentation")


# ============================================================
# 1. TEENCODE DICTIONARY
#    Chỉ chứa token-level replacements (1 token → 1 token/cụm)
#    KHÔNG chứa ok/oke vì mang nghĩa trung lập, không phải "tốt"
# ============================================================
TEENCODE_MAP = {
    # Phủ định / không
    "ko":    "không",
    "k":     "không",
    "kh":    "không",
    "khong": "không",
    "hok":   "không",
    "hem":   "không",
    "chx":   "chưa",
    "chua":  "chưa",

    # Đại từ
    "m":     "mình",
    "t":     "tôi",
    "mk":    "mình",
    "mn":    "mọi người",

    # Sản phẩm / mua sắm
    "sp":    "sản_phẩm",
    "sz":    "size",
    "sl":    "số_lượng",
    "đc":    "được",
    "dc":    "được",
    "dk":    "được",
    "r":     "rồi",
    "j":     "gì",
    "z":     "vậy",
    "vs":    "với",
    "ntn":   "như_thế_nào",
    "kb":    "không_biết",
    "thui":  "thôi",
    "giong": "giống",

    # Cảm thán cường độ (map sang từ trung lập, KHÔNG map sang "tốt")
    "vkl":   "rất",
    "vl":    "rất",
    "wl":    "rất",

    # Thời gian
    "2day":  "hôm_nay",
    "hom nay": "hôm_nay",

    # Giao tiếp
    "cmt":   "bình_luận",
    "rep":   "trả_lời",
    "inbox": "nhắn_tin",
}

# Cụm từ nhiều word cần replace TRƯỚC khi tokenize
PHRASE_MAP = {
    "m.n":        "mọi_người",
    "chất lg":    "chất_lượng",
    "giao hàg":   "giao_hàng",
    "phuc vu":    "phục_vụ",
    "nhiet tinh": "nhiệt_tình",
    "lâu vãi":    "rất_lâu",
    "đáng tiền":  "xứng_đáng",
}


# ============================================================
# 2. CÁC HÀM XỬ LÝ
# ============================================================

def remove_noise(text: str) -> str:
    """Bước 1: Xóa URL, emoji, ký tự đặc biệt, lowercase."""
    text = text.lower()
    text = re.sub(r'http\S+|www\S+', ' ', text)
    # Giữ chữ cái (kể cả có dấu), số, khoảng trắng, dấu câu cơ bản
    text = re.sub(r'[^\w\sàáâãèéêìíòóôõùúýăđơưạảấầẩẫậắặằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỷỹỵ!?,.]', ' ', text)
    return text


def normalize_repeated_chars(text: str) -> str:
    """Bước 2: đẹppppp → đẹp (chỉ collapse ≥3 lần lặp)."""
    return re.sub(r'(.)\1{2,}', r'\1\1', text)
    # Giữ lại 2 để không mất "oo" hợp lệ, chỉ collapse 3+


def remove_repeated_sentences(text: str) -> str:
    """
    Bước 3: Xóa câu lặp lại.
    "shop tốt shop tốt shop tốt" → "shop tốt"
    Tách theo dấu chấm + khoảng trắng, dedup theo nội dung strip.
    """
    # Tách câu theo dấu chấm hoặc xuống dòng
    parts = re.split(r'[.\n]+', text)
    seen = []
    for p in parts:
        p_strip = p.strip()
        if p_strip and p_strip not in seen:
            seen.append(p_strip)
    return '. '.join(seen)


def replace_phrases(text: str) -> str:
    """Bước 4: Replace cụm từ nhiều word TRƯỚC khi tokenize."""
    for phrase, replacement in PHRASE_MAP.items():
        text = text.replace(phrase, replacement)
    return text


def tokenize_vi(text: str) -> str:
    """Bước 5: Word segmentation bằng pyvi."""
    if not HAS_PYVI:
        return text
    try:
        return ViTokenizer.tokenize(text)
    except Exception:
        return text


def replace_teencode_on_tokens(text: str) -> str:
    """
    Bước 6: Replace teencode SAU khi tokenize.
    Chạy trên từng token riêng lẻ → tránh lỗi \b với Unicode.
    Chỉ replace khi TOÀN BỘ token khớp key (exact match).
    """
    tokens = text.split()
    replaced = [TEENCODE_MAP.get(tok, tok) for tok in tokens]
    return ' '.join(replaced)


def final_normalize(text: str) -> str:
    """Bước 7: Tách dấu câu, xóa khoảng trắng dư."""
    text = re.sub(r'([!?,.])', r' \1 ', text)
    text = ' '.join(text.split())
    return text


def clean_text(text: str) -> str:
    """Pipeline đầy đủ cho 1 text."""
    if not isinstance(text, str) or not text.strip():
        return ""
    text = remove_noise(text)
    text = normalize_repeated_chars(text)
    text = remove_repeated_sentences(text)
    text = replace_phrases(text)
    text = tokenize_vi(text)
    text = replace_teencode_on_tokens(text)
    text = final_normalize(text)
    return text


# ============================================================
# 3. PIPELINE CHÍNH
# ============================================================

def run_pipeline(
    input_path: str,
    output_path: str,
    samples_per_class: int = 3500,
    random_state: int = 42,
):
    if not os.path.exists(input_path):
        print(f"❌ Không tìm thấy file: {input_path}")
        return

    # --- Load ---
    df = pd.read_csv(input_path)
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    print(f"📥 Load xong: {len(df)} dòng")

    # --- Dedup trên comment GỐC (trước khi clean) ---
    before = len(df)
    df = df.drop_duplicates(subset=["comment"])
    print(f"🔁 Dedup raw: {before} → {len(df)} dòng")

    # --- Map label ---
    label_map = {"POS": 1, "NEG": 0, "NEU": 2}
    df["label_id"] = df["label"].map(label_map)
    df = df.dropna(subset=["label_id"])
    df["label_id"] = df["label_id"].astype(int)

    # --- Clean text ---
    print("🧹 Đang clean text...")
    tqdm.pandas()
    df["comment_clean"] = df["comment"].progress_apply(clean_text)

    # --- Xóa dòng rỗng sau clean ---
    df = df[df["comment_clean"].str.strip() != ""]

    # --- Dedup sau clean (collapse do teencode) ---
    before2 = len(df)
    df = df.drop_duplicates(subset=["comment_clean"])
    print(f"🔁 Dedup post-clean: {before2} → {len(df)} dòng")

    # --- Phân phối label trước sampling ---
    print("\n📊 Phân phối trước sampling:")
    for lid, lname in [(0, "NEG"), (1, "POS"), (2, "NEU")]:
        n = (df["label_id"] == lid).sum()
        print(f"   {lname} ({lid}): {n} samples")

    # --- Balanced sampling ---
    sampled = []
    for lid in [0, 1, 2]:
        sub = df[df["label_id"] == lid]
        n_take = min(len(sub), samples_per_class)
        sampled.append(sub.sample(n=n_take, random_state=random_state))
        print(f"   → Lấy {n_take} samples cho label {lid}")

    final_df = (
        pd.concat(sampled)
        .sample(frac=1, random_state=random_state)
        .reset_index(drop=True)
    )

    # --- Chỉ giữ các cột cần thiết ---
    keep_cols = [c for c in ["comment", "comment_clean", "label", "label_id", "rate"] if c in final_df.columns]
    final_df = final_df[keep_cols]

    # --- Export ---
    final_df.to_csv(output_path, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)

    print(f"\n✅ Xong! Đã lưu {len(final_df)} dòng → {output_path}")
    print("\n🔍 Preview 5 dòng:")
    print(final_df[["comment_clean", "label_id"]].head(5).to_string(index=False))


# ============================================================
# 4. CHẠY
# ============================================================
if __name__ == "__main__":
    run_pipeline(
        input_path="data/raw_vi/data.csv",
        output_path="data_clean.csv",
        samples_per_class=3500,
    )