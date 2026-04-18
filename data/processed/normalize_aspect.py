import json

# Aspect mapping
aspect_map = {
    "Product_Fashion": "Fashion",
    "Product_Device": "Device",
    "Product_General": "General"
}

infile = "data/processed/balanced_train_v3.jsonl"
outfile = "data/processed/balanced_train_v3_normalized.jsonl"

with open(infile, "r", encoding="utf-8") as fin, open(outfile, "w", encoding="utf-8") as fout:
    for line in fin:
        rec = json.loads(line)
        for op in rec.get("opinions", []):
            aspect = op.get("aspect")
            if aspect in aspect_map:
                op["aspect"] = aspect_map[aspect]
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"Đã chuẩn hóa aspect thành Fashion, Device, General. File mới: {outfile}")
