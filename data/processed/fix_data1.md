Bạn là một data engineer chuyên xử lý NLP dataset.

Tôi có file `data/processed/data_train_v4.jsonl`, mỗi dòng là một JSON record ABSA với cấu trúc:
{"text": "...", "opinions": [{"target": "...", "aspect": "...", "sentiment": "..."}], "global_sentiment": "..."}

Nhiệm vụ của bạn:
1. Đọc toàn bộ file.
2. Với mỗi field `target` trong tất cả opinions, áp dụng đúng 3 bước theo thứ tự sau:
   a. Lowercase toàn bộ chuỗi
   b. Strip leading/trailing whitespace
   c. Thay tất cả space bằng dấu `_` (kể cả multiple space liên tiếp, gộp thành 1 dấu `_`)
3. Không thay đổi bất kỳ field nào khác. Không chỉnh sửa field `text` gốc.
4. Ghi ra file mới: `data/processed/data_train_v4_norm.jsonl`
5. In báo cáo gồm:
   - Tổng số record đã xử lý
   - Tổng số target đã bị thay đổi (so với giá trị gốc)
   - Số unique target trước và sau normalize
   - Top 15 cặp thay đổi phổ biến nhất, định dạng: "trước → sau (N lần)"

Ví dụ transform mong đợi:
- "nhân viên"   → "nhân_viên"
- "Nhân_viên"   → "nhân_viên"
- "Nhân viên"   → "nhân_viên"
- "Giao hàng"   → "giao_hàng"
- "ứng dụng"    → "ứng_dụng"
- "tầm_giá"     → "tầm_giá"  (không đổi vì đã đúng chuẩn trừ lowercase)
- "Tầm_giá"     → "tầm_giá"
- "app"         → "app"      (single-token, không đổi)