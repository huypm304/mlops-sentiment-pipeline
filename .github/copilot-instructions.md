# Data Quality Audit Task

## Nhiệm vụ
Đọc file `train_final.jsonl`, phân tích chất lượng annotation, output ra:
1. `audit_summary.md` — báo cáo tổng hợp các vấn đề
2. `audit_errors.jsonl` — danh sách record lỗi cụ thể

---

## Files
- Input : `train_final.jsonl`
- Output: `audit_summary.md` + `audit_errors.jsonl`

---

## Các loại lỗi cần kiểm tra

### E1 — Offset sai (CRITICAL)
`text[start:end] != target`

```python
# Kiểm tra:
text[op["start"]:op["end"]] != op["target"]
```

### E2 — Target có leading/trailing space
`op["target"] != op["target"].strip()`

Ví dụ: `" giao hàng"`, `"áo "` — dấu cách thừa ở đầu/cuối.

### E3 — Target là opinion word, không phải noun phrase
Target khớp với danh sách opinion words:
```
Neg: tệ, xấu, kém, chậm, đắt, tồi, dở, lỗi, mỏng, rộng, nhỏ,
     to, bẩn, hôi, nhạt, cứng, nặng, sai, thiếu, trễ, lâu
Pos: đẹp, tốt, nhanh, rẻ, mượt, mịn, chắc, chuẩn, ổn, xinh,
     ngon, hay, tuyệt, ok, oke
Neu: bình_thường, tạm, được, thôi
```

### E4 — Duplicate aspect trong cùng 1 record
Cùng 1 record có 2+ opinions với cùng aspect.

Ví dụ:
```json
"opinions": [
  {"aspect": "Product", "target": "chất", ...},
  {"aspect": "Product", "target": "áo", ...}
]
```

### E5 — Sentiment sai rõ ràng (CRITICAL)
Dựa trên keyword xung quanh target (window ±5 tokens):

```
NEG keywords: không, tệ, xấu, kém, chậm, đắt, tồi, dở, lỗi, mỏng,
              thiếu, sai, trễ, lâu, hỏng, rách, bẩn, hôi, tệ_hại,
              không giống, không đúng, không đẹp, thất vọng, bực
POS keywords: đẹp, tốt, nhanh, rẻ, mượt, tuyệt, xinh, ngon, chất,
              ưng, thích, hài lòng, xuất sắc, hoàn hảo, chuẩn
NEU keywords: bình thường, tạm được, cũng được, ổn, tạm ổn,
              bình thường thôi, khắc phục được, cũng ok
```

Flag nếu:
- Opinion window chứa NEG keyword nhưng sentiment=1 (POS)
- Opinion window chứa POS keyword nhưng sentiment=0 (NEG)
- Opinion window chứa NEU keyword nhưng sentiment=1 (POS)

### E6 — Global sentiment conflict với aspect sentiments
Tất cả aspects đều NEG nhưng global=POS, hoặc ngược lại:
```
all(asp_sent == 0) and global == 1  → flag
all(asp_sent == 1) and global == 0  → flag
```

### E7 — Record không có opinions
`len(opinions) == 0`

### E8 — Text quá ngắn (≤ 2 tokens)
Có thể không đủ context để model học.

---

## Quy trình thực hiện

### Bước 1: Đọc và parse file
```python
import json
records = []
with open("train_final.jsonl") as f:
    for line in f:
        line = line.strip()
        if line:
            records.append(json.loads(line))
```

### Bước 2: Kiểm tra từng record theo 8 loại lỗi

Với mỗi record, lưu lại:
```python
{
  "line_no": int,           # số dòng trong file (1-indexed)
  "text": str,              # text gốc
  "errors": [               # list các lỗi tìm thấy
    {
      "type": "E1",         # mã lỗi
      "detail": str,        # mô tả cụ thể
      "opinion_idx": int    # index của opinion bị lỗi (-1 nếu là record-level)
    }
  ]
}
```

### Bước 3: Viết audit_errors.jsonl
Chỉ ghi các record có ít nhất 1 lỗi.
Mỗi dòng = 1 record lỗi theo format trên.

### Bước 4: Viết audit_summary.md
Theo template dưới đây.

---

## Template audit_summary.md

```markdown
# Data Quality Audit Report
**File**: train_final.jsonl
**Total records**: {N}
**Records có lỗi**: {M} ({pct}%)

---

## Tổng hợp theo loại lỗi

| Mã | Mô tả | Số records | % |
|----|-------|------------|---|
| E1 | Offset sai | X | X% |
| E2 | Target có space thừa | X | X% |
| E3 | Target là opinion word | X | X% |
| E4 | Duplicate aspect | X | X% |
| E5 | Sentiment sai rõ ràng | X | X% |
| E6 | Global conflict aspect | X | X% |
| E7 | Không có opinions | X | X% |
| E8 | Text quá ngắn | X | X% |

---

## Phân tích chi tiết

### E1 — Offset sai
[Top 5 ví dụ]
- line {N}: text="{...}" | target="{...}" | extracted="{...}"

### E2 — Target có space thừa
[Top 5 ví dụ]
- line {N}: target="{...}" → nên là "{...}"

### E3 — Target là opinion word
[Top 10 targets bị lỗi nhiều nhất]
- "{target}": {count} lần

### E4 — Duplicate aspect
[Top 5 ví dụ]
- line {N}: "{text}" → aspect {X} xuất hiện {N} lần

### E5 — Sentiment sai rõ ràng
[Top 10 ví dụ — quan trọng nhất]
- line {N}: target="{...}" | context="{...}" | predict={X} | nên là {Y}

### E6 — Global conflict
[Top 5 ví dụ]
- line {N}: aspects=[{sentiments}] | global={X}

---

## Ước tính tác động đến training

- E1 + E5 là nghiêm trọng nhất → ảnh hưởng trực tiếp đến
  Span F1 (E1) và Sentiment F1 (E5)
- E2 + E3 ảnh hưởng nhẹ hơn, fix bằng post-processing
- E4 + E6 gây confusion cho model khi học

---

## Khuyến nghị ưu tiên

1. [Tự động điền dựa trên số lượng lỗi tìm được]
```

---

## Lưu ý quan trọng

- **Không fix** bất kỳ record nào — chỉ report
- E5 chỉ flag khi **rõ ràng** sai, không flag trường hợp ambiguous
  - Ví dụ: "lâu" có thể NEG hoặc NEU tùy context → chỉ flag khi context rõ ràng
- Với E3: chỉ flag khi target **chính xác** khớp opinion word, không flag substring
  - `"đẹp"` → flag ✅
  - `"đóng_gói đẹp"` → không flag ❌ (noun phrase hợp lệ)
- In progress ra terminal sau mỗi 1000 records để biết đang chạy đến đâu