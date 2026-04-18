import json
import re

# Quy tắc mapping
FASHION = ["áo", "quần", "váy", "giày", "vải", "size", "form", "phom"]
ELECTRONICS = ["pin", "màn hình", "camera", "máy", "củ sạc", "cáp_sạc", "cục_sạc"]
SHIP_KEYWORDS = ["hàng", "đóng gói", "kiện hàng", "vận chuyển"]
SERVICE_SHIP = ["nhân viên giao", "shipper"]
PRICE_POS = ["hợp lý", "rẻ", "tốt", "ok"]
PRICE_NEG = ["mắc", "đắt", "cao", "chát"]

for split in ["val", "test"]:
    infile = f"data/processed/{split}_data.jsonl"
    outfile = f"data/processed/{split}_data_standardized.jsonl"
    with open(infile, "r", encoding="utf-8") as fin, open(outfile, "w", encoding="utf-8") as fout:
        for line in fin:
            rec = json.loads(line)
            text = rec["text"].lower()
            for op in rec.get("opinions", []):
                aspect = op.get("aspect")
                target = op.get("target", "").lower()
                sent = op.get("sentiment")
                # Quy tắc 3: Service/Ship overlap
                if any(x in target for x in SERVICE_SHIP):
                    op["aspect"] = "Ship"
                    continue
                # Quy tắc 1: Product -> Ship
                if aspect == "Product" and any(x in target for x in SHIP_KEYWORDS):
                    op["aspect"] = "Ship"
                    continue
                # Quy tắc 2: Product -> Fashion/Electronics/General
                if aspect == "Product":
                    if any(x in target for x in FASHION):
                        op["aspect"] = "Fashion"
                    elif any(x in target for x in ELECTRONICS):
                        op["aspect"] = "Electronics"
                    else:
                        op["aspect"] = "General"
                # Quy tắc 4: Price sentiment
                if op["aspect"] == "Price" and sent == 2:
                    window = text[max(0, op["start"]-20):op["end"]+20]
                    if any(x in window for x in PRICE_POS):
                        op["sentiment"] = 1
                    elif any(x in window for x in PRICE_NEG):
                        op["sentiment"] = 0
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Đã chuẩn hóa taxonomy cho {split} -> {outfile}")
