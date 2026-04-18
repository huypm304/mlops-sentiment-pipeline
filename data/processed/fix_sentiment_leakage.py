import json
import re

input_path = "data/processed/balanced_train_v3_fixed.jsonl"
output_path = "data/processed/balanced_train_v3_final.jsonl"

# Heuristic: Nếu câu có từ 'nhưng', 'tuy nhiên', 'mà' và tất cả sentiment giống nhau, sẽ đảo sentiment cho các aspect xuất hiện sau từ khóa đối lập

def flip_sentiment(sent):
    if sent == 0:
        return 1
    if sent == 1:
        return 0
    return 2

with open(input_path, encoding="utf-8") as fin, open(output_path, "w", encoding="utf-8") as fout:
    for line in fin:
        rec = json.loads(line)
        text = rec["text"]
        opinions = rec.get("opinions", [])
        if len(opinions) > 1 and re.search(r"nhưng|tuy nhiên|mà", text, re.IGNORECASE):
            sents = set(op.get("sentiment") for op in opinions)
            if len(sents) == 1:
                # Tìm vị trí từ khóa đối lập
                match = re.search(r"nhưng|tuy nhiên|mà", text, re.IGNORECASE)
                if match:
                    split_pos = match.end()
                    # Aspect xuất hiện sau từ khóa sẽ bị đảo sentiment
                    for op in opinions:
                        if op.get("start", 0) >= split_pos:
                            op["sentiment"] = flip_sentiment(op.get("sentiment"))
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Đã tự động sửa sentiment leakage cho các câu đối lập. File mới: {output_path}")
