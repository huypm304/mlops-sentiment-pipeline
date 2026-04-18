"""
balance_dataset.py
─────────────────
Thực hiện cả 3 chiến lược cân bằng aspect:

  STRATEGY A — Tách Product thành 3 sub-categories:
      Product → Product_Fashion | Product_Device | Product_General

  STRATEGY B — Downsample + Augment:
      - Downsample Product_Fashion/Device/General về target
      - Augment Ship/Price/App/Service bằng data augmentation

  STRATEGY C — Fix mislabeled + Contrastive examples:
      - Fix "hàng", "đóng gói" → Ship
      - Tạo contrastive examples (câu có 2+ aspects khác sentiment)

OUTPUT:
    data/processed/balanced_train_v3.jsonl

Chạy:
    python data/balance_dataset.py
"""

import json
import random
import re
import os
import unicodedata
from collections import Counter
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════

INPUT_FILE  = "data/processed/train_final_v3.jsonl"
OUTPUT_FILE = "data/processed/balanced_train_v3.jsonl"
RANDOM_SEED = 42

random.seed(RANDOM_SEED)

# ── NEW ASPECT TAXONOMY (Strategy A) ─────────────────────────────
# Product gốc (5,561) → chia thành 3 sub-category
FASHION_KEYWORDS = [
    "áo", "quần", "váy", "giày", " dép", "túi", "túi_xách", "túi_tote",
    "vải", "chất_vải", "vải vóc", "bề mặt", "bề_mặt",
    "size", "kích cỡ", "kích_thước", "form", "phom", "dáng",
    "mẫu", "mẫu mã", "ảnh mẫu", "ảnh_mẫu", "hình", "hình_ảnh",
    "màu", "màu sắc", "màu_sắc",
    "chân", "tay áo", "tay_áo", "cổ áo", "cổ_áo", "vai",
    "ren", "đường may", "đường_may", "chỉ",
    "bơm", "lót", "lót gót", "lót_gót",
    "váy", "đầm", "quần bò", "quần_bò", "quần lót", "quần_lót",
    "áo thun", "áo_thun", "áo sơ mi", "áo_sơ_mi",
    "nón", "mũ", "khăn", "thắt lưng", "thắt_lưng",
    "dây đeo", "dây_deo", "dây", "túi zip", "túi_zip",
    "bỉm", "tã", "khẩu trang", "khẩu_trang",
    "son", "kem", "phấn", "sáp", "mỹ phẩm", "mỹ_phẩm",
    "mùi", "thơm",
    "dài", "ngắn", "rộng", "chật", "bó",
    "đàn", "nhạc", "âm thanh", "âm_thanh", "loa", "tai_nghe",
    "trẻ", "bé", "em bé", "em_bé",
    "sữa", "bình", "bình sữa", "bình_sữa", "ly", "cốc",
    "giấy", "tăm", "bàn chải", "bàn_chải",
    "gối", "drape", "áo dài", "áo_dài",
    "len", "dây", "len", "vải",
]

DEVICE_KEYWORDS = [
    "pin", "sạc", "củ sạc", "củ_sạc", "cáp sạc", "cáp_sạc",
    "máy", "điện thoại", "điện_thoại", "đt", "dt",
    "màn hình", "màn_hình", "kính", "cảm ứng", "cảm_ứng",
    "camera", "cam", "chụp", "ảnh", "zoom",
    "wifi", "sóng", "mạng", "4g", "5g",
    "loa", "tai nghe", "tai_nghe", "tai_nghe bluetooth",
    "vân tay", "vân_tay", "khuôn mặt", "khuôn_mặt", "nhận diện",
    "chip", "cpu", "ram", "bộ nhớ", "bộ_nhớ", "rom",
    "ổ cứng", "ổ_cứng", "usb", "thẻ nhớ", "thẻ_nhớ",
    "bàn phím", "bàn_phím", "chuột", "laptop", "máy tính", "máy_tính",
    "máy hút bụi", "máy_hút_bụi", "máy giặt", "nồi",
    "bluetooth", "wifi", "smart", "app", "ứng dụng", "ứng_dụng",
    "phần mềm", "phần_mềm", "hệ điều hành", "hệ_điều_hành",
    "cập nhật", "cập_nhật", "update", "ch play", "ch_play",
    "game", "chơi game", "chơi_game", "lag", "đơ",
    "nhiệt", "nóng", "lạnh", "pin",
    "apple", "samsung", "xiaomi", "oppo", "vivo", "realme",
    "vsmart", "nokia", "iphone", "ipad",
    "airpods", "galaxy", "redmi", "mi", "oneplus",
    "công nghệ", "công_nghệ", "hiệu năng", "hiệu_năng",
    "linh kiện", "linh_kiện", "phụ kiện", "phụ_kiện",
    "tai nghe", "tai_nghe", "sạc", "ốp", "ốp lưng",
    "cường lực", "cường_lực", "dán", "kính",
    "zoom", "flash", "selfie", "ảnh chụp",
    "loa", "âm thanh", "âm_thanh", "nghe", "nghe nhìn",
    "bảo hành", "bảo_hành", "hư", "lỗi", "hỏng",
    "test", "kiểm tra", "kiểm_tra", "sửa", "sửa chữa",
    "cảm biến", "cảm_biến", "gyro", "gps",
    "màn", "màn cảm ứng", "màn cảm_ứng",
    "tải", "tải về", "download", "cài", "cài đặt",
    "bắt wifi", "bắt sóng", "wifi yếu",
    "pin", "sạc", "sạc nhanh", "sạc_nhanh", "dung lượng",
    "dung_lượng", "pin trâu", "pin yếu",
    "dán cường lực", "dán_cường_lực", "ốp lưng", "ốp_lưng",
    "micro", "mic", "loa", "âm",
]

# ── Mislabel Fix Map (Strategy C) ─────────────────────────────────
# Những target này bị gán sai aspect → fix về aspect đúng
MISLABEL_FIX = {
    # product -> ship
    "hàng": "Ship",
    "đóng gói": "Ship",
    "đóng_gói": "Ship",
    "giao hàng": "Ship",
    "giao_hàng": "Ship",
    "giao nhầm": "Ship",
    "giao nhận": "Ship",
    "vận chuyển": "Ship",
    "vận_chuyển": "Ship",
    "shipper": "Ship",
    "ship": "Ship",
    "người giao hàng": "Ship",
    "người_giao_hàng": "Ship",
    "thời gian giao hàng": "Ship",
    "thời_gian_giao_hàng": "Ship",
    "giao nhanh": "Ship",
    "giao chậm": "Ship",
    "giao đúng": "Ship",
    "gửi hàng": "Ship",
    "gửi nhầm": "Ship",
    "khâu đóng gói": "Ship",
    "khâu_đóng_gói": "Ship",
    "đóng hộp": "Ship",
    "đóng_hộp": "Ship",
    "gói hàng": "Ship",
    "gói_hàng": "Ship",
    "voucher": "Price",
    "khuyến mãi": "Price",
    "khuyến_mãi": "Price",
    "sale": "Price",
    "giảm giá": "Price",
    "giảm_giá": "Price",
    "đánh giá": "Price",
    "free ship": "Price",
    "freeship": "Price",
    "miễn phí": "Price",
    "miễn_phí": "Price",
    "giá": "Price",
    "tiền": "Price",
    "tầm giá": "Price",
    "tầm_giá": "Price",
    "giá tiền": "Price",
    "giá_thành": "Price",
    "giá cả": "Price",
    "giá_cả": "Price",
    "rẻ": "Price",
    "đắt": "Price",
    "mắc": "Price",
    "hợp túi tiền": "Price",
    "hợp túi_tiền": "Price",
    "túi tiền": "Price",
    "túi_tiền": "Price",
    "xứng đáng": "Price",
    "xứng_tiền": "Price",
    "tiền nào của đó": "Price",
    "bảo hành": "Service",
    "bảo_hành": "Service",
    "đổi trả": "Service",
    "đổi_trả": "Service",
    "trả hàng": "Service",
    "trả_hàng": "Service",
    "chăm sóc khách hàng": "Service",
    "chăm_sóc_khách_hàng": "Service",
    "cskh": "Service",
    "phản hồi": "Service",
    "phản_hồi": "Service",
    "tư vấn": "Service",
    "hỗ trợ": "Service",
    "CSKH": "Service",
    "tổng đài": "Service",
    "hotline": "Service",
    "gọi": "Service",
    "trả lời": "Service",
    "trả_lời": "Service",
    "shop": "Service",
    "shopee": "Service",
    "sendo": "Service",
    "lazada": "Service",
    "tiki": "Service",
    "thế giới di động": "Service",
    "thế_giới_di_động": "Service",
    "dmx": "Service",
    "cửa hàng": "Service",
    "cửa_hàng": "Service",
    "chủ shop": "Service",
    "chủ_shop": "Service",
    "seller": "Service",
    "ứng dụng": "App",
    "ứng_dụng": "App",
    "app": "App",
    "phần mềm": "App",
    "phần_mềm": "App",
    "phần mềm": "App",
    "phần_mềm": "App",
    "hệ điều hành": "App",
    "hệ_điều_hành": "App",
    "cập nhật": "App",
    "cập_nhật": "App",
    "ios": "App",
    "android": "App",
    "ch play": "App",
    "ch_play": "App",
    "appstore": "App",
    "google play": "App",
    "lag": "App",
    "đơ": "App",
    "đơ máy": "App",
    "treo": "App",
    "thoát": "App",
    "tải ứng dụng": "App",
    "tải_app": "App",
    "đăng nhập": "App",
    "đăng_nhập": "App",
    "load": "App",
    "lOAD": "App",
    "zing": "App",
    "zalo": "App",
    "facebook": "App",
    "fb": "App",
    "youtube": "App",
}

# ── Aspect target sizes (Strategy B) ──────────────────────────────
TARGET_SIZES = {
    "Product_General": 1800,  # downsample từ ~2,500
    "Product_Fashion": 800,   # downsample từ ~1,338
    "Product_Device" : 700,   # downsample từ ~1,038
    "Service"        : 1944,  # giữ nguyên (khá cân bằng)
    "Ship"           : 1800,  # augment từ ~1,500
    "Price"          : 1800,  # augment từ ~1,600
    "App"            : 1800,  # augment từ ~1,150
}

# ── Sentiment word lists cho augmentation ────────────────────────
NEG_WORDS = ["xấu", "tệ", "kém", "hỏng", "lỗi", "đắt", "mắc", "chậm",
             "lag", "đơ", "rách", "mỏng", "yếu", "lâu", "nhỏ", "to",
             "rộng", "chật", "bó", "nóng", "ẩu", "lừa", "hên", "gợi",
             "hôi", "trầy", "sứt", "bong", "tróc", "nhăn", "bẩn", "rách",
             "tắc", "nghẹt", "kém", "đần", "ngu", "chán", "bực",
             "lạc", "sai", "nhầm", "thiếu", "thừa", "hơi", "khá",
             "lúc", "thỉnh thoảng", "thất_vọng", "không_hài_lòng",
             "quá", "vcl", "vl", "wtf", "lần sau không", "không nên"]

POS_WORDS = ["đẹp", "tốt", "xịn", "ngon", "rẻ", "nhanh", "mượt", "mát",
             "êm", "nhẹ", "nặng", "ổn", "ok", "ổn định", "ổn_định",
             "chuẩn", "chắc", "bền", "đáng", "ưng", "thích", "tuyệt",
             "siêu", "cực", "quá", "hài lòng", "hài_lòng",
             "nhiệt tình", "nhiệt_tình", "thân thiện", "thân_thiện",
             "tận tâm", "tận_tâm", "mềm", "mịn", "xinh",
             "ổn áp", "ổn_áp", "trâu", "ngon", "bốc", "chắc",
             "siêu thật", "rất", "lắm", "quá", "lắm"]

NEU_WORDS = ["tạm", "bình thường", "bình_thường", "tàm", "tạm được",
             "tạm_dược", "được", "khá", "hơi", "trung bình",
             "trung_bình", "tb", "bt", "bth", "ko", "k", "m",
             "cũng", "cũng được", "cũng_được"]


# ═══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text) if text else ""


def classify_product_target(target: str) -> str:
    """Strategy A: Phân loại Product target vào sub-category."""
    t = target.lower().strip()

    for kw in FASHION_KEYWORDS:
        if kw in t:
            return "Product_Fashion"

    for kw in DEVICE_KEYWORDS:
        if kw in t:
            return "Product_Device"

    return "Product_General"


def fix_mislabel(target: str, current_aspect: str) -> str:
    """Strategy C: Fix những target bị gán sai aspect."""
    t = target.lower().strip()
    if t in MISLABEL_FIX:
        return MISLABEL_FIX[t]
    return current_aspect


def synonym_replace(text: str, sentiment: int) -> str:
    """Augmentation: Thay từ sentiment bằng synonym cùng sentiment."""
    words = text.split()
    if not words:
        return text

    candidates = NEG_WORDS if sentiment == 0 else POS_WORDS if sentiment == 1 else NEU_WORDS
    word_pool = candidates

    # Thay 1-2 từ ngẫu nhiên
    for _ in range(min(2, len(words))):
        if random.random() < 0.3:
            idx = random.randint(0, len(words) - 1)
            words[idx] = random.choice(word_pool)

    return " ".join(words)


def random_delete(text: str, p: float = 0.1) -> str:
    """Augmentation: Xóa ngẫu nhiên một phần câu."""
    words = text.split()
    if len(words) <= 3:
        return text
    kept = [w for w in words if random.random() > p]
    return " ".join(kept) if kept else text


def swap_word_order(text: str) -> str:
    """Augmentation: Đảo thứ tự 2 phrase trong câu."""
    parts = re.split(r"([,;.]|nhưng|mà|tuy|dù|và|or)", text)
    if len(parts) >= 3:
        mid = parts[1:-1]
        random.shuffle(mid)
        result = [parts[0]] + mid + [parts[-1]]
        return "".join(result)
    return text


def augment_sample(record: dict, n_copies: int = 1) -> list:
    """Tạo n_copies biến thể từ 1 record."""
    results = []
    for _ in range(n_copies):
        new_rec = {
            "text": record["text"],
            "opinions": [],
            "global_sentiment": record["global_sentiment"],
        }
        for op in record["opinions"]:
            new_op = dict(op)
            new_op["target"] = op["target"]
            new_rec["opinions"].append(new_op)

        # Áp dụng augmentation lên text
        aug_text = record["text"]
        if random.random() < 0.3:
            aug_text = synonym_replace(aug_text, record["global_sentiment"])
        if random.random() < 0.2:
            aug_text = random_delete(aug_text)
        if random.random() < 0.15:
            aug_text = swap_word_order(aug_text)

        new_rec["text"] = aug_text
        results.append(new_rec)

    return results


def create_contrastive_sample(rec1: dict, rec2: dict) -> dict:
    """Strategy C: Tạo câu có 2 aspects với sentiment khác nhau."""
    # Ghép 2 câu có aspect khác sentiment lại
    ops = []
    if rec1.get("opinions"):
        ops.append(rec1["opinions"][0])
    if rec2.get("opinions"):
        ops.append(rec2["opinions"][0])

    # Chỉ tạo contrastive nếu có 2 aspects khác sentiment
    if len(ops) >= 2:
        s1 = ops[0].get("sentiment", 1)
        s2 = ops[1].get("sentiment", 1)
        if s1 != s2:
            # Ghép câu với connector contrastive
            connector = random.choice(["nhưng ", "mà ", "tuy nhiên ", "dù ", "nhưng mà "])
            text = rec1["text"].strip() + connector + rec2["text"].strip()
            return {
                "text": text[:500],  # Giới hạn độ dài
                "opinions": ops[:2],
                "global_sentiment": rec2.get("global_sentiment", 1),
            }
    return None


# ═══════════════════════════════════════════════════════════════════
# MAIN BALANCING PIPELINE
# ═══════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  📊 DATASET BALANCING PIPELINE — ABSA v3")
    print("=" * 65)

    # ── Bước 1: Load toàn bộ data ──────────────────────────────────
    print("\n[1/6] Loading data...")
    records = []
    with open(INPUT_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    print(f"  ✅ Loaded {len(records):,} records")

    # ── Bước 2: Strategy C — Fix mislabeled aspects ─────────────────
    print("\n[2/6] Strategy C: Fixing mislabeled aspects...")
    fix_count = 0
    for rec in records:
        for op in rec["opinions"]:
            old_asp = op.get("aspect", "")
            new_asp = fix_mislabel(op.get("target", ""), old_asp)
            if new_asp != old_asp:
                fix_count += 1
                op["aspect"] = new_asp
    print(f"  ✅ Fixed {fix_count:,} mislabeled aspects")

    # ── Bước 3: Strategy A — Split Product → 3 sub-categories ───────
    print("\n[3/6] Strategy A: Splitting Product into sub-categories...")

    aspect_counter = Counter()
    for rec in records:
        for op in rec["opinions"]:
            asp = op.get("aspect", "")
            tgt = op.get("target", "")
            if asp == "Product":
                new_asp = classify_product_target(tgt)
                op["aspect"] = new_asp
            aspect_counter[op["aspect"]] += 1

    print(f"  ✅ After split:")
    for asp, cnt in sorted(aspect_counter.items()):
        print(f"      {asp:<20}: {cnt:>5,} ({cnt/len(records)*100:.1f}%)")

    # ── Bước 4: Count & Plan per new aspect ─────────────────────────
    print("\n[4/6] Planning per-aspect targets...")

    aspect_sentiment_counter = {a: Counter() for a in TARGET_SIZES}
    aspect_records = {a: [] for a in TARGET_SIZES}
    aspect_target_pool = {a: [] for a in TARGET_SIZES}

    for rec in records:
        for op in rec.get("opinions", []):
            asp = op.get("aspect", "")
            if asp not in TARGET_SIZES:
                continue
            sent = op.get("sentiment", 1)
            tgt = op.get("target", "").lower()
            aspect_sentiment_counter[asp][sent] += 1
            aspect_target_pool[asp].append((rec, op))

        # Đếm record theo primary aspect
        if rec.get("opinions"):
            primary_asp = rec["opinions"][0].get("aspect", "")
            if primary_asp in aspect_records:
                aspect_records[primary_asp].append(rec)

    # ── Bước 5: Downsample + Augment ────────────────────────────────
    print("\n[5/6] Strategy B: Downsampling & Augmenting...")

    balanced_records = []

    for asp, target_size in TARGET_SIZES.items():
        current_size = sum(aspect_sentiment_counter[asp].values())
        target_recs = target_size  # target số opinions

        print(f"\n  Processing: {asp}")
        print(f"    Current : {current_size:,} opinions")
        print(f"    Target  : {target_size:,} opinions")

        if current_size == 0:
            print(f"    ⚠️  No data for {asp}, skipping...")
            continue

        if current_size > target_size:
            # DOWNNSAMPLE
            diff = current_size - target_size
            print(f"    📉 Downsampling {diff:,} opinions...")

            # Giữ nguyên toàn bộ records có opinion này
            # Nhưng chỉ giữ subset opinions trong mỗi record
            sampled = []
            for rec in records:
                new_ops = []
                for op in rec.get("opinions", []):
                    if op.get("aspect") == asp:
                        new_ops.append(op)

                if new_ops:
                    # Giữ ngẫu nhiên subset
                    keep_count = max(1, int(len(new_ops) * target_size / current_size))
                    kept = random.sample(new_ops, min(keep_count, len(new_ops)))
                    new_rec = dict(rec)
                    new_rec["opinions"] = kept
                    sampled.append(new_rec)

            balanced_records.extend(sampled[:target_size])

        else:
            # AUGMENT
            diff = target_size - current_size
            print(f"    📈 Augmenting {diff:,} more opinions...")

            # 1. Giữ tất cả records gốc có aspect này
            aug_records = []
            for rec in records:
                ops_for_asp = [op for op in rec.get("opinions", []) if op.get("aspect") == asp]
                if ops_for_asp:
                    aug_records.append(rec)

            # Đếm để biết cần augment bao nhiêu
            aug_needed = target_size - len(aug_records)
            if aug_needed > 0:
                # Augment từng record
                to_aug = min(aug_needed, len(aug_records))
                for rec in random.sample(aug_records, to_aug):
                    auged = augment_sample(rec, n_copies=1)
                    for a in auged:
                        ops_for = [op for op in a["opinions"] if op.get("aspect") == asp]
                        if ops_for:
                            aug_records.append(a)
                            if len(aug_records) >= target_size:
                                break

            # Thêm contrastive examples
            contrastive_count = min(200, diff // 3)
            print(f"    🔀 Creating {contrastive_count} contrastive examples...")
            asp_recs = [r for r in records
                        if any(o.get("aspect") == asp for o in r.get("opinions", []))]
            other_recs = [r for r in records
                          if not any(o.get("aspect") == asp for o in r.get("opinions", []))]

            for _ in range(contrastive_count):
                if asp_recs and other_recs:
                    c = create_contrastive_sample(
                        random.choice(asp_recs),
                        random.choice(other_recs)
                    )
                    if c and c.get("opinions"):
                        # Merge opinions
                        merged = {
                            "text": c["text"],
                            "opinions": c["opinions"],
                            "global_sentiment": c["global_sentiment"],
                        }
                        aug_records.append(merged)

            balanced_records.extend(aug_records[:target_size])

    # ── Bước 6: Shuffle & Save ────────────────────────────────────────
    print("\n[6/6] Saving balanced dataset...")

    random.shuffle(balanced_records)

    # Đảm bảo mỗi record có text và opinions hợp lệ
    final_records = [
        r for r in balanced_records
        if r.get("text") and len(r.get("text", "")) > 2
        and r.get("opinions") and len(r.get("opinions")) > 0
        and r.get("global_sentiment", -1) in [0, 1, 2]
    ]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for rec in final_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"  ✅ Saved {len(final_records):,} records → {OUTPUT_FILE}")

    # ── Final Stats ─────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  📊 FINAL DISTRIBUTION (Balanced Dataset)")
    print("=" * 65)

    final_aspect = Counter()
    final_sentiment = Counter()
    for rec in final_records:
        for op in rec.get("opinions", []):
            final_aspect[op.get("aspect", "")] += 1
            final_sentiment[op.get("sentiment", -1)] += 1

    print(f"\n  Total records : {len(final_records):,}")
    print(f"\n  ASPECT DISTRIBUTION:")
    print(f"    {'Aspect':<20} {'Count':>7} {'%':>6} {'Target':>8} {'Bar'}")
    for asp in TARGET_SIZES:
        cnt = final_aspect.get(asp, 0)
        pct = cnt / max(len(final_records), 1) * 100
        tgt = TARGET_SIZES[asp]
        bar = "█" * int(cnt / max(tgt, 1) * 10)
        print(f"    {asp:<20} {cnt:>7,} {pct:>5.1f}% {tgt:>8,}  {bar}")

    print(f"\n  SENTIMENT DISTRIBUTION:")
    for sid, name in [(0, "Neg"), (1, "Pos"), (2, "Neu")]:
        cnt = final_sentiment.get(sid, 0)
        pct = cnt / max(sum(final_sentiment.values()), 1) * 100
        bar = "█" * int(pct / 5)
        print(f"    {name:<10}: {cnt:>6,} ({pct:>5.1f}%)  {bar}")

    print(f"\n  ✅ DONE! Balanced dataset ready: {OUTPUT_FILE}")
    print("=" * 65)


if __name__ == "__main__":
    main()
