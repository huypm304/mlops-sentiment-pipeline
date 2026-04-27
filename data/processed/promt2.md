Bạn là một data analyst chuyên phân tích dataset NLP.

Tôi có file `triplet_data_absolutely_clean.jsonl`. Mỗi dòng là một JSON record:
{
  "text": "...",
  "triplets": [
    {
      "aspect": "Fashion|Electronics|General|Service|Ship|Price|App",
      "sentiment": 0|1|2
    }
  ]
}
Sentiment: 0 = Neg, 1 = Pos, 2 = Neu.
Aspect taxonomy: Fashion, Electronics, General, Service, Ship, Price, App.

---

NHIỆM VỤ: Phân tích toàn bộ phân bố aspect × sentiment và đưa ra đánh giá cân bằng.

---

PHẦN 1 — Thống kê tổng quan:

Đếm tổng số triplet theo từng aspect.
Đếm số triplet theo từng sentiment (Neg/Pos/Neu).
In bảng:

| Aspect      | Neg | Pos | Neu | Total | Neg% | Pos% | Neu% |
|-------------|-----|-----|-----|-------|------|------|------|
| Fashion     |     |     |     |       |      |      |      |
| Electronics |     |     |     |       |      |      |      |
| General     |     |     |     |       |      |      |      |
| Service     |     |     |     |       |      |      |      |
| Ship        |     |     |     |       |      |      |      |
| Price       |     |     |     |       |      |      |      |
| App         |     |     |     |       |      |      |      |
| TOTAL       |     |     |     |       |      |      |      |

---

PHẦN 2 — Phát hiện ô mất cân bằng:

Với mỗi aspect, tính imbalance ratio = max_count / min_count trong 3 sentiment.
Flag "WARN" nếu ratio > 2.5 (một sentiment gấp 2.5 lần sentiment khác trong cùng aspect).
Flag "CRITICAL" nếu ratio > 4.0.

In danh sách các ô nguy hiểm theo format:
  [CRITICAL] App-Neu: 165 samples — ratio 3.7x so với App-Pos (614)
  [WARN]     Ship-Pos: 323 samples — ratio 1.8x so với Ship-Neg (518)

---

PHẦN 3 — So sánh với baseline v4 (nếu có thể):

Các ô yếu đã biết từ v4:
  - App-Neu: ~165 samples
  - Ship-Pos: ~323 samples
  - Ship-Neu: ~230 samples

Kiểm tra xem v9 đã cải thiện các ô này chưa. In delta:
  App-Neu:  v4=165 → v9=? (±?)
  Ship-Pos: v4=323 → v9=? (±?)
  Ship-Neu: v4=230 → v9=? (±?)

---

PHẦN 4 — Kiểm tra opinion coverage theo ô:

Với mỗi ô aspect × sentiment, đếm:
  - Số triplet có opinion_span hợp lệ (opinion != "" và opinion_span không rỗng)
  - Số triplet không có opinion (opinion = "" hoặc thiếu field)

In bảng opinion coverage:
| Aspect-Sent     | Has Opinion | No Opinion | Coverage% |
|-----------------|-------------|------------|-----------|
| Fashion-Neg     |             |            |           |
| ...             |             |            |           |

Flag các ô có coverage < 80% — đây là ô model sẽ khó học sentiment vì thiếu signal.

---

PHẦN 5 — Đánh giá tổng thể:

Dựa trên phân tích trên, đưa ra:

1. Điểm mạnh: các ô nào cân bằng tốt (ratio < 1.5).
2. Rủi ro training: các ô nào có thể khiến model bias — liệt kê theo thứ tự nguy hiểm.
3. Khuyến nghị cụ thể:
   - Ô nào nên augment thêm trước khi train.
   - Ô nào có thể dùng focal loss / class weight để bù.
   - Ô nào không cần làm gì thêm.

Không cần ghi file output. Chỉ cần in kết quả đầy đủ lên màn hình.