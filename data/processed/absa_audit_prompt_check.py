import json
import re

# Aspect chuẩn
aspect_set = set(["Fashion", "Device", "General", "Service", "Ship", "Price", "App"])

input_path = "data/processed/balanced_train_v3_normalized.jsonl"
output_path = "data/processed/absa_audit_prompt_check.tsv"

rows = []
with open(input_path, encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if idx > 50: break  # chỉ lấy 50 dòng đầu
        rec = json.loads(line)
        text = rec["text"]
        opinions = rec.get("opinions", [])
        errors = []
        for op in opinions:
            # Check offset
            start, end = op.get("start", -1), op.get("end", -1)
            target = op.get("target", "")
            if not (0 <= start < end <= len(text)) or text[start:end].strip().lower() != target.strip().lower():
                errors.append(f"Target '{target}' không khớp vị trí start/end hoặc text trích xuất: '{text[start:end]}'")
            # Check aspect
            aspect = op.get("aspect", "")
            if aspect not in aspect_set:
                errors.append(f"Aspect '{aspect}' không hợp lệ")
        # Check sentiment leakage (câu có từ 'nhưng', 'tuy nhiên', 'mà' mà tất cả sentiment giống nhau)
        if len(opinions) > 1:
            if re.search(r"nhưng|tuy nhiên|mà", text, re.IGNORECASE):
                sents = set(op.get("sentiment") for op in opinions)
                if len(sents) == 1:
                    errors.append("Câu đối lập nhưng tất cả sentiment giống nhau (nguy cơ leakage)")
        if errors:
            rows.append([idx, text, " | ".join(errors), "Xem lại từng opinion, offset, aspect, sentiment"])

with open(output_path, "w", encoding="utf-8") as f:
    f.write("| Dòng số | Text | Lỗi phát hiện | Đề xuất sửa đổi |\n")
    f.write("|:---|:---|:---|:---|\n")
    for row in rows:
        f.write(f"| {row[0]} | {row[1][:60].replace('|','/')}... | {row[2]} | {row[3]} |\n")

print(f"Đã kiểm tra xong 50 dòng đầu. Kết quả lưu ở: {output_path}")
if rows:
    print(f"Có {len(rows)} dòng có lỗi hoặc cần kiểm tra lại.")
else:
    print("Không phát hiện lỗi rõ ràng trong 50 dòng đầu.")
