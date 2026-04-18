# Data Train V5 Review

**File**: `data/processed/data_train_v5.jsonl`

## Executive Summary

`data_train_v5` là bản nâng cấp từ `v4` theo 3 bước:
- chuẩn hóa target surface form về chuẩn underscore
- bổ sung 470 record cho 3 ô yếu `App-Neu`, `Ship-Pos`, `Ship-Neu`
- merge và validate lại bằng rule offset normalized cùng global conflict kiểu unanimous-only

Điểm mạnh chính:
- Không còn duplicate text.
- Không còn surface-form split giữa `space` và `_`; target vocabulary đã được chuẩn hóa.
- Không còn lỗi offset đáng kể theo rule normalized span check.
- `App-Neu`, `Ship-Pos`, `Ship-Neu` đều tăng rõ rệt.
- Aspect distribution cân hơn so với `v4`, đặc biệt `Ship` và `App` được kéo lên.
- `global_sentiment` vẫn khá cân bằng.

Rủi ro còn lại:
- Cảnh báo sentiment heuristic `E5` vẫn cao, nhưng đây vẫn là cảnh báo mềm.
- Một số aspect vẫn mang thiên hướng `Neg`, đặc biệt `Fashion` và `General`.
- Contrast coverage không tăng đáng kể, vì batch augment mới chủ yếu là single-opinion records.
- Target concentration vẫn cao ở các lexical anchor như `shop`, `giá`, `áo`, `giao`.

Kết luận thực dụng:
- `data_train_v5` là bản dataset nên dùng để train tiếp nếu mục tiêu là cải thiện balance mà vẫn giữ dữ liệu ổn định.
- Đây là bản sạch và nhất quán hơn `v4` ở tầng target surface form.
- Nếu làm `v6`, ưu tiên tiếp theo không còn là normalize target nữa mà là tăng contrast coverage và giảm lexical shortcut.

## Dataset Overview

| Metric | Value |
|---|---:|
| Total records | 7,565 |
| Total opinions | 11,289 |
| Duplicate texts | 0 |
| Unique raw targets | 274 |
| Unique normalized targets | 274 |
| Mean tokens per text | 17.13 |
| Median tokens per text | 13 |
| Max tokens per text | 194 |
| Mean characters per text | 79.37 |
| Median characters per text | 60 |
| Max characters per text | 846 |

Nhận xét:
- Dataset gần như giữ nguyên quy mô của `v4`, chỉ loại phần conflict rõ ràng.
- Số unique raw target bằng đúng số unique normalized target, nghĩa là lớp chuẩn hóa target đã thành công và surface form đã được thống nhất.
- Tail dài vẫn còn nhưng không tăng thêm so với `v4`.

## Structural Audit

### Fatal Structure Errors

| Code | Meaning | Records |
|---|---|---:|
| E1 | Offset mismatch theo normalized span check | 0 |
| E2 | Target has leading or trailing space | 0 |
| E3 | Target is pure opinion word | 0 |
| E4 | Duplicate aspect in same record | 0 |
| E6 | Global conflict theo unanimous-only rule | 0 |
| E7 | Record has no opinions | 0 |
| E8 | Text too short (<= 2 tokens) | 0 |
| OVERLAP | Overlapping spans | 0 |
| Duplicate text | Repeated full text | 0 |

### Soft Warnings

| Code | Meaning | Records |
|---|---|---:|
| E5 | Heuristic sentiment-context warning | 624 |

### Interpretation

- Sau bước validate ở `v5`, dataset sạch về cấu trúc theo đúng rule merge cuối cùng.
- `E5` vẫn cần đọc như warning chứ không phải defect count.
- Nhiều warning xuất hiện vì context mixed, câu có đối lập hoặc từ khóa đánh lừa heuristic như `ổn nhưng`, `đúng hẹn`, `khá tốt`, `tầm_giá`.

### Notable Soft-Warning Examples

`E5` điển hình:
- line 2: target `khâu_giao_đơn` | aspect `Ship` | sentiment `Pos` | context `xét riêng phần ship, khâu_giao_đơn đúng hẹn và không phát`
- line 15: target `tầm_giá` | aspect `Price` | sentiment `Pos` | context `máy tốt trong tầm giá ... xài ổn.. pin`
- line 34: target `cửa_hàng` | aspect `Service` | sentiment `Pos` | context `dùng lâu hơi ì. trái_lại, cửa_hàng hỗ_trợ nhiệt_tình nên mình khá`
- line 60: target `đơn_hàng` | aspect `Ship` | sentiment `Neg` | context `tốt so với mong_đợi. bù_lại, đơn_hàng đi lòng_vòng nên chờ rất`
- line 63: target `app` | aspect `App` | sentiment `Pos` | context `xài app thì tốt đấy ổn_định nhưng`

## Label Distribution

### Global Sentiment

| Label | Count | Share |
|---|---:|---:|
| Neg (0) | 2,343 | 30.97% |
| Pos (1) | 2,319 | 30.65% |
| Neu (2) | 2,903 | 38.37% |

Đánh giá:
- `global_sentiment` vẫn cân khá đẹp.
- `Neu` nhỉnh lên nhưng vẫn trong ngưỡng hợp lý cho bài toán e-commerce review.

### Aspect Distribution

| Aspect | Count | Share |
|---|---:|---:|
| Service | 1,947 | 17.25% |
| General | 1,909 | 16.91% |
| Price | 1,768 | 15.66% |
| Fashion | 1,600 | 14.17% |
| App | 1,444 | 12.79% |
| Electronics | 1,372 | 12.15% |
| Ship | 1,249 | 11.06% |

Đánh giá:
- Aspect nhiều nhất là `Service`, ít nhất là `Ship`.
- Tỷ lệ max/min khoảng `1.56x`, tốt hơn `v4`.
- `Ship` không còn quá mỏng như trước.

## Aspect x Sentiment Distribution

| Aspect | Neg | Pos | Neu | Nhận xét |
|---|---:|---:|---:|---|
| App | 594 | 496 | 354 | Cân hơn rõ so với `v4`, `Neu` đã lên tốt |
| Electronics | 537 | 592 | 243 | Tương đối ổn |
| Fashion | 818 | 518 | 264 | Vẫn nghiêng `Neg` |
| General | 928 | 641 | 340 | Vẫn nghiêng `Neg` |
| Price | 434 | 666 | 668 | Cân rất đẹp, thiên `Pos/Neu` |
| Service | 605 | 770 | 572 | Cân tốt |
| Ship | 460 | 463 | 326 | Cân hơn rõ, đặc biệt `Pos` đã bắt kịp `Neg` |

Đánh giá:
- `App-Neu` là ô cải thiện rõ nhất.
- `Ship-Pos` và `Ship-Neu` đều đã thoát vùng mỏng.
- `Price` và `Service` tiếp tục là 2 aspect có cấu trúc sentiment đẹp nhất.
- `Fashion` và `General` vẫn giữ bias `Neg`, nhưng chưa đến mức méo nặng.

## Improvement Over V4

| Cell | V4 | V5 | Delta |
|---|---:|---:|---:|
| App-Neu | 165 | 354 | +189 |
| Ship-Pos | 323 | 463 | +140 |
| Ship-Neu | 230 | 326 | +96 |

Nhận xét:
- Mức tăng thực tế nhỏ hơn batch augment sinh ra vì còn bước lọc conflict ở merge cuối.
- Tuy vậy, cả 3 ô đều được cải thiện đủ rõ để ảnh hưởng tích cực tới train balance.

## Opinion Density Per Record

| Opinions per record | Count | Share |
|---|---:|---:|
| 1 | 4,446 | 58.77% |
| 2 | 2,579 | 34.09% |
| 3 | 478 | 6.32% |
| 4 | 59 | 0.78% |
| 5 | 3 | 0.04% |

Đánh giá:
- Tỷ lệ record 1-opinion tăng lên do batch augment mới là single-opinion.
- Đây là tradeoff rõ ràng của bước tăng weak cells: sentiment balance tốt hơn, nhưng multi-aspect density giảm nhẹ.

## Aspect Coverage Per Record

| Aspect | Records containing aspect | Share of all records |
|---|---:|---:|
| Service | 1,947 | 25.74% |
| General | 1,909 | 25.23% |
| Price | 1,768 | 23.37% |
| Fashion | 1,600 | 21.15% |
| App | 1,444 | 19.09% |
| Electronics | 1,372 | 18.14% |
| Ship | 1,249 | 16.51% |

## Common Multi-Aspect Combinations

| Combo | Count | Share |
|---|---:|---:|
| Electronics + Price | 410 | 5.42% |
| Electronics + Service | 351 | 4.64% |
| Fashion + Price | 281 | 3.71% |
| General + Ship | 262 | 3.46% |
| App + Electronics | 202 | 2.67% |
| General + Service | 188 | 2.49% |
| App + Ship | 171 | 2.26% |
| General + Price | 149 | 1.97% |
| Electronics + Price + Service | 115 | 1.52% |
| Fashion + Service | 112 | 1.48% |

Đánh giá:
- Các combo mạnh nhất gần như giữ nguyên so với `v4`.
- Batch augment mới không làm giàu thêm combo landscape, vì nó chủ yếu đắp vào 3 ô đơn lẻ.

## Contrast Pair Strength

| Contrast pair | Count |
|---|---:|
| Fashion vs Price | 238 |
| App vs Ship | 149 |
| Electronics vs Service | 126 |
| General vs Ship | 99 |
| App vs Price | 45 |
| Electronics vs Price | 43 |
| General vs Price | 36 |
| App vs Service | 32 |
| Price vs Service | 26 |
| App vs Electronics | 24 |

Đánh giá:
- Contrast strength gần như không đổi so với `v4`.
- `v5` giải quyết tốt balance của single-cell, nhưng chưa giải quyết thêm long-tail contrast pairs.

## Target Distribution And Lexical Concentration

### Top Targets Overall

| Target | Count |
|---|---:|
| shop | 816 |
| giá | 740 |
| áo | 646 |
| hàng | 488 |
| app | 445 |
| nhân_viên | 426 |
| giao | 395 |
| ứng_dụng | 394 |
| tầm_giá | 362 |
| pin | 332 |

### Target Concentration By Aspect

| Aspect | Most frequent target | Count | Share inside aspect |
|---|---|---:|---:|
| Service | shop | 816 | 41.91% |
| Price | giá | 740 | 41.86% |
| Fashion | áo | 646 | 40.38% |
| Ship | giao | 395 | 31.63% |
| App | app | 445 | 30.82% |
| General | hàng | 488 | 25.56% |
| Electronics | pin | 332 | 24.20% |

Đánh giá:
- Target vocabulary đã thống nhất nhưng lexical concentration vẫn cao.
- Đây là rủi ro còn lại lớn hơn target-noise: model có thể học shortcut `shop -> Service`, `giá -> Price`, `áo -> Fashion`, `giao -> Ship`.

## Target Normalization Outcome

Số liệu:
- `274` raw target forms
- `274` normalized target forms
- `0` variant groups còn sót lại

Ý nghĩa:
- Không còn tình trạng cùng một target tồn tại song song ở dạng `space`, `_`, hoặc viết hoa khác nhau.
- Đây là cải thiện quan trọng nhất của `v5` so với `v4` ở tầng annotation surface form.

## Length Tail Review

Số liệu:
- `246` record có độ dài từ `60` token trở lên.
- Record dài nhất đạt `194` token.

Rủi ro:
- Review dài vẫn là nguồn nhiễu context cho span sentiment.
- Tuy nhiên, tail dài này không tăng so với `v4`, nên đây không phải regression của `v5`.

## Overall Assessment

### What Is Better Than V4

- Target surface form đã được chuẩn hóa hoàn chỉnh.
- `App-Neu`, `Ship-Pos`, `Ship-Neu` tăng rõ.
- Aspect distribution cân hơn.
- `Ship` và `App` mạnh hơn trước ở tầng sentiment balance.
- Validation cuối giữ lại gần như toàn bộ dữ liệu hợp lệ.

### What Is Still Imperfect

- `E5` heuristic warnings vẫn cao.
- `Fashion` và `General` còn bias `Neg`.
- Contrast pair tail chưa được tăng thêm.
- Lexical concentration vẫn mạnh ở một số aspect chính.
- Tỷ lệ record single-opinion tăng lên, nên lợi ích multi-aspect không tăng theo cùng nhịp với sentiment balance.

## Final Verdict

`data_train_v5` là bản dataset tốt hơn `data_train_v4` để train tiếp.

Mức đánh giá:
- **Structure quality**: tốt
- **Target normalization quality**: rất tốt
- **Label balance**: khá tốt
- **Weak-cell recovery**: tốt
- **Contrast readiness**: trung bình, không tăng thêm đáng kể so với `v4`
- **Training readiness**: đạt

Nếu phải chọn một bản duy nhất để train tiếp ở thời điểm hiện tại, nên chọn `data_train_v5.jsonl`.

## Priority Recommendations For A Future V6

1. Tăng contrast cho các cặp yếu thay vì tiếp tục bơm single-opinion cells.
2. Giảm lexical concentration bằng cách đa dạng hóa target trong `Service`, `Price`, `Fashion`, `Ship`.
3. Rà lại nhóm review dài để giảm nhiễu context cho sentiment head.
4. Nếu augment tiếp, ưu tiên multi-aspect sentences thay vì chỉ bù từng ô đơn lẻ.
5. Giữ nguyên chuẩn target underscore cho toàn bộ pipeline từ đây trở đi.
