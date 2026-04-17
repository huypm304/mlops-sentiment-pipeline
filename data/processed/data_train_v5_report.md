# Data Train V5 Report

**Dataset**: `data/processed/data_train_v5.jsonl`

## Summary

`data_train_v5` được tạo bằng cách:
- chuẩn hóa target của `data_train_v4`
- bổ sung 470 record cho 3 ô yếu `App-Neu`, `Ship-Pos`, `Ship-Neu`
- merge, shuffle với `seed = 42`
- validate theo rule offset normalized và global conflict unanimous-only

## Merge Result

| Metric | Value |
|---|---:|
| Total records before filtering | 7826 |
| Total records after filtering | 7565 |
| Removed records | 261 |

## Removed By Error

| Error | Count |
|---|---:|
| E1 | 2 |
| GlobalConflict | 259 |

## Global Sentiment Distribution

| Label | Count |
|---|---:|
| Neg (0) | 2343 |
| Pos (1) | 2319 |
| Neu (2) | 2903 |

Nhận xét:
- `global_sentiment` khá cân bằng
- `Neu` nhỉnh hơn nhẹ, nhưng không phải mức lệch nguy hiểm

## Aspect x Sentiment Distribution

| Aspect | Neg | Pos | Neu |
|---|---:|---:|---:|
| App | 594 | 496 | 354 |
| Electronics | 537 | 592 | 243 |
| Fashion | 818 | 518 | 264 |
| General | 928 | 641 | 340 |
| Price | 434 | 666 | 668 |
| Service | 605 | 770 | 572 |
| Ship | 460 | 463 | 326 |

## Improvement Focus Check

Ba ô yếu được bổ sung ở bước augmentation đã cải thiện như sau:

| Cell | After V5 |
|---|---:|
| App-Neu | 354 |
| Ship-Pos | 463 |
| Ship-Neu | 326 |

Nhận xét:
- `App-Neu` đã tăng đáng kể và không còn quá mỏng
- `Ship-Pos` gần cân với `Ship-Neg`
- `Ship-Neu` đã lên mức dùng được

## Validation Interpretation

- `E1 = 2` cho thấy phần lớn offset vẫn nhất quán sau khi so sánh theo normalized surface form
- `GlobalConflict = 259` chủ yếu là các record unanimous sentiment nhưng global label không khớp, đã bị loại khỏi bộ final
- Không có dấu hiệu vỡ dataset hàng loạt như lần validate theo raw-string exact match trước đó

## Final Verdict

`data_train_v5` là bản dataset tốt hơn `v4` để train tiếp.

Đánh giá ngắn:
- **Structural consistency**: tốt
- **Label balance**: khá tốt
- **Weak-cell coverage**: cải thiện rõ rệt
- **Training readiness**: đạt

Nếu chọn một bản để train tiếp ở thời điểm hiện tại, nên dùng `data_train_v5.jsonl` thay cho `data_train_v4.jsonl`.
