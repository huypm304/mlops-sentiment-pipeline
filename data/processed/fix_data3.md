Bạn là một data quality engineer.

Tôi có 2 file ABSA:
- `data/processed/data_train_v4_norm.jsonl` — bộ train chính đã chuẩn hóa target
- `data/processed/augmented_weak_cells.jsonl` — data bổ sung cho các ô yếu

Cấu trúc mỗi record:
{"text": "...", "opinions": [{"target": "...", "aspect": "...", "start": int, "end": int, "sentiment": int}], "global_sentiment": int}

Sentiment encoding: 0 = Neg, 1 = Pos, 2 = Neu.

Nhiệm vụ:
1. Merge 2 file thành 1, shuffle toàn bộ (random seed = 42).

2. Chạy validation pipeline sau trên bộ merged:

   E1 — Offset mismatch:
   Với mỗi opinion có field start và end:
   - Lấy span = text[start:end]
   - Chuẩn hóa span: span.lower().replace(" ", "_")
   - Chuẩn hóa target: target.lower().replace(" ", "_")
   - Nếu span_norm != target_norm → flag E1
   - KHÔNG so sánh raw string, phải chuẩn hóa cả 2 phía trước khi so sánh

   E2 — Target có leading/trailing space:
   Kiểm tra target != target.strip()

   E4 — Duplicate aspect trong cùng 1 record:
   Kiểm tra list aspect trong opinions có giá trị lặp lại

   E7 — Record không có opinion:
   Kiểm tra len(opinions) == 0

   Duplicate text — Text trùng nhau:
   Kiểm tra text xuất hiện hơn 1 lần trong bộ merged (giữ lại bản đầu tiên, loại các bản sau)

   Global conflict — Conflict rõ ràng:
   Chỉ flag khi TẤT CẢ các điều kiện sau đều đúng:
   - Record có ít nhất 2 opinions
   - TẤT CẢ opinions đều có cùng sentiment (unanimous)
   - global_sentiment khác với sentiment unanimous đó
   Ví dụ loại: opinions = [Neg, Neg, Neg] nhưng global = Pos → flag
   Ví dụ KHÔNG loại: opinions = [Neg, Pos] và global = Neu → hợp lệ
   Ví dụ KHÔNG loại: opinions = [Neg] và global = Pos → single opinion, không flag

3. Nếu phát hiện lỗi: log ra `data/processed/merge_errors.txt` theo format:
   line_number | error_code | text (50 ký tự đầu)
   Xóa record lỗi khỏi bộ merged. Không sửa tay.

4. Ghi bộ sạch ra `data/processed/data_train_v5.jsonl`.

5. In báo cáo gồm:
   - Tổng record trước và sau khi lọc
   - Số record bị loại theo từng loại lỗi
   - Bảng phân bố aspect × sentiment của bộ final
   - Bảng global_sentiment distribution