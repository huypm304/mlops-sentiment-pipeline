# Fix E5 Task — Sửa Sentiment Sai

## Bối cảnh
File `train_e5_queue.jsonl` chứa các records bị flag là có sentiment sai
(E5). Script Python đã detect nhưng không tự fix được vì cần hiểu ngữ nghĩa.

## Files
- Input : `train_e5_queue.jsonl`
- Output: `train_e5_fixed.jsonl`

---

## Nhiệm vụ

Với mỗi record, đọc toàn bộ `text` và xem xét từng `opinion`:

1. Đánh giá sentiment của opinion đó có đúng không
2. Nếu sai → sửa lại `sentiment`
3. Nếu đúng → giữ nguyên
4. **Không thay đổi** bất kỳ field nào khác (text, target, aspect, start, end)

---

## Sentiment scale
```
0 = NEG  (tiêu cực)
1 = POS  (tích cực)
2 = NEU  (trung lập / mixed)
```

---

## Rules phán đoán sentiment

### Rule 1 — Đọc TOÀN BỘ câu, không chỉ nhìn target
```
"tầm giá ổn"
 target = "tầm giá"
 context = "ổn" → NEU, không phải POS
 → sentiment = 2
```

### Rule 2 — Phân biệt POS vs NEU
```
POS: khen rõ ràng
  "đẹp lắm", "rất tốt", "tuyệt vời", "xuất sắc", "siêu ổn"

NEU: chấp nhận được, không khen không chê
  "ổn", "tạm được", "bình thường", "cũng được", "khá ổn",
  "không tệ", "cũng ok", "tạm ổn", "được"
```

### Rule 3 — Phủ định đổi chiều
```
"không đẹp"    → NEG  (0)
"không tệ"     → NEU  (2)  ← double negation = trung lập
"không tồi"    → NEU  (2)
"chưa tốt"     → NEG  (0)
```

### Rule 4 — Concession (nhưng / tuy nhiên / mặc dù)
```
"ổn nhưng giao hàng hơi chậm"
  Product: NEU (ổn)
  Ship: NEG (chậm)
```

### Rule 5 — "Tiền nào của nấy" / "xứng đáng với giá"
```
→ Price: NEU (2)  — không khen không chê, chỉ nhận xét tương xứng
```

### Rule 6 — Global sentiment
Nếu sau khi fix tất cả opinion sentiment mà global_sentiment
không còn hợp lý → sửa global_sentiment luôn:
```
Tất cả aspects NEG  → global = 0
Tất cả aspects POS  → global = 1
Mixed (có cả NEG lẫn POS/NEU) → global = 2
Tất cả aspects NEU  → global = 2
```

---

## 10 Few-shot examples

### Example 1 — NEU bị nhầm thành POS
```
Input:
  text = "Mua máy được 1 tháng máy quá ổn trong tầm giá xài hằng ngày mượt mà"
  opinion: target="tầm giá", aspect="Price", sentiment=1

Phân tích:
  "trong tầm giá" = xứng đáng với tiền bỏ ra → NEU
  → sửa sentiment: 1 → 2

Output opinion: {"target": "tầm giá", "aspect": "Price", "sentiment": 2, ...}
```

### Example 2 — POS đúng, giữ nguyên
```
Input:
  text = "màn hình đẹp sắc nét rất hài lòng"
  opinion: target="màn hình", aspect="Product", sentiment=1

Phân tích:
  "đẹp sắc nét rất hài lòng" = khen rõ ràng → POS đúng
  → giữ nguyên

Output opinion: không thay đổi
```

### Example 3 — NEG bị nhầm thành POS
```
Input:
  text = "ứng dụng lag tệ quá không dùng được"
  opinion: target="ứng dụng", aspect="App", sentiment=1

Phân tích:
  "lag tệ quá không dùng được" = tiêu cực rõ ràng → NEG
  → sửa sentiment: 1 → 0

Output opinion: {"target": "ứng dụng", "aspect": "App", "sentiment": 0, ...}
```

### Example 4 — Concession, mỗi aspect một sentiment
```
Input:
  text = "ứng_dụng ổn nhưng giao hàng hơi chậm"
  opinions:
    [0] target="ứng_dụng", aspect="App",  sentiment=1  ← nghi ngờ
    [1] target="giao hàng", aspect="Ship", sentiment=0

Phân tích:
  "ứng_dụng ổn" = ổn thôi → NEU (2), không phải POS
  "giao hàng hơi chậm" = chậm → NEG (0) ✅

  → sửa opinions[0]: sentiment 1 → 2
  → global: mixed → 2

Output:
  opinions[0]: sentiment=2
  global_sentiment=2
```

### Example 5 — Double negation → NEU
```
Input:
  text = "chất lượng không tệ giao hàng cũng không chậm"
  opinions:
    [0] target="chất lượng", aspect="Product", sentiment=0
    [1] target="giao hàng",  aspect="Ship",    sentiment=0

Phân tích:
  "không tệ" = double negation = trung lập → NEU (2)
  "không chậm" = double negation = trung lập → NEU (2)
  → sửa cả 2: sentiment 0 → 2
  → global: 2

Output: cả 2 opinions sentiment=2, global_sentiment=2
```

### Example 6 — "Tiền nào của nấy"
```
Input:
  text = "chất lượng áo kém đúng là tiền nào của nấy"
  opinions:
    [0] target="áo",   aspect="Product", sentiment=0  ✅
    [1] target="tiền", aspect="Price",   sentiment=0  ← nghi ngờ

Phân tích:
  "tiền nào của nấy" = xứng đáng, không phải chê đắt → NEU
  → sửa opinions[1]: sentiment 0 → 2
  → global: mixed (Product NEG + Price NEU) → 0 hoặc 2
    "áo kém" = chủ đạo tiêu cực → global = 0 ✅ giữ nguyên
```

### Example 7 — Intensifier không đổi chiều
```
Input:
  text = "hàng rất đẹp chất lượng tốt"
  opinion: target="hàng", aspect="Product", sentiment=2  ← nghi ngờ

Phân tích:
  "rất đẹp chất lượng tốt" = khen rõ ràng với intensifier → POS
  → sửa: 2 → 1
```

### Example 8 — Giữ nguyên khi ambiguous
```
Input:
  text = "áo mặc cũng được tạm chấp nhận"
  opinion: target="áo", aspect="Product", sentiment=2

Phân tích:
  "cũng được tạm chấp nhận" = neutral rõ → NEU ✅
  → giữ nguyên
```

### Example 9 — NEG context rõ ràng
```
Input:
  text = "shop giả giao hàng không đúng giao hàng thiếu"
  opinion: target="shop", aspect="Service", sentiment=1  ← nghi ngờ

Phân tích:
  "shop giả" = lừa đảo → NEG rõ ràng
  → sửa: 1 → 0
  → global: 0
```

### Example 10 — App aspect ít context
```
Input:
  text = "load ứng dụng nhanh đa nhiệm ổn"
  opinion: target="ứng dụng", aspect="App", sentiment=1

Phân tích:
  "nhanh" = khen tốc độ → POS ✅
  (khác với "ổn" thuần túy)
  → giữ nguyên
```

---

## Quy trình thực hiện

1. Đọc `train_e5_queue.jsonl`
2. Với mỗi record:
   a. Đọc toàn bộ `text`
   b. Với từng opinion, áp dụng Rules 1-6
   c. Chỉ sửa `sentiment` và `global_sentiment` nếu cần
   d. **Không đổi** target, aspect, start, end
3. Ghi toàn bộ ra `train_e5_fixed.jsonl`
   — kể cả record không có thay đổi gì
   — mỗi dòng 1 JSON, không indent
4. Sau khi xong, in báo cáo:
   - Tổng records xử lý
   - Số opinions đã sửa sentiment
   - Số records đã sửa global_sentiment

---

## Lưu ý

- Khi **ambiguous** (không chắc) → **giữ nguyên**, đừng đoán
- Chỉ sửa khi **rõ ràng** sai theo Rules
- Không thêm hoặc xóa opinion
- Không sửa bất kỳ field nào ngoài `sentiment` và `global_sentiment`