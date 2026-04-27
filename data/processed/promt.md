Bạn là một NLP annotation auditor chuyên kiểm tra chất lượng dataset ABSA tiếng Việt.

Tôi có file `train_final_v9_aste_selective_merged.jsonl`. Mỗi dòng là một JSON record với cấu trúc:
{
  "text": "...",
  "triplets": [
    {
      "aspect": "...",
      "target": "...",
      "target_span": [start, end],
      "opinion": "...",
      "opinion_span": [start, end],
      "aspect_opinion_pair": "...",
      "sentiment": 0|1|2
    }
  ]
}

Sentiment encoding: 0 = Neg, 1 = Pos, 2 = Neu.
Aspect taxonomy: Fashion, Electronics, General, Service, Ship, Price, App.

---

NHIỆM VỤ: Chạy toàn bộ các kiểm tra sau trên từng record. Log lỗi ra file `audit_errors.jsonl`. In báo cáo tổng kết cuối cùng.

---

KIỂM TRA BẮT BUỘC (lỗi cứng — loại record):

C1 — Offset mismatch target:
  text[target_span[0]:target_span[1]] sau khi strip() phải khớp với target (sau normalize: lowercase, thay _ bằng space).
  Nếu không khớp → lỗi C1.

C2 — Offset mismatch opinion:
  text[opinion_span[0]:opinion_span[1]] sau khi strip() phải khớp với opinion (sau normalize tương tự).
  Nếu không khớp → lỗi C2.

C3 — Aspect không hợp lệ:
  aspect phải nằm trong: Fashion, Electronics, General, Service, Ship, Price, App.

C4 — Sentiment không hợp lệ:
  sentiment phải là 0, 1, hoặc 2.

C5 — Target và opinion overlap:
  Nếu target_span và opinion_span có ký tự chung (tức là intersect) → lỗi C5.
  Target là thứ được nói đến, opinion là thứ nói về target — hai span này không được chồng lên nhau.

C6 — Duplicate triplet trong cùng record:
  Nếu hai triplet có cùng (aspect, target_span, opinion_span) → lỗi C6.

---

KIỂM TRA CẢNH BÁO (soft warning — giữ record nhưng log để review):

W1 — Sentiment vs opinion word mismatch:
  Dùng danh sách heuristic sau để check:
  - Neg signals: xấu, tệ, lag, chậm, mắc, đắt, lỗi, kém, hỏng, yếu, mệt, thất_vọng, tệ_hại, dở
  - Pos signals: tốt, đẹp, nhanh, ổn, ok, xịn, ưng, ngon, rẻ, tuyệt, vừa, thích, hài_lòng, tốc_độ
  - Neu signals: bình_thường, tạm, được, trung_bình, ổn_định
  Nếu opinion chứa signal mạnh trái chiều với sentiment (ví dụ: opinion="chậm" nhưng sentiment=1) → cảnh báo W1.
  Lưu ý: không flag nếu opinion có từ phủ định đứng trước (không, chưa, chẳng).

W2 — Opinion không nằm trong text:
  opinion_span trỏ đến đoạn text nhưng opinion string không xuất hiện tại vị trí đó sau normalize → cảnh báo W2.
  (Đây là double-check của C2 nhưng dùng fuzzy match thay vì exact.)

W3 — Target quá chung chung mà không có context:
  Nếu target thuộc danh sách generic: shop, hàng, sản_phẩm, đồ, cái, thứ, này
  VÀ record chỉ có 1 triplet → cảnh báo W3 (target có thể không đủ thông tin).

W4 — Sentiment Neu nhưng opinion mang màu rõ ràng:
  Nếu sentiment=2 (Neu) nhưng opinion_word nằm trong Neg hoặc Pos signals mạnh → cảnh báo W4.
  Các trường hợp hợp lệ của Neu: "tạm", "bình_thường", "ổn" theo nghĩa trung tính — không flag.

W5 — Aspect-opinion pair không nhất quán:
  aspect_opinion_pair phải bằng target + " " + opinion (sau normalize).
  Nếu không khớp → cảnh báo W5.

W6 — Opinion là stop word hoặc quá ngắn:
  Nếu opinion sau strip() có độ dài < 2 ký tự, hoặc là một trong: và, hay, hoặc, rồi, thì, mà, là, có, được
  → cảnh báo W6.

---

FORMAT LOG LỖI (audit_errors.jsonl):
Mỗi dòng là một JSON:
{
  "line": ,
  "text_preview": <50 ký tự đầu của text>,
  "triplet_idx": ,
  "error_code": "C1"|"C2"|...|"W1"|...,
  "detail": ""
}

---

FORMAT BÁO CÁO CUỐI:
In ra sau khi xử lý xong toàn bộ file:

=== AUDIT REPORT ===
Total records: N
Total triplets: N

HARD ERRORS (record bị loại):
  C1 offset mismatch target:    N records
  C2 offset mismatch opinion:   N records
  C3 invalid aspect:            N records
  C4 invalid sentiment:         N records
  C5 target-opinion overlap:    N records
  C6 duplicate triplet:         N records
  Total records removed:        N (X%)

SOFT WARNINGS (giữ lại, cần review):
  W1 sentiment-opinion mismatch: N
  W2 opinion fuzzy mismatch:     N
  W3 generic target:             N
  W4 Neu but strong opinion:     N
  W5 pair string mismatch:       N
  W6 opinion too short:          N

CLEAN RECORDS: N (X%)

Top 10 dòng cần review nhất (có nhiều lỗi/warning nhất):
  line N: [list error codes]
  ...
===

Ghi file sạch (chỉ các record không có lỗi cứng) ra: `triplet_data_clean.jsonl`

KHÔNG sửa nội dung bất kỳ record nào. Chỉ loại hoặc giữ nguyên.