import torch
import numpy as np
import unicodedata
import re
from transformers import AutoTokenizer
# Lệnh import từ file model.py mà bạn sẽ tạo ở Local
from model import ABSAv3, extract_bio_spans 

class ABSA_Engine:
    def __init__(self, model_path="model/best_absa_v3.pt", model_name="Fsoft-AIC/videberta-base"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🚀 Đang khởi động ABSA Engine V3 trên thiết bị: {self.device}")
        
        # 1. Khai báo từ điển quy tắc (Dictionary)
        self.NEG_WORDS = ["xấu", "tệ", "lag", "mắc", "lỗi", "lâu", "đắt", "kém", "hỏng", "mỏng", "yếu", "chậm"]
        self.POS_WORDS = ["tốt", "đẹp", "nhanh", "ok", "ổn", "xịn", "ưng", "ngon", "rẻ", "tuyệt"]
        self.CONTRAST_WORDS = ["nhưng", "tuy", "dù", "mà", "nên"]
        self.STOP_CHARS = [",", ".", "!", "?", ";", "\n"]
        self.SENT_NAME = {0: "Neg 🔴", 1: "Pos 🟢", 2: "Neu 🟡"}
        self.UNCERTAINTY_THRESHOLD = 0.20

        # 2. Load Tokenizer & Model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        checkpoint = torch.load(model_path, map_location=self.device)
        
        self.model = ABSAv3(model_name).to(self.device).float()
        self.model.load_state_dict(checkpoint["model_state"]) # Giờ sẽ chạy phăm phăm!
        self.model.eval()
        print("✅ Đã nạp Model V3 thành công vào bộ nhớ!")

    def _get_refined_sentiment(self, target, context_full, raw_logits, global_pred):
        """
        Lớp MLOps Giải thích được (Explainable AI Layer) 
        Tích hợp Entropy, RegEx và Không gian Logit.
        """
        # 1. TÁCH VẾ CÂU (Closest Context Selection)
        refined_context = context_full.lower()
        for w in self.CONTRAST_WORDS:
            if w in refined_context:
                parts = refined_context.split(w)
                best_part = refined_context
                min_dist = 1e9
                target_low = target.lower()
                
                for p in parts:
                    if target_low in p:
                        dist = abs(refined_context.find(p) + len(p)/2 - refined_context.find(target_low))
                        if dist < min_dist:
                            best_part = p
                            min_dist = dist
                refined_context = best_part

        # 2. TRÍCH XUẤT XÁC SUẤT VÀ ENTROPY (Độ bất định)
        probs = torch.softmax(raw_logits, dim=-1)
        p_neg, p_pos, p_neu = probs[0].item(), probs[1].item(), probs[2].item()
        ai_decision = np.argmax([p_neg, p_pos, p_neu])
        
        # Shannon Entropy Formula
        entropy = - (p_neg*np.log(p_neg+1e-9) + p_pos*np.log(p_pos+1e-9) + p_neu*np.log(p_neu+1e-9))
        uncertainty = entropy / np.log(3)
        
        # 3. KHỚP TỪ KHÓA BẰNG REGEX (Chống nhiễu từ dính liền)
        neg_score = sum(1 for w in self.NEG_WORDS if re.search(rf"\b{w}\b", refined_context))
        pos_score = sum(1 for w in self.POS_WORDS if re.search(rf"\b{w}\b", refined_context))
        
        # Xử lý từ phủ định (Negation handling)
        if re.search(r"\b(không|chưa|chẳng)\s+\w*\s*(tốt|đẹp|ngon|xịn|ưng|ok|ổn)\b", refined_context):
            neg_score += 1
            pos_score = max(0, pos_score - 1)
            
        neg_signal = min(neg_score / 2.0, 1.0)
        pos_signal = min(pos_score / 2.0, 1.0)
        
        bias_neg, bias_pos = 1.0, 1.0

        # 4. TÍNH TOÁN BIAS TRÊN KHÔNG GIAN HIERARCHY
        # Điều chỉnh Threshold trong __init__ thành 0.2
        if uncertainty > self.UNCERTAINTY_THRESHOLD:
            # 1. Tín hiệu tiêu cực (Priority 1)
            if neg_signal > 0:
                # Tăng mạnh trọng số để thắng được cái Pos Bias của model
                bias_neg += 2.0 * neg_signal 
                
                # Xử lý trạng từ giảm nhẹ nhưng vẫn mang nghĩa Neg (hơi lâu, khá mắc)
                if re.search(r"\b(hơi|khá)\b", refined_context):
                    bias_neg += 0.5 

            # 2. Tín hiệu tích cực (Priority 2)
            if pos_signal > 0:
                bias_pos += 0.8 * pos_signal

            # 3. Hierarchical Consistency (Chiêu cuối)
            # Nếu AI quá bất định (>0.7), ép nó đi theo cảm xúc toàn cục (Global)
            if uncertainty > 0.7:
                if global_pred == 0:   # Toàn câu chê
                    bias_neg += 1.0
                elif global_pred == 1: # Toàn câu khen
                    bias_pos += 0.5

        # 5. ĐIỀU CHỈNH LOGIT
        logits = raw_logits.clone()
        if bias_neg > 1.0: logits[0] += np.log(bias_neg)
        if bias_pos > 1.0: logits[1] += np.log(bias_pos)
        
        final_idx = torch.argmax(logits).item()

        # 6. AUDIT LOG
        trace_msg = f"AI: {self.SENT_NAME.get(ai_decision)} (Uncertainty: {uncertainty:.2f})"
        
        if uncertainty > self.UNCERTAINTY_THRESHOLD:
            signal_str = []
            if neg_score > 0: signal_str.append(f"NEG={neg_score}")
            if pos_score > 0: signal_str.append(f"POS={pos_score}")
            if global_pred == 0: signal_str.append("GLB_NEG")
            elif global_pred == 1: signal_str.append("GLB_POS")
            
            trace_msg += f" | Signals: {'+'.join(signal_str)}" if signal_str else " | Signals: None"
            trace_msg += f" ➡️ {self.SENT_NAME.get(final_idx)}" if final_idx != ai_decision else " ➡️ AI Retained"
        else:
            trace_msg += " | Highly Confident (Rules Bypassed)"

        return final_idx, refined_context.strip(), trace_msg
        
    @torch.no_grad()
    def predict(self, text):
        text = unicodedata.normalize("NFC", text)
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, 
                           max_length=320, return_offsets_mapping=True, return_special_tokens_mask=True)
        
        input_ids = inputs["input_ids"].to(self.device)
        mask = inputs["attention_mask"].to(self.device)
        offsets = inputs.pop("offset_mapping")[0].cpu().numpy()
        special_mask = inputs.pop("special_tokens_mask")[0].cpu().numpy()
        seq_len = input_ids.shape[1]

        # Lượt 1: AI dự đoán BIO và Global Sentiment
        bio_em, _, _, _, g_log = self.model(input_ids, mask)
        bio_labels = self.model.crf.decode(bio_em, mask=mask.bool())[0]
        spans = extract_bio_spans(bio_labels) 
        
        global_pred = torch.argmax(g_log).item()
        
        # Fallback bắt buộc cho từ "App"
        text_low = text.lower()
        if "app" in text_low and not any(a == "App" for _,_,a in spans):
            spans.add((0, 0, "App"))

        if not spans: return {"global_sentiment": self.SENT_NAME.get(global_pred), "aspects": []}

        # Lượt 2: Mở rộng Dynamic Window bằng Char-level
        temp_span_masks = torch.zeros(1, 8, seq_len).to(self.device)
        sorted_spans = sorted(list(spans))
        refined_contexts_list = []

        for idx, (s_idx, e_idx, asp) in enumerate(sorted_spans):
            if idx >= 8: break
            char_lo, char_hi = offsets[s_idx][0], offsets[e_idx][1]

            while char_lo > 0 and text[char_lo-1] not in self.STOP_CHARS: char_lo -= 1
            while char_hi < len(text) and text[char_hi] not in self.STOP_CHARS: char_hi += 1
                
            context_raw = text[char_lo:char_hi]
            refined_contexts_list.append(context_raw)
            
            for i in range(seq_len):
                t_s, t_e = offsets[i]
                if t_s >= char_lo and t_e <= char_hi and t_e > 0 and not special_mask[i]:
                    temp_span_masks[0, idx, i] = 1.0

        # Lượt 3: AI đánh giá Sentiment dựa trên Context đã cô lập
        _, _, _, span_log, _ = self.model(input_ids, mask, span_masks=temp_span_masks)

        results = []
        for idx, (s_idx, e_idx, asp) in enumerate(sorted_spans):
            if idx >= 8: break
            target = "App" if (s_idx == 0 and e_idx == 0) else text[offsets[s_idx][0]:offsets[e_idx][1]].strip()
            
            # Label Correction: Ép nhãn khía cạnh theo từ khóa để tăng độ chính xác
            target_low = target.lower()
            if "giá" in target_low: asp = "Price"
            if "ship" in target_low or "giao" in target_low: asp = "Ship"
            if "app" in target_low or "diện" in target_low: asp = "App"

            # Lượt 4: Qua màng lọc của chuyên gia (Explainable MLOps Layer)
            final_idx, ctx_msg, trace_msg = self._get_refined_sentiment(
                target, refined_contexts_list[idx], span_log[0, idx], global_pred
            )
            
            results.append({
                "aspect": asp,
                "target": target,
                "sentiment": self.SENT_NAME.get(final_idx),
                "context_used": ctx_msg,
                "audit_trace": trace_msg
            })

        return {
            "global_sentiment": self.SENT_NAME.get(global_pred),
            "aspects": results
        }

if __name__ == "__main__":
    import json
    
    print("\n" + "="*60)
    print("🚀 KHỞI ĐỘNG BÀI TEST ENGINE LOCAL".center(60))
    print("="*60)

    # 1. Khởi tạo Engine (Sẽ mất vài giây để load model vào RAM/VRAM)
    engine = ABSA_Engine(model_path="model/best_absa_v3.pt")

    # 2. Bộ câu hỏi "tử thần"
    test_cases = [
        "áo rất xấu luôn thế mà giá còn hơi mắc nhưng nhân viên phục vụ rất tốt.",
        "App dùng hơi lag nhưng giá rẻ nên vẫn cho 5 sao, ship hơi lâu.",
        "Cái đồng hồ này đẹp tuyệt vời, nhân viên giao hàng rất nhanh."
    ]

    # 3. Chạy vòng lặp test
    for i, text in enumerate(test_cases):
        print(f"\n📝 [TEST #{i+1}] Input: {text}")
        
        # Gọi hàm predict cốt lõi
        result = engine.predict(text)
        
        # In kết quả theo format siêu ngầu
        print(f"🌍 Global Sentiment: {result.get('global_sentiment')}")
        print("-" * 60)
        
        if not result.get("aspects"):
            print("💡 Không tìm thấy khía cạnh nào.")
        else:
            for asp_data in result["aspects"]:
                asp = asp_data["aspect"]
                sent = asp_data["sentiment"]
                target = asp_data["target"]
                audit = asp_data["audit_trace"]
                
                print(f"📌 [{asp:10}] | {sent} | Target: '{target}'")
                print(f"   ∟ Audit: {audit}")
    
    print("\n" + "="*60)
    print("✅ HOÀN TẤT BÀI TEST LOCAL!".center(60))
    print("="*60)