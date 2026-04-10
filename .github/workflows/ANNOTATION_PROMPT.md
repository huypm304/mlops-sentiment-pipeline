# Annotation Task — Vietnamese ABSA Dataset

## Nhiệm vụ
Đọc file CSV đầu vào, với mỗi dòng hãy phân tích và sinh ra 1 JSON object theo đúng schema bên dưới, rồi ghi tất cả ra file JSONL (mỗi dòng 1 JSON object).

## File
- Input : `batch_input.csv`  (các cột: `comment_clean`, `label_id`, `rate`)
- Output: `batch_output.jsonl`

---

## Output Schema

```json
{
  "text": "<comment_clean nguyên văn>",
  "opinions": [
    {
      "target"   : "<chuỗi con xuất hiện trong text, là danh từ/cụm danh từ chỉ đối tượng được nhận xét>",
      "aspect"   : "<1 trong 5 nhãn: Product | Ship | Price | App | Service>",
      "sentiment": "<0=NEG | 1=POS | 2=NEU>",
      "start"    : "<char offset bắt đầu của target trong text, tính từ 0>",
      "end"      : "<char offset kết thúc, KHÔNG bao gồm ký tự tại vị trí end>"
    }
  ],
  "global_sentiment": "<label_id từ CSV: 0=NEG | 1=POS | 2=NEU>"
}
```

---

## Định nghĩa 5 Aspect

| Aspect  | Phủ sóng |
|---------|----------|
| Product | Chất lượng, mẫu mã, size, màu sắc, chất liệu, bao bì, đóng gói sản phẩm |
| Ship    | Giao hàng, shipper, tốc độ giao, tình trạng hàng khi nhận |
| Price   | Giá bán, phí ship, khuyến mãi, voucher, độ xứng đáng với tiền |
| App     | Ứng dụng, giao diện, tốc độ app, tính năng, lỗi kỹ thuật |
| Service | CSKH, tư vấn, đổi trả, hoàn tiền, thái độ nhân viên/shop |

---

## Rules bắt buộc

### R1 — target là NOUN PHRASE, KHÔNG chứa opinion word
```
✅ target = "giao_hàng"          (danh từ)
❌ target = "giao_hàng chậm"     (chứa opinion word "chậm")
❌ target = "chậm"               (opinion word, không phải target)
```

### R2 — sentiment của mỗi opinion là INDEPENDENT, KHÔNG sao chép global
```
text: "áo đẹp nhưng giao_hàng chậm"  → global_sentiment = 2 (NEU)
✅ opinions[0]: target="áo",          sentiment=1  (POS vì "đẹp")
✅ opinions[1]: target="giao_hàng",   sentiment=0  (NEG vì "chậm")
❌ opinions[0]: sentiment=2           (KHÔNG copy global vào opinion)
```

### R3 — Implicit target: dùng từ opinion làm target
Khi không có danh từ rõ ràng, lấy từ mang nghĩa nhận xét gần nhất làm target.
```
text: "giao nhanh lắm"
✅ target="giao", aspect="Ship", sentiment=1
```

### R4 — start/end là char offset trong text CHÍNH XÁC
Sau khi sinh xong, tự verify: `text[start:end] == target`
Nếu sai thì tìm lại offset đúng.

### R5 — Mỗi aspect chỉ xuất hiện TỐI ĐA 1 lần trong opinions
Nếu text đề cập cùng 1 aspect nhiều lần, chỉ giữ span quan trọng nhất (thường là span đầu tiên hoặc span có opinion word rõ nhất).

### R6 — Không bịa target không có trong text
```
text: "tệ lắm"
✅ target="tệ", aspect="Product", sentiment=0   (dùng opinion word làm target)
❌ target="sản_phẩm"                             (từ này không có trong text)
```

### R7 — global_sentiment lấy NGUYÊN từ label_id trong CSV, không tự đổi

---

## Xử lý các trường hợp đặc biệt

### Negation (phủ định)
```
"không đẹp"      → sentiment=0  (NEG, dù "đẹp" là POS word)
"không tệ"       → sentiment=2  (NEU, double negation = trung lập)
"chưa giao"      → sentiment=0  (NEG)
```

### Concession (nhưng / tuy nhiên / mặc dù)
```
"chất tốt nhưng giá đắt"
→ Product: POS,  Price: NEG
```

### Intensifier không đổi direction
```
"rất đẹp"   → POS  (intensifier tăng độ, không đổi chiều)
"hơi chậm"  → NEG  (hơi = giảm độ, vẫn NEG)
"khá ổn"    → NEU  (khá ổn = chấp nhận được = NEU)
```

---

## 10 Few-shot Examples (BẤT BIẾN — không thay đổi)

### Example 1 — Single POS
```
Input : text="chất_lượng sản_phẩm tuyệt_vời", label_id=1
Output:
{
  "text": "chất_lượng sản_phẩm tuyệt_vời",
  "opinions": [
    {"target": "chất_lượng", "aspect": "Product", "sentiment": 1, "start": 0, "end": 10}
  ],
  "global_sentiment": 1
}
```

### Example 2 — Mixed (NEU global, 2 opinions khác chiều)
```
Input : text="áo đẹp nhưng giao_hàng hơi chậm", label_id=2
Output:
{
  "text": "áo đẹp nhưng giao_hàng hơi chậm",
  "opinions": [
    {"target": "áo",         "aspect": "Product", "sentiment": 1, "start": 0,  "end": 2},
    {"target": "giao_hàng",  "aspect": "Ship",    "sentiment": 0, "start": 13, "end": 22}
  ],
  "global_sentiment": 2
}
```

### Example 3 — NEG với negation
```
Input : text="hàng không đẹp như hình", label_id=0
Output:
{
  "text": "hàng không đẹp như hình",
  "opinions": [
    {"target": "hàng", "aspect": "Product", "sentiment": 0, "start": 0, "end": 4}
  ],
  "global_sentiment": 0
}
```

### Example 4 — Implicit target
```
Input : text="giao nhanh lắm cảm_ơn shop", label_id=1
Output:
{
  "text": "giao nhanh lắm cảm_ơn shop",
  "opinions": [
    {"target": "giao",  "aspect": "Ship",    "sentiment": 1, "start": 0,  "end": 4},
    {"target": "shop",  "aspect": "Service", "sentiment": 1, "start": 21, "end": 25}
  ],
  "global_sentiment": 1
}
```

### Example 5 — Price aspect
```
Input : text="giá hơi đắt nhưng chất_lượng ổn", label_id=2
Output:
{
  "text": "giá hơi đắt nhưng chất_lượng ổn",
  "opinions": [
    {"target": "giá",         "aspect": "Price",   "sentiment": 0, "start": 0,  "end": 3},
    {"target": "chất_lượng",  "aspect": "Product", "sentiment": 2, "start": 18, "end": 28}
  ],
  "global_sentiment": 2
}
```

### Example 6 — App aspect + NEG
```
Input : text="ứng_dụng lag quá không dùng được", label_id=0
Output:
{
  "text": "ứng_dụng lag quá không dùng được",
  "opinions": [
    {"target": "ứng_dụng", "aspect": "App", "sentiment": 0, "start": 0, "end": 8}
  ],
  "global_sentiment": 0
}
```

### Example 7 — Service aspect
```
Input : text="shop tư_vấn nhiệt_tình giao hàng cũng nhanh", label_id=1
Output:
{
  "text": "shop tư_vấn nhiệt_tình giao hàng cũng nhanh",
  "opinions": [
    {"target": "shop",      "aspect": "Service", "sentiment": 1, "start": 0,  "end": 4},
    {"target": "giao hàng", "aspect": "Ship",    "sentiment": 1, "start": 23, "end": 32}
  ],
  "global_sentiment": 1
}
```

### Example 8 — Câu rất ngắn, single implicit
```
Input : text="đẹp lắm", label_id=1
Output:
{
  "text": "đẹp lắm",
  "opinions": [
    {"target": "đẹp", "aspect": "Product", "sentiment": 1, "start": 0, "end": 3}
  ],
  "global_sentiment": 1
}
```

### Example 9 — NEG rõ với nhiều aspect
```
Input : text="hàng kém_chất_lượng ship lâu mà giá lại đắt", label_id=0
Output:
{
  "text": "hàng kém_chất_lượng ship lâu mà giá lại đắt",
  "opinions": [
    {"target": "hàng", "aspect": "Product", "sentiment": 0, "start": 0,  "end": 4},
    {"target": "ship", "aspect": "Ship",    "sentiment": 0, "start": 20, "end": 24},
    {"target": "giá",  "aspect": "Price",   "sentiment": 0, "start": 32, "end": 35}
  ],
  "global_sentiment": 0
}
```

### Example 10 — Double negation → NEU
```
Input : text="chất_lượng không tệ giao_hàng cũng không chậm", label_id=2
Output:
{
  "text": "chất_lượng không tệ giao_hàng cũng không chậm",
  "opinions": [
    {"target": "chất_lượng", "aspect": "Product", "sentiment": 2, "start": 0,  "end": 10},
    {"target": "giao_hàng",  "aspect": "Ship",    "sentiment": 2, "start": 20, "end": 29}
  ],
  "global_sentiment": 2
}
```

---

## Cách thực hiện từng bước

1. Đọc toàn bộ `batch_input.csv`
2. Với mỗi row, lấy `comment_clean` làm `text`, `label_id` làm `global_sentiment`
3. Phân tích text theo rules và examples ở trên
4. Sinh JSON object theo đúng schema
5. **Tự verify**: với mỗi opinion, kiểm tra `text[start:end] == target`. Nếu sai → tìm lại offset đúng bằng `text.index(target)` hoặc `text.find(target)`
6. Ghi từng JSON object thành 1 dòng trong `batch_output.jsonl` (ensure_ascii=False)
7. Sau khi xong, in ra tổng số dòng đã xử lý và số dòng có lỗi offset (nếu có)