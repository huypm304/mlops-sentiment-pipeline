import json
import re

# Aspect chuẩn
aspect_set = set(["Fashion", "Device", "General", "Service", "Ship", "Price", "App"])

input_path = "data/processed/balanced_train_v3_normalized.jsonl"
output_path = "data/processed/balanced_train_v3_fixed.jsonl"
flagged_path = "data/processed/balanced_train_v3_flagged.tsv"

rows = []
fixed = 0
flagged = 0
with open(input_path, encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
    for idx, line in enumerate(fin, 1):
        rec = json.loads(line)
        text = rec["text"]
        opinions = rec.get("opinions", [])
        errors = []
        for op in opinions:
            # Sửa offset nếu target xuất hiện trong text
            target = op.get("target", "").strip()
            if target:
                # Tìm vị trí đầu tiên khớp target (case-insensitive, bỏ khoảng trắng đầu/cuối)
                match = re.search(re.escape(target), text, re.IGNORECASE)
                if match:
                    op["start"] = match.start()
                    op["end"] = match.end()
                else:
                    errors.append(f"Target '{target}' không tìm thấy trong text")
            # Sửa aspect nếu không hợp lệ
            aspect = op.get("aspect", "")
            if aspect not in aspect_set:
                op["aspect"] = "General"
                fixed += 1
        # Flag sentiment leakage (câu có từ 'nhưng', 'tuy nhiên', 'mà' mà tất cả sentiment giống nhau)
        if len(opinions) > 1:
            if re.search(r"nhưng|tuy nhiên|mà", text, re.IGNORECASE):
                sents = set(op.get("sentiment") for op in opinions)
                if len(sents) == 1:
                    errors.append("Câu đối lập nhưng tất cả sentiment giống nhau (nguy cơ leakage)")
        if errors:
            rows.append([idx, text, " | ".join(errors)])
            flagged += 1
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

with open(flagged_path, "w", encoding="utf-8") as f:
    f.write("Dòng số\tText\tLỗi phát hiện\n")
    for row in rows:
        f.write(f"{row[0]}\t{row[1][:60].replace(chr(9),' ')}...\t{row[2]}\n")

print(f"Đã sửa offset/aspect và flag sentiment leakage. File mới: {output_path}")
print(f"Có {flagged} dòng bị flag lỗi, chi tiết: {flagged_path}")
