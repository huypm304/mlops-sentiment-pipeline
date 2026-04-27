import torch
import unicodedata
from transformers import AutoTokenizer

# --- CẤU HÌNH ---
MODEL_PATH = "/content/drive/MyDrive/Colab Notebooks/Dataset/best_model_v5.pt" # Đường dẫn file Huy vừa train xong
MODEL_NAME = "Fsoft-AIC/videberta-base"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class ABSAEngine:
    def __init__(self, model_path, model_name, device):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.device = device
        # Khởi tạo model và nạp trọng số
        self.model = ABSAModel().to(device).float()
        self.model.load_state_dict(torch.load(model_path, map_location=device))
        self.model.eval()

        # MAPPING CHUẨN: Dựa trên phân tích RawID của Huy
        self.sent_map = {1: "Positive", 0: "Negative", 2: "Neutral"}

    def predict(self, text):
        clean_text = nfc(text)
        enc = self.tokenizer(clean_text, max_length=MAX_LEN, padding="max_length",
                             truncation=True, return_offsets_mapping=True,
                             return_special_tokens_mask=True, return_tensors="pt")

        ids = enc['input_ids'].to(self.device)
        mask = enc['attention_mask'].to(self.device)
        spec_mask = enc.pop("special_tokens_mask")[0]

        with torch.no_grad():
            # 1. Trích xuất BIO Spans
            _, bio_preds, _, _ = self.model(ids, mask)
            spans = sorted(list(extract_spans(bio_preds[0])), key=lambda x: x[0])

            if not spans:
                return {"global_sentiment": "N/A", "aspects": []}

            # 2. Build span_mask NGHIÊM NGẶT (Tránh rò rỉ context)
            L = ids.shape[1]
            span_mask = torch.zeros(1, MAX_OPS, L).to(self.device)

            for i, (start, end, asp) in enumerate(spans[:MAX_OPS]):
                # Xác định vùng giới hạn trái/phải để không nhìn lấn sang Aspect khác
                left_limit = spans[i-1][1] + 1 if i > 0 else 1
                right_limit = spans[i+1][0] - 1 if i < len(spans) - 1 else L - 2

                # Áp dụng Window nhưng không vượt quá giới hạn
                lo = max(start - 3, left_limit)
                hi = min(end + 8, right_limit)

                for j in range(lo, hi + 1):
                    if not spec_mask[j]:
                        span_mask[0, i, j] = 1.0

            # 3. Forward Pass lấy Sentiment & Global
            _, _, sent_logits, glob_logits = self.model(ids, mask, span_mask=span_mask)
            print(f"DEBUG Logits: {sent_logits[0][i]}")
            # 4. Đóng gói kết quả
            g_id = torch.argmax(glob_logits).item()
            results = {
                "global_sentiment": self.sent_map.get(g_id, "Unknown"),
                "aspects": []
            }

            for i, (start, end, asp) in enumerate(spans[:MAX_OPS]):
                s_id = torch.argmax(sent_logits[0][i]).item()
                results["aspects"].append({
                    "aspect": asp,
                    "sentiment": self.sent_map.get(s_id, "Unknown"),
                    "target": self.tokenizer.decode(ids[0][start:end+1]).strip(),
                    "audit_trace": f"RawID: {s_id}"
                })
            return results

# ==========================================
# THỰC THI BATCH TEST
# ==========================================
engine = ABSAEngine(MODEL_PATH, MODEL_NAME, DEVICE)

test_cases = [
    "để nói so sánh về giá bên tiktok và shopee thì củng không chênh lệch mấy nhưng lazada phí vận chuyển quá cao thế là mình gở ứng dụng luôn",
    "Sản phẩm tốt trong tầm giá pin trâu  chiến game ngon camera tạm ổn nhân viên hỗ trợ nhiệt tình",
    "Sản phẩm tốt , phục vụ nhiệt tình . Nhân viên rất tốt  . Điện thoại lướt rất mượt mà . Đáng túi tiền",
    "Sạc nhanh. Pin trâu. Loa bé tẹo. Màu máy xấu. So với giá tiền thì cũng tạm duyệt đc.",
    "Sản phẩm tốt trong tầm giá pin trâu chiến game ngon camera tạm ổn nhân viên hỗ trợ không tốt",
    "Giao hàng nhanh, nhân viên hỗ trợ nhanh chóng",
    "Sản phẩm quá tệ trong tầm giá. Pin tụt nhanh"
]

for i, text in enumerate(test_cases):
    res = engine.predict(text)
    print(f"\n📝 [TEST #{i+1}] Input: {text}")
    print(f"🌍 Global Sentiment: {res['global_sentiment']}")
    print("-" * 70)
    for asp in res['aspects']:
        print(f"👉 [{asp['aspect']:^12}] | Sentiment: {asp['sentiment']:^10} | Target: '{asp['target']:<12}' | {asp['audit_trace']}")