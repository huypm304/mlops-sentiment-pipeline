# ASTE Data QA Report
**Input**: data_train_v8_aste.modifier_force_auto_merged.jsonl
**Corrected Output**: data_train_v8_aste.modifier_force_auto_merged.qa_fixed.jsonl
**Total records**: 7565
**Records có lỗi**: 3172 (41.93%)

## Tổng hợp lỗi

| Loại lỗi | Số lần |
|---|---:|
| Span lệch | 2156 |
| Sentiment sai | 1399 |
| Aspect sai | 492 |

## Mẫu lỗi đã sửa

| STT | Nội dung lỗi | Hiện tại | Gợi ý sửa | Lý do |
|---:|---|---|---|---|
| 1 | Sentiment sai | sentiment: 1 | sentiment: 2 | Opinion "đúng hẹn" thể hiện polarity rõ ràng. |
| 2 | Sentiment sai | sentiment: 2 | sentiment: 0 | Opinion "quá tệ. máy lag đơ" thể hiện polarity rõ ràng. |
| 3 | Sentiment sai | sentiment: 2 | sentiment: 1 | Opinion "tuyệt vời" thể hiện polarity rõ ràng. |
| 4 | Sentiment sai | sentiment: 2 | sentiment: 1 | Opinion "tốt" thể hiện polarity rõ ràng. |
| 5 | Sentiment sai | sentiment: 2 | sentiment: 1 | Opinion "trâu" thể hiện polarity rõ ràng. |
| 6 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 7 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 8 | Sentiment sai | sentiment: 2 | sentiment: 1 | Opinion "vui tính" thể hiện polarity rõ ràng. |
| 9 | Sentiment sai | sentiment: 2 | sentiment: 0 | Opinion "hơi chật" thể hiện polarity rõ ràng. |
| 10 | Sentiment sai | sentiment: 2 | sentiment: 0 | Opinion "quá tệ nhưng k đòi" thể hiện polarity rõ ràng. |
| 11 | Sentiment sai | sentiment: 2 | sentiment: 0 | Opinion "quá tệ nhưng k đòi" thể hiện polarity rõ ràng. |
| 12 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 13 | Sentiment sai | sentiment: 0 | sentiment: 1 | Opinion "nhanh" thể hiện polarity rõ ràng. |
| 14 | Sentiment sai | sentiment: 0 | sentiment: 2 | Opinion "được" thể hiện polarity rõ ràng. |
| 15 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 16 | Sentiment sai | sentiment: 0 | sentiment: 1 | Opinion "trâu" thể hiện polarity rõ ràng. |
| 17 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 18 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 19 | Sentiment sai | sentiment: 2 | sentiment: 0 | Opinion "rộng" thể hiện polarity rõ ràng. |
| 20 | Aspect sai | aspect: General | aspect: Fashion | Target/opinion khớp mạnh với nhóm Fashion qua keyword "màu". |
| 21 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 22 | Aspect sai | aspect: Fashion | aspect: General | Target/opinion khớp mạnh với nhóm General qua keyword "mẫu". |
| 23 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 24 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 25 | Aspect sai | aspect: General | aspect: Fashion | Target/opinion khớp mạnh với nhóm Fashion qua keyword "màu". |
| 26 | Sentiment sai | sentiment: 2 | sentiment: 1 | Opinion "tốt" thể hiện polarity rõ ràng. |
| 27 | Aspect sai | aspect: General | aspect: Ship | Target/opinion khớp mạnh với nhóm Ship qua keyword "đóng_gói". |
| 28 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 29 | Sentiment sai | sentiment: 0 | sentiment: 1 | Opinion "hời" thể hiện polarity rõ ràng. |
| 30 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 31 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 32 | Sentiment sai | sentiment: 1 | sentiment: 0 | Opinion "rộng" thể hiện polarity rõ ràng. |
| 33 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 34 | Sentiment sai | sentiment: 2 | sentiment: 1 | Opinion "nhanh" thể hiện polarity rõ ràng. |
| 35 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 36 | Aspect sai | aspect: General | aspect: Fashion | Target/opinion khớp mạnh với nhóm Fashion qua keyword "màu". |
| 37 | Sentiment sai | sentiment: 0 | sentiment: 1 | Opinion "chắc" thể hiện polarity rõ ràng. |
| 38 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 39 | Sentiment sai | sentiment: 1 | sentiment: 2 | Opinion "không bị trễ" thể hiện polarity rõ ràng. |
| 40 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 41 | Sentiment sai | sentiment: 2 | sentiment: 0 | Opinion "nhỏ" thể hiện polarity rõ ràng. |
| 42 | Sentiment sai | sentiment: 1 | sentiment: 0 | Opinion "nóng" thể hiện polarity rõ ràng. |
| 43 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 44 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 45 | Sentiment sai | sentiment: 1 | sentiment: 2 | Opinion "quá ổn rồi, đừng đòi" thể hiện polarity rõ ràng. |
| 46 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 47 | Span lệch | opinion: "khá tốt" [431, 439] | opinion: "khá tốt" [431, 438] | Span không khớp exact substring trong text; tìm thấy match gần nhất tại [431, 438]. |
| 48 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 49 | Span lệch | opinion: "" [-1, -1] | opinion: "" [-1, -1] | Span nằm ngoài độ dài text và không có cách sửa chắc chắn. |
| 50 | Sentiment sai | sentiment: 1 | sentiment: 2 | Opinion "quá ok" thể hiện polarity rõ ràng. |
